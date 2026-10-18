"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="Cybersec NLP GraphRAG API")


@app.get("/health")
def health() -> dict[str, str]:
    """Return the API health status."""
    return {"status": "ok"}
