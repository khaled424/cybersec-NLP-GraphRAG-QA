"""HybridRAG: dense retrieval (FAISS) + knowledge-graph traversal, fused into cited answers.

Design by Membre 5 (Notebook 4A), generalised from the demo graph to the real STIX graph:

* **vector branch** - best chunk per document from the FAISS index, optionally re-ordered by a
  multilingual cross-encoder (:mod:`cybersec_nlp.rag.reranker`);
* **graph branch** - entities of the question are linked to graph nodes (NER), then the
  branch returns (a) typed STIX relations touching them and (b) the documents that mention
  the most linked entities (hubs are skipped unless several entities intersect);
* **fusion** - each branch gets a slot, then results alternate by rank (vector first) up to a budget;
* **generation** - local LLM prompted with numbered sources, then every sentence is re-attributed
  by :mod:`cybersec_nlp.rag.grounding` (unsupported sentences and fabricated identifiers are
  removed, nothing supported = abstention). Without LLM, an extractive answer is returned.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from time import perf_counter
from typing import Any

from cybersec_nlp.graph.minicypher import InMemoryGraph
from cybersec_nlp.llm.guardrails import check_prompt
from cybersec_nlp.llm.prompts import ABSTAIN_MESSAGE, SOC_SYSTEM_PROMPT
from cybersec_nlp.nlp.ner import CyberNER
from cybersec_nlp.rag.grounding import GroundingChecker
from cybersec_nlp.rag.reranker import CrossEncoderReranker
from cybersec_nlp.rag.vector_index import VectorIndex

STRATEGIES = ("vector", "graph", "hybrid")
_CITATION = re.compile(r"\[S(\d+)\]")
_FOLLOW_UP = re.compile(r"^(et\b|and\b|puis\b|what about\b|qu'en est-il\b|ce logiciel\b|cet incident\b|it\b)", re.IGNORECASE)


@dataclass(frozen=True)
class Evidence:
    doc_id: str
    source: str
    text: str
    kind: str
    locator: str
    score: float | None = None


@dataclass
class GraphRetriever:
    graph: InMemoryGraph
    documents: dict[str, dict[str, str]]
    ner: CyberNER = field(default_factory=CyberNER)
    hub_fraction: float = 0.05

    def __post_init__(self) -> None:
        self._mentions: dict[str, list[str]] = {}
        self._doc_entities: dict[str, set[str]] = {}
        self._relations: dict[str, list] = {}
        self._mention_count: dict[tuple[str, str], int] = {}
        for edge in self.graph.edges:
            if edge.rel == "MENTIONS":
                doc = self.graph.nodes[edge.src].name
                self._mention_count[(doc, edge.dst)] = int(edge.props.get("count", 1))
                self._mentions.setdefault(edge.dst, []).append(doc)
                self._doc_entities.setdefault(doc, set()).add(edge.dst)
            else:
                self._relations.setdefault(edge.src, []).append(edge)
                self._relations.setdefault(edge.dst, []).append(edge)
        self._hub_limit = max(3, int(self.hub_fraction * max(1, len(self.documents))))

    def link(self, question: str) -> list[str]:
        """Graph node ids of the entities named in the question."""
        from cybersec_nlp.graph.knowledge_graph import NER_TO_LABEL

        linked = []
        for key, label in sorted(self.ner.extract_keys(question)):
            node = self.graph.node_id(NER_TO_LABEL[label], key)
            if node in self.graph.nodes and node not in linked:
                linked.append(node)
        return linked

    def retrieve(self, question: str, k: int = 4) -> tuple[list[Evidence], dict[str, Any]]:
        linked = self.link(question)
        facts: list[Evidence] = []
        for node in linked:
            # A relation without a known supporting document never becomes evidence (provenance rule).
            supported = [e for e in self._relations.get(node, [])
                         if any(d in self.documents for d in e.props.get("doc_ids") or [])]
            for edge in sorted(supported, key=lambda e: -e.props.get("weight", 1))[:2]:
                src, dst = self.graph.nodes[edge.src], self.graph.nodes[edge.dst]
                doc_id = next(d for d in edge.props["doc_ids"] if d in self.documents)
                facts.append(Evidence(
                    doc_id, self.documents[doc_id]["source"],
                    f"{src.name} ({src.label}) {edge.rel} {dst.name} ({dst.label}) — association observée "
                    f"dans {edge.props.get('weight', 1)} document(s) (co-occurrence, non validée).",
                    "graph", f"{edge.src} -[{edge.rel}]-> {edge.dst}",
                    float(edge.props.get("weight", 1)),
                ))
        facts += self._documents_for(linked)
        unique, seen = [], set()
        for fact in sorted(facts, key=lambda f: -(f.score or 0)):
            if (fact.doc_id, fact.locator) not in seen:
                seen.add((fact.doc_id, fact.locator))
                unique.append(fact)
        return unique[:k], {"linked_entities": linked}

    def _documents_for(self, linked: list[str]) -> list[Evidence]:
        """Documents mentioning several linked entities first; otherwise the non-hub entities only."""
        counts = Counter(doc for node in linked for doc in self._mentions.get(node, []))
        multi = [doc for doc, c in counts.items() if c >= 2]
        if multi:
            ranked = sorted(multi, key=lambda d: (-counts[d], -self._weight(d, linked), d))
        else:
            selective = [n for n in linked if len(self._mentions.get(n, [])) <= self._hub_limit]
            docs = {doc for n in selective for doc in self._mentions.get(n, [])}
            ranked = sorted(docs, key=lambda d: (-self._weight(d, selective), d))
        evidence = []
        for doc in ranked[:4]:
            names = sorted(self.graph.nodes[n].name for n in self._doc_entities[doc] & set(linked))
            info = self.documents[doc]
            evidence.append(Evidence(
                doc, info["source"], f"{doc} mentionne {', '.join(names)} — « {info['title']} » : {info['text'][:400]}",
                "graph", f"Document:{doc} -[MENTIONS]-> {', '.join(names)}", float(counts[doc]),
            ))
        return evidence

    def _weight(self, doc: str, nodes: list[str]) -> int:
        """Total number of mentions of ``nodes`` in ``doc`` (tie-breaker)."""
        return sum(self._mention_count.get((doc, n), 0) for n in nodes)


def fuse(vector: list[Evidence], graph: list[Evidence], budget: int = 6) -> list[Evidence]:
    """Alternate vector and graph results by rank, without duplicates, up to ``budget``.

    The vector branch leads: on the 300-question benchmark of Notebook 4A it ranks the right
    document far better (graph-first fusion lowered MRR@4 from 0.76 to 0.63), while graph facts
    still reach the evidence at ranks 2, 4, … for relational questions.
    """
    selected, seen = [], set()
    for rank in range(max(len(vector), len(graph))):
        for branch in (vector, graph):
            if rank < len(branch):
                item = branch[rank]
                key = (item.kind, item.doc_id, item.locator)
                if key not in seen:
                    seen.add(key)
                    selected.append(item)
                    if len(selected) == budget:
                        return selected
    return selected


class HybridRAG:
    def __init__(self, index: VectorIndex, graph_retriever: GraphRetriever, llm=None,
                 k_vector: int = 4, k_graph: int = 4, budget: int = 6, min_vector_score: float = 0.83,
                 reranker: CrossEncoderReranker | None = None, rerank_candidates: int = 20) -> None:
        self.index, self.graph_retriever, self.llm = index, graph_retriever, llm
        self.k_vector, self.k_graph, self.budget = k_vector, k_graph, budget
        self.min_vector_score = min_vector_score
        self.reranker, self.rerank_candidates = reranker, rerank_candidates
        self.grounding = GroundingChecker(index.embedder)

    def vector_retrieve(self, question: str) -> list[Evidence]:
        """Dense retrieval; with a reranker, the top candidates are re-ordered by the cross-encoder.

        The abstention threshold stays on the bi-encoder score (calibrated in Notebook 4A), the
        reranker only changes the order of the candidates that pass it.
        """
        if self.reranker is None:
            hits = self.index.search(question, self.k_vector, self.min_vector_score)
        else:
            candidates = self.index.search(question, self.rerank_candidates, self.min_vector_score)
            hits = self.reranker.rerank(question, [c for c, _ in candidates], lambda c: c.text)[: self.k_vector]
        return [Evidence(c.doc_id, c.source, c.text, "vector", c.chunk_id, score) for c, score in hits]

    def retrieve(self, question: str, strategy: str = "hybrid") -> tuple[list[Evidence], dict[str, Any]]:
        if strategy not in STRATEGIES:
            raise ValueError(f"strategy must be one of {STRATEGIES}")
        start = perf_counter()
        vector = self.vector_retrieve(question) if strategy != "graph" else []
        graph, info = self.graph_retriever.retrieve(question, self.k_graph) if strategy != "vector" else ([], {})
        selected = fuse(vector, graph, self.budget)
        return selected, {"vector_hits": len(vector), "graph_hits": len(graph), **info,
                          "retrieval_ms": round(1000 * (perf_counter() - start), 1)}

    def generate(self, question: str, evidence: list[Evidence], use_llm: bool = True) -> tuple[str, str, dict[str, Any]]:
        """Return ``(answer, generator, grounding)``; generator is ``llm``, ``extractive`` or ``none``."""
        if not evidence:
            return ABSTAIN_MESSAGE, "none", {}
        if self.llm is None or not use_llm:
            lines = [f"- {e.text[:350]} [S{i}]" for i, e in enumerate(evidence[:3], 1)]
            return "Éléments les plus pertinents :\n" + "\n".join(lines), "extractive", {}
        sources = "\n".join(f"[S{i}] {e.text[:900]}" for i, e in enumerate(evidence, 1))
        raw = self.llm.chat([
            {"role": "system", "content": SOC_SYSTEM_PROMPT.format(abstain=ABSTAIN_MESSAGE)},
            {"role": "user", "content": f"Sources:\n{sources}\n\nQuestion: {question}\nAnswer:"},
        ], max_new_tokens=320)
        if ABSTAIN_MESSAGE in raw:
            return ABSTAIN_MESSAGE, "llm", {"raw_answer": raw, "supported_ratio": None}
        grounded = self.grounding.check(raw, [e.text for e in evidence])
        report = {
            "raw_answer": raw, "supported_ratio": round(grounded.supported_ratio, 3),
            "removed_sentences": [{"sentence": s, "reason": why} for s, why in grounded.unsupported],
        }
        if not grounded.supported:
            return ABSTAIN_MESSAGE, "llm", report
        return grounded.text, "llm", report

    def answer(self, question: str, strategy: str = "hybrid", use_llm: bool = True) -> dict[str, Any]:
        question = (question or "").strip()
        verdict = check_prompt(question)
        if not verdict.allowed:
            return {"question": question, "strategy": strategy, "answer": verdict.message, "evidence": [],
                    "trace": {"blocked": True, "reasons": list(verdict.reasons)}, "generator": "guardrail"}
        evidence, trace = self.retrieve(question, strategy)
        start = perf_counter()
        answer, generator, grounding = self.generate(question, evidence, use_llm)
        trace["answer_ms"] = round(1000 * (perf_counter() - start), 1)
        trace["grounding"] = grounding
        return {"question": question, "strategy": strategy, "answer": answer, "generator": generator,
                "evidence": [{"citation": f"S{i}", **asdict(e)} for i, e in enumerate(evidence, 1)],
                "trace": trace}


def contextualize(question: str, previous: str | None) -> tuple[str, bool]:
    """Expand a short follow-up ("Et quel correctif ?") with the previous standalone question."""
    question = question.strip()
    if previous and _FOLLOW_UP.match(question):
        return f"{question} (question précédente : {previous})", True
    return question, False


class SOCSession:
    """Conversation memory: short follow-ups are expanded with the previous question."""

    def __init__(self, rag: HybridRAG) -> None:
        self.rag = rag
        self.last_question: str | None = None

    def ask(self, question: str, **kwargs: Any) -> dict[str, Any]:
        contextual, follow_up = contextualize(question, self.last_question)
        result = self.rag.answer(contextual, **kwargs)
        if not follow_up:
            self.last_question = question.strip()
        return result
