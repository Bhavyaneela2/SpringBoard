"""FastAPI service for the Smart Code Inspection Platform."""
from __future__ import annotations
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any
from backend.analyzer import analyze_code, detect_language, SUPPORTED
from backend.agents import remediation_agent, pr_summary_agent
from backend.knowledge import answer_question, reindex_knowledge_base
from backend.reports import markdown_report

app = FastAPI(title="Smart Code Inspection Platform", version="1.0.0",
              description="Educational code inspection prototype. Findings are heuristic, not exhaustive.")
logger = logging.getLogger(__name__)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
                   allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])

class AnalyzeRequest(BaseModel):
    language: str | None = Field(default=None, description="Optional legacy field; language is detected automatically.")
    filename: str = "submitted"
    code: str

class AskRequest(BaseModel):
    question: str
    findings: list[dict] = Field(default_factory=list)

@app.get("/")
def root():
    return {"service": "Smart Code Inspection Platform", "status": "running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    try:
        language = detect_language(req.code, req.filename)
        if not language:
            raise HTTPException(status_code=400, detail="Could not detect Python or Java from the filename or source. Upload a .py/.java file or provide recognizable source.")
        result = analyze_code(req.code, language, req.filename)
        result["findings"] = remediation_agent(result.get("findings", []), language)
        result["pr_summary"] = pr_summary_agent(req.filename, result.get("findings", []))
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Analysis failed for filename=%s", req.filename)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc

@app.post("/report/markdown")
def report_markdown(result: dict[str, Any]):
    return {"markdown": markdown_report(result)}

@app.post("/ask")
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    return answer_question(req.question, req.findings)


@app.post("/rag/reindex")
def rag_reindex():
    """Rebuild the local vector index after updating secure_coding.md."""
    try:
        return reindex_knowledge_base()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"RAG indexing failed: {exc}") from exc
