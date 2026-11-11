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
