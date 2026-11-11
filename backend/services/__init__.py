"""Service layer: a single lazily created :class:`SOCEngine` shared by all requests."""

from functools import lru_cache

from fastapi import HTTPException

from cybersec_nlp.engine import ArtifactsMissingError, SOCEngine


@lru_cache(maxsize=1)
def _engine() -> SOCEngine:
    return SOCEngine()


def get_engine() -> SOCEngine:
    """FastAPI dependency; 503 with an actionable message when the pipeline has not been run."""
    try:
        return _engine()
    except ArtifactsMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
