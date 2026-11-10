"""Detection of knowledge-graph poisoning (GragPoison-style attacks).

A poisoning attack injects a few nodes/edges (or text properties) so that many future
queries retrieve attacker-controlled facts. Four complementary detectors run against the
graph, optionally compared with a *trusted baseline snapshot*:

* ``unprovenanced``   - edges without a source in the allow-list;
* ``hub_injection``   - new nodes whose degree is an outlier (one fact hijacks many queries);
* ``attribution_flip`` - a single-valued relation (e.g. ATTRIBUTED_TO) that changed target;
* ``prompt_injection`` - instructions or URLs hidden in text properties.
"""

from __future__ import annotations

import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field

from cybersec_nlp.graph.minicypher import Edge, InMemoryGraph

INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"\b(system\s+prompt|you\s+are\s+now|disregard)\b", re.IGNORECASE),
    re.compile(r"https?://", re.IGNORECASE),
)
SINGLE_VALUED_RELATIONS = frozenset({"ATTRIBUTED_TO"})


@dataclass(frozen=True)
class Finding:
    detector: str
    severity: str  # "high" | "medium"
    subject: str
    detail: str


@dataclass
class PoisonReport:
    findings: list[Finding] = field(default_factory=list)

    @property
    def flagged_edges(self) -> set[tuple[str, str, str]]:
        triples = (f.subject.split("|") for f in self.findings if f.subject.count("|") == 2)
        return {(src, rel, dst) for src, rel, dst in triples}

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
        hub_z_threshold: float = 3.0,
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
        return report

    def quarantine(self, graph: InMemoryGraph, report: PoisonReport) -> InMemoryGraph:
        """Return a copy without flagged edges, orphaned nodes, or overwritten trusted facts."""
        bad = report.flagged_edges
        clean = graph.copy()
        clean.edges = [e for e in clean.edges if (e.src, e.rel, e.dst) not in bad]
        flagged_nodes = {f.subject for f in report.findings if f.detector == "hub_injection"}
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
            Finding("unprovenanced", "high", _key(e), f"source={e.props.get('source')!r} not trusted")
            for e in graph.edges
            if e.props.get("source") not in self.trusted_sources
        ]

    def _hub_injection(self, graph: InMemoryGraph) -> list[Finding]:
        """Flag nodes absent from the baseline whose degree is a statistical outlier."""
        if self.baseline is None:
            return []
        degree = _degrees(graph)
        # Statistics come from the trusted baseline: an injected hub would inflate its own
        # standard deviation and hide itself if computed on the poisoned graph.
        reference = list(_degrees(self.baseline).values())
        if len(reference) < 3:
            return []
        mean, std = statistics.fmean(reference), statistics.pstdev(reference) or 1.0
        return [
            Finding("hub_injection", "high", node_id, f"new node with degree {d} (z={(d - mean) / std:.1f})")
            for node_id, d in degree.items()
            if node_id not in self.baseline.nodes and (d - mean) / std >= self.hub_z_threshold
        ]

    def _attribution_flip(self, graph: InMemoryGraph) -> list[Finding]:
        if self.baseline is None:
            return []
        trusted = {(e.src, e.rel): e.dst for e in self.baseline.edges if e.rel in SINGLE_VALUED_RELATIONS}
        return [
            Finding("attribution_flip", "high", _key(e), f"baseline target was {trusted[(e.src, e.rel)]}")
            for e in graph.edges
            if (e.src, e.rel) in trusted and trusted[(e.src, e.rel)] != e.dst
        ]

    @staticmethod
    def _prompt_injection(graph: InMemoryGraph) -> list[Finding]:
        findings = []
        for node in graph.nodes.values():
            for prop, value in node.props.items():
                if isinstance(value, str) and any(p.search(value) for p in INJECTION_PATTERNS):
                    findings.append(Finding("prompt_injection", "medium", node.id, f"property `{prop}`"))
        return findings
