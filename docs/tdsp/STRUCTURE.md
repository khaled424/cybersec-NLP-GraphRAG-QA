# Structure du dépôt selon le TDSP

Le dépôt suit le cycle de vie du **Team Data Science Process** : chaque phase a
un emplacement identifiable pour son code, ses données et ses livrables. Le
projet est **100 % NLP / Graph-RAG** : il n'entraîne pas de modèle de
machine learning (classification zero-shot, extraction d'entités, graphe de
connaissances, retrieval et génération).

| Phase TDSP | Emplacement | Contenu |
| --- | --- | --- |
| 1. Business Understanding | `docs/tdsp/`, `docs/report/` | Cadrage, rapport métier, critères de réussite |
| 2. Data Acquisition & Understanding | `src/cybersec_nlp/data/`, `notebooks/`, `data/` | Téléchargement, exploration, EDA ; données `raw/`, `interim/`, `processed/`, `external/` (hors Git) |
| 3. Modeling (pipeline NLP) | `src/cybersec_nlp/{features,nlp,graph,rag,evaluation,pipelines}/`, `configs/`, `docs/experiments/` | Prétraitement, zero-shot, NER, graphe, Graph-RAG, évaluation |
| 4. Deployment | `backend/`, `frontend/`, `infra/`, `.github/workflows/` | API FastAPI, interface, Docker, CI |
| 5. Security Audit (Membre 6) | `src/cybersec_nlp/{security,siem}/`, `notebooks/Notebook4_PartB_*.ipynb`, `reports/siem/` | Agentic RAG, audit GragPoison / OWASP LLM08, règles SIEM |
| 5. Customer Acceptance | `docs/report/`, `reports/` | Rapport final, validation avec les utilisateurs |

## Arborescence

```text
configs/               paramètres du pipeline et de l'API (Hydra / YAML)
data/                  raw, interim, processed, external (contenu ignoré par Git)
docs/                  adr, tdsp, experiments, report, assets
notebooks/             EDA et prototypage (001-EDA.ipynb)
reports/               figures et livrables générés
src/cybersec_nlp/      package Python, un sous-package par étape du pipeline
backend/  frontend/    couche de déploiement
infra/                 Dockerfiles et docker-compose
tests/                 tests unitaires et de fumée
```

## Commandes

```bash
python -m cybersec_nlp.data.download   # phase 2 : récupérer le dataset
python -m cybersec_nlp.data.explore    # phase 2 : résumé rapide
python -m cybersec_nlp.pipelines.build_knowledge_base   # phase 3
python -m uvicorn backend.main:app --reload             # phase 4
python -m pytest                                        # tests, dont sécurité et SIEM
```
