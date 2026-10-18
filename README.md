# cybersec-NLP-GraphRAG-QA

An academic project exploring NLP, knowledge graphs, and Graph-RAG for
cybersecurity incident analysis and question answering. Its initial dataset
contains defensive cybersecurity instruction-and-response examples.

## Architecture

- `ml/` — data workflows, machine-learning models, evaluation, and Graph-RAG
  components.
- `backend/` — FastAPI inference and service layer.
- `frontend/` — user-interface application and components.
- `infra/` — Dockerfiles and Docker Compose configuration.
- `configs/` — Hydra and API configuration.
- `scripts/` — dataset download and exploration utilities.
- `tests/` — unit and smoke tests.

## Quick Start

Install the project:

```bash
pip install -e .
```

For tests and linting, install the development extras as well:

```bash
pip install -e ".[dev]"
```

On Windows, run the PowerShell wrapper from the repository root:

```powershell
.\run.ps1 data
.\run.ps1 explore
```

Use `.\run.ps1 api`, `.\run.ps1 test`, or `.\run.ps1 lint` for the API and
quality checks. Alternatively, use the equivalent Make targets on systems
where `make` is available:

```bash
make data
make explore
make api
make test
make lint
```

The download command stores the dataset at `data/raw/cybersec_v1`. The current
dataset has `system`, `user`, and `assistant` fields and no explicit class
labels, so the EDA script reports that a class distribution is unavailable.

## Project Status

- [x] Monorepo-style starter architecture and Python package configuration.
- [x] FastAPI health-check endpoint.
- [x] Hugging Face dataset download and local save workflow.
- [x] Initial EDA summary for row count, columns, labels when present, and
  sample rows.
- [x] Windows PowerShell and Make command wrappers.
- [ ] Train and evaluate production cybersecurity models.
- [ ] Implement and index the complete Graph-RAG workflow.
- [ ] Build the user interface.

## Team

- Emna Trabelsi
- Ines Trabelsi
- Hejer Mnejja
- Walid Fehry
- Khaled Gannoun
- Adrian Salvador Ekomo Mesi Obono
