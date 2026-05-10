"""Preload the summarization model into the local cache."""

from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from backend.config import get_settings


def main() -> None:
    settings = get_settings()
    settings.model_cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading model: {settings.model_name}")
    AutoTokenizer.from_pretrained(settings.model_name, cache_dir=str(settings.model_cache_dir))
    AutoModelForSeq2SeqLM.from_pretrained(settings.model_name, cache_dir=str(settings.model_cache_dir))
    print(f"Model cached at: {settings.model_cache_dir}")


if __name__ == "__main__":
    main()
