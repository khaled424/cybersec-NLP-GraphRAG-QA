# 🛡️ Vigie — l'assistant SOC qui cite ses sources

**Projet :** Cybersécurité & Traitement Automatique du Langage (NLP, GNN & Graph-RAG) · méthodologie **TDSP**

*Vigie* (la vigie : le guetteur en haut du mât, qui repère la menace le premier) est un assistant pour les
analystes d'un SOC. Il répond aux questions **à partir de preuves citées**, trie les rapports d'incident,
interroge un graphe de connaissances **STIX 2.1** en langage naturel, audite sa propre base contre
l'empoisonnement et transforme les indicateurs en **règles de détection Splunk / Microsoft Sentinel**.
Tout tourne en local (LLM Qwen2.5-1.5B sur GPU) : aucune donnée ne quitte la machine.

| Besoin du SOC | Ce que fait Vigie | Mesure (corpus réel) |
| --- | --- | --- |
| Répondre vite et de façon traçable | HybridRAG : FAISS (E5 multilingue) + graphe STIX, réponses citées `[S#]` | Recall@4 0,81 · MRR 0,755 · ~4 ms de recherche |
| Ne pas inventer | contrôle de fidélité phrase par phrase, abstention | 99 % de phrases étayées · 100 % d'abstention hors domaine |
| Trier les rapports | catégorie SOC + entités (IP, CVE, malwares, logiciels, cibles…) | macro-F1 0,53 (7 catégories) · NER SecBERT micro-F1 0,91 |
| Interroger le graphe | agent ReAct Text-to-Cypher auto-correcteur | réponses exactes 0 → 4 / 10 grâce à l'agent |
| Rester sûr | garde-fou anti-injection, audit GragPoison, OWASP LLM08 | quarantaine : précision 1,00 · rappel 0,94 · 0 faux positif |
| Agir | règles SPL / KQL avec validation stricte des IOC | 19 faux IOC du corpus rejetés sur 20 |

**14 des 15 critères d'acceptation proposés sont atteints** (détail : `notebooks/00_Master_Notebook.ipynb`
ou page *Métriques* de Vigie). Les seuils sont des propositions à valider avec l'équipe et le SOC.

## Démarrage rapide

```bash
make install     # dépendances (requirements.txt), package en mode éditable, modèle spaCy
make pipeline    # corpus nettoyé → NER → graphe STIX → scripts Neo4j → index FAISS → classifieur (~2 min)
make mvp         # Vigie : API http://localhost:8000/docs + interface http://localhost:8501
```

Sous Windows : `.\run.ps1 install`, `.\run.ps1 pipeline`, puis `.\run.ps1 api` et `.\run.ps1 ui` dans deux terminaux.
Sans GPU CUDA, Vigie fonctionne en mode **extractif** (preuves citées, sans génération).
Docker (CPU) : `make pipeline` puis `docker compose -f infra/docker-compose.yml up --build`.

### Les pages de Vigie

| Page | Usage |
| --- | --- |
| 🛡️ **Assistant SOC** | conversation, stratégie de recherche (hybride / vecteurs / graphe), preuves dépliables, phrases non étayées signalées |
| 🏷️ **Analyse de rapport** | catégorie et confiance, entités surlignées, nœuds du graphe liés, brouillon de règle SIEM |
| 🕸️ **Graphe (agent)** | question → Cypher, trace ReAct complète, résultats |
| 📤 **Règles SIEM** | formulaire d'IOC → SPL, KQL, `savedsearches.conf`, règle Sentinel JSON (téléchargeables) |
| 🔐 **Sécurité** | test du garde-fou, audit d'empoisonnement du graphe chargé |
| 📊 **Métriques** | critères d'acceptation et résultats de chaque notebook |

## Notebooks (répartition du travail, 6 membres)

| Notebook | Responsable | Contenu |
| --- | --- | --- |
| `Notebook1_Preprocessing_NER_Graph` | Walid | nettoyage, EDA, LDA, NPMI, TF-IDF vs Word2Vec vs GloVe vs SBERT, NER (règles + SecBERT), graphe STIX 2.1, Neo4j |
| `Notebook2_PartA_GNN_PyG` | Membre 2 | GCN / GAT (PyTorch Geometric), texte seul vs GNN, graphe NER de Walid |
| `Notebook2_PartB_GTN_Leiden` | Membre 3 | Graph Transformer hétérogène, Hierarchical Leiden, cartographie des menaces |
| `Notebook3_LLM_FineTuning_Evaluation` | Membre 4 | prompting mesuré, LoRA réel, ROUGE / BERTScore / FactCC, garde-fou |
| `Notebook4_PartA_HybridRAG_Pipeline` | Membre 5 | chunking, FAISS, HybridRAG, benchmark sur le corpus réel |
| `Notebook4_PartB_AgenticRAG_Security_SIEM` | Membre 6 | agent ReAct, GragPoison, OWASP LLM08, export SIEM |
| `00_Master_Notebook` | Équipe | synthèse TDSP, résultats consolidés, démonstration du moteur de Vigie |

`make notebooks` les exécute dans l'ordre (≈ 1 h sur une RTX 4060). Détails : [`notebooks/README.md`](./notebooks/README.md).

## Architecture

```text
data/raw ──► cybersec_nlp.data ──► nlp.ner ──► graph.knowledge_graph ──► knowledge_graph.json / import.cypher
                                      │                                         │
                                      └──► rag.vector_index (FAISS, E5)         │
                                                    │                           │
question ──► llm.guardrails ──► rag.hybrid (vecteurs + graphe, fusion) ──► llm.local_llm ──► rag.grounding ──► réponse citée
                                rag.agentic (Text-to-Cypher ReAct) ◄──────────┘
security.graph_poison · security.owasp_llm08 · siem.rules · evaluation.report
                    └──────────── engine.SOCEngine ────────────┘
                         backend/ (FastAPI)   frontend/ (Streamlit)
```

- `src/cybersec_nlp/` — package partagé et testé (73 tests) : une seule implémentation pour les notebooks, l'API et l'interface.
- `notebooks/` — un notebook par membre + notebook maître ; chacun exporte ses métriques dans `reports/metrics/`.
- `backend/`, `frontend/`, `infra/` — Vigie (API, interface, Docker).
- `docs/` — rapport TDSP, structure du dépôt ([`docs/tdsp/STRUCTURE.md`](./docs/tdsp/STRUCTURE.md)), décisions d'architecture ([`docs/adr/`](./docs/adr/)).
- [Compte rendu TDSP phases 1–2](./docs/tdsp/PHASES_1_2.md) · [Guide de déploiement](./GUIDE_DEPLOIEMENT.md).

## 📊 Le dataset

- **Source :** [AlicanKiraz0/Cybersecurity-Dataset-v1](https://huggingface.co/datasets/AlicanKiraz0/Cybersecurity-Dataset-v1) (Apache 2.0), révision figée `410b35d5`, vérifiée par SHA-256 (`data/raw/cybersec_v1/provenance.json`).
- **Taille :** 2 411 paires `system` / `user` / `assistant` ; **2 194** conservées après nettoyage (doublons, réponses tronquées, blocs `<think>`).
- **Limites :** pas de labels (catégories obtenues par supervision faible ou LDA), peu d'IOC réels, pas de relations validées : les relations du graphe sont des associations candidates avec leurs documents sources.

## Qualité

```bash
make test        # pytest (les tests qui demandent les artefacts sont ignorés si le pipeline n'a pas tourné)
make lint        # ruff
```

## Team

- Emna Trabelsi
- Ines Trabelsi
- Hejer Mnejja
- Walid Fehry
- Khaled Gannoun
- Adrian Salvador Ekomo Mesi Obono
