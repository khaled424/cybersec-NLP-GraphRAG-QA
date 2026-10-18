.PHONY: install data explore api test lint

install:
	python -m pip install -e ".[dev]"

data:
	python scripts/download_data.py

explore:
	python scripts/explore_data.py

api:
	python -m uvicorn backend.main:app --reload

test:
	python -m pytest

lint:
	python -m ruff check .
