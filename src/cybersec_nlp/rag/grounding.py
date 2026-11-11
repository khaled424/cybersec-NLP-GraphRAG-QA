"""Sentence-level grounding check for generated answers (faithfulness guard).

Small local LLMs follow citation instructions unreliably and may add facts from their
parametric memory. Every generated sentence is therefore re-attributed:

1. the sentence is embedded and compared with every sentence of every evidence;
2. it is *supported* by the evidence with the highest similarity if that similarity reaches
   ``threshold`` **and** every precise identifier it contains (CVE, IP, hash, ATT&CK id) appears
   verbatim in the evidence set (sources holding those identifiers are cited too) — fabricated identifiers are the costliest error in a SOC;
3. a sentence that ties an identifier to other named entities (``CVE-2021-34527 affects log4j``) is
   supported only if one evidence sentence contains the identifier **together with** one of those
   entities — this catches real identifiers attributed to the wrong product;
4. unsupported sentences are removed and reported; if nothing is supported the system abstains.

The resulting ``supported_ratio`` is the faithfulness metric reported by the MVP.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

_SENTENCES = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý0-9\"'(\-•*])")
_MARKERS = re.compile(r"\s*\[S\d+(?:\s*,\s*S?\d+)*\]")
_IDENTIFIERS = re.compile(
    r"\bCVE-\d{4}-\d{4,7}\b|(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?!\w|\.\d)|\bT1\d{3}(?:\.\d{3})?\b|\b[a-fA-F0-9]{32,64}\b",
    re.IGNORECASE,
)


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCES.split(text.strip()) if len(s.strip()) > 3]


@dataclass
class GroundedAnswer:
    text: str
    supported: list[tuple[str, int, float]] = field(default_factory=list)  # sentence, evidence index (1-based), score
    unsupported: list[tuple[str, str]] = field(default_factory=list)  # sentence, reason

    @property
    def supported_ratio(self) -> float:
        total = len(self.supported) + len(self.unsupported)
        return len(self.supported) / total if total else 0.0


class GroundingChecker:
    def __init__(self, embedder, threshold: float = 0.82, ner=None) -> None:
        from cybersec_nlp.nlp.ner import CyberNER

        self.embedder = embedder
        self.threshold = threshold
        self.ner = ner or CyberNER()

    def _misattributed(self, sentence: str, identifiers: set[str], pieces: list[str]) -> list[str]:
        """Identifiers never seen in the same evidence sentence as the other entities of ``sentence``."""
        others = {key.lower() for key, label in self.ner.extract_keys(sentence)
                  if label not in ("CVE", "IP", "HASH", "ATTACK_ID")}
        if not identifiers or not others:
            return []
        lowered = [p.lower() for p in pieces]
        return sorted(x for x in identifiers
                      if not any(x in p and any(o in p for o in others) for p in lowered))

    def check(self, answer: str, evidence_texts: list[str]) -> GroundedAnswer:
        sentences = split_sentences(_MARKERS.sub("", answer))
        result = GroundedAnswer(text="")
        if not sentences or not evidence_texts:
            return result
        pieces, owner = [], []
        for i, text in enumerate(evidence_texts, 1):
            for piece in split_sentences(text) or [text]:
                pieces.append(piece)
                owner.append(i)
        lowered = [text.lower() for text in evidence_texts]
        corpus = " ".join(lowered)
        answer_vecs = self.embedder.encode(sentences, kind="query")
        evidence_vecs = self.embedder.encode(pieces, kind="passage")
        sims = answer_vecs @ evidence_vecs.T
        kept = []
        for row, sentence in enumerate(sims):
            best = int(np.argmax(sentence))
            score, source = float(sentence[best]), owner[best]
            ids = {m.lower() for m in _IDENTIFIERS.findall(sentences[row])}
            missing = sorted(x for x in ids if x not in corpus)
            holders = sorted({i for x in ids for i, text in enumerate(lowered, 1) if x in text} - {source})
            if score < self.threshold:
                result.unsupported.append((sentences[row], f"similarité {score:.2f} < {self.threshold}"))
            elif missing:
                result.unsupported.append((sentences[row], "identifiant absent des preuves : " + ", ".join(missing)))
            elif misattributed := self._misattributed(sentences[row], ids, pieces):
                result.unsupported.append((sentences[row], "association non étayée par une même preuve : "
                                           + ", ".join(misattributed)))
            else:
                result.supported.append((sentences[row], source, score))
                markers = "".join(f"[S{i}]" for i in [source, *holders])
                kept.append(f"{sentences[row].rstrip()} {markers}")
        result.text = " ".join(kept)
        return result
