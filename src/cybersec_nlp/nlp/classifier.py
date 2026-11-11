"""SOC report triage: weak labelling rules (Notebook 2A) and an inductive text classifier.

The dataset has no class column, so categories come from keyword rules (*weak supervision*).
To avoid the model simply re-reading the rules, every rule keyword is masked from the text
given to the model (``LEAK_GUARD``). The classifier (TF-IDF + logistic regression) is the
deployable "text only" model of Notebook 2A: unlike the transductive GNN it can score a new
report on its own, which is what the MVP needs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

# Rules authored by Membre 2 (Notebook 2A). stems match word prefixes, exact match whole words.
LABEL_SPEC: dict[str, dict[str, list[str]]] = {
    "Phishing & Social Eng.": {
        "stems": ["phish", "social engineering", "vishing", "smishing", "spear", "pretext",
                  "impersonat", "business email compromise"],
        "exact": ["bec"],
    },
    "Malware & Ransomware": {
        "stems": ["malware", "ransomware", "trojan", "botnet", "rootkit", "keylogger", "spyware",
                  "backdoor", "worm", "virus", "infostealer", "dropper", "command and control", "obfuscat"],
        "exact": ["c2"],
    },
    "Vulnerability & Exploit": {
        "stems": ["vulnerab", "exploit", "patch", "zero-day", "zero day", "buffer overflow",
                  "remote code execution", "privilege escalation", "cvss", "memory corruption", "use-after-free"],
        "exact": ["rce"],
    },
    "Web App Attacks": {
        "stems": ["sql injection", "cross-site", "injection", "owasp", "web application", "web app",
                  "api security", "session hijack", "deserializ"],
        "exact": ["xss", "csrf", "ssrf", "xxe", "waf"],
    },
    "Network & Intrusion": {
        "stems": ["firewall", "intrusion", "ddos", "denial of service", "port scan", "network segmentation",
                  "packet", "lateral movement", "vpn", "network traffic", "wireless", "wi-fi"],
        "exact": ["dns"],
    },
    "Identity & Crypto": {
        "stems": ["authentic", "authoriz", "password", "credential", "encrypt", "cryptograph", "certificate",
                  "single sign", "access control", "privileged access", "identit"],
        "exact": ["mfa", "sso", "pki", "iam", "tls", "ssl", "oauth", "saml", "oidc"],
    },
    "Cloud & Governance": {
        "stems": ["cloud", "container", "kubernetes", "compliance", "governance", "risk", "audit", "polic",
                  "regulat", "gdpr", "nist", "iso 27001", "devsecops", "supply chain", "azure"],
        "exact": ["aws", "gcp"],
    },
    "Detection & IR (SOC)": {
        "stems": ["siem", "incident response", "forensic", "threat hunting", "threat intelligence", "detection",
                  "monitor", "log analysis", "sigma", "yara", "playbook", "indicator of compromise"],
        "exact": ["soc", "edr", "ioc"],
    },
}


def _compile(spec: dict[str, list[str]]) -> re.Pattern[str]:
    parts = [rf"\b{re.escape(s)}\w*" for s in spec["stems"]] + [rf"\b{re.escape(e)}\b" for e in spec["exact"]]
    return re.compile("|".join(parts), re.IGNORECASE)


LABEL_RX = {name: _compile(spec) for name, spec in LABEL_SPEC.items()}
ALL_LABEL_RX = re.compile("|".join(rx.pattern for rx in LABEL_RX.values()), re.IGNORECASE)


def weak_label(question: str) -> str | None:
    """Category whose rules match most often in the question (ties: dictionary order)."""
    scores = {name: len(rx.findall(question or "")) for name, rx in LABEL_RX.items()}
    best = max(scores.values())
    return None if best == 0 else next(name for name, score in scores.items() if score == best)


def mask_label_keywords(text: str) -> str:
    """Leak guard: remove every rule keyword from the model input."""
    return ALL_LABEL_RX.sub(" ", text)


def clean_text(text: str) -> str:
    text = re.sub(r"https?://\S+", " ", text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(w for w in text.split() if w not in ENGLISH_STOP_WORDS and len(w) > 2)


@dataclass
class TrainingReport:
    classes: list[str]
    n_train: int
    n_test: int
    macro_f1: float
    accuracy: float
    per_class: dict[str, dict[str, float]]


class IncidentClassifier:
    """TF-IDF (1-2 grams) + balanced logistic regression on leak-guarded text."""

    def __init__(self) -> None:
        self.pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, max_features=30000)),
            ("lr", LogisticRegression(max_iter=2000, class_weight="balanced")),
        ])

    @staticmethod
    def prepare(text: str) -> str:
        return clean_text(mask_label_keywords(text))

    def fit(self, texts: list[str], labels: list[str]) -> IncidentClassifier:
        self.pipeline.fit([self.prepare(t) for t in texts], labels)
        return self

    @property
    def classes(self) -> list[str]:
        return [str(c) for c in self.pipeline.classes_]

    def predict_proba(self, text: str) -> dict[str, float]:
        probs = self.pipeline.predict_proba([self.prepare(text)])[0]
        return dict(sorted(zip(map(str, self.classes), map(float, probs)), key=lambda kv: -kv[1]))

    def predict(self, texts: list[str]) -> list[str]:
        return list(self.pipeline.predict([self.prepare(t) for t in texts]))

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.pipeline, path)

    @classmethod
    def load(cls, path: Path) -> IncidentClassifier:
        model = cls()
        model.pipeline = joblib.load(path)
        return model


def train_and_evaluate(
    questions: list[str], texts: list[str], min_per_class: int = 40, seed: int = 42
) -> tuple[IncidentClassifier, TrainingReport]:
    """Weak-label the questions, keep classes with enough examples, train on 80 %, test on 20 %."""
    labels = [weak_label(q) for q in questions]
    pairs = [(t, lab) for t, lab in zip(texts, labels) if lab is not None]
    counts: dict[str, int] = {}
    for _, lab in pairs:
        counts[lab] = counts.get(lab, 0) + 1
    pairs = [(t, lab) for t, lab in pairs if counts[lab] >= min_per_class]
    x, y = zip(*pairs)
    x_tr, x_te, y_tr, y_te = train_test_split(list(x), list(y), test_size=0.2, stratify=y, random_state=seed)
    model = IncidentClassifier().fit(x_tr, y_tr)
    pred = model.predict(x_te)
    report = classification_report(y_te, pred, output_dict=True, zero_division=0)
    per_class = {c: {k: float(report[c][k]) for k in ("precision", "recall", "f1-score", "support")}
                 for c in model.classes}
    return model, TrainingReport(
        classes=model.classes, n_train=len(x_tr), n_test=len(x_te),
        macro_f1=float(f1_score(y_te, pred, average="macro")),
        accuracy=float(accuracy_score(y_te, pred)), per_class=per_class,
    )


def top_terms(model: IncidentClassifier, label: str, n: int = 8) -> list[str]:
    """Most positive TF-IDF terms of a class (explainability in the MVP)."""
    vocab = np.array(model.pipeline.named_steps["tfidf"].get_feature_names_out())
    coef = model.pipeline.named_steps["lr"].coef_
    index = model.classes.index(label)
    # Binary logistic regression stores a single row: weights of class 1 (class 0 = opposite).
    coef = (coef[0] if index == 1 else -coef[0]) if coef.shape[0] == 1 else coef[index]
    return vocab[np.argsort(coef)[::-1][:n]].tolist()
