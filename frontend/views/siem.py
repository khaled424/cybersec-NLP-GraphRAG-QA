"""SIEM rule builder (Splunk SPL / Microsoft Sentinel KQL) with strict IOC validation."""

from __future__ import annotations

import re
from typing import Any

import streamlit as st

from frontend import api_client
from frontend.views.common import call

SEVERITIES = ["low", "medium", "high", "critical"]


def render_rule(rule: dict[str, Any], key: str) -> None:
    if not rule.get("valid"):
        st.error(rule.get("error", "Règle invalide"))
        return
    indicators = rule["indicators"]
    st.success(f"Indicateurs retenus : {sum(len(v) for v in indicators.values())} · rejetés : {len(rule['rejected'])}")
    if rule["rejected"]:
        with st.expander("Indicateurs rejetés (et pourquoi)"):
            for reason in rule["rejected"]:
                st.markdown(f"- {reason}")
    tabs = st.tabs(["Splunk SPL", "Sentinel KQL", "savedsearches.conf", "Règle Sentinel (JSON)"])
    files = [("spl", "rule.spl", "sql"), ("kql", "rule.kql", "sql"),
             ("splunk_savedsearch", "savedsearches.conf", "ini"), ("sentinel_rule", "sentinel_rule.json", "json")]
    for tab, (field, filename, language) in zip(tabs, files):
        with tab:
            st.code(rule[field], language=language)
            st.download_button(f"Télécharger {filename}", rule[field], file_name=filename, key=f"{key}-{field}")


def _split(text: str) -> list[str]:
    return [v for v in re.split(r"[\s,;]+", text) if v]


def render() -> None:
    st.title("📤 Règles SIEM")
    st.caption("Chaque indicateur est validé (format, plages internes/réservées/documentation, infrastructure "
               "bénigne connue) puis échappé : un IOC piégé venant du graphe ne peut pas modifier la requête.")
    with st.form("siem"):
        name = st.text_input("Nom de la règle", "CTI - Infrastructure C2")
        col1, col2 = st.columns(2)
        technique = col1.text_input("Technique MITRE ATT&CK", "T1071.001")
        severity = col2.select_slider("Sévérité", SEVERITIES, value="high")
        ips = st.text_area("Adresses IP", "89.62.172.13\n10.0.0.5\n8.8.8.8\n1.2.3.4\") | delete index=*")
        domains = st.text_area("Domaines", "c2-update.example-cdn.net")
        hashes = st.text_area("SHA-256", "")
        submitted = st.form_submit_button("Générer", type="primary")
    if submitted:
        payload = {"name": name, "technique": technique, "severity": severity, "ips": _split(ips),
                   "domains": _split(domains), "sha256": _split(hashes)}
        rule = call(api_client.siem_rule, payload, spinner="Validation des indicateurs…")
        if rule:
            render_rule(rule, key="builder")
