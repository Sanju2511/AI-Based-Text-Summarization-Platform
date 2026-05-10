"""Pydantic schemas for API responses."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class SummaryStats(BaseModel):
    original_words: int = Field(ge=0)
    summary_words: int = Field(ge=0)
    compression_ratio: float = Field(ge=0)
    estimated_read_time_minutes: float = Field(ge=0)


class SummaryResponse(BaseModel):
    summary: str
    format: Literal["paragraph", "bullet"]
    source_type: Literal["text", "pdf"]
    engine_used: str
    keywords: list[str]
    stats: SummaryStats
    warning: Optional[str] = None
    extracted_characters: int = Field(ge=0)
    model_name: str


class ExportRequest(BaseModel):
    title: str = "Summary Export"
    source_name: str = "User Input"
    summary: str
    keywords: list[str] = Field(default_factory=list)
    format: Literal["paragraph", "bullet"] = "paragraph"
    engine_used: str = "unknown"
