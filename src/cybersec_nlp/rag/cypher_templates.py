"""Schema-guided Text-to-Cypher: question → (anchor entity, asked type, relation) → validated query.

A 1.5 B-parameter LLM writes invalid Cypher most of the time (Notebook 4B). Most analyst
questions about the graph have the same shape — *"which <type> <verb> <entity>?"* — so they
can be parsed deterministically:

1. **asked type**: the noun after *which / what / quel(le)s* (``software`` → ``Software``,
   ``techniques`` → ``AttackPattern``, ``documents`` → ``Document``…);
2. **anchor**: an entity of the question linked to a graph node by the cyber NER
   (canonical key and real label, e.g. ``CVE-2021-44228`` → ``Vulnerability``);
3. **relation**: the relationship of the graph that connects the two labels (direction taken
   from the data), disambiguated by the verb (*affect*, *target*, *use*, *mention*).

The result is a single-hop query built from schema elements only, so it is always valid.
When the question does not fit (no anchor, unknown type, no connecting relation), the
generator defers to a fallback (the LLM) and the ReAct agent keeps its repair loop.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable

from cybersec_nlp.graph.minicypher import InMemoryGraph, Schema
from cybersec_nlp.nlp.ner import CyberNER

# Ordered: the first matching pattern wins ("attack techniques" before "attack").
TYPE_WORDS: tuple[tuple[str, str], ...] = (
    (r"attack\s+techniques?|techniques?\s+d['’]attaque|techniques?|attack\s+patterns?|tactics?|vecteurs?|vectors?",
     "AttackPattern"),
    (r"vulnerabilit\w*|vuln\w*|cves?|failles?", "Vulnerability"),
    (r"malwares?|maliciels?|logiciels?\s+malveillants?|malware\s+famil\w*", "Malware"),
    (r"software|softwares|logiciels?|products?|produits?|systems?|systèmes?|platforms?|plateformes?", "Software"),
    (r"tools?|outils?", "Tool"),
    (r"threat\s+actors?|actors?|acteurs?|groups?|groupes?|apts?", "ThreatActor"),
    (r"documents?|reports?|rapports?|sources?", "Document"),
    (r"sectors?|secteurs?|targets?|cibles?|industr\w*|organi[sz]ations?", "Target"),
    (r"indicators?|indicateurs?|iocs?|ips?|addresses|adresses|hash\w*", "Indicator"),
)
VERB_TO_RELATION: tuple[tuple[str, str], ...] = (
    (r"affect\w*|vulnerable|touch\w*", "AFFECTS"),
    (r"target\w*|cibl\w*|vis\w*", "TARGETS"),
    (r"use[sd]?|using|utilis\w*|employ\w*|leverag\w*", "USES"),
    (r"mention\w*|cite[sd]?|cit\w*|talk|parl\w*|describ\w*|décri\w*", "MENTIONS"),
    (r"exploit\w*", "EXPLOITS"),
    (r"indicat\w*", "INDICATES"),
)
_HEAD = re.compile(r"^\s*(?:which|what|quel(?:le)?s?|lesquel(?:le)?s)\s+(.{1,60})", re.IGNORECASE)


def asked_label(question: str) -> str | None:
    """Label of the requested result, read from the noun phrase after the interrogative word."""
    head = _HEAD.match(question)
    text = head.group(1) if head else question
    words = " ".join(text.split()[:4]).lower()
    for pattern, label in TYPE_WORDS:
        if re.match(rf"(?:the\s+|les\s+|des\s+)?(?:{pattern})\b", words, re.IGNORECASE):
            return label
    return None


class SchemaGuidedCypher:
    """Deterministic question → Cypher translator with an optional fallback generator."""

    def __init__(self, graph: InMemoryGraph, ner: CyberNER | None = None,
                 fallback: Callable[[str, Schema], str] | None = None) -> None:
        self.graph = graph
        self.ner = ner or CyberNER()
        self.fallback = fallback
        triples: Counter[tuple[str, str, str]] = Counter()
        for edge in graph.edges:
            triples[(graph.nodes[edge.src].label, edge.rel, graph.nodes[edge.dst].label)] += 1
        self.triples = triples
        self._by_lower = {node.name.lower(): node for node in graph.nodes.values() if node.label != "Document"}

    def anchors(self, question: str) -> list[tuple[str, str]]:
        """``(label, name)`` of graph nodes named in the question (NER canonical keys)."""
        found = []
        for key, _ in sorted(self.ner.extract_keys(question)):
            node = self._by_lower.get(key.lower())
            if node and (node.label, node.name) not in found:
                found.append((node.label, node.name))
        return found

    def relation(self, anchor_label: str, target_label: str, question: str) -> tuple[str, bool] | None:
        """``(relationship, anchor_is_source)`` linking the two labels, guided by the question's verb."""
        candidates = [(rel, src == anchor_label) for (src, rel, dst), _ in self.triples.most_common()
                      if {src, dst} == {anchor_label, target_label} and (src != dst)]
        if not candidates:
            return None
        lowered = question.lower()
        for pattern, rel in VERB_TO_RELATION:
            if re.search(rf"\b(?:{pattern})", lowered):
                preferred = [c for c in candidates if c[0] == rel]
                if preferred:
                    return preferred[0]
        return candidates[0]  # most frequent relation between the two labels

    def translate(self, question: str) -> str | None:
        target = asked_label(question)
        if target is None:
            return None
        for anchor_label, anchor_name in self.anchors(question):
            if anchor_label == target:
                continue
            found = self.relation(anchor_label, target, question)
            if found is None:
                continue
            rel, anchor_is_source = found
            value = anchor_name.replace("\\", "\\\\").replace("'", "\\'")
            anchor = f"(a:{anchor_label} {{name: '{value}'}})"
            answer = f"(x:{target})"
            pattern = f"{anchor}-[:{rel}]->{answer}" if anchor_is_source else f"{answer}-[:{rel}]->{anchor}"
            return f"MATCH {pattern} RETURN DISTINCT x.name LIMIT 50"
        return None

    def __call__(self, question: str, schema: Schema) -> str:
        """Generator interface of :class:`~cybersec_nlp.rag.agentic.AgenticRAG`."""
        query = self.translate(question)
        if query is not None:
            return query
        if self.fallback is not None:
            return self.fallback(question, schema)
        return "MATCH (unsupported question)"  # rejected by the backend -> the agent stops cleanly
