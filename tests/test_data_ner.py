"""Tests for corpus cleaning, cyber NER and the STIX knowledge graph."""

import pandas as pd
import pytest

from cybersec_nlp.data.loading import clean_dataset, is_truncated, normalize_text
from cybersec_nlp.graph.knowledge_graph import (
    build_knowledge_graph,
    extract_corpus_entities,
    graph_summary,
    to_cypher_script,
)
from cybersec_nlp.graph.minicypher import InMemoryGraph
from cybersec_nlp.nlp.ner import CyberNER


def test_normalize_text_strips_think_blocks_and_entities() -> None:
    raw = "<think>hidden</think> A &amp; B\\n  ok <think>unterminated"
    assert normalize_text(raw) == "A & B ok"


@pytest.mark.parametrize("text,expected", [("Done.", False), ("cut in the mid", True), ("", True)])
def test_is_truncated(text: str, expected: bool) -> None:
    assert is_truncated(text) is expected


def test_clean_dataset_dedupes_and_filters() -> None:
    raw = pd.DataFrame({
        "system": ["s"] * 4,
        "user": ["What is phishing attack?", "What is phishing attack?", "hi", None],
        "assistant": ["Short answer here about it.", "A much longer answer about phishing emails, fake invoices and malicious lures.",
                      "x " * 20 + ".", "y"],
    })
    corpus, steps = clean_dataset(raw)
    assert list(corpus["doc_id"]) == ["HF-00001"]
    assert "longer" in corpus.loc[0, "assistant"]
    assert [s.rows for s in steps] == [4, 3, 2, 1]


def test_ner_labels_keys_and_french_aliases() -> None:
    text = "Le rançongiciel LockBit exploite CVE-2023-4966 depuis 185.220.101.5 (T1486) contre les hôpitaux."
    found = {(e.key, e.label) for e in CyberNER().extract(text)}
    assert found == {("ransomware", "VECTOR"), ("lockbit", "MALWARE"), ("CVE-2023-4966", "CVE"),
                     ("185.220.101.5", "IP"), ("T1486", "ATTACK_ID"), ("hospital", "TARGET")}


def test_ner_rejects_invalid_ip_and_prefers_longest_span() -> None:
    ner = CyberNER()
    assert not [e for e in ner.extract("999.1.1.1") if e.label == "IP"]
    assert [(e.text, e.label) for e in ner.extract("spear phishing")] == [("spear phishing", "VECTOR")]


def test_bio_tags_align_with_offsets() -> None:
    text = "APT29 uses mimikatz"
    tokens = [(0, 5), (6, 10), (11, 19)]
    assert CyberNER().bio_tags(tokens, text) == ["B-THREAT_ACTOR", "O", "B-TOOL"]


@pytest.fixture
def corpus() -> pd.DataFrame:
    return pd.DataFrame({
        "doc_id": ["HF-00000", "HF-00001"],
        "raw_index": [0, 1],
        "user": ["How does APT29 use mimikatz?", "Is Log4j affected by CVE-2021-44228?"],
        "assistant": ["APT29 uses mimikatz for lateral movement.", "CVE-2021-44228 affects log4j servers."],
    })


def test_graph_has_mentions_and_typed_relations(corpus: pd.DataFrame) -> None:
    graph = build_knowledge_graph(corpus)
    summary = graph_summary(graph)
    assert summary["nodes"]["Document"] == 2
    rels = {(graph.nodes[e.src].name, e.rel, graph.nodes[e.dst].name) for e in graph.edges if e.rel != "MENTIONS"}
    assert ("apt29", "USES", "mimikatz") in rels and ("CVE-2021-44228", "AFFECTS", "log4j") in rels
    assert all(e.props["source"] for e in graph.edges)
    assert graph.nodes["Tool:mimikatz"].props["doc_count"] == 1


def test_graph_roundtrip_and_entities(corpus: pd.DataFrame) -> None:
    graph = build_knowledge_graph(corpus)
    clone = InMemoryGraph.from_dict(graph.to_dict())
    assert len(clone.nodes) == len(graph.nodes) and len(clone.edges) == len(graph.edges)
    records = extract_corpus_entities(corpus)
    assert {e["field"] for r in records for e in r["entities"]} == {"user", "assistant"}


def test_cypher_script_escapes_quotes() -> None:
    graph = InMemoryGraph()
    doc = graph.add_node("Document", "D'1", title="it's \\\\ tricky")
    tool = graph.add_node("Tool", "nmap")
    graph.add_edge(doc, "MENTIONS", tool, source="x")
    script = to_cypher_script(graph)
    assert "'D\\'1'" in script and "CREATE CONSTRAINT document_name" in script
    assert "MERGE (a)-[r:MENTIONS]->(b)" in script


def test_ner_handles_plurals_without_false_matches() -> None:
    found = {(e.text, e.key) for e in CyberNER().extract("Attacks on hospitals and banks via IIS and Windows.")}
    assert ("hospitals", "hospital") in found and ("banks", "bank") in found
    assert ("IIS", "iis") in found and ("Windows", "windows") in found


def test_version_numbers_are_not_ips() -> None:
    labels = [e.label for e in CyberNER().extract("Section 3.6.5.2 and version 1.2.3.4, host 89.62.172.13")]
    assert labels == ["IP"]


def test_ip_at_end_of_sentence_is_extracted() -> None:
    keys = [e.key for e in CyberNER().extract("Beacon to 89.62.172.13. Then 10.0.0.5.")]
    assert keys == ["89.62.172.13", "10.0.0.5"]


def test_deterministic_torch_restores_previous_state() -> None:
    import os

    import torch

    import cybersec_nlp.config  # noqa: F401 - sets CUBLAS_WORKSPACE_CONFIG on import
    from cybersec_nlp.reproducibility import deterministic_torch

    assert os.environ.get("CUBLAS_WORKSPACE_CONFIG")  # set when cybersec_nlp.config is imported
    before = torch.are_deterministic_algorithms_enabled()
    with deterministic_torch(0):
        assert torch.are_deterministic_algorithms_enabled()
    assert torch.are_deterministic_algorithms_enabled() == before
