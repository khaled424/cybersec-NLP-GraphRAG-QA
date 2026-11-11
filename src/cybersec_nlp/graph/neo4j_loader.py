"""Load the knowledge graph into a running Neo4j with parameterised, batched queries.

Configuration comes from the environment: ``NEO4J_URI``, ``NEO4J_USERNAME``,
``NEO4J_PASSWORD`` and optionally ``NEO4J_DATABASE``. Labels and relationship types are
checked against the schema whitelist before being placed in a query (they cannot be
parameterised in Cypher); every value is passed as a parameter.
"""

from __future__ import annotations

import os
from collections import defaultdict

from cybersec_nlp.graph.knowledge_graph import NODE_LABELS, RELATIONSHIPS
from cybersec_nlp.graph.minicypher import InMemoryGraph


def neo4j_settings() -> dict[str, str] | None:
    keys = ("NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD")
    if not all(os.getenv(k) for k in keys):
        return None
    return {
        "uri": os.environ["NEO4J_URI"], "user": os.environ["NEO4J_USERNAME"],
        "password": os.environ["NEO4J_PASSWORD"], "database": os.getenv("NEO4J_DATABASE", "neo4j"),
    }


def load_into_neo4j(graph: InMemoryGraph, settings: dict[str, str], batch_size: int = 1000) -> dict[str, int]:
    from neo4j import GraphDatabase

    nodes: dict[str, list[dict]] = defaultdict(list)
    for node in graph.nodes.values():
        nodes[node.label].append({"name": node.name, "props": node.props})
    edges: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for edge in graph.edges:
        key = (graph.nodes[edge.src].label, edge.rel, graph.nodes[edge.dst].label)
        edges[key].append({"src": graph.nodes[edge.src].name, "dst": graph.nodes[edge.dst].name, "props": edge.props})

    driver = GraphDatabase.driver(settings["uri"], auth=(settings["user"], settings["password"]))
    with driver, driver.session(database=settings["database"]) as session:
        for label, rows in nodes.items():
            _check(label, NODE_LABELS)
            session.run(f"CREATE CONSTRAINT {label.lower()}_name IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE")
            for start in range(0, len(rows), batch_size):
                session.run(
                    f"UNWIND $rows AS row MERGE (n:{label} {{name: row.name}}) SET n += row.props",
                    rows=rows[start:start + batch_size],
                )
        for (src, rel, dst), rows in edges.items():
            for value, allowed in ((src, NODE_LABELS), (rel, RELATIONSHIPS), (dst, NODE_LABELS)):
                _check(value, allowed)
            for start in range(0, len(rows), batch_size):
                session.run(
                    f"UNWIND $rows AS row MATCH (a:{src} {{name: row.src}}) MATCH (b:{dst} {{name: row.dst}}) "
                    f"MERGE (a)-[r:{rel}]->(b) SET r += row.props",
                    rows=rows[start:start + batch_size],
                )
    return {"nodes": len(graph.nodes), "edges": len(graph.edges)}


def _check(value: str, allowed: tuple[str, ...]) -> None:
    if value not in allowed:
        raise ValueError(f"{value!r} is not part of the graph schema")
