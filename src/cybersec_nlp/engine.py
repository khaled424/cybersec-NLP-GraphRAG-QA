"""``SOCEngine``: one façade over every project component (used by the API, the UI and the master notebook).

Components are loaded lazily from the artifacts produced by the pipeline / Notebook 1, so
starting the API is fast and a missing optional component (GPU LLM) degrades gracefully.
"""

from __future__ import annotations

import threading
from dataclasses import asdict
from functools import cached_property
from typing import Any

from cybersec_nlp import config
from cybersec_nlp.evaluation.report import acceptance_table, load_metrics
from cybersec_nlp.graph.knowledge_graph import graph_summary, load_graph
from cybersec_nlp.graph.minicypher import InMemoryGraph
from cybersec_nlp.llm.guardrails import check_prompt
from cybersec_nlp.llm.local_llm import LocalLLM
from cybersec_nlp.nlp.classifier import IncidentClassifier, top_terms
from cybersec_nlp.nlp.ner import CyberNER
from cybersec_nlp.pipelines.build_knowledge_base import read_jsonl
from cybersec_nlp.rag.agentic import (
    AgenticRAG,
    chain_repairers,
    direction_repairer,
    entity_linking_repairer,
    llm_cypher_generator,
    llm_cypher_repairer,
    schema_repairer,
    syntax_repairer,
)
from cybersec_nlp.rag.cypher_templates import SchemaGuidedCypher
from cybersec_nlp.rag.hybrid import GraphRetriever, HybridRAG, contextualize
from cybersec_nlp.rag.reranker import CrossEncoderReranker
from cybersec_nlp.rag.vector_index import VectorIndex
from cybersec_nlp.security.graph_poison import GraphPoisonDetector
from cybersec_nlp.siem import rules as siem
from cybersec_nlp.soc.attack import attack_references
from cybersec_nlp.soc.case import case_markdown
from cybersec_nlp.soc.triage import assess_priority, category_label, playbooks, priority_dict


class ArtifactsMissingError(RuntimeError):
    """Raised when the pipeline has not been run yet."""


class SOCEngine:
    def __init__(self, use_llm: bool = True) -> None:
        self.use_llm = use_llm and LocalLLM.is_available()
        self._lock = threading.Lock()
        for path in (config.RAG_DOCUMENTS, config.KNOWLEDGE_GRAPH_JSON, config.CLASSIFIER_PATH,
                     config.VECTOR_INDEX_DIR / "vectors.faiss"):
            if not path.exists():
                raise ArtifactsMissingError(
                    f"{path.relative_to(config.ROOT)} is missing: run `make pipeline` "
                    "(python -m cybersec_nlp.pipelines.build_knowledge_base) first.")

    # ------------------------------------------------------------------ lazy components
    @cached_property
    def documents(self) -> dict[str, dict[str, str]]:
        return {d["doc_id"]: d for d in read_jsonl(config.RAG_DOCUMENTS)}

    @cached_property
    def graph(self) -> InMemoryGraph:
        return load_graph(config.KNOWLEDGE_GRAPH_JSON)

    @cached_property
    def ner(self) -> CyberNER:
        return CyberNER()

    @cached_property
    def classifier(self) -> IncidentClassifier:
        return IncidentClassifier.load(config.CLASSIFIER_PATH)

    @cached_property
    def llm(self) -> LocalLLM | None:
        return LocalLLM(config.LLM_MODEL) if self.use_llm else None

    @cached_property
    def rag(self) -> HybridRAG:
        index = VectorIndex.load(config.VECTOR_INDEX_DIR)
        return HybridRAG(index, GraphRetriever(self.graph, self.documents, self.ner), llm=self.llm,
                         reranker=CrossEncoderReranker())

    @cached_property
    def agent(self) -> AgenticRAG:
        """Schema-guided Text-to-Cypher first; the LLM (if any) only for questions outside the patterns."""
        fallback = llm_cypher_generator(self.llm) if self.llm is not None else None
        repairers = [syntax_repairer, schema_repairer, entity_linking_repairer(self.graph, self.ner), direction_repairer]
        if self.llm is not None:
            repairers.append(llm_cypher_repairer(self.llm))
        return AgenticRAG(self.graph, SchemaGuidedCypher(self.graph, self.ner, fallback),
                          chain_repairers(*repairers), max_steps=6)

    # ------------------------------------------------------------------ use cases
    def status(self) -> dict[str, Any]:
        return {"documents": len(self.documents), "graph": graph_summary(self.graph),
                "llm": config.LLM_MODEL if self.use_llm else None, "embedding_model": config.EMBEDDING_MODEL}

    def ask(self, question: str, strategy: str = "hybrid", use_llm: bool = True,
            previous_question: str | None = None) -> dict[str, Any]:
        """Answer with citations; ``previous_question`` enables short follow-ups (conversation memory)."""
        contextual, follow_up = contextualize(question, previous_question)
        with self._lock:
            result = self.rag.answer(contextual, strategy=strategy, use_llm=use_llm and self.use_llm)
        result["follow_up"] = follow_up
        return result

    def analyze_report(self, text: str) -> dict[str, Any]:
        """Qualification of an incident report: category, suggested priority, TTPs, IOC verdicts, playbooks."""
        probabilities = self.classifier.predict_proba(text)
        category = next(iter(probabilities))
        entities = [e.to_dict() for e in self.ner.extract(text)]
        iocs = self._ioc_verdicts(entities)
        valid = {"ips": [i["value"] for i in iocs if i["type"] == "IP" and i["exportable"]],
                 "sha256": [i["value"] for i in iocs if i["type"] == "SHA-256" and i["exportable"]]}
        attack = attack_references(entities)
        technique = next((r["attack_id"] for r in attack if r["kind"] == "technique" and r["attack_id"].startswith("T")),
                         "T1071.001")
        priority = assess_priority(entities, category, sum(len(v) for v in valid.values()))
        draft = None
        if any(valid.values()):
            draft = self.siem_rule(f"SOC - {category_label(category)} - {priority.code}", "Règle issue de la qualification d'un signalement",
                                   technique.split(".")[0] if "." not in technique else technique,
                                   {"P1": "critical", "P2": "high", "P3": "medium", "P4": "low"}[priority.code], **valid)
        return {
            "category": category_label(category),
            "probabilities": {category_label(k): v for k, v in probabilities.items()},
            "explanation": top_terms(self.classifier, category),
            "priority": priority_dict(priority), "attack": attack, "iocs": iocs,
            "playbooks": playbooks(category, entities), "entities": entities,
            "linked_nodes": self.rag.graph_retriever.link(text), "draft_rule": draft,
        }

    def _ioc_verdicts(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """One row per IOC: validity for detection and enrichment from the CTI knowledge graph."""
        rows, seen = [], set()
        for entity in entities:
            key, label = entity["key"], entity["label"]
            if label not in ("IP", "HASH", "CVE") or key in seen:
                continue
            seen.add(key)
            if label == "IP":
                kind = "IP"
                try:
                    siem.validate_ip(key)
                    verdict, detail, exportable = "à surveiller", "adresse routable, exportable vers le SIEM", True
                except siem.InvalidIndicatorError as exc:
                    verdict, detail, exportable = "écarté", str(exc).rsplit(" : ", 1)[0], False
            elif label == "HASH":
                kind = {32: "MD5", 40: "SHA-1", 64: "SHA-256"}[len(key)]
                exportable = kind == "SHA-256"
                verdict = "à surveiller" if exportable else "à rechercher"
                detail = "empreinte exportable vers le SIEM" if exportable else "les règles générées utilisent SHA-256"
            else:
                kind, verdict, exportable = "CVE", "vulnérabilité", False
                affected = [self.graph.nodes[e.dst].name for e in self.graph.edges
                            if e.rel == "AFFECTS" and e.src == f"Vulnerability:{key}"]
                detail = ("logiciels associés dans la base : " + ", ".join(sorted(affected))) if affected else "à vérifier (NVD)"
            node = self.graph.nodes.get(f"{'Vulnerability' if label == 'CVE' else 'Indicator'}:{key}")
            rows.append({"value": key, "type": kind, "verdict": verdict, "detail": detail, "exportable": exportable,
                         "cti_documents": node.props.get("doc_count", 0) if node else 0})
        return rows

    @staticmethod
    def case_report(case: dict[str, Any]) -> str:
        return case_markdown(case)

    def cypher(self, question: str) -> dict[str, Any]:
        with self._lock:
            result = self.agent.ask(question)
        rows = [{k: v for k, v in r.items() if k != "_edge"} for r in result.rows[:50]]
        return {"available": True, "question": question, "query": result.final_query, "repaired": result.repaired,
                "rows": rows, "trace": [asdict(s) for s in result.trace]}

    def audit_graph(self) -> dict[str, Any]:
        """Poisoning audit of the current graph against itself as trusted baseline (detects unsafe content)."""
        from cybersec_nlp.graph.knowledge_graph import CORPUS_SOURCE

        report = GraphPoisonDetector({CORPUS_SOURCE}, baseline=self.graph).scan(self.graph)
        return {"findings": [asdict(f) for f in report.findings], "by_detector": report.by_detector(),
                "clean": report.is_clean}

    @staticmethod
    def siem_rule(name: str, description: str, technique: str, severity: str = "medium",
                  ips: list[str] | None = None, domains: list[str] | None = None,
                  sha256: list[str] | None = None) -> dict[str, Any]:
        try:
            rule = siem.DetectionRule(name=name, description=description, technique=technique, severity=severity,
                                      ips=ips or [], domains=domains or [], sha256=sha256 or [])
        except ValueError as exc:
            return {"valid": False, "error": str(exc)}
        return {"valid": True, "indicators": {"ips": rule.ips, "domains": rule.domains, "sha256": rule.sha256},
                "rejected": rule.rejected, "spl": siem.to_spl(rule), "kql": siem.to_kql(rule),
                "splunk_savedsearch": siem.to_splunk_savedsearch(rule),
                "sentinel_rule": siem.to_sentinel_analytics_rule(rule)}

    @staticmethod
    def guardrail(text: str) -> dict[str, Any]:
        verdict = check_prompt(text)
        return {"allowed": verdict.allowed, "reasons": list(verdict.reasons), "message": verdict.message}

    @staticmethod
    def metrics() -> dict[str, Any]:
        return {"metrics": load_metrics(), "acceptance": acceptance_table()}
