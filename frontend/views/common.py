"""Shared UI helpers: API calls, incident record (session), SOC badges and entity highlighting."""

from __future__ import annotations

import html
from collections.abc import Callable
from datetime import datetime
from typing import Any

import streamlit as st

from frontend.api_client import ApiError

ENTITY_COLORS = {
    "IP": "#f87171", "CVE": "#c084fc", "ATTACK_ID": "#a78bfa", "HASH": "#94a3b8", "MALWARE": "#fb923c",
    "TOOL": "#60a5fa", "THREAT_ACTOR": "#f472b6", "SOFTWARE": "#4ade80", "VECTOR": "#facc15", "TARGET": "#22d3ee",
}
PRIORITY_COLORS = {"P1": "#dc2626", "P2": "#ea580c", "P3": "#ca8a04", "P4": "#16a34a"}
STATUSES = ("Nouveau", "En cours d'investigation", "Qualifié — vrai positif", "Clos — faux positif", "Clos — résolu")


# ------------------------------------------------------------------ API
def call(fn: Callable[..., Any], *args: Any, spinner: str = "Traitement…") -> Any | None:
    """Run an API call with a spinner; show a readable error instead of a stack trace."""
    try:
        with st.spinner(spinner):
            return fn(*args)
    except ApiError as exc:
        st.error(str(exc))
        return None


# ------------------------------------------------------------------ incident record (dossier)
def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def case() -> dict[str, Any] | None:
    return st.session_state.get("case")


def open_case(report: str, triage: dict[str, Any]) -> dict[str, Any]:
    opened = datetime.now()
    title = f"{triage['category']} — {triage['priority']['code']}"
    st.session_state.case = {
        "id": opened.strftime("INC-%Y%m%d-%H%M%S"), "title": title, "status": STATUSES[0],
        "opened_at": opened.strftime("%Y-%m-%d %H:%M:%S"), "report": report, "triage": triage,
        "journal": [], "notes": "", "rules": [],
    }
    log(f"Dossier ouvert — priorité suggérée {triage['priority']['code']} ({triage['priority']['label']}), "
        f"catégorie « {triage['category']} »")
    return st.session_state.case


def log(event: str) -> None:
    """Append an entry to the incident's activity log (main courante)."""
    if case() is not None:
        case()["journal"].append({"time": now(), "event": event})


def case_banner() -> None:
    """Compact reminder of the open incident at the top of operational pages."""
    current = case()
    if current is None:
        st.caption("Aucun dossier ouvert — qualifiez un signalement depuis **Triage** pour en créer un.")
        return
    priority = current["triage"]["priority"]
    st.markdown(
        f"{priority_badge(priority['code'], priority['label'])} &nbsp; **{current['id']}** · {current['title']} · "
        f"<span style='opacity:.75'>{current['status']}</span>", unsafe_allow_html=True)


# ------------------------------------------------------------------ badges and highlighting
def priority_badge(code: str, label: str = "") -> str:
    color = PRIORITY_COLORS.get(code, "#64748b")
    text = f"{code} · {label}" if label else code
    return (f"<span style='background:{color};color:white;padding:2px 10px;border-radius:12px;"
            f"font-weight:600;font-size:0.85em'>{html.escape(text)}</span>")


def pill(text: str, color: str = "#334155", url: str | None = None) -> str:
    body = (f"<span style='background:{color};color:#f8fafc;padding:2px 8px;border-radius:10px;font-size:0.8em;"
            f"margin:0 4px 4px 0;display:inline-block'>{html.escape(text)}</span>")
    return f"<a href='{html.escape(url)}' target='_blank' style='text-decoration:none'>{body}</a>" if url else body


def highlight_entities(text: str, entities: list[dict[str, Any]]) -> str:
    """HTML with each entity span coloured by label (text is escaped: no HTML injection)."""
    parts, cursor = [], 0
    for e in sorted(entities, key=lambda e: e["start"]):
        if e["start"] < cursor:
            continue
        parts.append(html.escape(text[cursor:e["start"]]))
        color = ENTITY_COLORS.get(e["label"], "#94a3b8")
        parts.append(
            f'<span style="background:{color}26;border-bottom:2px solid {color};padding:0 2px;border-radius:3px" '
            f'title="{html.escape(e["label"])}">{html.escape(text[e["start"]:e["end"]])}'
            f'<sup style="color:{color};font-size:0.62em;margin-left:2px">{html.escape(e["label"])}</sup></span>')
        cursor = e["end"]
    parts.append(html.escape(text[cursor:]))
    return "<div style='line-height:2.1'>" + "".join(parts) + "</div>"


def legend() -> None:
    st.caption(" ".join(f"<span style='color:{c}'>■</span> {label}" for label, c in ENTITY_COLORS.items()),
               unsafe_allow_html=True)
