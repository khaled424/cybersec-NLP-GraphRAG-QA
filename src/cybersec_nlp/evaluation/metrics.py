"""Evaluation metrics used across notebooks and the MVP dashboard."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

_CITATION = re.compile(r"\[S(\d+)\]")


def precision_at_k(ranked: Sequence[str], relevant: set[str], k: int) -> float:
    return sum(d in relevant for d in ranked[:k]) / k


def recall_at_k(ranked: Sequence[str], relevant: set[str], k: int) -> float:
    return sum(d in relevant for d in ranked[:k]) / len(relevant) if relevant else 0.0


def reciprocal_rank(ranked: Sequence[str], relevant: set[str], k: int) -> float:
    return next((1 / i for i, d in enumerate(ranked[:k], 1) if d in relevant), 0.0)


def ndcg_at_k(ranked: Sequence[str], relevant: set[str], k: int) -> float:
    dcg = sum(1 / math.log2(i + 1) for i, d in enumerate(ranked[:k], 1) if d in relevant)
    ideal = sum(1 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal else 0.0


def dedupe(items: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(items))


def retrieval_scores(ranked: Sequence[str], relevant: set[str], k: int) -> dict[str, float]:
    ranked = dedupe(ranked)
    return {
        f"precision@{k}": precision_at_k(ranked, relevant, k),
        f"recall@{k}": recall_at_k(ranked, relevant, k),
        f"mrr@{k}": reciprocal_rank(ranked, relevant, k),
        f"ndcg@{k}": ndcg_at_k(ranked, relevant, k),
    }


def citation_validity(answer: str, n_evidence: int) -> float | None:
    """Share of citation markers that point to an existing evidence (None if no citation)."""
    cited = [int(i) for i in _CITATION.findall(answer)]
    if not cited:
        return None
    return sum(1 <= i <= n_evidence for i in cited) / len(cited)


def mean(values: Sequence[float]) -> float:
    values = [v for v in values if v is not None]
    return float(sum(values) / len(values)) if values else float("nan")
