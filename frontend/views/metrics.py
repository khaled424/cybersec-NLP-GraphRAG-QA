"""Project metrics dashboard: TDSP acceptance criteria and per-notebook results."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd
import streamlit as st

from frontend import api_client
from frontend.views.common import call

STATUS_ICON = {"atteint": "✅ atteint", "non atteint": "❌ non atteint", "non mesuré": "⏳ non mesuré"}


def _acceptance(rows: list[dict[str, Any]]) -> None:
    frame = pd.DataFrame(rows)
    met = (frame["statut"] == "atteint").sum()
    measured = (frame["statut"] != "non mesuré").sum()
    cols = st.columns(3)
    cols[0].metric("Critères atteints", f"{met} / {len(frame)}")
    cols[1].metric("Critères mesurés", f"{measured} / {len(frame)}")
    cols[2].metric("Taux de réussite (mesurés)", f"{met / measured:.0%}" if measured else "—")
    frame["valeur"] = frame["valeur"].map(lambda v: "—" if v is None or (isinstance(v, float) and math.isnan(v)) else f"{v:.3f}")
    frame["statut"] = frame["statut"].map(STATUS_ICON)
    st.dataframe(frame, hide_index=True, use_container_width=True)
    st.caption("Cibles **proposées** (le rapport TDSP phase 1 laisse les seuils à valider avec l'équipe et le SOC).")


def _records(data: dict[str, Any], key: str) -> pd.DataFrame:
    return pd.DataFrame(data.get(key, []))


def render() -> None:
    st.title("📊 Métriques du projet")
    payload = call(api_client.metrics, spinner="Chargement des métriques…")
    if not payload:
        return
    _acceptance(payload["acceptance"])
    metrics = payload["metrics"]
    tabs = st.tabs(["Données & NER", "Classification & graphes", "LLM & LoRA", "HybridRAG", "Sécurité & agent"])

    with tabs[0]:
        nb1 = metrics.get("notebook1", {})
        if nb1:
            st.markdown("**Nettoyage** (lignes conservées par étape)")
            st.bar_chart(pd.Series(nb1["cleaning"]), horizontal=True)
            st.markdown("**Représentations du texte** (Notebook 1, section 11)")
            st.dataframe(pd.DataFrame(nb1["vectorisation"]).set_index("représentation"), use_container_width=True)
            st.markdown("**NER SecBERT**")
            ner = nb1["ner"]
            c = st.columns(4)
            c[0].metric("Micro-F1", f"{ner['micro_f1']:.3f}")
            c[1].metric("Macro-F1", f"{ner['macro_f1']:.3f}")
            c[2].metric("Rappel entités inconnues", f"{ner['unseen_entity_recall']:.1%}")
            c[3].metric("Règles (inconnues)", f"{ner['rule_based_unseen_recall']:.0%}")
        else:
            st.info("Exécuter le Notebook 1 pour ces métriques.")
    with tabs[1]:
        nb2a, nb2b, pipe = metrics.get("notebook2a", {}), metrics.get("notebook2b", {}), metrics.get("pipeline", {})
        if pipe:
            st.metric("Classifieur de triage du MVP (macro-F1, test)", f"{pipe['classifier']['macro_f1']:.3f}")
        if nb2a:
            st.markdown("**Texte seul vs GNN (Notebook 2A)**")
            frame = _records(nb2a, "results")
            frame["modèle"] = frame["Modèle"] + " · " + frame["Graphe"]
            st.bar_chart(frame.set_index("modèle")["macro-F1"].sort_values(), horizontal=True)
        if nb2b:
            st.markdown("**HGT & Leiden (Notebook 2B)**")
            st.dataframe(_records(nb2b, "robustness_5_seeds"), hide_index=True, use_container_width=True)
            leiden = nb2b["leiden"]
            c = st.columns(3)
            c[0].metric("Modularité L0", f"{leiden['modularity_l0']:.3f}")
            c[1].metric("NMI vs thèmes", f"{leiden['nmi_vs_topics']:.3f}")
            c[2].metric("Clusters finaux", leiden["clusters_final"])
    with tabs[2]:
        nb3 = metrics.get("notebook3", {})
        if nb3:
            st.markdown("**Base vs LoRA (questions de test)**")
            frame = _records(nb3, "evaluation").set_index("modèle")
            st.bar_chart(frame[["ROUGE-L", "BERTScore F1", "FactCC (cohérentes)"]].T, stack=False)
            st.markdown("**Stratégies de prompt**")
            st.dataframe(_records(nb3, "prompting").set_index("stratégie"), use_container_width=True)
        else:
            st.info("Exécuter le Notebook 3 pour ces métriques.")
    with tabs[3]:
        nb4a = metrics.get("notebook4a", {})
        if nb4a:
            st.markdown("**Recherche sur le corpus réel (300 questions)**")
            st.dataframe(_records(nb4a, "real_retrieval").set_index("strategy"), use_container_width=True)
            st.markdown("**Réponses générées**")
            st.dataframe(pd.Series(nb4a["real_answers"], name="valeur").to_frame(), use_container_width=True)
    with tabs[4]:
        nb4b = metrics.get("notebook4b", {})
        if nb4b:
            st.markdown("**Agent Text-to-Cypher (graphe réel)**")
            st.dataframe(_records(nb4b, "real_agent").set_index("configuration"), use_container_width=True)
            poison = nb4b["real_poisoning"]
            c = st.columns(4)
            c[0].metric("Précision quarantaine", f"{poison['précision']:.2f}")
            c[1].metric("Rappel quarantaine", f"{poison['rappel']:.2f}")
            c[2].metric("Faux positifs (graphe sain)", poison["faux positifs sur le graphe sain"])
            c[3].metric("Fuites inter-locataires", nb4b["llm08"]["leaks_fixed"])
            st.markdown("**Inversion d'embeddings vs bruit**")
            st.line_chart(pd.DataFrame(nb4b["llm08"]["inversion"]).set_index("sigma"))
