# ADR 0002: Local LLM, sentence-level grounding and an in-memory Cypher backend

- **Status:** Accepted
- **Date:** 2026-11-11

## Context

The SOC assistant must answer from cited evidence, never leak analyst data, run on a
student laptop (RTX 4060, 8 GB) and be demonstrable without a Neo4j server or API key.
A 1.5 B-parameter model follows citation instructions unreliably and sometimes adds facts
from its parametric memory (measured in Notebook 4A).

## Decision

1. **LLM**: Qwen2.5-1.5B-Instruct run locally (`cybersec_nlp.llm.local_llm`), optional LoRA
   adapter (Notebook 3). Without CUDA the system answers extractively.
2. **Grounding**: every generated sentence is re-attributed to the evidence by embedding
   similarity; unsupported sentences and sentences containing identifiers (CVE, IP, hash,
   ATT&CK id) absent from the evidence are removed; nothing supported means abstention
   (`cybersec_nlp.rag.grounding`). The supported ratio is reported as a metric.
3. **Graph backend**: the STIX graph is served by `InMemoryGraph`, which accepts the
   read-only Cypher subset produced by Text-to-Cypher models and raises Neo4j-like errors.
   The same graph is exported to Neo4j (`import.cypher`, parameterised loader).
4. **Provenance rule**: a graph relation without a known supporting document never
   becomes evidence; the poisoning audit runs before any graph update or SIEM export.

## Consequences

- Reproducible, offline demonstrations and tests; no data leaves the machine.
- Semantic similarity cannot verify relations between correct identifiers (a real CVE
  attributed to the wrong product can pass the check): this residual risk is documented
  and requires human validation of answers used for decisions.
- Moving to Neo4j only requires an adapter exposing `run(query)` and `schema()`.
