"""Triage: qualification of an incident report (priority, category, TTPs, IOC, playbook) and case opening."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from frontend import api_client
from frontend.views.common import call, case, highlight_entities, legend, log, open_case, pill, priority_badge

EXAMPLES = {
    "Rançongiciel sur un hôpital": (
        "Alerte EDR 03:12 — le serveur de fichiers du service radiologie de l'hôpital chiffre ses partages. "
        "Note de rançon LockBit. L'accès initial semble venir de l'exploitation de CVE-2023-4966 sur la passerelle "
        "Citrix NetScaler ; mimikatz a été exécuté puis mouvement latéral via PsExec. Connexions sortantes vers "
        "89.62.172.13 et 10.0.0.5."),
    "Hameçonnage ciblé": (
        "Plusieurs utilisateurs du service comptable ont reçu un e-mail de spear phishing imitant le DAF avec une "
        "fausse facture. Deux personnes ont saisi leurs identifiants sur la page de connexion frauduleuse ; des "
        "connexions depuis 185.220.101.5 ont été observées ensuite."),
    "Kerberoasting": (
        "Le SIEM signale un volume anormal de demandes de tickets de service Kerberos (événement 4769, chiffrement "
        "RC4) depuis le poste WS-042 : suspicion de kerberoasting, suivie de tentatives de pass-the-hash vers les "
        "contrôleurs de domaine."),
}


def _render_qualification(text: str, result: dict[str, Any]) -> None:
    priority = result["priority"]
    head = st.columns([1.2, 1, 1])
    with head[0]:
        st.markdown("**Priorité suggérée**")
        st.markdown(priority_badge(priority["code"], priority["label"]), unsafe_allow_html=True)
        st.caption(f"{priority['response']} · escalade : **{priority['escalation']}**")
    with head[1]:
        probabilities = pd.Series(result["probabilities"])
        st.markdown("**Catégorie**")
        st.markdown(f"{result['category']}  \n<span style='opacity:.7'>confiance {probabilities.iloc[0]:.0%}</span>",
                    unsafe_allow_html=True)
        if probabilities.iloc[0] - probabilities.iloc[1] < 0.05:
            st.caption(f"⚠️ proche de « {probabilities.index[1]} » : à confirmer")
    with head[2]:
        exportable = sum(i["exportable"] for i in result["iocs"])
        st.metric("IOC exploitables", f"{exportable} / {len(result['iocs'])}")
    with st.expander("Justification de la priorité"):
        for reason in priority["reasons"]:
            st.markdown(f"- {reason}")
        st.caption("Heuristique transparente : chaque signal du signalement ajoute des points. À confirmer ou "
                   "corriger par l'analyste.")

    st.markdown("#### TTP — MITRE ATT&CK")
    if result["attack"]:
        colors = {"technique": "#1d4ed8", "software": "#7c3aed", "group": "#be185d"}
        st.markdown("".join(pill(f"{r['attack_id']} · {r['name']}" + (f" ({r['tactic']})" if r["tactic"] else ""),
                                 colors[r["kind"]], r["url"]) for r in result["attack"]), unsafe_allow_html=True)
        st.caption("Bleu : techniques · violet : logiciels · rose : groupes. Cliquer ouvre la fiche ATT&CK.")
    else:
        st.caption("Aucune technique ATT&CK reconnue dans le signalement.")

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### Indicateurs de compromission")
        if result["iocs"]:
            frame = pd.DataFrame(result["iocs"]).rename(columns={
                "value": "Indicateur", "type": "Type", "verdict": "Verdict", "detail": "Détail",
                "cti_documents": "Base CTI (docs)"}).drop(columns="exportable")
            st.dataframe(frame, hide_index=True, use_container_width=True)
        else:
            st.caption("Aucun IP, empreinte ou CVE dans le signalement.")
    with right:
        st.markdown("#### Entités extraites")
        st.markdown(highlight_entities(text, result["entities"]), unsafe_allow_html=True)
        legend()

    st.markdown("#### Réponse à incident — playbook de référence (NIST SP 800-61)")
    for book in result["playbooks"]:
        with st.expander(f"{book['name']} · {book['source']}", expanded=book is result["playbooks"][0]):
            cols = st.columns(len(book["phases"]))
            for col, (phase, steps) in zip(cols, book["phases"].items()):
                col.markdown(f"**{phase}**")
                for step in steps:
                    col.checkbox(step, key=f"{book['name']}-{phase}-{step}")
    st.caption("À adapter aux procédures internes du SOC.")


def _investigation_question(result: dict[str, Any]) -> str:
    """Pivot on the attack technique (well covered by the CTI base), then on the named threat."""
    by_label: dict[str, str] = {}
    for entity in result["entities"]:
        by_label.setdefault(entity["label"], entity["key"])
    technique = by_label.get("VECTOR") or by_label.get("TOOL")
    threat = by_label.get("MALWARE") or by_label.get("THREAT_ACTOR") or by_label.get("CVE")
    if technique and threat:
        return f"Comment détecter et contenir {technique} ({threat}) ?"
    if technique or threat:
        return f"Comment détecter et contenir {technique or threat} ?"
    return f"Quelles mesures de réponse pour un incident de type {result['category']} ?"


def _actions(text: str, result: dict[str, Any]) -> None:
    st.divider()
    cols = st.columns(3)
    current = case()
    if cols[0].button("📁 Ouvrir le dossier d'incident", type="primary", use_container_width=True,
                      disabled=current is not None and current["report"] == text):
        open_case(text, result)
        st.toast(f"Dossier {case()['id']} ouvert")
        st.rerun()
    if cols[1].button("🔎 Investiguer avec l'assistant", use_container_width=True):
        if case() is None:
            open_case(text, result)
        st.session_state.pending = _investigation_question(result)
        anchor = st.session_state.pending
        log(f"Investigation lancée : « {anchor} »")
        st.switch_page(st.session_state.pages["investigation"])
    if cols[2].button("📤 Créer la règle de détection", use_container_width=True,
                      disabled=not any(i["exportable"] for i in result["iocs"])):
        if case() is None:
            open_case(text, result)
        st.switch_page(st.session_state.pages["detection"])


def render() -> None:
    st.title("🚨 Triage — qualification d'un signalement")
    st.caption("Collez une alerte, un e-mail signalé ou un extrait de journal (français ou anglais). Vigie suggère la "
               "priorité, la catégorie, les TTP ATT&CK, le verdict des IOC enrichis par la base CTI et le playbook.")
    choice = st.segmented_control("Exemples", list(EXAMPLES), selection_mode="single", key="triage_example")
    default = EXAMPLES[choice] if choice else st.session_state.get("triage_text", EXAMPLES["Rançongiciel sur un hôpital"])
    text = st.text_area("Signalement", value=default, height=150)
    if st.button("Qualifier", type="primary"):
        result = call(api_client.analyze, text, spinner="Qualification en cours…")
        if result:
            st.session_state.triage_text, st.session_state.triage_result = text, result
    result = st.session_state.get("triage_result")
    if result and st.session_state.get("triage_text") == text:
        _render_qualification(text, result)
        _actions(text, result)
