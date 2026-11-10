"""Agentic RAG: a ReAct loop that repairs failing Text-to-Cypher queries.

Loop: *Thought -> Action (run Cypher) -> Observation*. When the database rejects a query
(or returns nothing) the agent asks a repairer for a corrected query, using the error and
the graph schema as feedback, up to ``max_steps``. Successful rows are re-ranked before
being handed to the generator. The generator/repairer are plain callables, so a real LLM
can be plugged in; deterministic schema-based implementations are provided for offline use.
"""

from __future__ import annotations

import difflib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from cybersec_nlp.graph.minicypher import CypherError, InMemoryGraph, Schema

CypherGenerator = Callable[[str, Schema], str]
CypherRepairer = Callable[[str, str, Schema], str]
_TOKEN = re.compile(r"[a-z0-9_]+")


@dataclass
class Step:
    thought: str
    action: str
    observation: str


@dataclass
class AgentResult:
    question: str
    final_query: str | None
    rows: list[dict[str, Any]]
    trace: list[Step] = field(default_factory=list)
    repaired: bool = False

    @property
    def success(self) -> bool:
        return bool(self.rows)


def _closest(word: str, options: list[str]) -> str | None:
    """Best fuzzy match, ignoring case and underscores (USES_MALWARE -> USES)."""
    norm = {o: o.lower().replace("_", "") for o in options}
    target = word.lower().replace("_", "")
    # a known token that is a prefix/suffix of the hallucinated one is a strong hint
    contained = [o for o, n in norm.items() if n and (n in target or target in n)]
    if contained:
        return max(contained, key=len)
    hit = difflib.get_close_matches(target, list(norm.values()), n=1, cutoff=0.6)
    return next((o for o, n in norm.items() if n == hit[0]), None) if hit else None


def schema_repairer(query: str, error: str, schema: Schema) -> str:
    """Deterministic repairer: map unknown labels/relationships/properties to the schema."""
    fixed = query
    for kind, options in (
        ("label", schema.labels),
        ("relationship type", schema.relationships),
        ("property", schema.properties),
    ):
        found = re.search(rf"Unknown {kind} `(\w+)`", error)
        if found:
            bad = found.group(1)
            good = _closest(bad, options)
            if good:
                fixed = re.sub(rf"\b{re.escape(bad)}\b", good, fixed)
    return fixed


def rerank(question: str, rows: list[dict[str, Any]], graph: InMemoryGraph) -> list[dict[str, Any]]:
    """Order rows by lexical overlap with the question, trusted provenance and connectivity."""
    q_tokens = set(_TOKEN.findall(question.lower()))
    degree: dict[str, int] = {}
    for edge in graph.edges:
        degree[edge.src] = degree.get(edge.src, 0) + 1
        degree[edge.dst] = degree.get(edge.dst, 0) + 1

    def score(row: dict[str, Any]) -> float:
        edge = row["_edge"]
        text = " ".join(str(v) for k, v in row.items() if k != "_edge").lower()
        overlap = len(q_tokens & set(_TOKEN.findall(text)))
        trust = 1.0 if edge.props.get("source") else 0.0
        return 2.0 * overlap + 1.5 * trust + 0.1 * degree.get(edge.dst, 0)

    return sorted(rows, key=score, reverse=True)


class AgenticRAG:
    """Self-correcting graph question-answering agent (ReAct)."""

    def __init__(
        self,
        graph: InMemoryGraph,
        generator: CypherGenerator,
        repairer: CypherRepairer = schema_repairer,
        max_steps: int = 4,
    ) -> None:
        self.graph = graph
        self.generator = generator
        self.repairer = repairer
        self.max_steps = max_steps

    def ask(self, question: str) -> AgentResult:
        schema = self.graph.schema()
        query = self.generator(question, schema)
        result = AgentResult(question, None, [])
        for step_no in range(1, self.max_steps + 1):
            try:
                rows = self.graph.run(query)
            except CypherError as exc:
                error = str(exc)
                result.trace.append(
                    Step(f"Step {step_no}: the query failed; fix it with the schema.", query, f"ERROR: {error}")
                )
                repaired = self.repairer(query, error, schema)
                if repaired == query:
                    result.trace.append(Step("No repair found; stop.", query, "ABORT"))
                    return result
                query, result.repaired = repaired, True
                continue
            if not rows:
                result.trace.append(Step(f"Step {step_no}: empty result.", query, "0 rows"))
                return result
            ranked = rerank(question, rows, self.graph)
            result.trace.append(Step(f"Step {step_no}: query valid; re-rank rows.", query, f"{len(rows)} rows"))
            result.final_query, result.rows = query, ranked
            return result
        result.trace.append(Step("Step budget exhausted.", query, "ABORT"))
        return result
