"""Tests for schema-guided Text-to-Cypher."""

import pandas as pd
import pytest

from cybersec_nlp.graph.knowledge_graph import build_knowledge_graph
from cybersec_nlp.rag.cypher_templates import SchemaGuidedCypher, asked_label


@pytest.fixture(scope="module")
def translator() -> SchemaGuidedCypher:
    corpus = pd.DataFrame({
        "doc_id": ["HF-00000", "HF-00001", "HF-00002"], "raw_index": [0, 1, 2],
        "user": ["Is log4j affected by CVE-2021-44228?", "Emotet and banks?", "Golden ticket on kerberos"],
        "assistant": ["CVE-2021-44228 affects log4j servers.", "Emotet targets the banking sector.",
                      "A golden ticket attack targets kerberos."],
    })
    return SchemaGuidedCypher(build_knowledge_graph(corpus))


@pytest.mark.parametrize("question,label", [
    ("Which software is affected by X?", "Software"), ("Which attack techniques target kerberos?", "AttackPattern"),
    ("Quels malwares ciblent les banques ?", "Malware"), ("Quels logiciels sont affectés ?", "Software"),
    ("Which documents mention nmap?", "Document"), ("Which threat actors use X?", "ThreatActor"),
    ("How does phishing work?", None),
])
def test_asked_label(question: str, label: str | None) -> None:
    assert asked_label(question) == label


@pytest.mark.parametrize("question,expected", [
    ("Which software is affected by CVE-2021-44228?", {"log4j"}),
    ("Which vulnerabilities affect log4j?", {"CVE-2021-44228"}),
    ("Quels malwares ciblent le secteur bancaire ?", {"emotet"}),
    ("Which software do golden ticket attacks target?", {"kerberos"}),
    ("Which documents mention emotet?", {"HF-00001"}),
])
def test_translate_runs_and_answers(translator: SchemaGuidedCypher, question: str, expected: set[str]) -> None:
    query = translator.translate(question)
    assert query is not None
    assert {r["x.name"] for r in translator.graph.run(query)} == expected


def test_unsupported_question_uses_fallback(translator: SchemaGuidedCypher) -> None:
    assert translator.translate("How does phishing work?") is None
    with_fallback = SchemaGuidedCypher(translator.graph, fallback=lambda q, s: "FALLBACK")
    assert with_fallback("How does phishing work?", translator.graph.schema()) == "FALLBACK"
