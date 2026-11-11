"""Detection of knowledge-graph poisoning (GragPoison-style attacks).

A poisoning attack injects a few nodes/edges (or text properties) so that many future
queries retrieve attacker-controlled facts. Four complementary detectors run against the
graph, optionally compared with a *trusted baseline snapshot*:

* ``unprovenanced``   - edges without a source in the allow-list;
* ``hub_injection``   - new nodes whose degree is an outlier for their label (robust z-score);
* ``attribution_flip`` - a single-valued relation (e.g. ATTRIBUTED_TO) that changed target;
* ``prompt_injection`` - instructions (or markdown-image exfiltration links) hidden in text properties;
* ``unmentioned_entity`` - an entity reachable through relations that no document mentions
  (every entity of the knowledge graph must come from a source document);
* ``provenance_mismatch`` - a derived edge cites supporting documents (``doc_ids``) that do not
  mention both of its endpoints (spoofed provenance: the source looks trusted but the
  evidence does not exist).
"""

from __future__ import annotations

import math
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field

from cybersec_nlp.graph.minicypher import Edge, InMemoryGraph
from cybersec_nlp.llm.guardrails import INJECTION_PATTERNS as GUARDRAIL_PATTERNS

# Indirect prompt injection: the instruction patterns of the input guardrail, plus the classic
# exfiltration trick of a markdown image whose URL carries data. Plain URLs are normal CTI content.
INJECTION_PATTERNS = (
    *GUARDRAIL_PATTERNS.values(),
    re.compile(r"!\[[^\]]*\]\(\s*https?://", re.IGNORECASE),
)
SINGLE_VALUED_RELATIONS = frozenset({"ATTRIBUTED_TO"})


@dataclass(frozen=True)
class Finding:
    detector: str
    severity: str  # "high" | "medium"
    subject: str  # human-readable: node id or "src|rel|dst"
    detail: str
    edge: tuple[str, str, str] | None = None  # structured edge (names may themselves contain "|")


@dataclass
class PoisonReport:
    findings: list[Finding] = field(default_factory=list)

    @property
    def flagged_edges(self) -> set[tuple[str, str, str]]:
        return {f.edge for f in self.findings if f.edge is not None}

    @property
    def is_clean(self) -> bool:
        return not self.findings

    def by_detector(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for finding in self.findings:
            counts[finding.detector] += 1
        return dict(counts)


def _key(edge: Edge) -> str:
    return f"{edge.src}|{edge.rel}|{edge.dst}"


def _degrees(graph: InMemoryGraph) -> dict[str, int]:
    degree = dict.fromkeys(graph.nodes, 0)
    for edge in graph.edges:
        degree[edge.src] += 1
        degree[edge.dst] += 1
    return degree


class GraphPoisonDetector:
    """Run all detectors; ``trusted_sources`` is the provenance allow-list."""

    def __init__(
        self,
        trusted_sources: set[str],
        baseline: InMemoryGraph | None = None,
        hub_z_threshold: float = 3.5,
    ) -> None:
        self.trusted_sources = trusted_sources
        self.baseline = baseline
        self.hub_z_threshold = hub_z_threshold

    def scan(self, graph: InMemoryGraph) -> PoisonReport:
        report = PoisonReport()
        report.findings += self._unprovenanced(graph)
        report.findings += self._hub_injection(graph)
        report.findings += self._attribution_flip(graph)
        report.findings += self._prompt_injection(graph)
        report.findings += self._provenance_mismatch(graph)
        report.findings += self._unmentioned_entity(graph)
        return report

    def quarantine(self, graph: InMemoryGraph, report: PoisonReport) -> InMemoryGraph:
        """Return a copy without flagged edges, orphaned nodes, or overwritten trusted facts."""
        bad = report.flagged_edges
        clean = graph.copy()
        clean.edges = [e for e in clean.edges if (e.src, e.rel, e.dst) not in bad]
        flagged_nodes = {f.subject for f in report.findings if f.detector in ("hub_injection", "unmentioned_entity")}
        clean.edges = [e for e in clean.edges if e.src not in flagged_nodes and e.dst not in flagged_nodes]
        clean.edges += self._restore_single_valued(clean)
        linked = {e.src for e in clean.edges} | {e.dst for e in clean.edges}
        clean.nodes = {k: n for k, n in clean.nodes.items() if k in linked or k in self._baseline_ids()}
        return clean

    def _restore_single_valued(self, graph: InMemoryGraph) -> list[Edge]:
        """Re-add trusted baseline facts whose poisoned replacement was just removed."""
        if self.baseline is None:
            return []
        present = {(e.src, e.rel) for e in graph.edges}
        return [
            Edge(e.src, e.rel, e.dst, dict(e.props))
            for e in self.baseline.edges
            if e.rel in SINGLE_VALUED_RELATIONS and (e.src, e.rel) not in present
        ]

    def _baseline_ids(self) -> set[str]:
        return set(self.baseline.nodes) if self.baseline else set()

    def _unprovenanced(self, graph: InMemoryGraph) -> list[Finding]:
        return [
            Finding("unprovenanced", "high", _key(e), f"source={e.props.get('source')!r} not trusted",
                    edge=(e.src, e.rel, e.dst))
            for e in graph.edges
            if e.props.get("source") not in self.trusted_sources
        ]

    def _hub_injection(self, graph: InMemoryGraph) -> list[Finding]:
        """Flag new nodes whose degree is an outlier for their label in the trusted baseline.

        Degrees are heavy-tailed (a few hubs such as ``windows``), so the score is a *robust*
        z-score on ``log1p(degree)``: median and MAD of the baseline nodes of the same label.
        """
        if self.baseline is None:
            return []
        reference: dict[str, list[float]] = defaultdict(list)
        for node_id, degree in _degrees(self.baseline).items():
            reference[self.baseline.nodes[node_id].label].append(math.log1p(degree))
        everything = [v for values in reference.values() for v in values]
        if len(everything) < 3:
            return []
        findings = []
        for node_id, degree in _degrees(graph).items():
            if node_id in self.baseline.nodes:
                continue
            values = reference.get(graph.nodes[node_id].label) or everything
            median = statistics.median(values)
            mad = statistics.median(abs(v - median) for v in values)
            z = (math.log1p(degree) - median) / max(1.4826 * mad, 0.25)
            if z >= self.hub_z_threshold:
                findings.append(Finding("hub_injection", "high", node_id, f"new node with degree {degree} (robust z={z:.1f})"))
        return findings

    def _attribution_flip(self, graph: InMemoryGraph) -> list[Finding]:
        if self.baseline is None:
            return []
        trusted = {(e.src, e.rel): e.dst for e in self.baseline.edges if e.rel in SINGLE_VALUED_RELATIONS}
        return [
            Finding("attribution_flip", "high", _key(e), f"baseline target was {trusted[(e.src, e.rel)]}",
                    edge=(e.src, e.rel, e.dst))
            for e in graph.edges
            if (e.src, e.rel) in trusted and trusted[(e.src, e.rel)] != e.dst
        ]

    @staticmethod
    def _unmentioned_entity(graph: InMemoryGraph) -> list[Finding]:
        """Entities that only exist through typed relations: no document ever mentions them."""
        mentioned = {e.dst for e in graph.edges if e.rel == "MENTIONS"}
        if not mentioned:
            return []  # graph without documents (e.g. curated CTI feed): detector not applicable
        linked = {n for e in graph.edges if e.rel != "MENTIONS" for n in (e.src, e.dst)}
        return [
            Finding("unmentioned_entity", "high", node_id, "entity linked by relations but mentioned by no document")
            for node_id in sorted(linked - mentioned)
            if graph.nodes[node_id].label != "Document"
        ]

    @staticmethod
    def _provenance_mismatch(graph: InMemoryGraph) -> list[Finding]:
        """Edges whose cited documents (``doc_ids``) mention neither endpoint pair."""
        mentions: dict[str, set[str]] = defaultdict(set)
        for edge in graph.edges:
            if edge.rel == "MENTIONS":
                mentions[graph.nodes[edge.src].name].add(edge.dst)
        if not mentions:
            return []
        findings = []
        for edge in graph.edges:
            doc_ids = edge.props.get("doc_ids")
            if edge.rel == "MENTIONS" or not doc_ids:
                continue
            if not any({edge.src, edge.dst} <= mentions.get(doc, set()) for doc in doc_ids):
                findings.append(Finding("provenance_mismatch", "high", _key(edge),
                                        f"none of {len(doc_ids)} cited document(s) mention both endpoints",
                                        edge=(edge.src, edge.rel, edge.dst)))
        return findings

    @staticmethod
    def _prompt_injection(graph: InMemoryGraph) -> list[Finding]:
        findings = []
        for node in graph.nodes.values():
            for prop, value in node.props.items():
                if isinstance(value, str) and any(p.search(value) for p in INJECTION_PATTERNS):
                    findings.append(Finding("prompt_injection", "medium", node.id, f"property `{prop}`"))
        return findings
