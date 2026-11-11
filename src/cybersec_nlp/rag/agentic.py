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


LABEL_SYNONYMS = {
    "cve": "Vulnerability", "vuln": "Vulnerability", "technique": "AttackPattern", "tactic": "AttackPattern",
    "attack": "AttackPattern", "attacktechnique": "AttackPattern", "actor": "ThreatActor", "apt": "ThreatActor",
    "group": "ThreatActor", "threatgroup": "ThreatActor", "sector": "Target", "industry": "Target",
    "organization": "Target", "victim": "Target", "product": "Software", "os": "Software", "application": "Software",
    "ioc": "Indicator", "ip": "Indicator", "ipaddress": "Indicator", "report": "Document", "doc": "Document",
}  # domain synonyms LLMs commonly use for the STIX labels of the project graph


def _closest(word: str, options: list[str]) -> str | None:
    """Best fuzzy match, ignoring case and underscores (USES_MALWARE -> USES)."""
    synonym = LABEL_SYNONYMS.get(word.lower().replace("_", ""))
    if synonym in options:
        return synonym
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
            bad = re.escape(found.group(1))
            good = _closest(found.group(1), options)
            if not good:
                continue
            # Replace only in label / type / property positions, never inside quoted values.
            if kind == "property":
                fixed = re.sub(rf"(?<=\.){bad}\b|(?<=\{{)\s*{bad}(?=\s*:)|(?<=,)\s*{bad}(?=\s*:)", good, fixed)
            else:
                fixed = re.sub(rf"(?<=:)\s*{bad}\b", good, fixed)
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


EMPTY_RESULT = "No rows returned. Entity names must be canonical keys of the graph."
_ORDER_BY = re.compile(r"\s+ORDER\s+BY\s+.+?(?=\s+LIMIT\b|\s*;?\s*$)", re.IGNORECASE | re.DOTALL)
_VAR_LENGTH = re.compile(r"\*\s*\d*\s*(?:\.\.\s*\d*)?(?=\s*\])")
_NODE_FILTER = re.compile(r"\((\w+)(?::(\w+))?\s*\{\s*(\w+)\s*:\s*(['\"])(.*?)\4\s*\}\s*\)")


def syntax_repairer(query: str, error: str, schema: Schema) -> str:
    """Remove constructs the backend rejects but that do not change the answer set."""
    if "Syntax error" not in error:
        return query
    fixed = _ORDER_BY.sub("", query)
    fixed = _VAR_LENGTH.sub("", fixed)
    return fixed.replace(";", "").strip()


def entity_linking_repairer(graph: InMemoryGraph, ner=None) -> CypherRepairer:
    """Rewrite ``(x:Label {prop: 'Value'})`` to the canonical ``{name: 'key'}`` and label of a graph node.

    Names are matched case-insensitively, then through the NER canonical key (aliases, e.g.
    'banking sector' -> 'banking'). Triggered on empty results and on unknown labels/properties.
    """
    from cybersec_nlp.nlp.ner import CyberNER

    ner = ner or CyberNER()
    by_name: dict[str, list[tuple[str, str]]] = {}  # lower-case name -> [(label, stored name)]
    for node in graph.nodes.values():
        by_name.setdefault(node.name.lower(), []).append((node.label, node.name))

    def resolve(value: str, label: str | None) -> tuple[str, str] | None:
        """``(label, name)`` of the graph node designated by ``value`` (same label preferred)."""
        candidates = [value.lower()] + sorted(key.lower() for key, _ in ner.extract_keys(value))
        for candidate in candidates:
            matches = by_name.get(candidate)
            if matches:
                return next((m for m in matches if m[0] == label), matches[0])
        return None

    def repair(query: str, error: str, schema: Schema) -> str:
        if error != EMPTY_RESULT and not error.startswith(("Unknown label", "Unknown property")):
            return query

        def substitute(match: re.Match[str]) -> str:
            var, label, _, _, value = match.groups()
            found = resolve(value, label)
            if not found:
                return match.group(0)
            new_label, name = found
            return f"({var}:{new_label} {{name: '{name}'}})"

        return _NODE_FILTER.sub(substitute, query)

    return repair


def direction_repairer(query: str, error: str, schema: Schema) -> str:
    """On an empty result, try the relationship in the opposite direction (a classic LLM error)."""
    if error != EMPTY_RESULT:
        return query
    if re.search(r"\]\s*->", query):
        return re.sub(r"-\s*\[(.*?)\]\s*->", r"<-[\1]-", query, count=1)
    return re.sub(r"<-\s*\[(.*?)\]\s*-(?!>)", r"-[\1]->", query, count=1)


def chain_repairers(*repairers: CypherRepairer) -> CypherRepairer:
    """Try each repairer in order; the first one that changes the query wins."""

    def repair(query: str, error: str, schema: Schema) -> str:
        for repairer in repairers:
            fixed = repairer(query, error, schema)
            if fixed.strip() != query.strip():
                return fixed
        return query

    return repair


_CYPHER_LINE = re.compile(r"(MATCH\b.*?RETURN\b[^\n`]*)", re.IGNORECASE | re.DOTALL)
TEXT_TO_CYPHER_PROMPT = """You translate a question into ONE read-only Cypher query for a Neo4j graph.
Schema:
{schema}
Rules:
- Use exactly this pattern: MATCH (a:Label {{name: 'value'}})-[:REL]->(b:Label) RETURN b.name LIMIT 20
  (the arrow may be reversed: <-[:REL]-). Use only labels and relationships from the schema.
- Filter entities with the `name` property. Names are lower-case (e.g. 'apt28', 'nmap', 'openssl');
  CVE identifiers are upper-case (e.g. 'CVE-2014-0160').
- Output only the query, nothing else.
Examples:
Question: Which software is affected by CVE-2014-0160?
MATCH (v:Vulnerability {{name: 'CVE-2014-0160'}})-[:AFFECTS]->(s:Software) RETURN s.name LIMIT 20
Question: Which documents mention nmap?
MATCH (d:Document)-[:MENTIONS]->(t:Tool {{name: 'nmap'}}) RETURN d.name LIMIT 20"""


def extract_cypher(text: str) -> str:
    """First ``MATCH ... RETURN ...`` statement of an LLM answer (code fences removed)."""
    match = _CYPHER_LINE.search(text.replace("```cypher", "").replace("```", ""))
    return " ".join(match.group(1).split()) if match else text.strip()


def llm_cypher_generator(llm) -> CypherGenerator:
    def generate(question: str, schema: Schema) -> str:
        answer = llm.chat([
            {"role": "system", "content": TEXT_TO_CYPHER_PROMPT.format(schema=schema.describe())},
            {"role": "user", "content": question},
        ], max_new_tokens=80)
        return extract_cypher(answer)

    return generate


def llm_cypher_repairer(llm) -> CypherRepairer:
    def repair(query: str, error: str, schema: Schema) -> str:
        answer = llm.chat([
            {"role": "system", "content": TEXT_TO_CYPHER_PROMPT.format(schema=schema.describe())},
            {"role": "user", "content": f"This query failed:\n{query}\nDatabase error: {error}\nReturn the corrected query."},
        ], max_new_tokens=80)
        return extract_cypher(answer)

    return repair


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
        tried = {query}
        for step_no in range(1, self.max_steps + 1):
            try:
                rows = self.graph.run(query)
            except CypherError as exc:
                error = str(exc)
                result.trace.append(
                    Step(f"Step {step_no}: the query failed; fix it with the schema.", query, f"ERROR: {error}")
                )
                repaired = self.repairer(query, error, schema)
                if repaired in tried:
                    result.trace.append(Step("No new repair found; stop.", query, "ABORT"))
                    return result
                tried.add(repaired)
                query, result.repaired = repaired, True
                continue
            if not rows:
                result.trace.append(Step(f"Step {step_no}: empty result; check entity names and labels.", query, "0 rows"))
                repaired = self.repairer(query, EMPTY_RESULT, schema)
                if repaired in tried:
                    return result
                tried.add(repaired)
                query, result.repaired = repaired, True
                continue
            ranked = rerank(question, rows, self.graph)
            result.trace.append(Step(f"Step {step_no}: query valid; re-rank rows.", query, f"{len(rows)} rows"))
            result.final_query, result.rows = query, ranked
            return result
        result.trace.append(Step("Step budget exhausted.", query, "ABORT"))
        return result
