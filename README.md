# cybersec-nlp-graphrag

Monorepo-style starter structure for cybersecurity incident analysis and
question answering with NLP, knowledge graphs, and Graph-RAG.

## Getting started

```bash
python -m pip install -e ".[dev]"
make test
make api
```

The API health check is available at `GET /health`. Start the Hydra-based
training skeleton with `make train`.

## Project layout

- `ml/`: data, models, evaluation, and Graph-RAG pipelines
- `backend/`: FastAPI application, routes, schemas, and services
- `frontend/`: UI placeholder
- `configs/`: Hydra YAML configuration
- `infra/`: Dockerfiles and Compose configuration
- `tests/`: smoke tests

TODO: Document data sources, model choices, and end-to-end workflows as they
are implemented.
