"""Smoke tests for the API."""

from backend.main import app, health


def test_health_returns_ok() -> None:
    assert health() == {"status": "ok"}


def test_health_route_is_registered() -> None:
    assert any(route.path == "/health" for route in app.routes)
