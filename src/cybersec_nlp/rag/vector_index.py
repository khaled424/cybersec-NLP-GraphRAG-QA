"""Dense vector index (FAISS ``IndexFlatIP`` on L2-normalised vectors = cosine similarity).

Embeddings: ``intfloat/multilingual-e5-small`` (French questions over an English corpus),
which expects ``query: `` / ``passage: `` prefixes. The index and its chunk table are saved
together and reloaded as a unit.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import faiss
import numpy as np

from cybersec_nlp import config
from cybersec_nlp.rag.chunking import chunk_document


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    source: str
    text: str


class Embedder:
    """Lazy SentenceTransformer wrapper with E5 prefixes."""

    def __init__(self, model_name: str = config.EMBEDDING_MODEL, device: str | None = None) -> None:
        self.model_name = model_name
        self.device = device
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device=self.device)
        return self._model

    def token_count(self, text: str) -> int:
        return len(self.model.tokenizer.encode(text, add_special_tokens=False))

    def encode(self, texts: list[str], kind: str) -> np.ndarray:
        prefix = "query: " if kind == "query" else "passage: "
        vectors = self.model.encode([prefix + t for t in texts], batch_size=64, show_progress_bar=False,
                                    normalize_embeddings=True)
        return np.ascontiguousarray(vectors, dtype=np.float32)


class VectorIndex:
    def __init__(self, embedder: Embedder, chunks: list[Chunk], index: faiss.Index) -> None:
        self.embedder, self.chunks, self.index = embedder, chunks, index

    @classmethod
    def build(cls, documents: list[dict[str, str]], embedder: Embedder | None = None, budget: int = 200) -> VectorIndex:
        """``documents``: dicts with ``doc_id``, ``text`` and ``source`` (rag_documents.jsonl)."""
        embedder = embedder or Embedder()
        budget = min(budget, embedder.model.max_seq_length - 8)
        chunks = [
            Chunk(f"{d['doc_id']}#{i:04d}", d["doc_id"], d["source"], piece)
            for d in documents
            for i, piece in enumerate(chunk_document(d["text"], budget, embedder.token_count), 1)
        ]
        vectors = embedder.encode([c.text for c in chunks], kind="passage")
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(embedder, chunks, index)

    def search(self, query: str, k: int = 5, min_score: float = 0.0, per_document: bool = True) -> list[tuple[Chunk, float]]:
        """Top chunks; with ``per_document`` only the best chunk of each document is kept."""
        vector = self.embedder.encode([query], kind="query")
        scores, positions = self.index.search(vector, min(self.index.ntotal, k * 8 if per_document else k))
        results, seen = [], set()
        for score, pos in zip(scores[0], positions[0]):
            if pos < 0 or score < min_score:
                break
            chunk = self.chunks[int(pos)]
            if per_document and chunk.doc_id in seen:
                continue
            seen.add(chunk.doc_id)
            results.append((chunk, float(score)))
            if len(results) == k:
                break
        return results

    def save(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / "vectors.faiss"))
        meta = {"embedding_model": self.embedder.model_name, "dimension": self.index.d,
                "chunks": [asdict(c) for c in self.chunks]}
        (directory / "index_metadata.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, directory: Path, embedder: Embedder | None = None) -> VectorIndex:
        meta = json.loads((directory / "index_metadata.json").read_text(encoding="utf-8"))
        embedder = embedder or Embedder(meta["embedding_model"])
        index = faiss.read_index(str(directory / "vectors.faiss"))
        return cls(embedder, [Chunk(**c) for c in meta["chunks"]], index)
