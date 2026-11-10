"""Tests for the in-memory Cypher backend and the ReAct agent."""

import pytest

from cybersec_nlp.graph.minicypher import CypherError, InMemoryGraph
from cybersec_nlp.rag.agentic import AgenticRAG, schema_repairer


@pytest.fixture
def graph() -> InMemoryGraph:
    g = InMemoryGraph()
    apt = g.add_node("Actor", "APT29")
    emo = g.add_node("Malware", "Emotet", family="loader")
    cob = g.add_node("Malware", "CobaltStrike")
    g.add_edge(apt, "USES", emo, source="mitre")
    g.add_edge(apt, "USES", cob, source="mitre")
    return g


def test_valid_query_returns_rows(graph: InMemoryGraph) -> None:
    rows = graph.run("MATCH (a:Actor {name: 'APT29'})-[:USES]->(m:Malware) RETURN m.name")
    assert {r["m.name"] for r in rows} == {"Emotet", "CobaltStrike"}


def test_reverse_direction(graph: InMemoryGraph) -> None:
    rows = graph.run("MATCH (m:Malware {name: 'Emotet'})<-[:USES]-(a:Actor) RETURN a.name")
    assert [r["a.name"] for r in rows] == ["APT29"]


@pytest.mark.parametrize("clause", ["CREATE (x:Actor)", "MATCH (a)-[:USES]->(b) DELETE a"])
def test_write_clauses_rejected(graph: InMemoryGraph, clause: str) -> None:
    with pytest.raises(CypherError, match="read-only"):
        graph.run(clause)


def test_unknown_relationship_error_lists_schema(graph: InMemoryGraph) -> None:
    with pytest.raises(CypherError, match="USES"):
        graph.run("MATCH (a:Actor)-[:USES_MALWARE]->(m:Malware) RETURN m.name")


def test_agent_repairs_hallucinated_schema(graph: InMemoryGraph) -> None:
    def bad_generator(question: str, schema) -> str:
        return "MATCH (a:Threat_Actor {name: 'APT29'})-[:USES_MALWARE]->(m:Malware) RETURN m.name"

    result = AgenticRAG(graph, bad_generator).ask("Which malware does APT29 use?")
    assert result.success and result.repaired
    assert ":USES]" in result.final_query and "Threat_Actor" not in result.final_query
    assert sum("ERROR" in s.observation for s in result.trace) == 2


def test_agent_aborts_when_unrepairable(graph: InMemoryGraph) -> None:
    result = AgenticRAG(graph, lambda q, s: "not cypher").ask("?")
    assert not result.success and result.trace[-1].observation == "ABORT"


def test_agent_respects_step_budget(graph: InMemoryGraph) -> None:
    flip = iter(["MATCH (a:X)-[:USES]->(b) RETURN b.name", "MATCH (a:Y)-[:USES]->(b) RETURN b.name"] * 5)
    agent = AgenticRAG(graph, lambda q, s: next(flip), repairer=lambda q, e, s: next(flip), max_steps=2)
    assert not agent.ask("?").success


def test_schema_repairer_is_noop_on_unrelated_error(graph: InMemoryGraph) -> None:
    assert schema_repairer("q", "Syntax error", graph.schema()) == "q"
