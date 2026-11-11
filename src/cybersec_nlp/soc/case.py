"""Incident record (dossier d'incident) and its ticket-ready Markdown export."""

from __future__ import annotations

from datetime import datetime
from typing import Any

STATUSES = ("Nouveau", "En cours d'investigation", "Qualifié — vrai positif", "Clos — faux positif",
            "Clos — résolu")


def new_case_id(now: datetime | None = None) -> str:
    return (now or datetime.now()).strftime("INC-%Y%m%d-%H%M%S")


def _attack_lines(refs: list[dict[str, str]]) -> list[str]:
    return [f"- [{r['attack_id']}]({r['url']}) {r['name']}" + (f" — {r['tactic']}" if r.get("tactic") else "")
            for r in refs]


def case_markdown(case: dict[str, Any]) -> str:
    """Ticket-ready summary of an incident record (fields produced by the triage + UI journal)."""
    triage = case.get("triage", {})
    priority = triage.get("priority", {})
    lines = [
        f"# {case['id']} — {case.get('title', 'Incident')}",
        "",
        f"- **Statut :** {case.get('status', STATUSES[0])}",
        f"- **Ouvert le :** {case.get('opened_at', '')}",
        (f"- **Priorité suggérée :** {priority.get('code', '—')} ({priority.get('label', '—')}) — "
        f"escalade : {priority.get('escalation', '—')}"),
        f"- **Catégorie :** {triage.get('category', '—')}",
        "",
        "## Signalement",
        "",
        "> " + case.get("report", "").replace("\n", "\n> "),
        "",
        "## Justification de la priorité",
        *[f"- {r}" for r in priority.get("reasons", [])],
        "",
        "## TTP (MITRE ATT&CK)",
        *(_attack_lines(triage.get("attack", [])) or ["- aucune"]),
        "",
        "## Indicateurs de compromission",
        "",
        "| Indicateur | Type | Verdict | Détail |",
        "| --- | --- | --- | --- |",
        *[f"| `{i['value']}` | {i['type']} | {i['verdict']} | {i['detail']} |" for i in triage.get("iocs", [])],
        "",
        "## Actions recommandées (playbook de référence)",
    ]
    for book in triage.get("playbooks", []):
        lines += [f"### {book['name']} ({book['source']})", ""]
        for phase, actions in book["phases"].items():
            lines += [f"**{phase}**", *[f"- [ ] {a}" for a in actions], ""]
    journal = [f"- `{e['time']}` {e['event']}" for e in case.get("journal", [])]
    lines += ["## Main courante", *(journal or ["- vide"])]
    if case.get("notes"):
        lines += ["", "## Notes de l'analyste", "", case["notes"]]
    lines += ["", "---", "*Généré par Vigie — éléments suggérés à confirmer par l'analyste.*"]
    return "\n".join(lines) + "\n"
