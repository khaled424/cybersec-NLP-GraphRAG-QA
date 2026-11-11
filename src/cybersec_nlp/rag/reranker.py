"""Cross-encoder re-ranking of retrieval candidates.

The bi-encoder (E5 + FAISS) retrieves fast but scores the query and the passage
independently. A cross-encoder reads them **together** and ranks the top candidates more
precisely. The multilingual MS-MARCO model handles French questions over the English corpus.
Only the best chunk of the top ``k`` documents is re-scored, so the cost stays small
(~20 pairs per question).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

from cybersec_nlp import config

T = TypeVar("T")


class CrossEncoderReranker:
    def __init__(self, model_name: str = config.RERANKER_MODEL, device: str | None = None,
                 max_chars: int = 2000) -> None:
        self.model_name = model_name
        self.device = device
        self.max_chars = max_chars
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self.model_name, device=self.device)
        return self._model

    def rerank(self, query: str, items: Sequence[T], text_of: Callable[[T], str]) -> list[tuple[T, float]]:
        """Items sorted by cross-encoder relevance (highest first) with their scores."""
        if not items:
            return []
        scores = self.model.predict([(query, text_of(item)[: self.max_chars]) for item in items],
                                    show_progress_bar=False)
        return sorted(zip(items, map(float, scores)), key=lambda pair: -pair[1])
