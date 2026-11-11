"""Pivot CTI: natural-language question → Cypher over the STIX graph (self-correcting ReAct agent)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend import api_client
from frontend.views.common import call, case_banner, log

EXAMPLES = ["Which malware targets the banking sector?", "Quels logiciels sont affectés par CVE-2021-44228 ?",
            "Which documents mention mimikatz?", "Quelles techniques d'attaque ciblent kerberos ?",
            "Which threat actors use stuxnet?"]


def render() -> None:
    st.title("🕸️ Pivot CTI")
    case_banner()
    st.caption("Interrogez le graphe de connaissances STIX 2.1 (CVE, malwares, acteurs, techniques, secteurs) en "
               "langage naturel. Les questions « quel(s) <type> … <entité> ? » sont traduites par gabarits ; les "
               "autres par le LLM, réparé par l'agent si la base renvoie une erreur. Accès en lecture seule.")
    question = st.selectbox("Question de pivot", EXAMPLES, index=0, accept_new_options=True)
    if not st.button("Pivoter", type="primary"):
        return
    result = call(api_client.cypher, question, spinner="Traduction et exécution…")
    if not result:
        return
    found = bool(result["rows"])
    st.subheader(("✅ " if found else "❌ ") + (f"{len(result['rows'])} résultat(s)" if found else "Aucun résultat")
                 + (" après réparation" if result["repaired"] else ""))
    if result["query"]:
        st.code(result["query"], language="cypher")
    if found:
        st.dataframe(pd.DataFrame(result["rows"]), hide_index=True, use_container_width=True)
        log(f"Pivot CTI : « {question} » → {len(result['rows'])} résultat(s)")
    with st.expander("Trace de l'agent (ReAct)", expanded=not found):
        for i, step in enumerate(result["trace"], 1):
            ok = step["observation"].endswith("rows")
            st.markdown(f"{'✅' if ok else '⚠️'} **Étape {i}** — {step['thought']}")
            st.code(step["action"], language="cypher")
            st.caption(step["observation"])
