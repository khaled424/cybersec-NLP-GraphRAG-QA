"""Conversational SOC assistant (HybridRAG with citations, abstention and fidelity check)."""

from __future__ import annotations

from typing import Any

import streamlit as st

from frontend import api_client
from frontend.views.common import call

EXAMPLES = ["Quelle CVE affecte log4j ?", "Comment détecter une attaque Kerberoasting ?",
            "Comment Mimikatz est-il utilisé pour le mouvement latéral ?", "Quel est le prix du zorbax interstellaire ?"]
STRATEGY_HELP = {"hybrid": "Hybride (vecteurs + graphe)", "vector": "Vecteurs seuls (FAISS)", "graph": "Graphe seul (STIX)"}


def _render_answer(result: dict[str, Any]) -> None:
    st.markdown(result["answer"])
    trace = result.get("trace", {})
    if trace.get("blocked"):
        return
    grounding = trace.get("grounding") or {}
    cols = st.columns(4)
    cols[0].metric("Générateur", result.get("generator", "—"))
    cols[1].metric("Recherche", f"{trace.get('retrieval_ms', 0):.0f} ms")
    cols[2].metric("Génération", f"{trace.get('answer_ms', 0) / 1000:.1f} s")
    ratio = grounding.get("supported_ratio")
    cols[3].metric("Phrases étayées", "—" if ratio is None else f"{ratio:.0%}",
                   help="Part des phrases du LLM retrouvées dans les preuves (les autres sont retirées).")
    if grounding.get("removed_sentences"):
        with st.expander(f"⚠️ {len(grounding['removed_sentences'])} phrase(s) non étayée(s) retirée(s)"):
            for item in grounding["removed_sentences"]:
                st.markdown(f"- ~~{item['sentence']}~~ — *{item['reason']}*")
    if result.get("evidence"):
        with st.expander(f"📚 Preuves ({len(result['evidence'])}) — liens graphe : {', '.join(trace.get('linked_entities', [])) or 'aucun'}"):
            for ev in result["evidence"]:
                icon = "🕸️" if ev["kind"] == "graph" else "📄"
                st.markdown(f"**[{ev['citation']}]** {icon} `{ev['doc_id']}` · {ev['locator']}")
                st.caption(ev["text"][:600])


def render() -> None:
    st.title("🛡️ Vigie — assistant SOC")
    st.caption("Réponses construites **uniquement** à partir du corpus et du graphe STIX, avec citations [S#]. "
               "Hors sujet ou preuves insuffisantes → abstention. Les questions de suivi courtes (« Et … ? ») "
               "reprennent la question précédente.")
    with st.sidebar:
        st.subheader("Réglages")
        strategy = st.radio("Stratégie de recherche", list(STRATEGY_HELP), format_func=STRATEGY_HELP.get)
        use_llm = st.toggle("Génération par LLM local (Qwen2.5-1.5B)", value=True,
                            help="Désactivé : réponse extractive (extraits des preuves), instantanée.")
        if st.button("🗑️ Nouvelle conversation", use_container_width=True):
            st.session_state.history, st.session_state.last_question = [], None

    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last_question", None)
    for turn in st.session_state.history:
        with st.chat_message("user"):
            st.markdown(turn["question"])
        with st.chat_message("assistant", avatar="🛡️"):
            _render_answer(turn["result"])

    if not st.session_state.history:
        st.markdown("**Exemples :**")
        cols = st.columns(len(EXAMPLES))
        for col, example in zip(cols, EXAMPLES):
            if col.button(example, use_container_width=True):
                st.session_state.pending = example
                st.rerun()

    question = st.chat_input("Posez votre question (français ou anglais)…") or st.session_state.pop("pending", None)
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant", avatar="🛡️"):
            result = call(api_client.ask, question, strategy, use_llm, st.session_state.last_question,
                          spinner="Recherche des preuves et rédaction…")
            if result:
                _render_answer(result)
                st.session_state.history.append({"question": question, "result": result})
                if not result.get("follow_up"):
                    st.session_state.last_question = question
