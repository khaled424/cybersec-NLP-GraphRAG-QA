"""Thin HTTP client of the SOC assistant API (the UI never imports the ML stack directly)."""

from __future__ import annotations

import os
from typing import Any

import httpx

API_URL = os.getenv("CYBERSEC_API_URL", "http://localhost:8000")
TIMEOUT = httpx.Timeout(180.0, connect=5.0)  # first LLM call loads the model


class ApiError(RuntimeError):
    """Readable error raised for any failed API call."""


def _request(method: str, path: str, **kwargs: Any) -> Any:
    try:
        response = httpx.request(method, f"{API_URL}{path}", timeout=TIMEOUT, **kwargs)
    except httpx.HTTPError as exc:
        raise ApiError(f"API injoignable ({API_URL}) : lancez `make api`. Détail : {exc}") from exc
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ApiError(f"Erreur {response.status_code} : {detail}")
    return response.json()


def health() -> bool:
    try:
        return _request("GET", "/health")["status"] == "ok"
    except ApiError:
        return False


def status() -> dict[str, Any]:
    return _request("GET", "/status")


def ask(question: str, strategy: str, use_llm: bool, previous_question: str | None) -> dict[str, Any]:
    return _request("POST", "/ask", json={"question": question, "strategy": strategy, "use_llm": use_llm,
                                          "previous_question": previous_question})


def analyze(text: str) -> dict[str, Any]:
    return _request("POST", "/analyze", json={"text": text})


def cypher(question: str) -> dict[str, Any]:
    return _request("POST", "/cypher", json={"question": question})


def siem_rule(payload: dict[str, Any]) -> dict[str, Any]:
    return _request("POST", "/siem/rules", json=payload)


def guardrail(text: str) -> dict[str, Any]:
    return _request("POST", "/guardrail", json={"text": text})


def audit_graph() -> dict[str, Any]:
    return _request("GET", "/audit/graph")


def metrics() -> dict[str, Any]:
    return _request("GET", "/metrics")
