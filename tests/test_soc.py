"""Tests for the SOC workflow module (ATT&CK references, priority, playbooks, incident record)."""

from cybersec_nlp.soc.attack import attack_references
from cybersec_nlp.soc.case import case_markdown, new_case_id
from cybersec_nlp.soc.triage import assess_priority, playbooks


def _entities(*pairs: tuple[str, str]) -> list[dict]:
    return [{"key": k, "label": lab} for k, lab in pairs]


def test_attack_references_are_unique_and_linked() -> None:
    refs = attack_references(_entities(("mimikatz", "TOOL"), ("ransomware", "VECTOR"), ("apt29", "THREAT_ACTOR"),
                                       ("T1059", "ATTACK_ID"), ("unknown", "SOFTWARE")))
    ids = [r["attack_id"] for r in refs]
    assert ids == ["T1003.001", "T1059", "T1486", "S0002", "G0016"]
    assert refs[0]["url"] == "https://attack.mitre.org/techniques/T1003/001/"
    assert refs[-1]["url"] == "https://attack.mitre.org/groups/G0016/"


def test_priority_levels_and_reasons() -> None:
    critical = assess_priority(_entities(("ransomware", "VECTOR"), ("lockbit", "MALWARE"), ("hospital", "TARGET")),
                               "Malware & Ransomware", valid_iocs=1)
    assert critical.code == "P1" and critical.escalation.startswith("N3") and len(critical.reasons) == 4
    low = assess_priority([], "Cloud & Governance", valid_iocs=0)
    assert low.code == "P4" and low.reasons == ["aucun signal de gravité détecté"]


def test_playbooks_triggered_by_entities() -> None:
    books = playbooks("Vulnerability & Exploit", _entities(("phishing", "VECTOR")))
    assert [b["name"] for b in books] == ["Hameçonnage / ingénierie sociale", "Vulnérabilité / exploitation"]
    assert books[0]["source"] == "entités du signalement" and "Confinement" in books[1]["phases"]


def test_case_markdown_contains_ticket_sections() -> None:
    case = {"id": new_case_id(), "title": "Test", "report": "line1\nline2", "journal": [{"time": "10:00", "event": "x"}],
            "triage": {"category": "C", "priority": {"code": "P2", "label": "Élevée", "escalation": "N2", "reasons": ["r"]},
                       "attack": [], "iocs": [{"value": "1.2.3.4", "type": "IP", "verdict": "v", "detail": "d"}],
                       "playbooks": playbooks("Web App Attacks", [])}}
    md = case_markdown(case)
    assert case["id"].startswith("INC-") and "P2 (Élevée)" in md and "> line2" in md
    assert "`1.2.3.4`" in md and "- [ ] " in md and "`10:00` x" in md
