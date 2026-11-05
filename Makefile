.PHONY: install data explore api test lint

install:
	python -m pip install -e ".[dev]"

data:
	python -m cybersec_nlp.data.download

explore:
	python -m cybersec_nlp.data.explore

api:
	python -m uvicorn backend.main:app --reload

test:
	python -m pytest

lint:
	python -m ruff check .
