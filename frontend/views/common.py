"""Shared UI helpers (error handling, entity highlighting, colours)."""

from __future__ import annotations

import html
from collections.abc import Callable
from typing import Any

import streamlit as st

from frontend.api_client import ApiError

ENTITY_COLORS = {
    "IP": "#d62728", "CVE": "#9467bd", "ATTACK_ID": "#8c564b", "HASH": "#7f7f7f", "MALWARE": "#e6550d",
    "TOOL": "#3182bd", "THREAT_ACTOR": "#e377c2", "SOFTWARE": "#31a354", "VECTOR": "#bcbd22", "TARGET": "#17becf",
}


def call(fn: Callable[..., Any], *args: Any, spinner: str = "Traitement…") -> Any | None:
    """Run an API call with a spinner; show a readable error instead of a stack trace."""
    try:
        with st.spinner(spinner):
            return fn(*args)
    except ApiError as exc:
        st.error(str(exc))
        return None


def highlight_entities(text: str, entities: list[dict[str, Any]]) -> str:
    """HTML with each entity span coloured by label (text is escaped: no HTML injection)."""
    parts, cursor = [], 0
    for e in sorted(entities, key=lambda e: e["start"]):
        if e["start"] < cursor:
            continue
        parts.append(html.escape(text[cursor:e["start"]]))
        color = ENTITY_COLORS.get(e["label"], "#555")
        parts.append(
            f'<span style="background:{color}22;border-bottom:2px solid {color};padding:0 2px;border-radius:3px" '
            f'title="{html.escape(e["label"])}">{html.escape(text[e["start"]:e["end"]])}'
            f'<sup style="color:{color};font-size:0.65em;margin-left:2px">{html.escape(e["label"])}</sup></span>')
        cursor = e["end"]
    parts.append(html.escape(text[cursor:]))
    return "<div style='line-height:2.1'>" + "".join(parts) + "</div>"


def legend() -> None:
    st.caption(" ".join(f"<span style='color:{c}'>■</span> {label}" for label, c in ENTITY_COLORS.items()),
               unsafe_allow_html=True)
