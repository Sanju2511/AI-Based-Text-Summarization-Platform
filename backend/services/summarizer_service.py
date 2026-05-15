"""Summarization service with local-model and fallback modes."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from backend.config import Settings
from backend.services.text_utils import clean_text, format_summary, split_sentences, summarize_extractive, word_count


@dataclass
class SummarizationResult:
    summary: str
    engine_used: str
    warning: Optional[str]


class SummarizerService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._pipeline = None
        self._load_error: Optional[str] = None

    def _is_extractive_only(self) -> bool:
        return self.settings.summarizer_mode.strip().lower() == "extractive_only"

    def _load_pipeline(self) -> None:
        if self._pipeline is not None or self._load_error is not None:
            return

        if self._is_extractive_only():
            self._load_error = "The service is configured to use extractive-only summarization."
            return

        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

            self.settings.model_cache_dir.mkdir(parents=True, exist_ok=True)
            model_source = self._resolve_model_source()
            local_only = not self.settings.allow_model_download
            tokenizer = AutoTokenizer.from_pretrained(
                model_source,
                cache_dir=str(self.settings.model_cache_dir),
                local_files_only=local_only,
            )
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_source,
                cache_dir=str(self.settings.model_cache_dir),
                local_files_only=local_only,
            )
            self._pipeline = pipeline(
                "summarization",
                model=model,
                tokenizer=tokenizer,
                framework="pt",
                device=-1,
            )
        except Exception as exc:  # pragma: no cover - depends on environment/model
            self._load_error = str(exc)
            self._pipeline = None

    def _resolve_model_source(self) -> str:
        repo_dir = self.settings.model_cache_dir / f"models--{self.settings.model_name.replace('/', '--')}"
        ref_file = repo_dir / "refs" / "main"
        if ref_file.exists():
            snapshot_id = ref_file.read_text(encoding="utf-8").strip()
            snapshot_dir = repo_dir / "snapshots" / snapshot_id
            if snapshot_dir.exists():
                return str(snapshot_dir)
        return self.settings.model_name

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 1800) -> list[str]:
        sentences = split_sentences(text)
        if not sentences:
            return [text]

        chunks: list[str] = []
        current: list[str] = []
        current_len = 0
        for sentence in sentences:
            sentence_len = len(sentence)
            if current and current_len + sentence_len > chunk_size:
                chunks.append(" ".join(current))
                current = [sentence]
                current_len = sentence_len
            else:
                current.append(sentence)
                current_len += sentence_len

        if current:
            chunks.append(" ".join(current))
        return chunks

    def _transformer_summary(self, text: str, summary_size: str) -> str:
        if self._pipeline is None:
            raise RuntimeError("Summarization pipeline is unavailable.")

        length_map = {
            "short": (45, 90),
            "medium": (70, 150),
            "detailed": (110, 220),
        }
        min_length, max_length = length_map.get(summary_size, (70, 150))
        parts: list[str] = []

        for chunk in self._chunk_text(text):
            prompt_text = self._build_model_input(chunk)
            dynamic_max = min(max_length, max(40, math.ceil(len(chunk.split()) * 0.65)))
            dynamic_min = min(min_length, max(20, dynamic_max - 18))
            output = self._pipeline(
                prompt_text,
                min_length=dynamic_min,
                max_length=dynamic_max,
                do_sample=False,
                truncation=True,
            )
            parts.append(output[0]["summary_text"].strip())

        combined = " ".join(parts).strip()
        if len(parts) > 1:
            second_pass = self._pipeline(
                self._build_model_input(combined),
                min_length=min_length,
                max_length=max_length,
                do_sample=False,
                truncation=True,
            )
            return second_pass[0]["summary_text"].strip()
        return combined

    def _build_model_input(self, text: str) -> str:
        if "t5" in self.settings.model_name.lower():
            return f"summarize: {text}"
        return text

    def summarize(self, text: str, summary_size: str, output_format: str) -> SummarizationResult:
        cleaned_text = clean_text(text)
        sentence_limit_map = {
            "short": 3,
            "medium": 4,
            "detailed": 5,
        }
        sentence_limit = sentence_limit_map.get(summary_size, 4)

        if self._is_extractive_only():
            extractive_summary = summarize_extractive(cleaned_text, sentence_limit=sentence_limit + 1)
            return SummarizationResult(
                summary=format_summary(extractive_summary, output_format),
                engine_used="extractive:deployment-safe-mode",
                warning=(
                    "This deployment uses the extractive summarization mode to keep the hosted app stable on a "
                    "free cloud instance."
                ),
            )

        if word_count(cleaned_text) < 120:
            hybrid_summary = summarize_extractive(cleaned_text, sentence_limit=sentence_limit)
            return SummarizationResult(
                summary=format_summary(hybrid_summary, output_format),
                engine_used="hybrid:extractive-short-input",
                warning=None,
            )

        self._load_pipeline()

        if self._pipeline is not None:
            summary = self._transformer_summary(cleaned_text, summary_size)
            return SummarizationResult(
                summary=format_summary(summary, output_format),
                engine_used=f"huggingface:{self.settings.model_name}",
                warning=None,
            )

        fallback = summarize_extractive(cleaned_text, sentence_limit=sentence_limit + 1)
        warning = (
            "Transformer model could not be loaded, so the app used a fallback extractive summary. "
            f"Reason: {self._load_error}"
        )
        return SummarizationResult(
            summary=format_summary(fallback, output_format),
            engine_used="fallback:extractive",
            warning=warning,
        )
