"""FastAPI entrypoint for the summarization platform."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from backend.config import BASE_DIR, get_settings
from backend.schemas import ExportRequest, SummaryResponse, SummaryStats
from backend.services.export_service import build_summary_pdf
from backend.services.pdf_service import extract_text_from_pdf
from backend.services.summarizer_service import SummarizerService
from backend.services.text_utils import build_stats, clean_text, extract_keywords


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")
summarizer = SummarizerService(settings)


@app.on_event("startup")
def ensure_output_dir() -> None:
    settings.output_dir.mkdir(parents=True, exist_ok=True)


@app.get("/")
def serve_index() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.post("/api/summarize", response_model=SummaryResponse)
async def summarize(
    input_text: str = Form(default=""),
    summary_size: str = Form(default="medium"),
    output_format: str = Form(default="paragraph"),
    pdf_file: Optional[UploadFile] = File(default=None),
) -> SummaryResponse:
    if summary_size not in {"short", "medium", "detailed"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid summary size option.")
    if output_format not in {"paragraph", "bullet"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid output format option.")

    source_type = "text"
    extracted_characters = 0

    if pdf_file is not None and pdf_file.filename:
        source_text, extracted_characters = await extract_text_from_pdf(pdf_file, settings)
        source_type = "pdf"
    else:
        source_text = clean_text(input_text)

    if not source_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide either text input or a valid PDF file.",
        )

    if len(source_text) < 80:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a longer input so the summary can be meaningful.",
        )

    if len(source_text) > settings.max_input_chars:
        source_text = source_text[: settings.max_input_chars]
        extracted_characters = len(source_text)

    result = summarizer.summarize(source_text, summary_size=summary_size, output_format=output_format)
    keywords = extract_keywords(source_text)
    stats = SummaryStats(**build_stats(source_text, result.summary))

    return SummaryResponse(
        summary=result.summary,
        format=output_format,
        source_type=source_type,
        engine_used=result.engine_used,
        keywords=keywords,
        stats=stats,
        warning=result.warning,
        extracted_characters=extracted_characters or len(source_text),
        model_name=settings.model_name,
    )


@app.post("/api/export")
async def export_summary(payload: ExportRequest) -> Response:
    pdf_bytes = build_summary_pdf(
        title=payload.title,
        source_name=payload.source_name,
        summary=payload.summary,
        keywords=payload.keywords,
        engine_used=payload.engine_used,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="summary_export.pdf"'},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
