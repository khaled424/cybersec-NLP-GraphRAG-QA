"""Consolidated metrics of the whole project and TDSP acceptance check (master notebook, MVP).

Each notebook writes ``reports/metrics/<name>_metrics.json``. This module reads them and
compares key values with the **proposed** acceptance thresholds below. The TDSP phase 1
report leaves the thresholds to be validated by the team and the SOC: they are explicit
here so the discussion starts from numbers.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from cybersec_nlp import config

METRIC_FILES = {
    "pipeline": "pipeline_metrics.json",
    "notebook1": "notebook1_metrics.json",
    "notebook2a": "notebook2a_metrics.json",
    "notebook2b": "notebook2b_metrics.json",
    "notebook3": "notebook3_metrics.json",
    "notebook4a": "notebook4a_metrics.json",
    "notebook4b": "notebook4b_metrics.json",
}


def load_metrics() -> dict[str, dict[str, Any]]:
    """All available metric files (missing notebooks are simply absent)."""
    out = {}
    for name, filename in METRIC_FILES.items():
        path = config.METRICS_DIR / filename
        if path.exists():
            out[name] = json.loads(path.read_text(encoding="utf-8"))
    return out


def _row(rows: list[dict[str, Any]], key: str, value: str) -> dict[str, Any]:
    return next(r for r in rows if r.get(key) == value)


@dataclass(frozen=True)
class Criterion:
    need: str
    metric: str
    owner: str
    target: float
    higher_is_better: bool
    extract: Callable[[dict[str, dict[str, Any]]], float]


CRITERIA: tuple[Criterion, ...] = (
    Criterion("Tri des rapports", "Macro-F1 classifieur de triage (texte, 7 catégories)", "Notebook 2A / MVP", 0.50, True,
              lambda m: m["pipeline"]["classifier"]["macro_f1"]),
    Criterion("Extraction d'entités", "Micro-F1 NER SecBERT (vs étiquettes silver)", "Notebook 1", 0.85, True,
              lambda m: m["notebook1"]["ner"]["micro_f1"]),
    Criterion("Extraction d'entités", "Rappel sur entités jamais vues (généralisation)", "Notebook 1", 0.20, True,
              lambda m: m["notebook1"]["ner"]["unseen_entity_recall"]),
    Criterion("Cartographie des attaques", "Modularité Leiden (niveau 0)", "Notebook 2B", 0.30, True,
              lambda m: m["notebook2b"]["leiden"]["modularity_l0"]),
    Criterion("Assistant QA", "Recall@4 recherche hybride (known-item, 300 questions)", "Notebook 4A", 0.70, True,
              lambda m: _row(m["notebook4a"]["real_retrieval"], "strategy", "hybrid")["Recall@4"]),
    Criterion("Assistant QA", "Abstention correcte hors domaine", "Notebook 4A", 0.90, True,
              lambda m: m["notebook4a"]["real_answers"]["abstention correcte hors domaine"]),
    Criterion("Assistant QA", "Phrases générées étayées par les preuves", "Notebook 4A", 0.80, True,
              lambda m: m["notebook4a"]["real_answers"]["phrases étayées (moyenne)"]),
    Criterion("Assistant QA", "Latence de génération (s)", "Notebook 4A", 10.0, False,
              lambda m: m["notebook4a"]["real_answers"]["latence génération (s)"]),
    Criterion("LLM adapté au domaine", "BERTScore F1 du modèle LoRA (questions de test)", "Notebook 3", 0.80, True,
              lambda m: _row(m["notebook3"]["evaluation"], "modèle", "LoRA (fine-tuné)")["BERTScore F1"]),
    Criterion("Sécurité", "Détection d'injections de prompt", "Notebook 3", 0.90, True,
              lambda m: m["notebook3"]["guardrail"]["detection_rate"]),
    Criterion("Sécurité", "Faux positifs du garde-fou", "Notebook 3", 0.10, False,
              lambda m: m["notebook3"]["guardrail"]["false_positive_rate"]),
    Criterion("Sécurité", "Rappel de la quarantaine (empoisonnement du graphe réel)", "Notebook 4B", 0.90, True,
              lambda m: m["notebook4b"]["real_poisoning"]["rappel"]),
    Criterion("Sécurité", "Précision de la quarantaine", "Notebook 4B", 0.90, True,
              lambda m: m["notebook4b"]["real_poisoning"]["précision"]),
    Criterion("Sécurité", "Fuites inter-locataires (OWASP LLM08)", "Notebook 4B", 0.0, False,
              lambda m: m["notebook4b"]["llm08"]["leaks_fixed"]),
    Criterion("Graph-RAG agentique", "Réponses exactes Text-to-Cypher avec agent", "Notebook 4B", 0.50, True,
              lambda m: _row(m["notebook4b"]["real_agent"], "configuration", "Agent + réparation LLM")["exacte"]),
)


def acceptance_table(metrics: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """One row per criterion: value, proposed target and status (met / not met / not measured)."""
    metrics = load_metrics() if metrics is None else metrics
    rows = []
    for c in CRITERIA:
        try:
            value = float(c.extract(metrics))
        except (KeyError, StopIteration, TypeError, IndexError):
            value = math.nan
        if math.isnan(value):
            status = "non mesuré"
        else:
            met = value >= c.target if c.higher_is_better else value <= c.target
            status = "atteint" if met else "non atteint"
        rows.append({"besoin": c.need, "métrique": c.metric, "source": c.owner, "valeur": value,
                     "cible proposée": ("≥ " if c.higher_is_better else "≤ ") + f"{c.target:g}", "statut": status})
    return rows
