"""Safe, text-only source validation and deterministic inspection agents."""
from __future__ import annotations

import ast
import logging
import re
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

SUPPORTED = {"python", "java"}
MAX_SOURCE_BYTES = 300_000
SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
logger = logging.getLogger(__name__)

SECURITY_RULES = [
    ("SEC001", "HIGH", "Possible SQL injection", [r"""(?:execute|executemany)\s*\(\s*["'][^"']*(?:SELECT|INSERT|UPDATE|DELETE)[^"']*["']\s*\+""", r"""(?:query|sql)\s*=\s*(?:"[^"]*(?:SELECT|INSERT|UPDATE|DELETE)[^"]*"|'[^']*(?:SELECT|INSERT|UPDATE|DELETE)')\s*\+""", r"""execute\s*\(\s*f["'].*(?:SELECT|INSERT|UPDATE|DELETE)"""], "SQL text may be assembled using string concatenation or interpolation.", "Use parameterized queries/prepared statements and pass values separately.", "SQL injection"),
    ("SEC002", "HIGH", "Possible hardcoded secret", [r"""(?i)\b(?:password|passwd|api[_-]?key|secret|access[_-]?token)\b\s*=\s*["'][^"']{4,}["']"""], "A credential-like value appears to be assigned directly in source code.", "Read secrets from environment variables or a secrets manager; rotate any real exposed credential.", "Hardcoded credential"),
    ("SEC003", "MEDIUM", "Potential unsafe dynamic evaluation", [r"\beval\s*\(", r"\bexec\s*\("], "Dynamic evaluation can execute data as code when input is not trusted.", "Avoid eval/exec for user-controlled data; use explicit parsing and allow-listed operations.", "Code injection"),
    ("SEC004", "MEDIUM", "Possible insecure deserialization", [r"\bpickle\.loads?\s*\(", r"\bObjectInputStream\s*\("], "Deserializing untrusted data can lead to unsafe object construction.", "Prefer constrained formats such as JSON and validate the schema.", "Insecure deserialization"),
    ("SEC005", "MEDIUM", "Potential XSS-prone HTML output", [r"innerHTML\s*=", r"dangerouslySetInnerHTML"], "HTML is inserted directly; untrusted content may be interpreted as markup or script.", "Use safe text APIs or context-aware output encoding.", "Cross-site scripting"),
    ("SEC006", "MEDIUM", "Potential disabled TLS verification", [r"verify\s*=\s*False", r"setHostnameVerifier\s*\(\s*\(\s*host"], "TLS certificate or hostname verification appears to be disabled.", "Use the platform's default certificate and hostname verification.", "Transport security"),
]

QUALITY_RULES = [
    ("QUAL001", "LOW", "Debug print statement", [r"^\s*print\s*\(", r"System\.out\.print(?:ln)?\s*\("], "Debug output may expose details or clutter production logs.", "Use structured logging at an appropriate level.", "Maintainability"),
    ("QUAL002", "LOW", "TODO/FIXME marker", [r"\bTODO\b", r"\bFIXME\b"], "A TODO/FIXME marker may indicate unfinished work.", "Resolve the item or track it in the issue tracker.", "Maintainability"),
    ("QUAL003", "LOW", "Deeply nested conditional logic", [r"^\s{16,}(?:if|for|while|try)\b"], "Deep nesting makes control flow harder to understand and test.", "Extract smaller functions and use guard clauses.", "Complexity"),
]


def detect_language(code: str, filename: str = "") -> str | None:
    extension = Path(filename).suffix.lower()
    if extension == ".py":
        return "python"
    if extension == ".java":
        return "java"
    text = code or ""
    if re.search(r"^\s*(?:from\s+\w+\s+import|import\s+\w+|def\s+\w+\s*\()", text, re.MULTILINE):
        return "python"
    if re.search(r"\b(?:public\s+)?class\s+\w+|System\.out\.|public\s+static\s+void\s+main", text):
        return "java"
    return None


def validate_source(code: str, language: str) -> dict[str, Any]:
    language = language.lower().strip()
    if language not in SUPPORTED:
        return {"valid": False, "message": "Unsupported language. Only Python and Java are supported."}
    if not code.strip():
        return {"valid": False, "message": "The submitted source code is empty."}
    if len(code.encode("utf-8")) > MAX_SOURCE_BYTES:
        return {"valid": False, "message": "Source code exceeds the 300 KB limit."}
    if language == "python":
        try:
            ast.parse(code)
            return {"valid": True, "message": "Python syntax parsed successfully."}
        except SyntaxError as exc:
            return {"valid": False, "message": f"Python syntax error on line {exc.lineno}: {exc.msg}"}
    javac = shutil.which("javac")
    if not javac:
        return {"valid": True, "message": "Java syntax check skipped because javac is not installed; static inspection will continue."}
    with tempfile.TemporaryDirectory(prefix="code_review_") as td:
        match = re.search(r"\bpublic\s+(?:final\s+)?class\s+([A-Za-z_$][\w$]*)", code)
        path = Path(td) / f"{match.group(1) if match else 'SubmittedCode'}.java"
        path.write_text(code, encoding="utf-8")
        try:
            proc = subprocess.run([javac, str(path)], cwd=td, capture_output=True, text=True, timeout=8)
        except subprocess.TimeoutExpired:
            return {"valid": False, "message": "Java syntax check timed out."}
        if proc.returncode == 0:
            return {"valid": True, "message": "Java compilation syntax check passed."}
        output = (proc.stderr or proc.stdout).strip().splitlines()
        return {"valid": False, "message": "Java compiler reported: " + (output[0][:220] if output else "unknown compilation error")}


def _run_rules(code: str, filename: str, rules: list[tuple], agent: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for line_no, line in enumerate(code.splitlines(), start=1):
        for rule_id, severity, title, patterns, message, recommendation, category in rules:
            if any(re.search(pattern, line) for pattern in patterns):
                findings.append({
                    "rule_id": rule_id, "agent": agent, "category": category,
                    "severity": severity, "title": title, "line": line_no,
                    "file": filename, "message": message, "explanation": message,
                    "impact": "Potential issue; confirm exploitability and context during review.",
                    "recommendation": recommendation, "evidence": line.strip()[:240],
                    "confirmed": False, "corrected_code": None,
                })
    return findings


def code_analysis_agent(code: str, filename: str) -> list[dict[str, Any]]:
    return _run_rules(code, filename, QUALITY_RULES, "Code Analysis Agent")


def security_vulnerability_agent(code: str, filename: str) -> list[dict[str, Any]]:
    return _run_rules(code, filename, SECURITY_RULES, "Security Vulnerability Agent")


def analyze_agents_parallel(code: str, filename: str) -> list[dict[str, Any]]:
    findings, _ = _analyze_agents_parallel_with_warnings(code, filename)
    return findings


def _analyze_agents_parallel_with_warnings(
    code: str, filename: str
) -> tuple[list[dict[str, Any]], list[str]]:
    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="inspection-agent") as executor:
        futures = {
            "Code Analysis Agent": executor.submit(code_analysis_agent, code, filename),
            "Security Vulnerability Agent": executor.submit(security_vulnerability_agent, code, filename),
        }
        findings: list[dict[str, Any]] = []
        warnings: list[str] = []
        for agent_name, future in futures.items():
            try:
                findings.extend(future.result())
            except Exception as exc:
                logger.exception("%s failed for filename=%s", agent_name, filename)
                warnings.append(f"{agent_name} failed: {exc}")
    unique: dict[tuple[str, int, str], dict[str, Any]] = {}
    for finding in findings:
        unique[(finding["rule_id"], finding["line"], finding["evidence"])] = finding
    return sorted(unique.values(), key=lambda item: (-SEVERITY_RANK[item["severity"]], item["line"], item["rule_id"])), warnings


def analyze_code(code: str, language: str, filename: str = "submitted") -> dict[str, Any]:
    language = language.lower().strip()
    validation = validate_source(code, language)
    if not validation["valid"]:
        return {"filename": filename, "language": language, "validation": validation, "findings": [], "severity_counts": {}, "summary": "Analysis stopped because validation failed."}
    findings, warnings = _analyze_agents_parallel_with_warnings(code, filename)
    counts = {severity: sum(1 for item in findings if item["severity"] == severity) for severity in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")}
    summary = f"Inspection completed for {filename}. Found {len(findings)} potential issue(s)."
    if not findings:
        summary = f"No configured rules matched {filename}; this does not prove the code is secure."
    return {"filename": filename, "language": language, "validation": validation, "findings": findings, "severity_counts": counts, "summary": summary, "warnings": warnings}
