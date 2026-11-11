"""Natural language → Cypher with the self-correcting ReAct agent."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend import api_client
from frontend.views.common import call

EXAMPLES = ["Which malware targets the banking sector?", "Which software is affected by CVE-2021-44228?",
            "Which documents mention mimikatz?", "Which attack techniques target kerberos?"]


def render() -> None:
    st.title("🕸️ Interroger le graphe (agent ReAct)")
    st.caption("Le LLM traduit la question en Cypher ; si la base renvoie une erreur ou rien, l'agent répare la "
               "requête (syntaxe → schéma → liaison d'entités → sens de la relation → LLM). Accès en lecture seule.")
    question = st.selectbox("Question", EXAMPLES, index=0, accept_new_options=True)
    if not st.button("Exécuter", type="primary"):
        return
    result = call(api_client.cypher, question, spinner="Génération et exécution du Cypher…")
    if not result:
        return
    if not result["available"]:
        st.warning(result["reason"])
        return
    status = "✅ Réponse trouvée" if result["rows"] else "❌ Aucune réponse"
    st.subheader(f"{status}{' après réparation' if result['repaired'] else ''}")
    if result["query"]:
        st.code(result["query"], language="cypher")
    if result["rows"]:
        st.dataframe(pd.DataFrame(result["rows"]), hide_index=True, use_container_width=True)
    st.markdown("**Trace ReAct**")
    for i, step in enumerate(result["trace"], 1):
        ok = step["observation"].endswith("rows")
        with st.expander(f"{'✅' if ok else '⚠️'} Étape {i} — {step['thought']}", expanded=not ok):
            st.code(step["action"], language="cypher")
            st.caption(step["observation"])
