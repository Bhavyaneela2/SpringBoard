"""Deterministic remediation and pull-request review agents."""
from collections import Counter

def remediation_agent(findings: list[dict], language: str = "python") -> list[dict]:
    """Attach actionable guidance; source snippets are never auto-modified."""
    result = []
    for finding in findings:
        item = dict(finding)
        item["remediation_status"] = "Suggested — developer review required"
        item["why_it_matters"] = item.get("impact", "The finding may affect quality or security if confirmed.")
        comment = "//" if language == "java" else "#"
        item["corrected_code"] = item.get("corrected_code") or (
            f"{comment} Apply: {item.get('recommendation', 'Review this finding.')}"
        )
        item["knowledge_base_guidance"] = f"Consult secure-coding guidance for {item.get('category', 'this issue')}."
        result.append(item)
    return result

def pr_summary_agent(filename: str, findings: list[dict]) -> dict:
    counts = Counter(f.get("severity", "INFO") for f in findings)
    if not findings:
        verdict = "No matches from the configured demo rules. Manual review and broader scanning are still recommended."
    elif counts.get("CRITICAL", 0) or counts.get("HIGH", 0):
        verdict = "Changes requested: address high-risk findings and verify fixes before merging."
    else:
        verdict = "Review recommended: assess the findings and resolve applicable issues before merging."
    security = [f for f in findings if f.get("agent") == "Security Vulnerability Agent"]
    quality = [f for f in findings if f.get("agent") == "Code Analysis Agent"]
    bullets = [f"- [{f.get('severity')}] {f.get('title')} (line {f.get('line')}): {f.get('recommendation')}" for f in findings]
    return {
        "title": f"Code review summary — {filename}",
        "verdict": verdict,
        "total_findings": len(findings),
        "severity_counts": dict(counts),
        "quality_assessment": f"{len(quality)} code-quality finding(s) require review.",
        "security_assessment": f"{len(security)} security finding(s) require verification.",
        "critical_issues": [f.get("title") for f in findings if f.get("severity") in {"CRITICAL", "HIGH"}],
        "roadmap": [
            "1. Verify and remediate Critical/High findings before merging.",
            "2. Address Medium findings and add regression tests.",
            "3. Resolve Low findings during normal maintenance.",
        ],
        "findings": bullets
    }
