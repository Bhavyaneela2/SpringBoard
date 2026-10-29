from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
import streamlit as st

from backend.reports import json_report, markdown_report
from frontend.uploads import decode_uploaded_source, upload_digest

st.set_page_config(page_title="Sentinel Review", layout="wide", initial_sidebar_state="expanded")
API_URL = os.getenv("CODE_REVIEW_API", "http://127.0.0.1:8000")
SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO")


def init_state() -> None:
    defaults = {"review_result": None, "submission_id": None, "history": [], "assistant_messages": []}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
        :root { --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --soft:#f8fafc; --blue:#2563eb; --indigo:#6366f1; }
        .stApp { background:#f8fafc; color:var(--ink); font-family:'Inter',system-ui,sans-serif; }
        [data-testid="stSidebar"] { background:#ffffff; border-right:1px solid #e2e8f0; box-shadow:4px 0 18px #0f172a08; }
        .brand-block { padding:.35rem .2rem 1rem; }
        .brand-title { color:#111827; font-family:'Inter',system-ui,sans-serif; font-size:24px; font-weight:800; letter-spacing:-.035em; line-height:1.2; margin:0; }
        .brand-subtitle { color:#64748b; font-size:.78rem; font-weight:500; line-height:1.45; margin:.35rem 0 0; }
        [data-testid="stSidebar"] [data-testid="stRadio"] > div { gap:.25rem; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label { border-radius:9px; padding:.55rem .7rem; color:#334155; font-size:1rem; font-weight:500; transition:background .15s ease,color .15s ease; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#eff6ff; color:var(--blue); }
        [data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child { display:none; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) { background:#eff6ff; color:#2563eb; font-weight:700; }
        h1,h2,h3 { color:var(--ink); letter-spacing:-.03em; }
        h1 { font-size:2rem; } h2 { font-size:1.35rem; } h3 { font-size:1.05rem; }
        p, label, [data-testid="stCaptionContainer"] { color:#475569; }
        .eyebrow { color:var(--blue); text-transform:uppercase; letter-spacing:.14em; font-size:.75rem; font-weight:700; }
        .hero { padding:1.65rem 1.8rem; border:1px solid #dbeafe; border-radius:16px; background:#ffffff; box-shadow:0 8px 24px #0f172a0b; }
        .hero h1 { margin:.25rem 0 .45rem; font-size:2.2rem; color:var(--ink); }
        .hero p { color:var(--muted); margin:0; max-width:760px; font-size:1rem; }
        .metric-card { background:#ffffff; border:1px solid var(--line); border-radius:14px; padding:1.05rem 1.15rem; min-height:112px; box-shadow:0 4px 14px #0f172a08; }
        .metric-label { color:var(--muted); font-size:.8rem; text-transform:uppercase; letter-spacing:.07em; font-weight:600; }
        .metric-value { color:var(--ink); font-size:2rem; font-weight:700; margin-top:.3rem; }
        .metric-note { color:#94a3b8; font-size:.8rem; }
        .status-pill { display:inline-block; padding:.3rem .72rem; border-radius:999px; font-size:.78rem; font-weight:700; background:#dbeafe; color:#1d4ed8; }
        .status-pill.good { background:#dcfce7; color:#15803d; }
        .status-pill.warn { background:#fef3c7; color:#b45309; }
        .section-card { background:#ffffff; border:1px solid var(--line); border-radius:14px; padding:1.25rem; box-shadow:0 5px 18px #0f172a08; }
        .stButton > button { border-radius:9px; border:1px solid #cbd5e1; color:#334155; background:#ffffff; font-weight:600; min-height:2.5rem; transition:all .15s ease; }
        [data-testid="stSidebar"] .stButton > button { background:#2563eb; border-color:#2563eb; color:#ffffff; }
        [data-testid="stSidebar"] .stButton > button:hover { background:#1d4ed8; border-color:#1d4ed8; color:#ffffff; }
        .stButton > button:hover { border-color:var(--blue); color:var(--blue); box-shadow:0 3px 10px #2563eb1c; }
        .stButton > button[kind="primary"] { background:linear-gradient(90deg,#2563eb,#6366f1); color:#ffffff; border:0; box-shadow:0 5px 14px #2563eb33; }
        .stTextInput input, .stTextArea textarea, [data-baseweb="select"] > div { background:#ffffff; color:var(--ink); border-color:#cbd5e1; border-radius:9px; }
        .stTextArea textarea { font-family:'JetBrains Mono',monospace !important; font-size:.9rem; line-height:1.6; }
        code, pre { font-family:'JetBrains Mono',monospace !important; }
        [data-testid="stFileUploader"] { border:1px dashed #93c5fd; border-radius:12px; padding:.45rem; background:#eff6ff; }
        [data-testid="stExpander"] { background:#ffffff; border:1px solid var(--line); border-radius:11px; margin:.5rem 0; }
        [data-testid="stMetric"] { background:#ffffff; border:1px solid var(--line); border-radius:12px; padding:.8rem; }
        [data-testid="stMetricValue"] { color:var(--ink); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def metric(label: str, value: int, note: str) -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def current_findings() -> list[dict[str, Any]]:
    return (st.session_state.get("review_result") or {}).get("findings", [])


def render_finding(finding: dict[str, Any], language: str) -> None:
    severity = finding.get("severity", "INFO")
    title = finding.get("title", "Finding")
    with st.expander(f"{severity}  ·  {title}  ·  line {finding.get('line', '?')}"):
        st.caption(f"{finding.get('agent', 'Agent')}  •  {finding.get('category', 'Category')}  •  {finding.get('rule_id', '')}")
        st.write(finding.get("explanation", finding.get("message", "")))
        st.code(finding.get("evidence", ""), language=None)
        cols = st.columns(2)
        with cols[0]:
            st.markdown("**Impact**")
            st.write(finding.get("why_it_matters", finding.get("impact", "")))
        with cols[1]:
            st.markdown("**Recommended remediation**")
            st.write(finding.get("recommendation", ""))
        st.markdown("**Suggested corrected example**")
        st.code(finding.get("corrected_code") or "No corrected example was generated.", language=language)


def render_findings(findings: list[dict[str, Any]], language: str, title: str = "Findings") -> None:
    st.subheader(f"{title} · {len(findings)}")
    if not findings:
        st.success("No findings detected by the configured checks. This does not prove the code is secure.")
        return
    c1, c2, c3, c4 = st.columns([1, 1.3, 1.5, 2])
    severity = c1.selectbox("Severity", ["All", *SEVERITIES], key=f"{title}_severity")
    category_values = sorted({str(item.get("category", "Unknown")) for item in findings})
    category = c2.selectbox("Category", ["All", *category_values], key=f"{title}_category")
    agent_values = sorted({str(item.get("agent", "Unknown")) for item in findings})
    agent = c3.selectbox("Agent", ["All", *agent_values], key=f"{title}_agent")
    search = c4.text_input("Search findings", key=f"{title}_search", placeholder="SQL injection, line, rule...")
    visible = [
        item for item in findings
        if (severity == "All" or item.get("severity") == severity)
        and (category == "All" or item.get("category") == category)
        and (agent == "All" or item.get("agent") == agent)
        and (not search.strip() or search.lower() in str(item).lower())
    ]
    for finding in visible:
        render_finding(finding, language)
    if not visible:
        st.info("No findings match the selected filters.")


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            '<div class="brand-block"><div class="brand-title">Sentinel Review</div>'
            '<div class="brand-subtitle">AI Code Review &amp; Security Analysis</div></div>',
            unsafe_allow_html=True,
        )
        pages = {
            "Overview": "Overview",
            "Code Review": "Code Review",
            "Security Findings": "Security Findings",
            "Remediation": "Remediation",
            "PR Summary": "PR Summary",
            "AI Code Assistant": "AI Code Assistant",
            "Reports": "Reports",
            "Knowledge Base": "Knowledge Base",
        }
        selected = st.radio("Workspace", list(pages), label_visibility="collapsed")
        if st.button("New code review", use_container_width=True):
            st.session_state["review_result"] = None
            st.session_state["submission_id"] = None
            st.rerun()
        st.divider()
        st.markdown('<span class="status-pill good">● System operational</span>', unsafe_allow_html=True)
        st.caption(f"API · {API_URL}")
        if st.button("Check backend connection", use_container_width=True):
            try:
                response = requests.get(f"{API_URL}/health", timeout=3)
                st.success("Backend connected." if response.ok else f"Backend returned {response.status_code}")
            except requests.RequestException as exc:
                st.error(f"Backend unavailable: {exc}")
    return pages[selected]


def render_overview() -> None:
    history = st.session_state["history"]
    total_findings = sum(item["total"] for item in history)
    critical_high = sum(item["critical_high"] for item in history)
    quality = sum(item["quality"] for item in history)
    security = sum(item["security"] for item in history)
    st.markdown('<div class="hero"><div class="eyebrow">SECURE CODE REVIEW PLATFORM</div><h1>Review code with confidence.</h1><p>Upload Python or Java source, run parallel quality and security checks, and turn findings into an actionable review.</p></div>', unsafe_allow_html=True)
    st.write("")
    cards = st.columns(4)
    with cards[0]: metric("Files analyzed", len(history), "This session")
    with cards[1]: metric("Total findings", total_findings, "Across analyzed files")
    with cards[2]: metric("Critical / high", critical_high, "Needs attention")
    with cards[3]: metric("Security findings", security, "Heuristic signals")
    st.write("")
    left, right = st.columns([1.5, 1])
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Severity distribution")
        distribution = {severity: sum(item["severity_counts"].get(severity, 0) for item in history) for severity in SEVERITIES}
        st.bar_chart(distribution, height=245, color="#62a5ff")
        st.caption("Only completed analyses in this browser session are included.")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Workspace health")
        st.write(f"**Code quality signals:** {quality}")
        st.write(f"**Security signals:** {security}")
        st.write("**Resolved issues:** Not tracked")
        st.caption("Resolution is not reported until a verified persistence workflow exists.")
        if st.button("Start a new code review", type="primary", use_container_width=True):
            st.session_state["review_result"] = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    if history:
        st.subheader("Recent analysis history")
        st.dataframe(history, use_container_width=True, hide_index=True)
    else:
        st.info("No analyses yet. Open Code Review to upload a source file and begin.")


def render_code_review() -> None:
    st.markdown('<div class="eyebrow">CODE REVIEW</div>', unsafe_allow_html=True)
    st.title("Analyze a source file")
    st.caption("Upload a .py or .java file, or paste source code. The language is detected automatically and submitted code is never executed.")
    uploaded = st.file_uploader("Drop source file here", type=["py", "java"], key="source_upload")
    default_code = st.session_state.get("source_editor_paste", "")
    filename = "pasted_source.py"
    upload_error = None
    if uploaded is not None:
        filename = uploaded.name
        try:
            raw = uploaded.getvalue()
            code_text = decode_uploaded_source(filename, raw)
            editor_key = f"source_editor_upload_{upload_digest(filename, raw)}"
        except ValueError as exc:
            code_text, editor_key, upload_error = "", "source_editor_invalid", str(exc)
    else:
        code_text, editor_key = default_code, "source_editor_paste"
    if upload_error:
        st.error(upload_error)
    file_size = len(code_text.encode("utf-8")) if code_text else 0
    suffix = Path(filename).suffix.lower()
    detected_label = {"py": "Python", "java": "Java"}.get(suffix.lstrip("."), "Detected from source")
    st.caption(f"**{filename}**  ·  {file_size:,} bytes  ·  Detected language: **{detected_label}**")
    code_text = st.text_area("Source editor", value=code_text, height=390, key=editor_key, placeholder="Paste Python or Java source here...")
    if st.button("🔍  Analyze Code", type="primary", use_container_width=True):
        if upload_error or not code_text.strip():
            st.error("Analysis was not started because the submitted source is invalid or empty.")
            return
        with st.spinner("Running Code Analysis and Security Vulnerability agents in parallel..."):
            try:
                response = requests.post(f"{API_URL}/analyze", json={"filename": filename, "code": code_text}, timeout=45)
                try:
                    payload = response.json()
                except ValueError:
                    payload = {"detail": response.text or "The backend returned an invalid response."}
                if response.status_code >= 400:
                    st.error(f"Analysis failed ({response.status_code}): {payload.get('detail', payload)}")
                    return
                if not isinstance(payload, dict) or "findings" not in payload:
                    st.error("Analysis failed: the backend response did not contain findings.")
                    return
                st.session_state["review_result"] = payload
                submission_id = upload_digest(filename, code_text.encode("utf-8"))
                st.session_state["submission_id"] = submission_id
                if not any(item["id"] == submission_id for item in st.session_state["history"]):
                    findings = payload.get("findings", [])
                    st.session_state["history"].append({
                        "id": submission_id, "file": filename, "language": payload.get("language", "unknown"),
                        "total": len(findings), "critical_high": sum(f.get("severity") in {"CRITICAL", "HIGH"} for f in findings),
                        "quality": sum(f.get("agent") == "Code Analysis Agent" for f in findings),
                        "security": sum(f.get("agent") == "Security Vulnerability Agent" for f in findings),
                        "severity_counts": payload.get("severity_counts", {}),
                    })
                st.success("Analysis completed successfully.")
            except requests.RequestException as exc:
                st.error(f"Analysis service is unavailable: {exc}")
    result = st.session_state.get("review_result")
    if result:
        render_results(result)


def render_results(result: dict[str, Any]) -> None:
    language = result.get("language", "unknown")
    st.divider()
    st.subheader(f"Latest review · {language.title()}")
    validation = result.get("validation", {})
    (st.success if validation.get("valid") else st.error)(validation.get("message", "Validation completed"))
    for warning in result.get("warnings", []):
        st.warning(warning)
    counts = result.get("severity_counts", {})
    cards = st.columns(5)
    for card, severity in zip(cards, SEVERITIES):
        with card:
            metric(severity.title(), counts.get(severity, 0), "Current review")
    findings = result.get("findings", [])
    render_findings(findings, language)


def render_pr_summary() -> None:
    result = st.session_state.get("review_result")
    if not result:
        st.info("Run an analysis to generate a pull-request summary.")
        return
    summary = result.get("pr_summary", {})
    st.markdown('<div class="eyebrow">PR SUMMARY AGENT</div>', unsafe_allow_html=True)
    st.title(summary.get("title", "Pull-request review"))
    st.success(summary.get("verdict", "Review completed"))
    a, b = st.columns(2)
    with a:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Quality assessment")
        st.write(summary.get("quality_assessment", ""))
        st.subheader("Security assessment")
        st.write(summary.get("security_assessment", ""))
        st.markdown("</div>", unsafe_allow_html=True)
    with b:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Critical issues")
        for issue in summary.get("critical_issues", []) or ["None detected by configured checks"]:
            st.write(f"• {issue}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.subheader("Prioritized remediation roadmap")
    for step in summary.get("roadmap", []):
        st.write(step)
    st.download_button("Download summary as Markdown", markdown_report(result), "pr_summary.md", "text/markdown")


def render_assistant() -> None:
    st.markdown('<div class="eyebrow">AI CODE ASSISTANT</div>', unsafe_allow_html=True)
    st.title("Ask about your review")
    st.caption("Answers are grounded in the secure-coding knowledge base and the current findings when available.")
    for message in st.session_state["assistant_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Ask about SQL injection, a finding, or a secure-coding practice...")
    if question:
        st.session_state["assistant_messages"].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Retrieving secure-coding guidance..."):
                try:
                    response = requests.post(f"{API_URL}/ask", json={"question": question, "findings": current_findings()}, timeout=45)
                    response.raise_for_status()
                    answer = response.json()
                    content = answer.get("answer", "No answer returned.")
                    st.markdown(content)
                    for source in answer.get("sources", []):
                        st.caption(f"Source: {source.get('source')} · chunk {source.get('chunk')}")
                    st.session_state["assistant_messages"].append({"role": "assistant", "content": content})
                except requests.RequestException as exc:
                    st.error(f"Assistant unavailable: {exc}")


def render_reports() -> None:
    result = st.session_state.get("review_result")
    st.markdown('<div class="eyebrow">REPORTS</div>', unsafe_allow_html=True)
    st.title("Exportable review artifacts")
    if not result:
        st.info("Run an analysis to create JSON and Markdown reports.")
        return
    st.download_button("Download JSON report", json_report(result), "code_review_report.json", "application/json", use_container_width=True)
    st.download_button("Download Markdown report", markdown_report(result), "code_review_report.md", "text/markdown", use_container_width=True)
    st.caption("Reports contain the actual findings from the current analysis.")


def render_knowledge_base() -> None:
    from backend.knowledge import CHROMA_PATH, KB_DIR
    st.markdown('<div class="eyebrow">KNOWLEDGE BASE</div>', unsafe_allow_html=True)
    st.title("Secure-coding references")
    documents = sorted(KB_DIR.glob("*.md"))
    st.write(f"**{len(documents)}** Markdown documents available")
    for document in documents:
        with st.expander(document.name):
            st.markdown(document.read_text(encoding="utf-8"))
    st.caption(f"Persistent vector index: `{CHROMA_PATH}`")
    if st.button("Rebuild knowledge index"):
        try:
            with st.spinner("Rebuilding embeddings and vector index..."):
                response = requests.post(f"{API_URL}/rag/reindex", timeout=120)
            if response.ok:
                st.success("Knowledge index rebuilt successfully.")
            else:
                st.error(f"Index rebuild failed: {response.text}")
        except requests.RequestException as exc:
            st.error(f"Index rebuild unavailable: {exc}")


init_state()
inject_styles()
page = render_sidebar()
if page == "Overview":
    render_overview()
elif page == "Code Review":
    render_code_review()
elif page == "Security Findings":
    result = st.session_state.get("review_result")
    render_findings([f for f in (result or {}).get("findings", []) if f.get("agent") == "Security Vulnerability Agent"], (result or {}).get("language", "python"), "Security Findings")
elif page == "Remediation":
    result = st.session_state.get("review_result")
    if result:
        render_findings(result.get("findings", []), result.get("language", "python"), "Remediation Workspace")
    else:
        st.info("Run an analysis to populate remediation guidance.")
elif page == "PR Summary":
    render_pr_summary()
elif page == "AI Code Assistant":
    render_assistant()
elif page == "Reports":
    render_reports()
elif page == "Knowledge Base":
    render_knowledge_base()
