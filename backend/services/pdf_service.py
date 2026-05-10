"""PDF extraction and validation."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from pypdf import PdfReader

from backend.config import Settings
from backend.services.text_utils import clean_text


def validate_pdf_upload(file: UploadFile, settings: Settings) -> None:
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported for upload.",
        )


async def extract_text_from_pdf(file: UploadFile, settings: Settings) -> tuple[str, int]:
    validate_pdf_upload(file, settings)
    raw_bytes = await file.read()

    if not raw_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded PDF is empty.")

    if len(raw_bytes) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"PDF exceeds the {settings.max_upload_mb} MB upload limit.",
        )

    if not raw_bytes.startswith(b"%PDF"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is not a valid PDF.")

    try:
        reader = PdfReader(BytesIO(raw_bytes))
    except Exception as exc:  # pragma: no cover - library-specific failures
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Could not read PDF: {exc}") from exc

    if len(reader.pages) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The PDF does not contain any pages.")

    extracted_pages: list[str] = []
    for page in reader.pages[:25]:
        page_text = page.extract_text() or ""
        if page_text.strip():
            extracted_pages.append(page_text)

    text = clean_text(" ".join(extracted_pages))
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable text was found in the uploaded PDF.",
        )

    if len(text) > settings.max_input_chars:
        text = text[: settings.max_input_chars]

    return text, len(text)

