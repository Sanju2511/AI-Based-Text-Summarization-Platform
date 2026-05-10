"""Smoke test for the summarization platform."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from backend.main import app


def build_sample_pdf() -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    lines = [
        "Project meetings generated long notes every week with decisions, blockers, and action items.",
        "The summarization platform reduces that content into concise updates for project reviews.",
        "It also extracts important terms so reviewers can scan the document faster and identify themes.",
        "This helps teams save time, improve communication, and track the most relevant next steps.",
    ]
    y = 720
    for line in lines:
        pdf.drawString(72, y, line)
        y -= 20
    pdf.save()
    return buffer.getvalue()


def main() -> None:
    client = TestClient(app)
    sample_text = (
        "Artificial intelligence is transforming education by supporting personalized learning, "
        "automating repetitive tasks, and helping teachers analyze student progress. "
        "Schools can use AI tools to identify learning gaps more quickly and recommend targeted study plans "
        "for different students. These systems can highlight performance trends and surface common mistakes. "
        "At the same time, institutions must address privacy, transparency, and bias so automated systems "
        "do not create unfair outcomes. Responsible adoption requires staff training, governance, "
        "and clear human oversight in every critical decision."
    )

    text_response = client.post(
        "/api/summarize",
        data={"input_text": sample_text, "summary_size": "medium", "output_format": "paragraph"},
    )
    assert text_response.status_code == 200, text_response.text

    pdf_response = client.post(
        "/api/summarize",
        data={"summary_size": "short", "output_format": "bullet"},
        files={"pdf_file": ("sample.pdf", build_sample_pdf(), "application/pdf")},
    )
    assert pdf_response.status_code == 200, pdf_response.text

    export_response = client.post(
        "/api/export",
        json={
            "title": "AI Summary Export",
            "source_name": "Smoke Test",
            "summary": text_response.json()["summary"],
            "keywords": text_response.json()["keywords"],
            "format": "paragraph",
            "engine_used": text_response.json()["engine_used"],
        },
    )
    assert export_response.status_code == 200, export_response.text
    assert export_response.headers["content-type"] == "application/pdf"

    print("Smoke test passed.")


if __name__ == "__main__":
    main()
