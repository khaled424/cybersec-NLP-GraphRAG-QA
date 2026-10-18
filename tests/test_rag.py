"""Smoke tests for Graph-RAG package imports."""


def test_rag_modules_are_importable() -> None:
    from ml.rag import generator, pipeline, retriever

    assert generator is not None
    assert pipeline is not None
    assert retriever is not None
