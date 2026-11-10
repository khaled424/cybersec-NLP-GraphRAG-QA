"""Controls and audits for OWASP LLM08:2025 - Vector and Embedding Weaknesses.

Covered risks:

* **cross-tenant leakage** - a shared vector index returning another tenant's chunks;
* **embedding inversion** - recovering source text from stolen vectors;
* **sensitive data in the index** - secrets/PII embedded verbatim.

Embeddings are deterministic hashed character n-grams, so everything runs offline; the
controls are independent of the embedding model used in production.
"""

from __future__ import annotations

import re
import zlib
from dataclasses import dataclass

import numpy as np

DIM = 256


def embed(text: str, dim: int = DIM) -> np.ndarray:
    """L2-normalised hashed character 3-gram embedding (deterministic, no model download)."""
    vec = np.zeros(dim)
    padded = f" {text.lower()} "
    for i in range(len(padded) - 2):
        vec[zlib.crc32(padded[i : i + 3].encode()) % dim] += 1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm else vec


@dataclass(frozen=True)
class Chunk:
    tenant: str
    text: str


class VectorStore:
    """Vector store whose isolation is enforced *before* scoring.

    ``enforce_isolation=False`` reproduces the vulnerable pattern (global top-k) and exists
    only so the audit can demonstrate the leak.
    """

    def __init__(self, enforce_isolation: bool = True) -> None:
        self.enforce_isolation = enforce_isolation
        self._chunks: list[Chunk] = []
        self._vectors: list[np.ndarray] = []

    def add(self, chunk: Chunk) -> None:
        self._chunks.append(chunk)
        self._vectors.append(embed(chunk.text))

    def search(self, tenant: str, query: str, k: int = 3) -> list[Chunk]:
        if not tenant:
            raise PermissionError("A tenant identifier is required for every query.")
        idx = [i for i, c in enumerate(self._chunks) if not self.enforce_isolation or c.tenant == tenant]
        if not idx:
            return []
        scores = np.stack([self._vectors[i] for i in idx]) @ embed(query)
        return [self._chunks[idx[i]] for i in np.argsort(-scores)[:k]]


def audit_tenant_isolation(store: VectorStore, probes: dict[str, list[str]]) -> list[str]:
    """Query as each tenant with probes; return every leaked chunk (empty list = pass)."""
    leaks = []
    for tenant, queries in probes.items():
        for query in queries:
            leaks += [
                f"{tenant} saw {c.tenant}: {c.text!r}" for c in store.search(tenant, query) if c.tenant != tenant
            ]
    return leaks


def inversion_recovery_rate(
    texts: list[str], candidates: list[str], noise_sigma: float, seed: int = 0, round_decimals: int | None = None
) -> float:
    """Share of stolen vectors for which a nearest-candidate attack recovers the right text.

    The attacker holds (possibly protected) vectors and a dictionary of candidate sentences.
    Mitigations modelled: Gaussian noise added before storage and coordinate rounding.
    """
    rng = np.random.default_rng(seed)
    cand_vecs = np.stack([embed(c) for c in candidates])
    hits = 0
    for text in texts:
        stolen = embed(text) + rng.normal(0.0, noise_sigma, DIM)
        if round_decimals is not None:
            stolen = np.round(stolen, round_decimals)
        hits += candidates[int(np.argmax(cand_vecs @ stolen))] == text
    return hits / len(texts)


_SECRET_PATTERNS = {
    "aws_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "bearer_token": re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{16,}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}


def scrub_sensitive(text: str) -> tuple[str, list[str]]:
    """Redact secrets/PII before embedding; return the clean text and the kinds redacted."""
    kinds = []
    for kind, pattern in _SECRET_PATTERNS.items():
        text, count = pattern.subn(f"[REDACTED:{kind}]", text)
        kinds += [kind] * count
    return text, kinds
