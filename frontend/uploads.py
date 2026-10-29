"""Pure helpers for validating and decoding uploaded source files."""
from __future__ import annotations

import hashlib
from pathlib import Path

MAX_UPLOAD_BYTES = 300_000
SUPPORTED_EXTENSIONS = {".py", ".java"}


def upload_digest(filename: str, content: bytes) -> str:
    return hashlib.sha256(filename.encode("utf-8") + b"\0" + content).hexdigest()[:16]


def decode_uploaded_source(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload a Python (.py) or Java (.java) source file.")
    if not content:
        raise ValueError("The uploaded file is empty. Select a source file containing code.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("The uploaded file exceeds the 300 KB size limit.")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("The uploaded file is not valid UTF-8 text.") from exc
