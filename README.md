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

## Documentation

- [Compte rendu TDSP — phases 1 et 2](./docs/tdsp/PHASES_1_2.md) — cadrage,
  inventaire des données, décisions ouvertes et consignes de partage avec
  l'équipe.
- [Guide de déploiement et de mise en production](./GUIDE_DEPLOIEMENT.md) —
  étapes, vérifications et contrôles de sécurité pour faire évoluer le
  prototype vers une solution fiable.
- [Rapport projet TDSP](./rapport-projet-cybersecurity-tdsp.md) — objectifs,
  architecture proposée et feuille de route.

## Quick Start

Install the project and development tools:

```bash
pip install -e ".[dev]"
```

On Windows, run the PowerShell wrapper from the repository root:

```powershell
.\run.ps1 data
.\run.ps1 explore
```

Use the other PowerShell commands as needed:

```powershell
.\run.ps1 api
.\run.ps1 test
.\run.ps1 lint
```

The download command stores the dataset at `data/raw/cybersec_v1`. The current
dataset has `system`, `user`, and `assistant` fields and no explicit class
labels, so the EDA script reports that a class distribution is unavailable.

## 📊 Le Dataset

- **Source:** [AlicanKiraz0/Cybersecurity-Dataset-v1](https://huggingface.co/datasets/AlicanKiraz0/Cybersecurity-Dataset-v1), sous licence Apache 2.0.
- **Taille :** environ 2 500 paires d'instructions et de réponses, structurées avec les champs `system`, `user` et `assistant`.
- **Absence de labels explicites :** le dataset ne fournit pas de classes prêtes à l'emploi. Nous utiliserons donc une classification *zero-shot*, sans entraînement sur des labels de classes du dataset.
- **Format `.arrow` :** les fichiers Arrow sont des fichiers binaires, donc illisibles directement dans un éditeur de texte. Ce format est optimisé pour le chargement et le traitement avec Hugging Face `datasets`; utilisez Python et `load_from_disk` pour lire le dataset enregistré.

## Project Status

- [x] Monorepo-style starter architecture and Python package configuration.
- [x] FastAPI health-check endpoint.
- [x] Hugging Face dataset download and local save workflow
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
