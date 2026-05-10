"""PDF export helpers."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def build_summary_pdf(title: str, source_name: str, summary: str, keywords: list[str], engine_used: str) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=LETTER, title=title)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        leading=16,
        spaceAfter=8,
    )

    story = [
        Paragraph(title, title_style),
        Spacer(1, 8),
        Paragraph(f"<b>Source:</b> {source_name}", body_style),
        Paragraph(f"<b>Engine:</b> {engine_used}", body_style),
        Spacer(1, 10),
        Paragraph("<b>Summary</b>", styles["Heading2"]),
    ]

    for line in summary.splitlines():
        story.append(Paragraph(line.replace("&", "&amp;"), body_style))

    if keywords:
        story.extend(
            [
                Spacer(1, 10),
                Paragraph("<b>Keywords</b>", styles["Heading2"]),
                Paragraph(", ".join(keywords), body_style),
            ]
        )

    document.build(story)
    return buffer.getvalue()

