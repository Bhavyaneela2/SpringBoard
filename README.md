# Smart Code Inspection Platform with Vulnerability Detection System

An original educational starter implementation for reviewing Python and Java source code. It includes:
- Streamlit developer portal
- FastAPI backend
- Python syntax validation
- Java syntax-check attempt when `javac` is installed
- Built-in heuristic code-quality/security checks
- Severity-scored findings and remediation guidance
- Pull-request-style review summary
- RAG assistant with markdown chunking, Sentence Transformers embeddings, persistent Chroma vector search, source metadata, and optional OpenAI grounded answer generation
- JSON report export from the interface

## Important scope notes
This is a working starter / academic prototype, not a replacement for a professional SAST product. Built-in checks are heuristic and can miss issues or flag false positives. Java syntax checking is only available if a JDK (`javac`) is installed. The assistant builds a persistent Chroma vector index from the local secure-coding knowledge base using Sentence Transformers embeddings. Semantic retrieval works without an LLM API; setting `OPENAI_API_KEY` enables optional grounded answer generation with the OpenAI API. The first index build downloads the embedding model and may require internet access. If no API key is configured, the app displays retrieved passages rather than pretending an LLM generated the answer.

The source files were written specifically for this project and are not copied from a third-party project. No tool can guarantee a universal "0% plagiarism" result; run your institution's checker and cite any external standards or libraries used in your report.

## Requirements
- Python 3.10+
- Windows, macOS, or Linux
- Optional: JDK 17+ for Java syntax validation

## Run on Windows (VS Code)
1. Extract the ZIP.
2. Open the extracted `Smart_Code_Inspection_Platform` folder in VS Code.
3. Open Terminal > New Terminal.
4. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt:

   ```bat
   .venv\Scripts\activate.bat
   ```

5. Install packages:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

6. Start the backend in Terminal 1:

   ```powershell
   uvicorn backend.main:app --reload
   ```

   API documentation: http://127.0.0.1:8000/docs

7. Start the UI in Terminal 2 (activate the same environment first):

   ```powershell
   streamlit run frontend/app.py
   ```

   The portal normally opens at http://localhost:8501.

The UI detects Python or Java from the uploaded `.py`/`.java` extension or recognizable source syntax; there is no manual language selector. The backend never executes submitted source.

The Streamlit workspace provides Overview, Code Review, Security Findings, Remediation, PR Summary, AI Code Assistant, Reports, and Knowledge Base pages. Dashboard totals and history are based only on completed analyses in the current browser session; resolved-issue counts are intentionally not shown because resolution is not persisted.

## Run on macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload
```
In a second terminal:
```bash
source .venv/bin/activate
streamlit run frontend/app.py
```

## Configure and run the RAG assistant

1. The first `/ask` request automatically chunks every Markdown file in `knowledge_base/`, embeds the chunks, and stores them in `data/chroma`. The bundled knowledge base includes general secure-coding notes, Java guidance, Python guidance, and an OWASP Top 10 educational summary; it does not require a separate SQL-only document. The embedding model defaults to `sentence-transformers/all-MiniLM-L6-v2`.
2. Optional: set an OpenAI key in the same PowerShell terminal before starting the backend:

   ```powershell
   $env:OPENAI_API_KEY = "your-api-key"
   $env:OPENAI_MODEL = "gpt-4o-mini"
   ```

   Do not commit the key to source control. Without a key, semantic vector retrieval still works and the assistant shows relevant passages.
3. If you add or edit Markdown files in `knowledge_base/`, rebuild the index by calling `POST http://127.0.0.1:8000/rag/reindex` (for example, from `/docs`). The index is also automatically rebuilt when the source file fingerprint changes on a fresh RAG initialization.
4. `POST /ask` returns `retrieval`, `generation`, and `sources` metadata so the UI/API can identify how the answer was produced.

Copy `.env.example` to `.env` as a reference for optional configuration. Keep real credentials in the process environment and never commit them.

## Run tests

From the project root with the virtual environment active:

```powershell
python -m unittest discover -s tests -v
```

The RAG unit tests mock the vector retrieval/model layer, so they do not need a network connection or API key. End-to-end semantic search requires installing the dependencies and downloading the embedding model on first use.

## Test via API
Open `/docs`, choose `POST /analyze`, and send:
```json
{
  "filename": "sample.py",
  "code": "import sqlite3\nuser = input()\nquery = \"SELECT * FROM users WHERE name = '\" + user + \"'\""
}
```

## Project structure
```
backend/
  __init__.py
  main.py            FastAPI endpoints
  analyzer.py        syntax validation and built-in checks
  agents.py          remediation and PR summary helpers
  knowledge.py       chunking, embedding, Chroma vector retrieval, optional grounded LLM generation
frontend/
  app.py             Streamlit developer portal
knowledge_base/
  secure_coding.md          general secure-coding notes
  java_secure_coding.md     Java secure-coding guidance
  python_secure_coding.md   Python secure-coding guidance
  owasp_top_10.md           OWASP Top 10 educational summary
samples/
  vulnerable_example.py
  clean_example.py
tests/
  test_analyzer.py
```

## Workflow
1. User pastes or uploads `.py` / `.java` source.
2. API validates language and syntax where supported.
3. Static heuristic rules identify likely security and quality issues.
4. Findings receive severity, line number, rule ID, explanation and remediation.
5. Summary helper produces a PR-style overview.
6. RAG helper retrieves semantically relevant secure-coding passages using embeddings and Chroma; optional OpenAI generation answers from retrieved context.
7. User can download a JSON report.

## Limitations and safety
- Never upload secrets or confidential source code to a service you do not control.
- Uploaded code is analyzed as text; the app does not execute the submitted program.
- The Java syntax check uses a temporary file and invokes `javac` only if available. Do not treat compilation as a security sandbox.
- Findings are indicative and should be verified by a developer.
