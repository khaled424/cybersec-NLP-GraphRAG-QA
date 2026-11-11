"""Tests for weak labelling, the leak guard and the incident classifier."""

from cybersec_nlp.nlp.classifier import (
    IncidentClassifier,
    mask_label_keywords,
    top_terms,
    weak_label,
)


def test_weak_label_and_ties() -> None:
    assert weak_label("How to detect a phishing email?") == "Phishing & Social Eng."
    assert weak_label("Tell me a joke") is None


def test_leak_guard_masks_rule_keywords() -> None:
    masked = mask_label_keywords("Ransomware spreads via phishing")
    assert "ransomware" not in masked.lower() and "phishing" not in masked.lower()


def test_classifier_fit_predict_save_load(tmp_path) -> None:
    texts = ["invoice lure link sender spoofed domain"] * 5 + ["encrypted files bitcoin note locker"] * 5
    labels = ["A"] * 5 + ["B"] * 5
    model = IncidentClassifier().fit(texts, labels)
    probs = model.predict_proba("spoofed sender lure")
    assert next(iter(probs)) == "A" and abs(sum(probs.values()) - 1) < 1e-6
    model.save(tmp_path / "m.joblib")
    assert IncidentClassifier.load(tmp_path / "m.joblib").predict(["bitcoin note"]) == ["B"]
    assert top_terms(model, "B", 3)


def test_hybrid_classifier_with_precomputed_embeddings(tmp_path) -> None:
    import numpy as np

    texts = ["invoice lure link sender spoofed domain"] * 5 + ["encrypted files bitcoin note locker"] * 5
    labels = ["A"] * 5 + ["B"] * 5
    emb = np.array([[1.0, 0.0]] * 5 + [[0.0, 1.0]] * 5)
    model = IncidentClassifier(embedding_weight=1.0).fit(texts, labels, emb)
    assert model.predict(texts[:1] + texts[-1:], emb[[0, -1]]) == ["A", "B"]
    model.save(tmp_path / "h.joblib")
    loaded = IncidentClassifier.load(tmp_path / "h.joblib")
    assert loaded.embedding_weight == 1.0 and top_terms(loaded, "A", 2)
