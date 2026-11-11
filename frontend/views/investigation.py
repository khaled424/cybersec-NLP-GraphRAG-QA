"""Investigation: conversational assistant grounded in the CTI base (cited evidence, abstention)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from frontend import api_client
from frontend.views.common import call, case_banner, log

EXAMPLES = ["Quelle CVE affecte log4j ?", "Comment détecter une attaque Kerberoasting ?",
            "Comment Mimikatz est-il utilisé pour le mouvement latéral ?", "Quelles mesures contre un rançongiciel ?"]
STRATEGIES = {"hybrid": "Hybride (documents + graphe)", "vector": "Documents seuls", "graph": "Graphe CTI seul"}


def _render_answer(result: dict[str, Any]) -> None:
    st.markdown(result["answer"])
    trace = result.get("trace", {})
    if trace.get("blocked"):
        st.caption("Requête bloquée par le garde-fou anti-injection (OWASP LLM01).")
        return
    grounding = trace.get("grounding") or {}
    cols = st.columns(4)
    cols[0].metric("Mode", {"llm": "LLM local", "extractive": "Extraits", "none": "Abstention"}.get(result["generator"],
                                                                                                  result["generator"]))
    cols[1].metric("Recherche", f"{trace.get('retrieval_ms', 0):.0f} ms")
    cols[2].metric("Rédaction", f"{trace.get('answer_ms', 0) / 1000:.1f} s")
    ratio = grounding.get("supported_ratio")
    cols[3].metric("Phrases étayées", "—" if ratio is None else f"{ratio:.0%}",
                   help="Part des phrases du LLM rattachées à une preuve ; les autres sont retirées.")
    if grounding.get("removed_sentences"):
        with st.expander(f"⚠️ {len(grounding['removed_sentences'])} affirmation(s) non étayée(s) retirée(s)"):
            for item in grounding["removed_sentences"]:
                st.markdown(f"- ~~{item['sentence']}~~ — *{item['reason']}*")
    if result.get("evidence"):
        linked = ", ".join(trace.get("linked_entities", [])) or "aucune"
        with st.expander(f"📚 Sources ({len(result['evidence'])}) · entités pivots : {linked}"):
            for ev in result["evidence"]:
                icon = "🕸️ fait CTI" if ev["kind"] == "graph" else "📄 document"
                st.markdown(f"**[{ev['citation']}]** {icon} · `{ev['doc_id']}` · {ev['locator']}")
                st.caption(ev["text"][:600])


def render() -> None:
    st.title("🔎 Investigation")
    case_banner()
    st.caption("Réponses fondées **uniquement** sur la base CTI (documents + graphe STIX), avec sources [S#]. "
               "Preuves insuffisantes → abstention. Les questions de suivi (« Et … ? ») reprennent le contexte.")
    with st.sidebar:
        st.subheader("Recherche")
        strategy = st.radio("Sources interrogées", list(STRATEGIES), format_func=STRATEGIES.get)
        use_llm = st.toggle("Rédaction par le LLM local", value=True,
                            help="Désactivé : extraits des sources, sans rédaction (instantané).")
        if st.button("🗑️ Nouvelle conversation", use_container_width=True):
            st.session_state.history, st.session_state.last_question = [], None

    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last_question", None)
    for turn in st.session_state.history:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(turn["question"])
        with st.chat_message("assistant", avatar="🛡️"):
            _render_answer(turn["result"])

    if not st.session_state.history:
        cols = st.columns(len(EXAMPLES))
        for col, example in zip(cols, EXAMPLES):
            if col.button(example, use_container_width=True):
                st.session_state.pending = example
                st.rerun()

    question = st.chat_input("Question d'investigation (français ou anglais)…") or st.session_state.pop("pending", None)
    if question:
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(question)
        with st.chat_message("assistant", avatar="🛡️"):
            result = call(api_client.ask, question, strategy, use_llm, st.session_state.last_question,
                          spinner="Recherche des sources et rédaction…")
            if result:
                _render_answer(result)
                st.session_state.history.append({"question": question, "result": result})
                if not result.get("follow_up"):
                    st.session_state.last_question = question
                sources = ", ".join(sorted({e["doc_id"] for e in result.get("evidence", [])})[:4]) or "aucune"
                log(f"Investigation : « {question} » → {result['generator']}, sources {sources}")
