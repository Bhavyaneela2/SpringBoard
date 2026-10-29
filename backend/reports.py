"""Export review results as stable JSON and Markdown documents."""
from __future__ import annotations

import json
from typing import Any


def markdown_report(result: dict[str, Any]) -> str:
    summary = result.get("pr_summary", {})
    lines = [
        f"# Code Review Report — {result.get('filename', 'submitted')}",
        "",
        f"- **Detected language:** {result.get('language', 'unknown')}",
        f"- **Overall result:** {summary.get('verdict', 'Not available')}",
        f"- **Total findings:** {len(result.get('findings', []))}",
        "",
        "## Severity breakdown",
        "",
    ]
    for severity, count in result.get("severity_counts", {}).items():
        lines.append(f"- **{severity.title()}:** {count}")
    lines.extend(["", "## Findings", ""])
    findings = result.get("findings", [])
    if not findings:
        lines.append("No configured rules matched. This does not prove the code is secure.")
    for finding in findings:
        lines.extend([
            f"### {finding.get('severity', 'INFO')} — {finding.get('title', 'Finding')}",
            f"- **Agent:** {finding.get('agent', 'Unknown')}",
            f"- **Location:** line {finding.get('line', '?')}",
            f"- **Category:** {finding.get('category', 'Unknown')}",
            f"- **Evidence:** `{finding.get('evidence', '')}`",
            f"- **Explanation:** {finding.get('explanation', finding.get('message', ''))}",
            f"- **Recommendation:** {finding.get('recommendation', '')}",
            "",
        ])
    lines.extend(["## Remediation roadmap", ""])
    lines.extend(f"- {item}" for item in summary.get("roadmap", []))
    return "\n".join(lines) + "\n"


def json_report(result: dict[str, Any]) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)
