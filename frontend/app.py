"""Vigie — l'assistant du Centre d'Opérations de Sécurité (SOC). Streamlit entry point.

Run: ``mise run ui`` (the API must run: ``mise run api``), or ``mise run mvp`` for both.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # allow `streamlit run frontend/app.py`

from frontend import api_client
from frontend.views import case, detection, home, investigation, metrics, pivot, security, triage
from frontend.views.common import case as current_case
from frontend.views.common import priority_badge

st.set_page_config(page_title="Vigie · SOC", page_icon="🛡️", layout="wide")

PAGES = {
    "home": st.Page(home.render, title="Poste analyste", icon="🏠", default=True),
    "triage": st.Page(triage.render, title="Triage", icon="🚨", url_path="triage"),
    "investigation": st.Page(investigation.render, title="Investigation", icon="🔎", url_path="investigation"),
    "pivot": st.Page(pivot.render, title="Pivot CTI", icon="🕸️", url_path="pivot"),
    "case": st.Page(case.render, title="Dossier d'incident", icon="🗂️", url_path="dossier"),
    "detection": st.Page(detection.render, title="Règles de détection", icon="📤", url_path="detection"),
    "security": st.Page(security.render, title="Sécurité de l'assistant", icon="🔐", url_path="securite"),
    "metrics": st.Page(metrics.render, title="Pilotage", icon="📊", url_path="pilotage"),
}
st.session_state.pages = PAGES  # used by st.switch_page in the views


def sidebar() -> None:
    with st.sidebar:
        st.markdown("## 🛡️ Vigie")
        st.caption("Assistant du Centre d'Opérations de Sécurité")
        current = current_case()
        if current is not None:
            code = current["triage"]["priority"]["code"]
            st.markdown(f"{priority_badge(code)} **{current['id']}**  \n<span style='opacity:.75;font-size:.85em'>"
                        f"{current['status']}</span>", unsafe_allow_html=True)
        if not api_client.health():
            st.error(f"API hors ligne ({api_client.API_URL}) — lancez `mise run api`.")
            return
        try:
            info = api_client.status()
        except api_client.ApiError as exc:
            st.warning(str(exc))
            return
        llm = "LLM local actif" if info["llm"] else "mode extractif (pas de GPU)"
        st.caption(f"🟢 API en ligne · {llm}  \nBase CTI : {info['documents']} documents, {info['graph']['n_nodes']} nœuds")


sidebar()
st.navigation({
    "Opérations": [PAGES[k] for k in ("home", "triage", "investigation", "pivot", "case")],
    "Détection": [PAGES["detection"]],
    "Supervision de Vigie": [PAGES["security"], PAGES["metrics"]],
}).run()
