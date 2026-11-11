"""STIX 2.1 / MITRE ATT&CK-aligned knowledge graph built from NER output (Notebook 1).

Nodes
    ``Document`` (one per cleaned Q/A pair) and one node per entity type:
    ``Indicator`` (IP, hash), ``Vulnerability`` (CVE), ``AttackPattern`` (ATT&CK id or named
    technique), ``Malware``, ``Tool``, ``ThreatActor``, ``Software``, ``Target`` (STIX identity
    sector).

Relationships
    * ``(Document)-[:MENTIONS]->(entity)`` — factual: the entity occurs in the document;
    * typed STIX relationships derived when two entities co-occur in the **same sentence**:
      ``USES``, ``TARGETS``, ``EXPLOITS``, ``INDICATES`` and the custom ``AFFECTS``
      (vulnerability → software). They carry ``method="sentence_cooccurrence"``, a ``weight``
      (number of supporting documents) and the supporting ``doc_ids``: they are *candidate*
      relations, not validated facts.

Every edge has ``source`` (provenance) so the poisoning audit (Notebook 4B) can verify it.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd

from cybersec_nlp.graph.minicypher import InMemoryGraph
from cybersec_nlp.nlp.ner import CyberNER, Entity

CORPUS_SOURCE = "cybersec-dataset-v1"
NER_TO_LABEL = {
    "IP": "Indicator", "HASH": "Indicator", "CVE": "Vulnerability", "ATTACK_ID": "AttackPattern",
    "VECTOR": "AttackPattern", "MALWARE": "Malware", "TOOL": "Tool", "THREAT_ACTOR": "ThreatActor",
    "SOFTWARE": "Software", "TARGET": "Target",
}
STIX_TYPE = {
    "Document": "report", "Indicator": "indicator", "Vulnerability": "vulnerability",
    "AttackPattern": "attack-pattern", "Malware": "malware", "Tool": "tool",
    "ThreatActor": "threat-actor", "Software": "software", "Target": "identity",
}
# (source label, relationship, target label) allowed for sentence co-occurrence.
RELATION_RULES: tuple[tuple[str, str, str], ...] = (
    ("ThreatActor", "USES", "Malware"), ("ThreatActor", "USES", "Tool"),
    ("ThreatActor", "USES", "AttackPattern"), ("Malware", "USES", "AttackPattern"),
    ("ThreatActor", "TARGETS", "Target"), ("Malware", "TARGETS", "Target"),
    ("AttackPattern", "TARGETS", "Target"), ("AttackPattern", "TARGETS", "Software"),
    ("Malware", "EXPLOITS", "Vulnerability"), ("Vulnerability", "AFFECTS", "Software"),
    ("Indicator", "INDICATES", "Malware"), ("Indicator", "INDICATES", "ThreatActor"),
)
NODE_LABELS = tuple(STIX_TYPE)
RELATIONSHIPS = ("MENTIONS",) + tuple(sorted({r for _, r, _ in RELATION_RULES}))
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
MAX_DOC_IDS = 25


def extract_corpus_entities(corpus: pd.DataFrame, ner: CyberNER | None = None) -> list[dict[str, Any]]:
    """Per-document entities with offsets in their field (``entities.json`` format)."""
    ner = ner or CyberNER()
    records = []
    for row in corpus.itertuples(index=False):
        entities = [
            {**e.to_dict(), "field": field}
            for field in ("user", "assistant")
            for e in ner.extract(getattr(row, field))
        ]
        records.append({"doc_id": row.doc_id, "entities": entities})
    return records


def _sentence_entities(text: str, ner: CyberNER) -> Iterable[list[Entity]]:
    for sentence in _SENTENCE.split(text):
        found = ner.extract(sentence)
        if len(found) > 1:
            yield found


def build_knowledge_graph(corpus: pd.DataFrame, ner: CyberNER | None = None) -> InMemoryGraph:
    """Build the document/entity graph and the candidate STIX relationships."""
    ner = ner or CyberNER()
    graph = InMemoryGraph()
    rules = {(a, b): rel for a, rel, b in RELATION_RULES}
    derived: dict[tuple[str, str, str], set[str]] = defaultdict(set)

    for row in corpus.itertuples(index=False):
        doc = graph.add_node("Document", row.doc_id, title=row.user[:160], stix_type="report")
        mentioned: dict[str, int] = {}
        for field in ("user", "assistant"):
            text = getattr(row, field)
            for entity in ner.extract(text):
                label = NER_TO_LABEL[entity.label]
                node = graph.node_id(label, entity.key)
                if node not in graph.nodes:
                    graph.add_node(label, entity.key, ner_label=entity.label, stix_type=STIX_TYPE[label])
                mentioned[node] = mentioned.get(node, 0) + 1
            for group in _sentence_entities(text, ner):
                nodes = {(NER_TO_LABEL[e.label], e.key) for e in group}
                for src_label, src_name in nodes:
                    for dst_label, dst_name in nodes:
                        rel = rules.get((src_label, dst_label))
                        if rel and (src_label, src_name) != (dst_label, dst_name):
                            key = (graph.node_id(src_label, src_name), rel, graph.node_id(dst_label, dst_name))
                            derived[key].add(row.doc_id)
        for node, count in mentioned.items():
            graph.add_edge(doc, "MENTIONS", node, source=CORPUS_SOURCE, method="ner", count=count, doc_id=row.doc_id)

    for (src, rel, dst), doc_ids in sorted(derived.items()):
        graph.add_edge(
            src, rel, dst, source=CORPUS_SOURCE, method="sentence_cooccurrence",
            weight=len(doc_ids), doc_ids=sorted(doc_ids)[:MAX_DOC_IDS],
        )
    for node in graph.nodes.values():
        if node.label != "Document":
            node.props["doc_count"] = 0
    for edge in graph.edges:
        if edge.rel == "MENTIONS":
            graph.nodes[edge.dst].props["doc_count"] += 1
    return graph


def graph_summary(graph: InMemoryGraph) -> dict[str, Any]:
    nodes: dict[str, int] = defaultdict(int)
    edges: dict[str, int] = defaultdict(int)
    for node in graph.nodes.values():
        nodes[node.label] += 1
    for edge in graph.edges:
        edges[edge.rel] += 1
    return {"nodes": dict(nodes), "edges": dict(edges), "n_nodes": len(graph.nodes), "n_edges": len(graph.edges)}


def save_graph(graph: InMemoryGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(graph.to_dict(), ensure_ascii=False), encoding="utf-8")


def load_graph(path: Path) -> InMemoryGraph:
    return InMemoryGraph.from_dict(json.loads(path.read_text(encoding="utf-8")))


# ----------------------------------------------------------------------------- Cypher export
def _literal(value: Any) -> str:
    """Cypher literal for a JSON-like value (strings escaped; used only for our own data)."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_literal(v) for v in value) + "]"
    if value is None:
        return "null"
    text = str(value).replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
    return f"'{text}'"


def _map(props: dict[str, Any]) -> str:
    return "{" + ", ".join(f"{k}: {_literal(v)}" for k, v in props.items()) + "}"


def to_cypher_script(graph: InMemoryGraph, batch_size: int = 500) -> str:
    """Idempotent import script for ``cypher-shell -f`` (constraints, then UNWIND/MERGE batches)."""
    lines = ["// Generated by cybersec_nlp.graph.knowledge_graph — STIX 2.1 aligned schema", ""]
    labels = sorted({n.label for n in graph.nodes.values()})
    for label in labels:
        if label not in NODE_LABELS:
            raise ValueError(f"unexpected label {label}")
        lines.append(f"CREATE CONSTRAINT {label.lower()}_name IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE;")
    lines.append("")
    for label in labels:
        rows = [{"name": n.name, **n.props} for n in graph.nodes.values() if n.label == label]
        for start in range(0, len(rows), batch_size):
            chunk = ", ".join(_map(r) for r in rows[start:start + batch_size])
            lines.append(f"UNWIND [{chunk}] AS row MERGE (n:{label} {{name: row.name}}) SET n += row;")
    lines.append("")
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for edge in graph.edges:
        src, dst = graph.nodes[edge.src], graph.nodes[edge.dst]
        groups[(src.label, edge.rel, dst.label)].append({"src": src.name, "dst": dst.name, "props": edge.props})
    for (src_label, rel, dst_label), rows in sorted(groups.items()):
        if rel not in RELATIONSHIPS:
            raise ValueError(f"unexpected relationship {rel}")
        for start in range(0, len(rows), batch_size):
            chunk = ", ".join(_map(r) for r in rows[start:start + batch_size])
            lines.append(
                f"UNWIND [{chunk}] AS row MATCH (a:{src_label} {{name: row.src}}) "
                f"MATCH (b:{dst_label} {{name: row.dst}}) MERGE (a)-[r:{rel}]->(b) SET r += row.props;"
            )
    return "\n".join(lines) + "\n"


ANALYST_QUERIES = """// Requêtes analyste SOC (Neo4j Browser ou cypher-shell)

// 1. Logiciels affectés par une CVE (relations candidates, avec preuves)
MATCH (v:Vulnerability)-[r:AFFECTS]->(s:Software)
RETURN v.name AS cve, s.name AS software, r.weight AS documents, r.doc_ids[0..3] AS preuves
ORDER BY documents DESC LIMIT 25;

// 2. Techniques utilisées par un acteur
MATCH (a:ThreatActor {name: 'apt29'})-[r:USES]->(t)
RETURN labels(t)[0] AS type, t.name AS element, r.weight AS documents ORDER BY documents DESC;

// 3. Documents qui mentionnent une technique et un malware
MATCH (d:Document)-[:MENTIONS]->(:AttackPattern {name: 'lateral movement'}),
      (d)-[:MENTIONS]->(m:Malware)
RETURN d.name AS doc_id, d.title AS question, m.name AS malware LIMIT 20;

// 4. Secteurs ciblés et vecteurs associés
MATCH (p:AttackPattern)-[r:TARGETS]->(t:Target)
RETURN t.name AS secteur, collect(p.name)[0..8] AS vecteurs, sum(r.weight) AS poids ORDER BY poids DESC;

// 5. Entités les plus citées (hubs) par type
MATCH (d:Document)-[:MENTIONS]->(e)
RETURN labels(e)[0] AS type, e.name AS entite, count(d) AS documents ORDER BY documents DESC LIMIT 30;

// 6. Indicateurs (IP, hash) et ce qu'ils indiquent
MATCH (i:Indicator)-[r:INDICATES]->(x) RETURN i.name, labels(x)[0], x.name, r.doc_ids LIMIT 25;
"""


def export_neo4j_scripts(graph: InMemoryGraph, directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    import_path, queries_path = directory / "import.cypher", directory / "queries.cypher"
    import_path.write_text(to_cypher_script(graph), encoding="utf-8")
    queries_path.write_text(ANALYST_QUERIES, encoding="utf-8")
    return import_path, queries_path
