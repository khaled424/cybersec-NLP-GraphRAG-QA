"""HTTP routes of the SOC assistant API."""

from typing import Any

from fastapi import APIRouter, Depends

from backend.schemas import AskRequest, CaseExportRequest, QuestionRequest, SiemRuleRequest, TextRequest
from backend.services import get_engine
from cybersec_nlp.engine import SOCEngine

router = APIRouter()
Engine = Depends(get_engine)


@router.get("/status", summary="Composants chargés (documents, graphe, LLM)")
def status(engine: SOCEngine = Engine) -> dict[str, Any]:
    return engine.status()


@router.post("/ask", summary="Question à l'assistant HybridRAG (réponse citée)")
def ask(request: AskRequest, engine: SOCEngine = Engine) -> dict[str, Any]:
    return engine.ask(request.question, request.strategy, request.use_llm, request.previous_question)


@router.post("/analyze", summary="Qualification d'un signalement : priorité, catégorie, TTP ATT&CK, IOC, playbook")
def analyze(request: TextRequest, engine: SOCEngine = Engine) -> dict[str, Any]:
    return engine.analyze_report(request.text)


@router.post("/cypher", summary="Question en langage naturel → Cypher (agent ReAct auto-correcteur)")
def cypher(request: QuestionRequest, engine: SOCEngine = Engine) -> dict[str, Any]:
    return engine.cypher(request.question)


@router.post("/siem/rules", summary="Règle de détection Splunk SPL / Microsoft Sentinel KQL")
def siem_rules(request: SiemRuleRequest) -> dict[str, Any]:
    return SOCEngine.siem_rule(**request.model_dump())


@router.post("/guardrail", summary="Vérification anti-injection de prompt (OWASP LLM01)")
def guardrail(request: TextRequest) -> dict[str, Any]:
    return SOCEngine.guardrail(request.text)


@router.get("/audit/graph", summary="Audit d'empoisonnement du graphe de connaissances")
def audit_graph(engine: SOCEngine = Engine) -> dict[str, Any]:
    return engine.audit_graph()


@router.get("/metrics", summary="Métriques consolidées et critères d'acceptation TDSP")
def metrics() -> dict[str, Any]:
    return SOCEngine.metrics()


@router.post("/cases/export", summary="Fiche d'incident au format Markdown (prête pour le ticket)")
def export_case(request: CaseExportRequest) -> dict[str, str]:
    return {"markdown": SOCEngine.case_report(request.model_dump())}
