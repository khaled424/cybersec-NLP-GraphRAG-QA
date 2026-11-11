"""Streamlit entry point of Vigie, the SOC assistant MVP (``make ui``; the API must run: ``make api``)."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # allow `streamlit run frontend/app.py`

from frontend import api_client
from frontend.views import agent, assistant, metrics, report, security, siem

st.set_page_config(page_title="Vigie · Assistant SOC", page_icon="🛡️", layout="wide")

PAGES = [
    st.Page(assistant.render, title="Assistant SOC", icon="🛡️", url_path="assistant", default=True),
    st.Page(report.render, title="Analyse de rapport", icon="🏷️", url_path="rapport"),
    st.Page(agent.render, title="Graphe (agent)", icon="🕸️", url_path="graphe"),
    st.Page(siem.render, title="Règles SIEM", icon="📤", url_path="siem"),
    st.Page(security.render, title="Sécurité", icon="🔐", url_path="securite"),
    st.Page(metrics.render, title="Métriques", icon="📊", url_path="metriques"),
]


def sidebar_status() -> None:
    with st.sidebar:
        st.markdown("### 🛡️ Vigie")
        st.caption("L'assistant SOC qui cite ses sources")
        if not api_client.health():
            st.error(f"API hors ligne ({api_client.API_URL}). Lancez `make api`.")
            return
        try:
            info = api_client.status()
        except api_client.ApiError as exc:
            st.warning(str(exc))
            return
        graph = info["graph"]
        st.success("API en ligne")
        st.caption(f"{info['documents']} documents · {graph['n_nodes']} nœuds · {graph['n_edges']} arêtes  \n"
                   f"LLM : {info['llm'] or 'désactivé (réponses extractives)'}")


sidebar_status()
st.navigation(PAGES).run()
