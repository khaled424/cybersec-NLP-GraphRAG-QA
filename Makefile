.PHONY: install data train api frontend test lint

install:
	python -m pip install -e ".[dev]"

data:
	python scripts/download_data.py

train:
	python -m ml.pipelines.train

api:
	uvicorn backend.main:app --reload

frontend:
	python frontend/app.py

test:
	python -m pytest

lint:
	ruff check .
