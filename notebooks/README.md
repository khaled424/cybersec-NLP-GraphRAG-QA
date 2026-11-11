# Notebooks

Les notebooks suivent la répartition du travail (6 membres, 4 notebooks académiques) et la méthodologie TDSP.
La logique réutilisable vit dans `src/cybersec_nlp/` (testée) ; les notebooks l'exécutent, l'expliquent et la
**mesurent**. Chaque notebook exporte ses métriques dans `reports/metrics/`.

| Ordre | Notebook | Responsable | Étape TDSP | Contenu |
| --- | --- | --- | --- | --- |
| 1 | `Notebook1_Preprocessing_NER_Graph.ipynb` | Walid | 2 — Data | Nettoyage, spaCy, LDA, NPMI, TF-IDF vs Word2Vec vs GloVe vs SBERT, NER (règles + SecBERT), graphe STIX 2.1, scripts Neo4j, livrables Jalon 1 |
| 2 | `Notebook2_PartA_GNN_PyG.ipynb` | Membre 2 | 3 — Modeling | GCN / GAT (PyG), 4 graphes dont celui du NER, texte seul vs GNN, sur-smoothing, attention |
| 3 | `Notebook2_PartB_GTN_Leiden.ipynb` | Membre 3 | 3 — Threat mapping | HGT hétérogène, robustesse 5 seeds, occlusion, Hierarchical Leiden, cartographie, PyVis |
| 4 | `Notebook3_LLM_FineTuning_Evaluation.ipynb` | Membre 4 | 3 — Model tuning | Température / top-p mesurés, zero/few-shot, CoT, self-consistency, LoRA réel, ROUGE / BERTScore / FactCC, juge LLM, garde-fou |
| 5 | `Notebook4_PartA_HybridRAG_Pipeline.ipynb` | Membre 5 | 4 — Operationalization | Démo contrôlée + passage à l'échelle : FAISS (E5), graphe STIX, LLM local, benchmark réel, abstention, fidélité |
| 6 | `Notebook4_PartB_AgenticRAG_Security_SIEM.ipynb` | Membre 6 | 5 — Security audit | Agent ReAct Text-to-Cypher, GragPoison, OWASP LLM08, export SIEM (SPL / KQL), sur démo puis graphe réel |
| 7 | `00_Master_Notebook.ipynb` | Équipe | 1 → 5 | Synthèse TDSP, résultats consolidés, démonstration du moteur du MVP, critères d'acceptation |
| — | `001-EDA.ipynb` | Équipe | 2 — Data | Profilage initial du dataset |

**Exécution** : `make pipeline` puis `make notebooks` (dans l'ordre ci-dessus ; GPU CUDA requis pour les
Notebooks 3, 4A §7 et 4B §6.1). Les données brutes et les artefacts lourds (`data/`, `artifacts/`) ne sont pas versionnés.
