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
| 7 | `Synthese_TDSP.ipynb` | Équipe | 1 → 5 | Synthèse TDSP, résultats consolidés, démonstration du moteur de Vigie, critères d'acceptation |
| ★ | **`00_Master_Notebook.ipynb`** | Équipe | 1 → 5 | **Livrable final** : toutes les cellules des notebooks ci-dessus (0 → 7), une partie par notebook |
| — | `001-EDA.ipynb` | Équipe | 2 — Data | Profilage initial du dataset |

**Notebook maître.** Il est **généré** par `scripts/build_master_notebook.py` : ne pas le modifier à la main, mais
modifier le notebook source puis lancer `mise run master` (reconstruction + exécution). Chaque partie démarre par une
cellule d'isolation (remise à zéro du noyau, libération du GPU). Son texte est une **version condensée** des cellules
Markdown (`scripts/master_summaries.md`, une entrée par cellule source) ; `mise run master-text` l'actualise sans
réexécuter le code. Une cellule source modifiée reprend son texte complet et la construction le signale.

**Exécution** : `mise run pipeline` puis `mise run notebooks` (dans l'ordre ci-dessus ; GPU CUDA requis pour les
Notebooks 3, 4A §7 et 4B §6.1). Les données brutes et les artefacts lourds (`data/`, `artifacts/`) ne sont pas versionnés.
