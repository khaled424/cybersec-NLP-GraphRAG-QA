# Structure du dépôt selon le TDSP

Le dépôt suit le cycle de vie du **Team Data Science Process** : chaque phase a
un emplacement identifiable pour son code, ses données et ses livrables, et la
répartition du travail suit le plan à 6 membres (4 notebooks académiques).

| Phase TDSP | Emplacement | Contenu |
| --- | --- | --- |
| 1. Business Understanding | `docs/tdsp/`, `docs/report/` | Cadrage SOC, rapport métier, critères de réussite proposés (`cybersec_nlp.evaluation.report`) |
| 2. Data Acquisition & Understanding | `notebooks/Notebook1_*`, `notebooks/001-EDA.ipynb`, `src/cybersec_nlp/data/`, `data/` | Acquisition figée (SHA-256), nettoyage, EDA, NER, graphe STIX, export Neo4j |
| 3. Modeling | `notebooks/Notebook2_PartA_*`, `Notebook2_PartB_*`, `Notebook3_*`, `Notebook4_PartA_*`, `src/cybersec_nlp/{nlp,graph,rag,llm,evaluation}/` | GCN/GAT, HGT + Leiden, LLM (prompting, LoRA), HybridRAG |
| 4. Deployment | `backend/`, `frontend/`, `infra/`, `src/cybersec_nlp/engine.py`, `.github/workflows/` | API FastAPI, interface Streamlit, Docker, CI |
| 5. Security Audit & Acceptance | `notebooks/Notebook4_PartB_*`, `notebooks/00_Master_Notebook.ipynb`, `src/cybersec_nlp/{security,siem}/`, `reports/` | Agent ReAct, GragPoison, OWASP LLM08, SIEM, critères d'acceptation |

## Arborescence

```text
data/                  raw (copie brute figée), processed (livrables du Notebook 1) — contenu ignoré par Git
artifacts/             index FAISS, classifieur, modèles fine-tunés (SecBERT, LoRA) — ignoré par Git
notebooks/             Notebooks 1, 2A, 2B, 3, 4A, 4B, Synthese_TDSP, EDA de profilage
                       + 00_Master_Notebook (livrable, généré par scripts/build_master_notebook.py)
scripts/               build_master_notebook.py, master_summaries.md (texte condensé du maître)
reports/metrics/       métriques JSON exportées par chaque notebook (lues par le maître et le MVP)
reports/siem/          règles SPL / KQL générées
reports/figures/       graphes interactifs (PyVis)
src/cybersec_nlp/      package partagé et testé
  config.py            chemins et constantes (source unique)
  data/                chargement vérifié et nettoyage du corpus
  nlp/                 NER cyber (STIX), classifieur de triage
  graph/               graphe STIX 2.1, backend Cypher en mémoire, export / import Neo4j
  rag/                 chunking, index FAISS, HybridRAG, contrôle de fidélité, agent ReAct
  llm/                 LLM local (Qwen2.5-1.5B), prompts, garde-fou anti-injection
  security/            détection d'empoisonnement du graphe, contrôles OWASP LLM08
  siem/                génération de règles Splunk / Sentinel
  evaluation/          métriques de recherche, rapport d'acceptation
  pipelines/           construction de bout en bout des artefacts
  engine.py            façade SOCEngine (API, interface, notebook maître)
backend/               API FastAPI (routes, schémas, service)
frontend/              interface Streamlit (6 pages) + client HTTP
infra/                 Dockerfiles et docker-compose
tests/                 tests unitaires et d'API
```

## Flux de données entre membres

```text
Notebook 1 (Walid) ──► corpus_clean.parquet, entities.json, knowledge_graph.json, rag_documents.jsonl,
                       df_clean_eda.parquet, neo4j/import.cypher
     ├──► Notebook 2A (GCN/GAT : graphe D = entités du NER)
     ├──► Notebook 2B (HGT + Leiden : entités du NER, thèmes LDA)
     ├──► Notebook 4A (HybridRAG : contrat RAG + graphe STIX) ◄── LLM local du Notebook 3
     └──► Notebook 4B (agent Cypher, audit, SIEM sur le graphe réel) ◄── LLM local du Notebook 3
Tous ──► reports/metrics/*.json ──► Synthese_TDSP + page « Pilotage » de Vigie
Tous ──► scripts/build_master_notebook.py ──► 00_Master_Notebook (livrable : toutes les cellules, ordre TDSP)
```

## Commandes

Avec mise (`mise run <tâche>`, liste complète dans [`docs/COMMANDES.md`](../COMMANDES.md)) ou make :

```bash
make install     # dépendances, package, modèle spaCy
make pipeline    # artefacts : corpus, NER, graphe, Cypher, index FAISS, classifieur
make notebooks   # exécute les notebooks dans l'ordre (GPU recommandé)
make mvp         # API (http://localhost:8000/docs) + interface (http://localhost:8501)
make test lint   # qualité
```
