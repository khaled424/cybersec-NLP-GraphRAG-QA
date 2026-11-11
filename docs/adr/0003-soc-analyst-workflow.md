# ADR 0003: Vigie follows the SOC analyst workflow

- **Status:** Accepted
- **Date:** 2026-11-11

## Context

Vigie is meant for the analysts of a Security Operations Centre (SOC). A generic
"question-answering demo" layout does not match how they work: an alert is **qualified**
(priority, category, TTPs, IOCs), **investigated**, turned into **detections**, and every
step is traced in an **incident record** that ends up in the ticketing tool.

## Decision

1. **Navigation by workflow**: *Opérations* (Poste analyste, Triage, Investigation,
   Pivot CTI, Dossier d'incident), *Détection* (Règles de détection), *Supervision de Vigie*
   (Sécurité de l'assistant, Pilotage). SOC vocabulary throughout (signalement,
   qualification, P1–P4, IOC, TTP, pivot, confinement / éradication / rétablissement,
   escalade, main courante).
2. **Incident record carried across pages**: opening a case on the triage page pre-fills
   the investigation question and the detection rule; investigations, pivots, rules and
   status changes are logged automatically with a timestamp; the record exports to a
   ticket-ready Markdown file (`/cases/export`).
3. **Suggestions, never decisions**: the priority is a transparent heuristic whose
   reasons are displayed; playbooks are reference steps from NIST SP 800-61; category
   predictions show their confidence and are flagged when ambiguous. Explicit evidence
   (entities) takes precedence over the weakly supervised category for playbooks.
4. **Trustworthy references only**: MITRE ATT&CK mappings are a curated list of
   unambiguous techniques, software and groups (`cybersec_nlp.soc.attack`); entities
   without a reliable mapping get none.
5. **Session-scoped case**: the record lives in the analyst's session (no database). Its
   export is the hand-off to the SOC ticketing system.

## Consequences

- The MVP demonstrates the full alert → detection loop in a few clicks.
- Priority and playbooks must be calibrated with the SOC before production use.
- Persistence, multi-analyst assignment and SOAR/ticketing integrations are out of scope
  for the MVP; the Markdown export and the API are the integration points.
