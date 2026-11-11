"""Incident report triage: category, entities, linked graph nodes and draft SIEM rule."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend import api_client
from frontend.views.common import call, highlight_entities, legend
from frontend.views.siem import render_rule

EXAMPLE = ("Our hospital was hit by LockBit ransomware. The attackers exploited CVE-2023-4966 in Citrix NetScaler, "
           "used mimikatz for lateral movement over SMB and beaconed to 89.62.172.13 and 10.0.0.5.")


def render() -> None:
    st.title("🏷️ Analyse de rapport d'incident")
    st.caption("Tri automatique (catégorie SOC), extraction des entités cyber alignées STIX 2.1, liaison au graphe "
               "et brouillon de règle SIEM à partir des indicateurs valides.")
    text = st.text_area("Rapport (texte libre)", value=st.session_state.get("report_text", EXAMPLE), height=160)
    if not st.button("Analyser", type="primary") or not text.strip():
        return
    st.session_state.report_text = text
    result = call(api_client.analyze, text, spinner="Analyse…")
    if not result:
        return

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Catégorie")
        probabilities = pd.Series(result["probabilities"], name="probabilité")
        st.metric("Catégorie prédite", result["category"], f"{probabilities.iloc[0]:.0%} de confiance",
                  delta_color="off")
        if probabilities.iloc[0] - probabilities.iloc[1] < 0.05:
            st.warning(f"Confiance faible : « {probabilities.index[0]} » et « {probabilities.index[1]} » sont presque "
                       "à égalité. À confirmer par l'analyste.")
        st.bar_chart(probabilities.sort_values(), horizontal=True, height=260)
        st.caption("Termes les plus indicatifs de cette catégorie : " + ", ".join(result["explanation"]))
    with right:
        st.subheader("Entités")
        st.markdown(highlight_entities(text, result["entities"]), unsafe_allow_html=True)
        legend()
        if result["entities"]:
            st.dataframe(pd.DataFrame(result["entities"])[["text", "label", "key"]].drop_duplicates(),
                         hide_index=True, use_container_width=True)
        st.markdown("**Nœuds du graphe liés :** " + (", ".join(f"`{n}`" for n in result["linked_nodes"]) or "aucun"))

    st.subheader("Brouillon de règle SIEM")
    if result["draft_rule"]:
        render_rule(result["draft_rule"], key="report")
    else:
        st.info("Aucun indicateur (IP, empreinte SHA-256) dans ce rapport.")
