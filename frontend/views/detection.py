"""Detection engineering: Splunk SPL / Microsoft Sentinel KQL rules from validated IOCs."""

from __future__ import annotations

import re
from typing import Any

import streamlit as st

from frontend import api_client
from frontend.views.common import call, case, case_banner, log

SEVERITIES = {"low": "Basse", "medium": "Moyenne", "high": "Élevée", "critical": "Critique"}
PRIORITY_TO_SEVERITY = {"P1": "critical", "P2": "high", "P3": "medium", "P4": "low"}


def render_rule(rule: dict[str, Any], key: str) -> None:
    if not rule.get("valid"):
        st.error(rule.get("error", "Règle invalide"))
        return
    indicators = rule["indicators"]
    st.success(f"Indicateurs retenus : {sum(len(v) for v in indicators.values())} · écartés : {len(rule['rejected'])}")
    if rule["rejected"]:
        with st.expander("Indicateurs écartés (motif)"):
            for reason in rule["rejected"]:
                st.markdown(f"- {reason}")
    tabs = st.tabs(["Splunk SPL", "Microsoft Sentinel KQL", "savedsearches.conf", "Règle analytique Sentinel (JSON)"])
    files = [("spl", "regle.spl", "sql"), ("kql", "regle.kql", "sql"),
             ("splunk_savedsearch", "savedsearches.conf", "ini"), ("sentinel_rule", "regle_sentinel.json", "json")]
    for tab, (field, filename, language) in zip(tabs, files):
        with tab:
            st.code(rule[field], language=language)
            st.download_button(f"Télécharger {filename}", rule[field], file_name=filename, key=f"{key}-{field}")


def _split(text: str) -> list[str]:
    return [v for v in re.split(r"[\s,;]+", text) if v]


def _defaults() -> dict[str, Any]:
    """Pre-fill from the open incident: exportable IOCs, first ATT&CK technique, severity from priority."""
    current = case()
    if current is None:
        return {"name": "CTI - Infrastructure de commande et contrôle", "technique": "T1071.001", "severity": "high",
                "ips": "89.62.172.13\n10.0.0.5\n8.8.8.8", "sha256": ""}
    triage = current["triage"]
    techniques = [r["attack_id"] for r in triage["attack"] if r["kind"] == "technique" and r["attack_id"][0] == "T"]
    iocs = triage["iocs"]
    return {"name": f"{current['id']} - {triage['category']}", "technique": techniques[0] if techniques else "T1071.001",
            "severity": PRIORITY_TO_SEVERITY[triage["priority"]["code"]],
            "ips": "\n".join(i["value"] for i in iocs if i["type"] == "IP"),
            "sha256": "\n".join(i["value"] for i in iocs if i["type"] == "SHA-256")}


def render() -> None:
    st.title("📤 Règles de détection")
    case_banner()
    st.caption("Chaque IOC est validé (format, plages internes / réservées / de documentation, infrastructure bénigne "
               "connue) puis échappé : un indicateur piégé ne peut pas modifier la requête. Pré-rempli depuis le "
               "dossier ouvert.")
    defaults = _defaults()
    with st.form("detection"):
        name = st.text_input("Nom de la règle", defaults["name"])
        col1, col2 = st.columns(2)
        technique = col1.text_input("Technique MITRE ATT&CK", defaults["technique"])
        severity = col2.select_slider("Sévérité", list(SEVERITIES), value=defaults["severity"], format_func=SEVERITIES.get)
        ips = st.text_area("Adresses IP", defaults["ips"])
        domains = st.text_area("Domaines", "")
        hashes = st.text_area("Empreintes SHA-256", defaults["sha256"])
        submitted = st.form_submit_button("Générer la règle", type="primary")
    if submitted:
        payload = {"name": name, "technique": technique, "severity": severity, "ips": _split(ips),
                   "domains": _split(domains), "sha256": _split(hashes)}
        rule = call(api_client.siem_rule, payload, spinner="Validation des indicateurs…")
        if rule:
            st.session_state.last_rule = rule
            if rule.get("valid") and case() is not None:
                case()["rules"].append(name)
                log(f"Règle de détection générée « {name} » ({technique}, {sum(len(v) for v in rule['indicators'].values())} IOC)")
    if st.session_state.get("last_rule"):
        render_rule(st.session_state.last_rule, key="builder")
