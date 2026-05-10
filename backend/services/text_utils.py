"""Text utility helpers."""

from __future__ import annotations

import math
import re
from collections import Counter


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "with",
    "will",
    "can",
    "into",
    "than",
    "then",
    "them",
    "such",
    "also",
    "using",
    "used",
    "use",
    "over",
    "under",
    "more",
    "most",
}


def clean_text(raw_text: str) -> str:
    text = raw_text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+", text.strip())
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def extract_keywords(text: str, limit: int = 8) -> list[str]:
    words = re.findall(r"\b[a-zA-Z][a-zA-Z'-]{2,}\b", text.lower())
    filtered = [word for word in words if word not in STOPWORDS]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(limit)]


def format_summary(text: str, output_format: str) -> str:
    sentences = split_sentences(text)
    if output_format == "bullet":
        return "\n".join(f"- {sentence}" for sentence in sentences) if sentences else f"- {text}"
    return text


def estimate_read_time_minutes(text: str, words_per_minute: int = 200) -> float:
    words = max(word_count(text), 1)
    return round(words / words_per_minute, 2)


def summarize_extractive(text: str, sentence_limit: int = 4) -> str:
    sentences = split_sentences(text)
    if len(sentences) <= sentence_limit:
        return " ".join(sentences)

    tokens = [re.findall(r"\b[a-zA-Z][a-zA-Z'-]{2,}\b", sentence.lower()) for sentence in sentences]
    counts = Counter(word for sentence_words in tokens for word in sentence_words if word not in STOPWORDS)

    scored: list[tuple[int, float, str]] = []
    for idx, sentence in enumerate(sentences):
        sentence_words = tokens[idx]
        if not sentence_words:
            continue
        score = sum(counts[word] for word in sentence_words) / math.sqrt(len(sentence_words))
        scored.append((idx, score, sentence))

    top_sentences = sorted(sorted(scored, key=lambda item: item[1], reverse=True)[:sentence_limit], key=lambda item: item[0])
    return " ".join(sentence for _, _, sentence in top_sentences)


def build_stats(original_text: str, summary_text: str) -> dict[str, float | int]:
    original_words = word_count(original_text)
    summary_words = word_count(summary_text)
    compression_ratio = round((summary_words / original_words), 2) if original_words else 0.0
    return {
        "original_words": original_words,
        "summary_words": summary_words,
        "compression_ratio": compression_ratio,
        "estimated_read_time_minutes": estimate_read_time_minutes(summary_text),
    }

