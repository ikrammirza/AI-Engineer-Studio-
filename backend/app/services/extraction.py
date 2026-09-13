import io

from docx import Document as DocxDocument
from fastapi import HTTPException
from pypdf import PdfReader

SUPPORTED_TYPES = {
    "text/plain",
    "text/markdown",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def extract_text(raw_bytes: bytes, content_type: str) -> str:
    if content_type in ("text/plain", "text/markdown"):
        return raw_bytes.decode("utf-8")

    if content_type == "application/pdf":
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = DocxDocument(io.BytesIO(raw_bytes))
        paragraphs = [p.text for p in doc.paragraphs]
        return "\n".join(paragraphs)

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported file type: {content_type}. "
        f"Allowed: {', '.join(SUPPORTED_TYPES)}",
    )