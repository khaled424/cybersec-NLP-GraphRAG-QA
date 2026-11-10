# Notebooks

Ce dossier est réservé à l'exploration des données, à l'analyse exploratoire
(EDA) et au prototypage d'expériences NLP ou graphes.

- Les notebooks servent à explorer et documenter des hypothèses.
- La logique destinée à être réutilisée en production doit être déplacée vers
  `src/cybersec_nlp/` (`data/`, `features/`, `nlp/`, `graph/`, `rag/` ou `pipelines/`).
- Indiquez les prérequis, les données attendues et les étapes d'exécution dans
  le notebook. N'ajoutez pas de données privées ou de fichiers volumineux au
  dépôt.

## Index des notebooks

| Notebook | Responsable | Contenu |
| --- | --- | --- |
| `001-EDA.ipynb` | Équipe (TDSP phase 2) | Analyse exploratoire du dataset |
| `Notebook4_PartB_AgenticRAG_Security_SIEM.ipynb` | Membre 6 | Agentic RAG (ReAct), audit sécurité (GragPoison, OWASP LLM08), export SIEM (SPL/KQL) |

Le notebook 4B s'exécute hors ligne (graphe en mémoire, LLM simulé) :
`jupyter nbconvert --to notebook --execute --inplace notebooks/Notebook4_PartB_AgenticRAG_Security_SIEM.ipynb`.
Ses sorties (règles SIEM) sont écrites dans `reports/siem/`.
