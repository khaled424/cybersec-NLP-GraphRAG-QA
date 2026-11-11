"""Input guardrail against prompt injection (OWASP LLM01), shared by Notebook 3 and the MVP.

Pattern matching is a first line of defence only: it reduces obvious attacks and gives an
auditable verdict, but must be combined with output checks (citations, abstention) and
least-privilege tools (read-only graph access).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

INJECTION_PATTERNS: dict[str, re.Pattern[str]] = {
    "override_instructions": re.compile(
        r"(ignore|disregard|forget)\s+(all\s+|any\s+)?(the\s+)?(previous|prior|above|earlier)?\s*(instructions|rules|prompts?)",
        re.IGNORECASE),
    "french_override": re.compile(r"ignore[rz]?\s+(toutes\s+)?(les\s+)?(instructions|consignes|règles)", re.IGNORECASE),
    "system_prompt_exfiltration": re.compile(r"(reveal|show|print|display|révèle|affiche)\b.{0,40}\bsystem\s+prompt", re.IGNORECASE),
    "role_hijack": re.compile(r"\byou\s+are\s+now\b|\btu\s+es\s+maintenant\b", re.IGNORECASE),
    # "jailbreak" alone is a legitimate topic (iOS jailbreak); flag the LLM-jailbreak phrasings only.
    "jailbreak": re.compile(r"\bjailbreak(?:\s+(?:mode|prompt)|\s*:)|\bmode\s+(?:dan|unrestricted|développeur)\b",
                            re.IGNORECASE),
    "dan_persona": re.compile(r"\bDAN\b"),  # case-sensitive: "dan" is also a truncated word
    "destructive_request": re.compile(r"(efface|supprime|delete|drop)\s+(la\s+base|les\s+logs|the\s+database|all\s+logs)", re.IGNORECASE),
}
MAX_QUESTION_CHARS = 2000


@dataclass(frozen=True)
class GuardrailVerdict:
    allowed: bool
    reasons: tuple[str, ...]

    @property
    def message(self) -> str:
        if self.allowed:
            return "Requête autorisée."
        return "Requête bloquée par le garde-fou : " + ", ".join(self.reasons)


def check_prompt(text: str) -> GuardrailVerdict:
    reasons = [name for name, pattern in INJECTION_PATTERNS.items() if pattern.search(text or "")]
    if len(text or "") > MAX_QUESTION_CHARS:
        reasons.append("too_long")
    if not (text or "").strip():
        reasons.append("empty")
    return GuardrailVerdict(not reasons, tuple(reasons))
