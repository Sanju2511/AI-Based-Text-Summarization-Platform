"""Configuration helpers for the summarization app."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    app_name: str = "AI-Based Text Summarization Platform"
    model_name: str = os.getenv("SUMMARIZER_MODEL_NAME", "sshleifer/distilbart-cnn-12-6")
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "8"))
    max_input_chars: int = int(os.getenv("MAX_INPUT_CHARS", "20000"))
    summary_min_length: int = int(os.getenv("SUMMARY_MIN_LENGTH", "60"))
    summary_max_length: int = int(os.getenv("SUMMARY_MAX_LENGTH", "220"))
    model_cache_dir: Path = Path(os.getenv("MODEL_CACHE_DIR", str(BASE_DIR / "models" / "hf_cache")))
    output_dir: Path = BASE_DIR / "outputs" / "generated"
    allowed_extensions: tuple[str, ...] = (".pdf",)
    allow_model_download: bool = os.getenv("ALLOW_MODEL_DOWNLOAD", "0").lower() in {"1", "true", "yes"}


def get_settings() -> Settings:
    return Settings()
