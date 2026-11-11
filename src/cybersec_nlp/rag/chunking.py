"""Sentence-aware chunking with a token budget and a one-sentence overlap (Notebook 4A, Membre 5)."""

from __future__ import annotations

import re
from collections.abc import Callable

TokenCounter = Callable[[str], int]
_BOUNDARY = re.compile(r"(?<=[.!?])\s+|\n+")


def word_count(text: str) -> int:
    return len(text.split())


def _split_long_word(word: str, budget: int, count: TokenCounter) -> list[str]:
    pieces, start = [], 0
    while start < len(word):
        end = min(len(word), start + budget)
        while count(word[start:end]) > budget and end > start + 1:
            end -= 1
        pieces.append(word[start:end])
        start = end
    return pieces


def _units(text: str, budget: int, count: TokenCounter) -> list[str]:
    """Sentences, with sentences longer than the budget split on words."""
    units = []
    for segment in _BOUNDARY.split(text.strip()):
        segment = " ".join(segment.split())
        if not segment:
            continue
        if count(segment) <= budget:
            units.append(segment)
            continue
        words = [p for w in segment.split() for p in (_split_long_word(w, budget, count) if count(w) > budget else [w])]
        pending: list[str] = []
        for word in words:
            if pending and count(" ".join([*pending, word])) > budget:
                units.append(" ".join(pending))
                pending = []
            pending.append(word)
        if pending:
            units.append(" ".join(pending))
    return units


def chunk_document(text: str, budget: int = 120, count: TokenCounter = word_count) -> list[str]:
    """Group sentences up to ``budget`` tokens; repeat the last short sentence as overlap."""
    chunks: list[str] = []
    current: list[str] = []
    for unit in _units(text, budget, count):
        if current and count(" ".join([*current, unit])) > budget:
            chunks.append(" ".join(current))
            overlap = current[-1]
            keep = count(overlap) <= budget // 4 and count(f"{overlap} {unit}") <= budget
            current = [overlap] if keep else []
        current.append(unit)
    if current:
        chunks.append(" ".join(current))
    return chunks
