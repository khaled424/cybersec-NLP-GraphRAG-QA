"""Smoke tests for NLP package imports."""


def test_nlp_modules_are_importable() -> None:
    from cybersec_nlp.features import preprocessing
    from cybersec_nlp.graph import knowledge_graph
    from cybersec_nlp.nlp import classifier, ner

    assert all(m is not None for m in (classifier, ner, preprocessing, knowledge_graph))
