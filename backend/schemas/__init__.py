"""Request models of the SOC assistant API (validated by FastAPI / Pydantic)."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, examples=["Quelle CVE affecte log4j ?"])
    strategy: Literal["vector", "graph", "hybrid"] = "hybrid"
    use_llm: bool = True
    previous_question: str | None = Field(default=None, max_length=2000)


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500, examples=["Which malware targets the banking sector?"])


class SiemRuleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="Règle générée par l'assistant SOC", max_length=500)
    technique: str = Field(default="T1071.001", pattern=r"^T\d{4}(\.\d{3})?$")
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    ips: list[str] = Field(default_factory=list, max_length=500)
    domains: list[str] = Field(default_factory=list, max_length=500)
    sha256: list[str] = Field(default_factory=list, max_length=500)


class CaseExportRequest(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    title: str = Field(default="Incident", max_length=200)
    status: str = Field(default="Nouveau", max_length=60)
    opened_at: str = Field(default="", max_length=40)
    report: str = Field(default="", max_length=20000)
    notes: str = Field(default="", max_length=20000)
    triage: dict[str, Any] = Field(default_factory=dict)
    journal: list[dict[str, str]] = Field(default_factory=list, max_length=500)
