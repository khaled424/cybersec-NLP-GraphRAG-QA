"""FastAPI application of Vigie, the SOC assistant (TDSP stage 4 — deployment).

Run: ``uvicorn backend.main:app`` (``make api``). Interactive docs at ``/docs``.
"""

from fastapi import FastAPI

from backend.api import router

app = FastAPI(
    title="Vigie API",
    description="Assistant SOC : HybridRAG cité, triage de rapports, agent Cypher, audit de sécurité et export SIEM.",
    version="1.0.0",
)
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return the API health status."""
    return {"status": "ok"}
