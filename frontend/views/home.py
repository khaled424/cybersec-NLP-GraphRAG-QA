"""Analyst workstation: open incident, quick actions and state of the CTI knowledge base."""

from __future__ import annotations

import streamlit as st

from frontend import api_client
from frontend.views.common import call, case, priority_badge

NODE_LABELS = {"Vulnerability": "CVE", "Malware": "Malwares", "ThreatActor": "Acteurs", "AttackPattern": "Techniques",
               "Tool": "Outils", "Indicator": "IOC"}


def render() -> None:
    st.title("🛡️ Poste analyste")
    st.caption("Vigie assiste le SOC sur tout le cycle : **qualification** des signalements, **investigation** "
               "appuyée sur la base CTI, **pivot** dans le graphe, **règles de détection** — chaque élément suggéré "
               "reste à valider par l'analyste.")

    current = case()
    with st.container(border=True):
        st.subheader("Dossier en cours")
        if current is None:
            st.info("Aucun dossier ouvert. Commencez par qualifier un signalement (e-mail, alerte, extrait de journal).")
        else:
            priority = current["triage"]["priority"]
            st.markdown(f"{priority_badge(priority['code'], priority['label'])} &nbsp; **{current['id']}** — "
                        f"{current['title']}", unsafe_allow_html=True)
            cols = st.columns(4)
            cols[0].metric("Statut", current["status"])
            cols[1].metric("Escalade", priority["escalation"])
            cols[2].metric("IOC", len(current["triage"]["iocs"]))
            cols[3].metric("Entrées main courante", len(current["journal"]))

    st.subheader("Actions")
    actions = st.columns(4)
    pages = [("🚨 Qualifier un signalement", "triage"), ("🔎 Investiguer", "investigation"),
             ("🕸️ Pivoter dans la CTI", "pivot"), ("📤 Créer une règle de détection", "detection")]
    for col, (label, path) in zip(actions, pages):
        if col.button(label, use_container_width=True):
            st.switch_page(st.session_state.pages[path])

    st.subheader("Base de connaissances CTI")
    info = call(api_client.status, spinner="Lecture de la base…")
    if info:
        nodes = info["graph"]["nodes"]
        cols = st.columns(len(NODE_LABELS) + 1)
        cols[0].metric("Documents", info["documents"])
        for col, (label, title) in zip(cols[1:], NODE_LABELS.items()):
            col.metric(title, nodes.get(label, 0))
        st.caption(f"Graphe STIX 2.1 : {info['graph']['n_nodes']} nœuds, {info['graph']['n_edges']} relations · "
                   f"LLM : {info['llm'] or 'indisponible (réponses extractives)'} · embeddings : {info['embedding_model']}")
