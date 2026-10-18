"""Smoke tests for machine-learning package imports."""


def test_ml_modules_are_importable() -> None:
    from ml.models import classifier, gnn, ner
    from ml.pipelines import train

    assert classifier is not None
    assert gnn is not None
    assert ner is not None
    assert train is not None
