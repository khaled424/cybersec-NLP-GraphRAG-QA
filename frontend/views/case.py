"""Incident record: status, analyst notes, activity log (main courante) and ticket export."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from frontend import api_client
from frontend.views.common import STATUSES, call, case, log, priority_badge


def render() -> None:
    st.title("🗂️ Dossier d'incident")
    current = case()
    if current is None:
        st.info("Aucun dossier ouvert. Qualifiez un signalement dans **Triage** puis cliquez sur « Ouvrir le dossier ».")
        return
    triage = current["triage"]
    priority = triage["priority"]
    st.markdown(f"{priority_badge(priority['code'], priority['label'])} &nbsp; **{current['id']}** — "
                f"ouvert le {current['opened_at']}", unsafe_allow_html=True)

    left, right = st.columns([1, 1])
    with left:
        title = st.text_input("Intitulé", current["title"])
        status = st.selectbox("Statut", STATUSES, index=STATUSES.index(current["status"]))
        if title != current["title"]:
            current["title"] = title
        if status != current["status"]:
            log(f"Statut : {current['status']} → {status}")
            current["status"] = status
        st.markdown(f"**Catégorie :** {triage['category']}  \n**Escalade :** {priority['escalation']}  \n"
                    f"**TTP :** {', '.join(r['attack_id'] for r in triage['attack']) or '—'}  \n"
                    f"**Règles de détection :** {', '.join(current['rules']) or '—'}")
    with right:
        notes = st.text_area("Notes de l'analyste", current["notes"], height=180,
                             placeholder="Constats, hypothèses, actions réalisées, décision de clôture…")
        if notes != current["notes"]:
            current["notes"] = notes

    st.subheader("Main courante")
    entry = st.text_input("Ajouter une entrée", placeholder="ex. Poste WS-042 isolé par l'équipe N2")
    if st.button("Ajouter") and entry.strip():
        log(entry.strip())
        st.rerun()
    if current["journal"]:
        st.dataframe(pd.DataFrame(current["journal"][::-1]).rename(columns={"time": "Horodatage", "event": "Événement"}),
                     hide_index=True, use_container_width=True)

    st.subheader("Export")
    markdown = call(api_client.export_case, current, spinner="Préparation de la fiche…")
    if markdown:
        st.download_button("⬇️ Télécharger la fiche incident (Markdown, prête pour le ticket)", markdown,
                           file_name=f"{current['id']}.md", type="primary")
        with st.expander("Aperçu de la fiche"):
            st.markdown(markdown)
