# Texte condensé du notebook maître

Version courte des cellules Markdown des notebooks de l'équipe, utilisée par
`scripts/build_master_notebook.py` pour le notebook maître (le livrable) : mêmes résultats,
lecture plus rapide. Les notebooks d'origine gardent leur texte complet.

- Chaque bloc commence par `<!-- résumé <empreinte> · <notebook> -->` ; l'empreinte identifie
  la cellule source remplacée. Les titres sont au niveau du notebook source (le maître les décale).
- Si la cellule source est modifiée, le résumé ne s'applique plus : le maître reprend le texte
  complet et la construction signale le résumé comme obsolète. Il suffit alors de mettre à jour
  le bloc avec l'empreinte de la nouvelle cellule (fonction `fingerprint` du script).
- Après une modification de ce fichier : `mise run master-text` (texte seul, sans réexécution).

<!-- résumé a49c12a5d03c · 001-EDA -->
# 001 — Profilage initial du jeu de données `Cybersecurity-Dataset-v1`

**TDSP Phase 2 — Data Acquisition & Understanding** · analyse en lecture seule, avant toute modélisation.

- **Objectif** : comprendre le corpus de façon fiable et reproductible.
- **Données** : [`AlicanKiraz0/Cybersecurity-Dataset-v1`](https://huggingface.co/datasets/AlicanKiraz0/Cybersecurity-Dataset-v1) (Hugging Face).
- **Références** : `docs/tdsp/Rapport_Business_Understanding.pdf`, `docs/tdsp/PHASES_1_2.md`.
- Tous les chiffres sont **calculés à l'exécution** : aucune valeur codée en dur.

<!-- résumé 2009c13152a4 · 001-EDA -->
## Sommaire

| § | Contenu |
|---|---|
| 1 | Objectif et périmètre |
| 2 | Environnement, chargement, empreinte SHA-256, schéma |
| 3 | Qualité structurelle : manquants, doublons, anomalies de format |
| 4 | Statistiques de longueur et nombre de tokens |
| 5 | Visualisations |
| 6 | Inspection manuelle (sorties masquées) |
| 7 | Déduplication normalisée et similarité sémantique |
| 8 | Couverture thématique candidate (lexique, k-means) |
| 9 | Refus, risques et complétude des réponses |
| 10 | Candidats CVE / IPv4 renforcés |
| 11 | Dossier des lignes incomplètes |
| 12 – 14 | Constats, limites, synthèse exécutive |

<!-- résumé 05e7a031991a · 001-EDA -->
## Lecture du code

Chaque cellule de code commence par un commentaire qui annonce son rôle. Les sections 7 à 9 réutilisent les copies normalisées de la section 7.1, la synthèse (section 14) agrège toutes les métriques, et la source n'est jamais modifiée.

<!-- résumé d47d6d9b53aa · 001-EDA -->
## Section 1 — Objectif et périmètre

Profiler le corpus (structure, statistiques, anomalies) puis lever les six limites de la première version (sections 7 à 11), **sans jamais modifier la source** : toutes les mesures portent sur des copies normalisées.

| Inclus | Exclu |
|---|---|
| Structure, manquants, doublons, longueurs, visualisations | Toute modification du dataset |
| Similarité sémantique et classes candidates (exploratoires) | Étiquettes définitives, classification supervisée (Phase 3) |
| Motifs de refus × risque, candidats CVE / IPv4 | Véracité des réponses, annotation NER |

**Rappels** : un *embedding* représente un texte par un vecteur (textes proches ⇒ vecteurs proches) ; la *silhouette* mesure la séparation des clusters ; un *lexique* est une liste de mots-clés de travail, forcément incomplète.

<!-- résumé 5723d83034c4 · 001-EDA -->
## Section 2 — Environnement et chargement

Imports, graine fixée (42), téléchargement du Parquet Hugging Face avec **empreinte SHA-256** (traçabilité) et contrôle du schéma. Si les données manquent, le chargement **échoue** : aucune donnée de substitution n'est utilisée.

<!-- résumé bab4b129f46a · 001-EDA -->
## Section 3 — Validation structurelle

Manquants, chaînes vides et chaînes d'espaces (trois diagnostics distincts), types inattendus, lignes mal formées, doublons exacts et répétitions dans une colonne (légitimes pour le prompt `system`, suspectes pour les questions). Chaque mesure est donnée en valeur absolue et en %.

<!-- résumé d487c48d49b0 · 001-EDA -->
## Section 4 — Statistiques descriptives des textes

Pour `system`, `user` et `assistant` : nombre de caractères et de mots (mot = suite séparée par des espaces, à ne pas confondre avec un token), position et dispersion (minimum → P99), textes anormalement courts (< 50 caractères) ou longs (> P99). Le nombre de **tokens GPT-2** donne un ordre de grandeur de l'encombrement, pas celui du modèle final.

<!-- résumé ff4b7b19ccee · 001-EDA -->
## Section 5 — Visualisations

| Graphique | Question tranchée |
|---|---|
| Barres des champs défectueux | Où sont les valeurs manquantes ou vides ? |
| Histogrammes des longueurs | Les trois champs ont-ils des distributions différentes ? |
| Boîtes user vs assistant | Questions courtes, réponses longues ? |
| Nuage + corrélation | La longueur de la réponse suit-elle celle de la question ? |

<!-- résumé 54f9034db8cd · 001-EDA -->
## Section 6 — Inspection manuelle

Les statistiques décrivent la forme, pas le fond : un échantillon reproductible (typique, court, long, suspect) est lu pour vérifier le contenu et le ton, et repérer fuites ou hors-sujet. Les secrets (e-mails, clés, jetons) sont **masqués à l'affichage** uniquement.

<!-- résumé 032b182b24e3 · 001-EDA -->
## Section 7 — Déduplication normalisée et similarité sémantique

1. **Doublons normalisés** : *strict* (NFKC, casse, espaces, blocs `think` retirés) puis *large* (ponctuation en plus), sur des copies.
2. **Similarité sémantique** : embeddings `all-MiniLM-L6-v2` (GPU), distribution des plus proches voisins, paires au-delà de 0,90 et 0,80.
3. **Groupes de redondance** : clustering agglomératif au seuil cosinus 0,85.

*Statut : exploratoire.*

<!-- résumé 73bb05acc48f · 001-EDA -->
## Section 8 — Couverture thématique candidate

Il n'existe pas de taxonomie validée : deux vues croisées préparent les étiquettes de la Phase 3.

1. **Lexique** de classes de sécurité appliqué aux questions (questions multi-classes et sans classe comptées).
2. **TF-IDF + k-means**, k choisi par la silhouette, termes dominants par cluster.
3. **Table croisée** lexique × clusters.

*Statut : classes candidates, pas des étiquettes.*

<!-- résumé d220f11cbdaa · 001-EDA -->
## Section 9 — Refus, risques et complétude des réponses

Des indicateurs structurels, sans jugement des réponses :

1. **Refus** détectés dans les 600 premiers caractères de la réponse ;
2. **Risque** : formulations « dual-use » dans la question (indicatif) ;
3. **Risque × refus** : les paires « risque sans refus » sont prioritaires pour la revue humaine ;
4. **Complétude** : blocs de code, titres, URL, réponses tronquées, gabarits répétés.

<!-- résumé f8153bb36905 · 001-EDA -->
## Section 10 — Candidats CVE et IPv4 renforcés

Les regex brutes laissent passer des faux positifs (années douteuses, numéros de version `1.2.3.4`). On resserre :

- **CVE** : année plausible (1999 → année courante), séquence ≥ 100 ;
- **IPv4** : octets ≤ 255, puis adresses publiques vs privées (RFC 1918, bouclage, lien-local, CGNAT) ;
- un échantillon en contexte par type, matière première du NER.

*Statut : candidats, pas des annotations.*

<!-- résumé e7a9b788ff80 · 001-EDA -->
## Section 11 — Dossier des lignes incomplètes

Les lignes à champ défectueux ne donnent pas de paire Q/R complète. On liste leurs identifiants avec leur contexte (± 1 ligne) et une matrice de décision (annoter / exclure / compléter). **La décision revient à la revue d'équipe**, pas au code.

<!-- résumé dda400dc0ab8 · 001-EDA -->
## Section 12 — Premiers constats de qualité

Consolidation des contrôles des sections 3 à 6 : catégorie, effectif, %, méthode, preuve, impact et action recommandée. Un contrôle à 0 anomalie ne prouve pas l'absence de problème, seulement que ce contrôle n'a rien trouvé.

<!-- résumé d46619e2949f · 001-EDA -->
## Section 13 — Limites et prochaines étapes

| Limite initiale | Traitement | Reste à faire |
|---|---|---|
| Diversité | déduplication normalisée + similarité (S7) | trancher en revue |
| Couverture thématique | lexique + k-means (S8) | valider les classes |
| Conformité défensive | refus × risque (S9) | revue humaine |
| Entités | candidats CVE / IPv4 (S10) | annotation NER |
| Lignes incomplètes | dossier + matrice (S11) | décision d'équipe |
| Qualité sémantique | complétude + gabarits (S9.2) | véracité invérifiable sans source de référence (NVD, ATT&CK) |

**Hypothèses à ne pas lire comme des résultats** : le caractère « défensif » du corpus (déclaré par le fournisseur), les lexiques et les clusters (conventions de travail), les seuils 0,90 / 0,80 / 0,85 (choix de lecture).

**Suite** : arbitrages humains, nettoyage sur copie avec identifiants stables, découpage respectant la déduplication, annotation.

<!-- résumé abe7967205e8 · 001-EDA -->
## Section 14 — Synthèse exécutive

Statut calculé à partir des seules métriques ci-dessus. Il évalue la préparation à l'étape suivante, pas l'aptitude à entraîner un modèle :

| Statut | Condition |
|---|---|
| `BLOCKED BY DATA QUALITY ISSUES` | champs critiques inutilisables ou plus de ~5 % de lignes mal formées |
| `READY FOR NEXT EDA STAGE` | aucun défaut structurel |
| `READY WITH INVESTIGATION REQUIRED` | défauts mineurs isolés, à qualifier |

<!-- résumé fe6148cb5d6f · 001-EDA -->
### Provenance et reproductibilité

Graine 42 · empreinte SHA-256 du Parquet (section 2) · versions des bibliothèques affichées · source jamais modifiée · embeddings `all-MiniLM-L6-v2` sur GPU si disponible. Le nettoyage du corpus qui découle de ce profilage est fait dans la partie 1.

<!-- résumé 460841a5ae39 · Notebook1_Preprocessing_NER_Graph -->
# Notebook 1 — Preprocessing NLP, NER cyber & base Neo4j

**Responsable :** Walid Fehry · **Chapitre 1** (NLP fondamental, vectorisation, graphes) · **TDSP 2** · **Livrables (Jalon 1)** : corpus prétraité, entités cyber (JSON), graphe STIX 2.1, scripts Cypher Neo4j.

| Besoin SOC | Réponse | § |
| --- | --- | --- |
| Comprendre le corpus | nettoyage tracé, statistiques, thèmes LDA, co-occurrences NPMI | 2 – 9 |
| Représenter le texte | TF-IDF vs Word2Vec vs GloVe vs SBERT, mesurés | 10 – 11 |
| Extraire IP, CVE, malwares, logiciels, cibles | NER à règles (STIX) + fine-tuning de SecBERT | 12 |
| Relier menaces, vecteurs et cibles | graphe STIX 2.1 / MITRE ATT&CK, import Neo4j | 13 – 14 |
| Alimenter l'équipe | livrables dans `data/processed/` | 15 |

**Données** : `AlicanKiraz0/Cybersecurity-Dataset-v1` (2 411 paires *system / user / assistant*, Apache 2.0), révision figée et vérifiée par SHA-256. La logique partagée avec l'équipe et le MVP est dans `src/cybersec_nlp/` (testée) ; ce notebook l'exécute et la mesure.

<!-- résumé c6715972c089 · Notebook1_Preprocessing_NER_Graph -->
## 4. Nettoyage

Implémenté une seule fois (`cybersec_nlp.data.loading.clean_dataset`) : **toute l'équipe et le MVP utilisent le même corpus**.

1. suppression de `system` et des lignes sans question ou réponse ;
2. dédoublonnage des questions (la réponse la plus longue est gardée) ;
3. normalisation : entités HTML, `\n` littéraux, blocs `<think>`, espaces ;
4. retrait des textes trop courts ou **tronqués**.

Identifiant stable `doc_id = HF-<ligne brute>`, réutilisé comme provenance dans le graphe et dans les citations du RAG.

<!-- résumé 23c7db902607 · Notebook1_Preprocessing_NER_Graph -->
> **Interprétation.** **2 194 documents** conservés sur 2 411 (91 %). L'essentiel des retraits (200 lignes) vient des réponses tronquées ou trop courtes, qui donneraient des preuves RAG coupées. Les 389 réponses à blocs `<think>` sont nettoyées. Médiane : ~400 mots par réponse, ~19 par question ; le RAG doit donc découper les réponses (Notebook 4A).

<!-- résumé 687011e3557a · Notebook1_Preprocessing_NER_Graph -->
## 6. Prétraitement NLP (spaCy)

- Termes techniques (`C++`, `AES-256`, `HTTP/2`, `Node.js`…) masqués avant spaCy puis restaurés : ni découpés ni lemmatisés.
- Deux versions, traitées à l'identique pour questions et réponses : `*_clean` (lemmes) et `*_analysis` (lemmes sans mots vides).
- `user_topic` (pour le LDA et le NPMI) retire en plus les mots de consigne très fréquents et propres aux questions.

<!-- résumé 66bd7ca42a82 · Notebook1_Preprocessing_NER_Graph -->
## 8. Modélisation de thèmes (LDA)

LDA sur les questions (`user_analysis`), avec un corpus aligné ligne à ligne sur le DataFrame.

<!-- résumé bb016fdb02b6 · Notebook1_Preprocessing_NER_Graph -->
> **Choix de k** : le k qui maximise la cohérence C_V (modifiable via `K_OVERRIDE`, section 1).

<!-- résumé 67659403226d · Notebook1_Preprocessing_NER_Graph -->
> **Interprétation.** Cohérence C_V **faible** (0,21 → 0,29, encore croissante à k = 12) : les thèmes sont portés par des verbes de consigne. Ce sont des **pseudo-labels bruités**, utiles à l'exploration et au Notebook 2B, pas des catégories métier. T10 (vulnérabilités applicatives) domine (~27 % des requêtes).

<!-- résumé bbdde42ff4b8 · Notebook1_Preprocessing_NER_Graph -->
## 9. Co-occurrences : NPMI et communautés de Louvain

NPMI(a, b) = PMI(a, b) / −log₂ P(a, b), dans [−1, 1]. Les paires non observées ou trop rares (< `NPMI_MIN_COOC`) valent `NaN`, et non 0 (qui signifierait « indépendants »).

<!-- résumé d18d8084ead6 · Notebook1_Preprocessing_NER_Graph -->
> **Interprétation.** 130 mots, 137 arêtes, 21 communautés : le graphe retrouve des **expressions techniques stables** (*privilege escalation*, NPMI 0,54 ; *dll hijacking* ; *c2 communication* ; *rop gadget*), mêlées à des tournures de consigne (*provide example*), comme le LDA.

<!-- résumé 7de628a2e4d1 · Notebook1_Preprocessing_NER_Graph -->
## 10. Embeddings

- **Sentence-Transformers** : un vecteur par question (texte brut) → projection 2D, clustering comparé au LDA, recherche sémantique.
- **Word2Vec** : un vecteur par mot (textes lemmatisés) → comparé aux communautés NPMI.

<!-- résumé 71d53a6a530d · Notebook1_Preprocessing_NER_Graph -->
> **Interprétation.** Les clusters SBERT recoupent peu le LDA (ARI 0,09) et se séparent mal (silhouette 0,03) : le corpus est un **continuum** de sujets. Les voisins Word2Vec sont pertinents (*vulnerability* → *flaw* ; *encryption* → *aes-256-gcm*), et ~48 % tombent dans la même communauté NPMI. Sur « detect ransomware », les embeddings trouvent des questions pertinentes, TF-IDF non.

<!-- résumé 1d3145651f86 · Notebook1_Preprocessing_NER_Graph -->
## 11. Vectorisation : TF-IDF vs Word2Vec vs GloVe vs SBERT

Même protocole pour les quatre représentations, sur deux tâches mesurées :

| Tâche | Protocole | Métriques |
| --- | --- | --- |
| A. Recherche (préfigure le RAG) | chaque question doit retrouver sa propre réponse | Recall@1, Recall@10, MRR@10 |
| B. Catégorisation (préfigure le tri SOC) | régression logistique, catégories du Notebook 2A, mots-clés masqués, CV à 5 plis | macro-F1 |

TF-IDF : creuse (uni + bigrammes) · Word2Vec : dense, entraîné sur le corpus · GloVe : dense, pré-entraîné sur Wikipedia · SBERT : contextuel (`all-MiniLM-L6-v2`).

<!-- résumé a19353535d1c · Notebook1_Preprocessing_NER_Graph -->
> **Interprétation.** **TF-IDF gagne les deux tâches** (Recall@1 0,77 ; macro-F1 0,56) : questions et réponses partagent des termes techniques rares. SBERT suit en recherche (0,71) mais perd en catégorisation (0,49). Word2Vec (corpus) bat GloVe (Wikipedia) : 0,50 vs 0,16 en Recall@1. **Décision** : TF-IDF pour les baselines « texte seul » ; encodeur **multilingue E5** pour le RAG (Notebook 4A), car les analystes posent leurs questions en français sur un corpus anglais.

<!-- résumé e6700c17ab9a · Notebook1_Preprocessing_NER_Graph -->
## 12. NER cyber : IP, CVE, malwares, logiciels, cibles

### 12.1 Extracteur à règles aligné sur STIX 2.1

`CyberNER` combine des **regex validées** (IPv4, CVE, ATT&CK `T####`, empreintes MD5 / SHA) et des **lexiques** (malwares, outils, acteurs, logiciels, vecteurs, secteurs), avec des alias français (« rançongiciel » → *ransomware*). En cas de chevauchement, le span le plus long gagne.

| Label | STIX 2.1 | | Label | STIX 2.1 |
| --- | --- | --- | --- | --- |
| `IP` | ipv4-addr / indicator | | `MALWARE` | malware |
| `CVE` | vulnerability | | `TOOL` | tool |
| `ATTACK_ID` | attack-pattern (ATT&CK) | | `THREAT_ACTOR` | threat-actor |
| `HASH` | file hashes / indicator | | `SOFTWARE` | software |
| `VECTOR` | attack-pattern (nommé) | | `TARGET` | identity (secteur) |

<!-- résumé 34de4782b53b · Notebook1_Preprocessing_NER_Graph -->
### 12.2 Fine-tuning de SecBERT (classification de tokens)

Un lexique ne reconnaît que ce qu'il contient : on fine-tune **SecBERT** (BERT pré-entraîné sur des textes cyber) en étiquetage **BIO**, avec les étiquettes *silver* de l'extracteur à règles.

**Anti-circularité** : 20 % des termes du lexique sont retirés de l'entraînement (leurs phrases sont exclues du train et de la validation). Au test :

- **F1 par entité** (span et label exacts) contre les étiquettes silver ;
- **rappel sur entités inconnues** : mentions des termes retirés retrouvées (règles : **0 %** par construction).

Découpage 70 / 15 / 15 **par document**.

<!-- résumé 3e245c0e7023 · Notebook1_Preprocessing_NER_Graph -->
> **Interprétation.** SecBERT reproduit les règles (**micro-F1 0,91** ; précision 0,92, rappel 0,90 ; macro-F1 0,76) et retrouve **32 % des entités jamais vues** (210 mentions de 37 termes retirés, contre 0 % pour les règles) : il **généralise**. Les labels fréquents sont bien appris (SOFTWARE 0,95, VECTOR 0,90, CVE 0,87) ; les labels rares échouent (THREAT_ACTOR jamais prédit ; IP : 4 mentions au test, score non significatif). Entraînement **reproductible** (graine + noyaux CUDA déterministes). **Décision** : le graphe et le MVP gardent l'extracteur à règles (déterministe, explicable) ; SecBERT (`artifacts/notebook1/ner_secbert`) sert à enrichir les lexiques. Une annotation manuelle reste nécessaire.

<!-- résumé 41ba25238d34 · Notebook1_Preprocessing_NER_Graph -->
## 13. Ontologie STIX 2.1 / MITRE ATT&CK et graphe de connaissances

```
(Document)-[:MENTIONS]->(Indicator | Vulnerability | AttackPattern | Malware | Tool | ThreatActor | Software | Target)
(ThreatActor)-[:USES]->(Malware | Tool | AttackPattern)       (Malware)-[:USES]->(AttackPattern)
(ThreatActor | Malware | AttackPattern)-[:TARGETS]->(Target)   (AttackPattern)-[:TARGETS]->(Software)
(Malware)-[:EXPLOITS]->(Vulnerability)                         (Vulnerability)-[:AFFECTS]->(Software)
(Indicator)-[:INDICATES]->(Malware | ThreatActor)
```

- `MENTIONS` est **factuel** : l'entité apparaît dans le document (`doc_id`).
- Les relations typées sont des **candidates** (co-occurrence dans une même phrase), avec `method`, `weight` et `doc_ids` comme preuves.
- Chaque arête a une **provenance** (`source`), exploitée par l'audit d'empoisonnement (Notebook 4B).

<!-- résumé 7e0cb7270d19 · Notebook1_Preprocessing_NER_Graph -->
> **Interprétation.** **2 573 nœuds** (2 194 documents, 379 entités) et **5 277 arêtes** : 4 926 `MENTIONS` et 351 relations candidates (258 `TARGETS`, 55 `AFFECTS`, 38 `USES`). Les plus soutenues sont plausibles (*privilege escalation → windows*, 28 documents ; *golden ticket → kerberos* ; *xss → http*). Les **hubs** (*windows* : 458 documents, *http* : 365) relient des documents sans rapport : le RAG les neutralise et le Notebook 2B les filtre. Le graphe répond à des questions relationnelles que le plein texte traite mal (malwares du secteur bancaire, techniques de WannaCry).

<!-- résumé 1d3ee553a68d · Notebook1_Preprocessing_NER_Graph -->
## 14. Ingestion Neo4j et requêtes analyste

1. **Script** `data/processed/neo4j/import.cypher` : contraintes d'unicité puis lots `UNWIND … MERGE`, **idempotent** (`cypher-shell -u neo4j -p <mot de passe> -f data/processed/neo4j/import.cypher`).
2. **Python** `neo4j_loader.load_into_neo4j` : requêtes **paramétrées** (aucune valeur concaténée), activé si les variables `NEO4J_*` sont définies.

Sans serveur, les requêtes SOC (`queries.cypher`) s'exécutent sur le graphe en mémoire (`InMemoryGraph`).

<!-- résumé 4243cff344be · Notebook1_Preprocessing_NER_Graph -->
## 16. Conclusion

- **Données** : 2 194 documents traçables (`doc_id`), dataset figé et vérifié (SHA-256).
- **Représentations** : TF-IDF est la meilleure baseline ; un encodeur multilingue est retenu pour le RAG.
- **NER** : règles STIX 2.1 (10 types, alias français, pluriels) + SecBERT reproductible (micro-F1 0,91 ; 32 % sur entités inconnues).
- **Graphe** : STIX 2.1 / ATT&CK avec provenance, import Neo4j idempotent, requêtes analyste.
- **Limites** : corpus pédagogique (peu d'IOC réels), LDA générique, relations non validées, NER sans annotation manuelle.
- **Pistes** : annoter 100 – 200 phrases ; ajouter un corpus CTI narratif (rapports, ATT&CK STIX).

<!-- résumé 2a75cc1b48c7 · Notebook2_PartA_GNN_PyG -->
# 📘 Notebook 2A — GNN & PyTorch Geometric (GCN / GAT)

**Responsable :** Emna Trabelsi · **Chapitre 2** (Transformers pour texte et graphe) · **TDSP 3** (Modeling)

- **Objectif métier (OM4)** : relier menaces, vecteurs et cibles pour passer de la réaction à l'anticipation.
- **Objectif data science (DS4)** : classer les incidents avec un GNN ; mesure clé = **macro-F1 du GNN vs texte seul**.
- **Démarche** : message passing → graphes d'incidents (similarité + entités) → objet PyG → MLP / GCN / GAT → analyses (homophilie, sur-lissage, attention).
- **Interfaces** : données du Notebook 1 (Walid Fehry), passation au Notebook 2B (Hejer Mnejja).

<!-- résumé 2373772d0c13 · Notebook2_PartA_GNN_PyG -->
---
## ⚙️ 1) Initialisation
Environnement du dépôt (`pip install -e ".[dev]"`), GPU si disponible (CPU possible). Données : corpus nettoyé du Notebook 1 (`data/processed/corpus_clean.parquet`).

<!-- résumé 27081a262cb4 · Notebook2_PartA_GNN_PyG -->
---
# 2) Quiz & formules — GCN et GAT
Un GNN applique aux graphes l'idée de l'attention du Chapitre 2 : décider **quels voisins écouter**.

### ✅ Quiz
Renseigner `answers_student` (`'A'`, `'B'` ou `'C'`), puis exécuter la correction.

<!-- résumé 2aa389d29ca5 · Notebook2_PartA_GNN_PyG -->
### 🔎 Formules clés

**GCN** : moyenne normalisée des voisins, avec des poids **fixes** (fonction des degrés) :
$$H^{(l+1)} = \sigma\!\left(\hat D^{-1/2}\,\hat A\,\hat D^{-1/2}\,H^{(l)}\,W^{(l)}\right),\qquad \hat A = A + I$$

**GAT** : poids de voisinage **appris par attention** (multi-têtes, comme le Transformer, mais limitée aux voisins) :
$$e_{ij}=\text{LeakyReLU}\big(a^\top[Wh_i \,\Vert\, Wh_j]\big),\qquad \alpha_{ij}=\underset{j\in\mathcal N(i)}{\text{softmax}}(e_{ij}),\qquad h_i' = \sigma\Big(\sum_{j\in\mathcal N(i)}\alpha_{ij}\,Wh_j\Big)$$

> 💡 GCN : « je fais la moyenne de l'avis de mes voisins ». GAT : « je choisis à quels voisins faire confiance ».

<!-- résumé 5e01f90cf8ee · Notebook2_PartA_GNN_PyG -->
---
# 4) Boîte à outils : modèles & entraînement
Définis une fois, réutilisés sur Cora puis sur le graphe cyber : `MLP` (sans graphe, référence), `GCN`, `GAT` (multi-têtes, attention lisible) et `train_eval` (early stopping sur le **macro-F1 de validation**, jamais sur le test).

<!-- résumé 5208132111fb · Notebook2_PartA_GNN_PyG -->
---
# 5) Échauffement sur **Cora** (MLP vs GCN vs GAT)
2 708 articles reliés par citations, 7 classes : la boîte à outils est validée sur le « Hello World » des GNN.

<!-- résumé d38491c189b3 · Notebook2_PartA_GNN_PyG -->
> 💡 Le MLP ne voit que les features ; GCN et GAT voient aussi les **voisins**. Hypothèse testée ensuite sur le cyber : *les incidents voisins aident-ils à classer un incident ?*

<!-- résumé e9b8ddad14c3 · Notebook2_PartA_GNN_PyG -->
---
# 6) Données cyber
Corpus `AlicanKiraz0/Cybersecurity-Dataset-v1`, **nettoyé une seule fois par le Notebook 1** (identifiant `doc_id`).

> ⚠️ Le dataset **n'a pas de catégorie d'incident** : les labels sont fabriqués en section 7 (ou lus dans une colonne `label` si l'équipe en fournit une).

<!-- résumé 99f48983ae2a · Notebook2_PartA_GNN_PyG -->
### Prétraitement
Minuscules, ponctuation, tokenisation et mots vides retirés pour **TF-IDF** ; texte naturel conservé pour **SBERT** (un Transformer a besoin de la phrase entière).

<!-- résumé fb34a91f6002 · Notebook2_PartA_GNN_PyG -->
---
# 7) Étiquettes (supervision faible) + split
Catégorie = règle de mots-clés la plus fréquente dans la question. Deux garde-fous :

1. **Anti-fuite (`LEAK_GUARD`)** : les mots-clés des règles sont masqués dans le texte vu par le modèle (sinon il « relit » la règle).
2. **Graphe indépendant des règles** : aucune entité du graphe n'est un mot-clé de label (vérifié par un test automatique).

<!-- résumé 19ecb8d96f53 · Notebook2_PartA_GNN_PyG -->
Règles définies une seule fois dans `cybersec_nlp.nlp.classifier`, partagées avec le pipeline et le MVP.

<!-- résumé fdbcef20a10d · Notebook2_PartA_GNN_PyG -->
---
# 8) Features & baselines **texte seul**
- **TF-IDF (+ SVD)** : baseline statistique ;
- **SBERT** (`all-MiniLM-L6-v2`) : features des nœuds et graphe kNN.

Ces baselines fixent le score à battre (DS4).

<!-- résumé 531f89af8a54 · Notebook2_PartA_GNN_PyG -->
---
# 9) Construction des graphes
Nœuds = incidents. Comparer plusieurs graphes mesure **l'impact de la qualité du graphe** sur le macro-F1 :

| Graphe | Arêtes |
|---|---|
| **A. kNN sémantique** | les k plus proches voisins (cosinus SBERT) |
| **B. Entités partagées** | incidents qui partagent une entité (lexique de ce notebook) |
| **C. Hybride** | A ∪ B |
| **D. NER du Notebook 1** | incidents qui partagent une entité du NER de Walid Fehry (section 13) |

> 💡 **Homophilie** = % d'arêtes entre incidents de même classe : plus elle est haute, plus un GNN peut aider.

<!-- résumé 8bb7bf66032e · Notebook2_PartA_GNN_PyG -->
---
# 10) Objet PyTorch Geometric & entraînement
`Data(x, edge_index, y)` : `x` = SBERT `[N, 384]`, `edge_index` = arêtes `[2, E]`, `y` = labels, plus les masques train / val / test. Cadre **transductif** : tout le graphe est visible, seuls les labels du train entrent dans la perte. Déséquilibre : poids de classes + macro-F1.

<!-- résumé ed7412b7b8d0 · Notebook2_PartA_GNN_PyG -->
> 🗣️ Un gain faible ou négatif n'est pas un échec : il s'explique par l'**homophilie** (section 9). Le modèle est choisi sur la **validation**, jamais sur le test.

<!-- résumé dd2a689eefd7 · Notebook2_PartA_GNN_PyG -->
---
# 12) Analyses pour la soutenance
### 12.1 Sur-lissage : combien de couches ?
Plus on empile de couches GCN, plus les représentations se ressemblent ; on le vérifie sur le graphe hybride.

<!-- résumé 94d9cd67ef58 · Notebook2_PartA_GNN_PyG -->
### 12.2 Interpréter GAT
Les poids d'attention $\alpha_{ij}$ montrent quels voisins comptent : un atout de **traçabilité** (DS4).

<!-- résumé dbf7be65a059 · Notebook2_PartA_GNN_PyG -->
### 12.3 t-SNE des embeddings
Features SBERT brutes vs embeddings appris par GAT : les classes doivent mieux se séparer après message passing.

<!-- résumé d9ef4e4e1c1a · Notebook2_PartA_GNN_PyG -->
---
# 13) Intégration du NER de Walid Fehry (graphe D)
Le graphe D vient de `entities.json` (Notebook 1), avec le même `doc_id`, la même projection et le même anti-fuite que le graphe B. Comparer B et D mesure l'apport d'un NER plus complet sur l'homophilie et le macro-F1.

<!-- résumé b456d7fe769e · Notebook2_PartA_GNN_PyG -->
---
# 14) Export & passation à Hejer Mnejja (Notebook 2B)
Le graphe PyG et les embeddings sont exportés : la conversion texte → graphe n'est pas à refaire.

<!-- résumé 240c88c87bdd · Notebook2_PartA_GNN_PyG -->
---
## ✅ 15) Auto-vérifications
Contrôles rapides que chaque section a été exécutée correctement.

<!-- résumé f6286006cd5e · Notebook2_PartA_GNN_PyG -->
---
## 🎯 Check-list soutenance
- **Problème** : classer les incidents en s'appuyant sur la **structure** (OM4 / DS4).
- **Pipeline** : texte → SBERT → graphe (kNN / entités / hybride / NER) → `Data` PyG → GCN / GAT.
- **Résultat clé** : texte seul vs GNN (macro-F1 moyen ± écart-type sur 3 graines, choix sur la validation).
- **Concepts** : message passing, GCN vs GAT, sur-lissage, transductif, homophilie, anti-fuite.
- **Limite** : labels issus de règles de mots-clés (supervision faible).
- **Passation** : `incident_graph_hybrid.pt` + embeddings → Notebook 2B.

<!-- résumé b8e851461a5d · Notebook2_PartA_GNN_PyG -->
---
## 📊 16) Métriques exportées
`reports/metrics/notebook2a_metrics.json`, lu par la synthèse et la page *Pilotage* de Vigie.

<!-- résumé 926c75d8d9a9 · Notebook2_PartB_GTN_Leiden -->
# Notebook 2B — Graph Transformers (HGT) & clustering Hierarchical Leiden

**Responsable :** Hejer Mnejja · **Chapitre 2** (Transformers & GTN) · **TDSP 3** (Modeling / *Threat Mapping*)

**Objectifs** : graphe hétérogène Document / Entité traçable → classification par **HGT** comparée au texte seul → clusters **Hierarchical Leiden** → cartographie menaces → vecteurs → cibles (PyVis).

**Entrées** (Notebook 1, Walid Fehry) : corpus nettoyé, thèmes LDA et entités du NER, joints par le même identifiant.

**Limites assumées** : corpus pédagogique (clusters = groupes thématiques, pas des campagnes) ; entités non validées ; labels = **pseudo-labels LDA** (tirés des questions, alors que les features viennent des réponses, pour limiter la circularité) ; cadre transductif.

<!-- résumé 81723d5a8737 · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** Corpus du Notebook 1 réutilisé tel quel : **2 194 documents**. `corpus_id` (HF-xxxxx) joint thèmes et entités, `doc_id` indexe les nœuds du graphe.

<!-- résumé be5adea48332 · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** Pseudo-labels = **12 thèmes LDA** du Notebook 1, déséquilibrés (583 documents pour T10, 56 pour T3) : prédire la classe majoritaire donne ~27 % d'accuracy et ~0,04 de macro-F1. Thèmes génériques ⇒ score atteignable limité.

<!-- résumé b66b65ffbdbf · Notebook2_PartB_GTN_Leiden -->
## 3. Entités du NER (Notebook 1)
Entités de `entities.json` (NER de Walid Fehry, STIX 2.1), regroupées en familles : **VECTEUR**, **MALWARE**, **OUTIL**, **SOFTWARE**, **CIBLE**, **ACTEUR**, **CVE**, **IP**.

<!-- résumé c38c1c3e834c · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** **198 entités** retenues sur 379 (présentes dans au moins 2 documents et au plus 30 % du corpus). Le graphe couvre **82 % des documents** avec 4 745 arêtes `MENTIONNE` (~2,2 entités par document), bien plus que le lexique initial.

<!-- résumé 2bf0cf85586f · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** Split 1 535 / 329 / 330, sans question partagée entre entraînement et test. Les 7 854 arêtes `SIMILAIRE_A` donnent ~7 voisins par document.

<!-- résumé 4c7184fcf38e · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** 2 types de nœuds (2 194 documents, 198 entités) et 3 types d'arêtes. Les entités fréquentes sont des **hubs** (*windows* : 458 documents, *http* : 365).

<!-- résumé 0932a8514280 · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** Baseline texte : **macro-F1 0,317** (accuracy 0,364), loin au-dessus du hasard (~0,04). C'est la référence à battre.

<!-- résumé b7f3a92dddc1 · Notebook2_PartB_GTN_Leiden -->
## 7. Graph Transformer hétérogène (HGT)
`HGTConv` : attention multi-têtes qui dépend du **type de nœud et d'arête** (le GTN original de Yun et al. n'existe pas dans PyG). Ablation : entités seules vs entités + similarité.

<!-- résumé 8fcc7cb0928b · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** HGT reste **sous la baseline** : 0,147 (entités seules) et 0,213 (+ similarité) contre 0,317. La conclusion se tire en 7b (5 découpages).

<!-- résumé 8a0264c1e2ca · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** La perte baisse mais le macro-F1 de validation plafonne (~0,21) : le modèle **sur-apprend** la structure. T10 est prédit avec une bonne précision (0,73) mais un faible rappel ; T7 n'est jamais reconnu (thèmes LDA voisins qui se recouvrent).

<!-- résumé 9b347085820c · Notebook2_PartB_GTN_Leiden -->
## 7b. Robustesse : 5 découpages
Un seul run sur ~360 documents de test est fragile : chaque graine change le split et l'initialisation, et l'on rapporte moyenne ± écart-type.

<!-- résumé 6d15de196939 · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** Baseline **0,322 ± 0,023** vs HGT **0,183 ± 0,015** (entités + similarité) et 0,158 ± 0,011 (entités seules). L'écart (~0,14) vaut six fois la variabilité : **le graphe n'apporte pas de gain** sur ces pseudo-labels, comme dans le Notebook 2A. La catégorie d'un document dépend de son texte, pas de ses voisins.

<!-- résumé 473bd815adda · Notebook2_PartB_GTN_Leiden -->
## 7c. Influence des entités (occlusion)
`HGTConv` n'expose pas ses poids d'attention : on **retire une entité** du graphe et on mesure la variation des prédictions (de 0 à 1) sur les documents qui la mentionnent (effet direct) et sur les autres (effet **non local**).

<!-- résumé 3a18ff80c050 · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** Effet **direct** de 0,06 à 0,36, effet **non local** ≤ 0,04. Les entités les plus influentes sont des hubs génériques (*http* : 212 prédictions changées, *privilege escalation*, *windows*, *tls*) : le modèle reste local et s'appuie sur des entités peu discriminantes.

<!-- résumé 6d4eb704c9d6 · Notebook2_PartB_GTN_Leiden -->
## 8. Clustering Hierarchical Leiden
Poids document–document = cosinus + `ALPHA_ENT` × nombre d'entités partagées (plafonné à 3).

<!-- résumé 38656feef471 · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** Graphe très dense (2 193 nœuds, 270 264 arêtes, ~246 voisins par nœud), surtout à cause des entités fréquentes ; abaisser `ENT_MAX_FRAC` (ex. 0,10) réduirait l'effet des hubs.

<!-- résumé 9c2af75575ae · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** Leiden récursif (igraph, `graspologic` n'étant pas installé) : **7 clusters au niveau 0** (grandes familles) et **149 clusters finaux** (≤ 40 documents) sur 4 niveaux.

<!-- résumé 1f5268158cea · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** **Modularité 0,44** : structure en communautés nette (au-dessus du seuil usuel de 0,3). NMI de 0,23 avec les thèmes LDA : les clusters regroupent par sujet fin et entités partagées, pas par thème générique. La pureté (0,46) est gonflée par les nombreux petits clusters.

<!-- résumé 10fb7a211761 · Notebook2_PartB_GTN_Leiden -->
> **Interprétation.** Clusters **lisibles et cohérents** : firmware / UEFI, JWT / OAuth, DLL hijacking, botnets IoT (*mirai*), C2 via DNS, SSRF, CSRF, élévation de privilèges, LFI / PHP, chacun avec ses vecteurs, outils et secteurs. **C'est le résultat le plus solide de cette partie** et la base du *threat mapping*. Bruit résiduel (*exchange* compte aussi les « key exchange ») : ce sont des groupes thématiques, pas des campagnes d'attaque.

<!-- résumé a977411d14c6 · Notebook2_PartB_GTN_Leiden -->
## 10. Visualisation interactive (PyVis)
Documents colorés par cluster (niveau 0), entités en losanges colorés par type ; arêtes `MENTIONNE` (gris) et `SIMILAIRE_A` (orange, épaisseur = score). Limité aux `MAX_DOCS` documents les plus connectés.

<!-- résumé 6acdcf5cfad3 · Notebook2_PartB_GTN_Leiden -->
> **Lecture.** Une même couleur doit former un groupe compact ; les entités fréquentes servent de ponts entre clusters ; les arêtes orange renforcent la cohésion interne, les grises relient les clusters.

<!-- résumé 0f373dfe6226 · Notebook2_PartB_GTN_Leiden -->
## 11. Exports pour l'équipe
- `artifacts/notebook2b/doc_clusters.csv` : identifiants, clusters (niveau 0 et final), thème, prédiction HGT ;
- `artifacts/notebook2b/hgt_doc_embeddings.npy` : embeddings de documents (réutilisables par le Notebook 4A d'Ines Trabelsi) ;
- `artifacts/notebook2b/cluster_table.csv` et `reports/metrics/notebook2b_metrics.json` (synthèse et MVP).

<!-- résumé a65f656444fc · Notebook2_PartB_GTN_Leiden -->
## 12. Conclusion

- **Classification** : baseline 0,322 ± 0,023 vs HGT 0,183 ± 0,015 sur 5 graines : **pas de gain du graphe**, conclusion identique au Notebook 2A.
- **Relations non locales** : effet surtout local (≤ 0,04 hors des documents concernés) ; l'occlusion mesure l'influence des entités, pas l'attention de HGT.
- **Clustering** : modularité 0,44, 7 familles, 149 groupes fins ; cartographie thématique exploitable.
- **Limites** : pseudo-labels génériques, entités non validées, corpus pédagogique, cadre transductif.
- **Pistes** : labels métier, relations validées (CVE → logiciel), filtrage des hubs, `graspologic`.

<!-- résumé f78d0c79c573 · Notebook3_LLM_FineTuning_Evaluation -->
# 🛡️ Notebook 3 — LLMs, prompt engineering, PEFT / LoRA & évaluation

**Responsable :** Khaled Gannoun · **Chapitre 3** (Large Language Models) · **TDSP 3** (Modeling, Model Tuning & Evaluation)

1. **Configuration** : **Qwen2.5-1.5B-Instruct** en local (aucune donnée ne sort de la machine) ; effet **mesuré** de la température et du *top-p*.
2. **Prompt engineering** : zero-shot, few-shot, Chain-of-Thought et Self-Consistency sur une tâche SOC évaluable.
3. **PEFT / LoRA** : fine-tuning réel sur le corpus CTI, dans 8 Go de GPU.
4. **Évaluation** base vs LoRA sur des questions **jamais vues** : ROUGE, BERTScore, FactCC, LLM-as-a-Judge.
5. **Garde-fou** anti-injection de prompt (OWASP LLM01), évalué.

> Tous les chiffres sont calculés par les cellules (graine `SEED`). Durée : ~25 min sur une RTX 4060.

<!-- résumé 1483fcd8e24e · Notebook3_LLM_FineTuning_Evaluation -->
### Effet mesuré de la température et du *top-p*
5 réponses au même prompt avec deux réglages ; diversité mesurée par *distinct-2* et par le ROUGE-L entre réponses (élevé = réponses redondantes).

<!-- résumé da60b0801a68 · Notebook3_LLM_FineTuning_Evaluation -->
> **Interprétation.** À T = 0,2 / top-p 0,9, les réponses sont bien plus stables (ROUGE-L entre réponses 0,39 vs 0,21 ; distinct-2 0,74 vs 0,91) qu'à T = 1,0 / top-p 1,0. Un SOC veut la même recommandation pour la même question : **température basse** (le MVP utilise même un décodage glouton suivi du contrôle de fidélité).

<!-- résumé 444d9672ad4f · Notebook3_LLM_FineTuning_Evaluation -->
## 💡 Étape 2 : Prompt engineering mesuré
**Tâche** : classer une question d'analyste dans l'une des 8 catégories SOC (règles du Notebook 2A) ; test stratifié de 8 questions par catégorie, jamais utilisées comme exemples.

| Stratégie | Principe |
| --- | --- |
| Zero-shot | catégories + question |
| Few-shot | + un exemple résolu par catégorie |
| Chain-of-Thought | court raisonnement puis `Category: …` |
| Self-Consistency | 5 raisonnements (T = 0,7), vote majoritaire |

Métriques : accuracy, macro-F1, réponses non interprétables, latence.

<!-- résumé 5ccdf1d9f18b · Notebook3_LLM_FineTuning_Evaluation -->
> **Interprétation.** Sur 64 questions, le zero-shot est faible (macro-F1 0,18) ; **un exemple par catégorie** presque double le score (0,34). Le CoT seul aide moins (0,29) : un modèle de 1,5 B se perd dans son raisonnement (16 % de conclusions non interprétables). La **Self-Consistency** est la meilleure (macro-F1 **0,36**, accuracy 0,39, accord des votes 61 %), mais ~5 fois plus lente que le CoT (1,1 s par question). Les catégories étant des pseudo-labels, ces scores mesurent surtout le respect de la consigne.

<!-- résumé 9fe011cf8ec6 · Notebook3_LLM_FineTuning_Evaluation -->
### Chain-of-Thought sur un incident (démonstration qualitative)
Cadre imposé **entités → impact → recommandation** : extraire d'abord les entités rend le raisonnement vérifiable par l'analyste.

<!-- résumé 413108b8d980 · Notebook3_LLM_FineTuning_Evaluation -->
## 📦 Étape 3 : Fine-tuning PEFT / LoRA

### 3.1 Dataset d'instructions
Paires question → réponse du **corpus réel**, au format conversationnel de Qwen ; découpage **par document** (questions de test jamais vues à l'entraînement).

<!-- résumé 4217f2e0976d · Notebook3_LLM_FineTuning_Evaluation -->
### 3.2 Configuration LoRA et entraînement
`r = 16`, `lora_alpha = 32`, projections **Query** et **Value**, dropout 0,05. Le modèle de base est **gelé** (bf16) : seules les matrices de bas rang sont entraînées, ce qui tient dans 8 Go de GPU.

<!-- résumé 137461e154fd · Notebook3_LLM_FineTuning_Evaluation -->
> **Interprétation.** **2,2 M de paramètres entraînés** (0,14 % du modèle) : 800 exemples, 1 époque, **2,4 min**, 4,6 Go de GPU au maximum. La perte baisse régulièrement (moyenne 1,85) : l'adaptateur apprend le style et le vocabulaire CTI. Entraînement **déterministe** : résultats identiques à chaque exécution.

<!-- résumé 7bc7466e7d1b · Notebook3_LLM_FineTuning_Evaluation -->
## 📊 Étape 4 : Évaluation — modèle de base vs LoRA
Mêmes prompts, décodage glouton, **40 questions de test**.

| Métrique | Mesure |
| --- | --- |
| ROUGE-1 / 2 / L | recouvrement lexical avec la réponse de référence |
| BERTScore F1 | similarité sémantique (embeddings RoBERTa) |
| FactCC | cohérence factuelle (part de phrases jugées *CORRECT*) |

<!-- résumé 716e7e472e70 · Notebook3_LLM_FineTuning_Evaluation -->
> **Interprétation.** LoRA progresse en **recouvrement** (ROUGE-1 0,325 → 0,366 ; BERTScore 0,825 → 0,840 ; réponses de 182 → 216 mots) mais **FactCC baisse** (0,65 → 0,60) : plus de texte, plus d'affirmations non vérifiables. Bilan **mitigé** : 1 époque sur 800 exemples adapte le style, pas la connaissance. FactCC, entraîné sur des articles d'actualité, est hors de son domaine : c'est un indicateur.

<!-- résumé 020c0704339b · Notebook3_LLM_FineTuning_Evaluation -->
### LLM-as-a-Judge
Le modèle note **fidélité** et **pertinence** (0 – 5). Vérification préalable sur un **cas piège** (réponse fausse : *brute force SSH* au lieu d'*injection SQL*), puis 10 réponses par modèle.

<!-- résumé 549f5e3098fe · Notebook3_LLM_FineTuning_Evaluation -->
> **Interprétation.** Le juge donne **3/5 en fidélité à une réponse fausse** : un juge de 1,5 B n'est **pas fiable**. Ses notes (base 4,8 / 4,2 ; LoRA 4,4 / 3,6) restent indicatives ; la décision repose sur les métriques automatiques et sur le contrôle de fidélité du Notebook 4A.

<!-- résumé 9ef3c5c86477 · Notebook3_LLM_FineTuning_Evaluation -->
## 🛡️ Étape 5 : Garde-fou anti-injection de prompt (OWASP LLM01)
Les motifs sont intégrés au garde-fou partagé `cybersec_nlp.llm.guardrails` (aussi utilisé par le MVP), puis évalués sur des requêtes légitimes et malveillantes.

<!-- résumé 6ee110b211b5 · Notebook3_LLM_FineTuning_Evaluation -->
> **Interprétation.** **10/10 attaques bloquées, 0/10 requête légitime bloquée** (dont « Explain the previous incident's root cause »). Le jeu est petit et écrit par l'équipe : score optimiste. « jailbreak » seul n'est plus bloqué (*iOS jailbreak* est un sujet légitime). C'est une première ligne de défense, complétée par la lecture seule, l'abstention et le contrôle de fidélité.

<!-- résumé bb4ed13c4b2b · Notebook3_LLM_FineTuning_Evaluation -->
**Bilan**

| Pilier | Résultat |
| --- | --- |
| Inférence locale | Qwen2.5-1.5B-Instruct (fp16, GPU) ; aucune donnée ne quitte la machine |
| Génération | température basse = réponses stables (ROUGE-L 0,39 vs 0,21) |
| Prompting | Self-Consistency > Few-shot > CoT > Zero-shot (macro-F1 0,36 / 0,34 / 0,29 / 0,18) |
| LoRA | 0,14 % des paramètres, 2,4 min ; BERTScore 0,825 → 0,840, FactCC 0,65 → 0,60 |
| Évaluation | 40 questions jamais vues ; juge LLM non fiable |
| Sécurité | 10/10 attaques bloquées, 0/10 faux positif |

Adaptateur : `artifacts/notebook3/lora_qwen_cti` (chargé par `LocalLLM(adapter_path=…)`). **Pistes** : plusieurs époques avec validation, sélection des exemples par qualité, juge plus robuste ou annotation humaine.

<!-- résumé 7890c8ddcd74 · Notebook4_PartA_HybridRAG_Pipeline -->
# Notebook 4A — HybridRAG pour un SOC

**Responsable :** Ines Trabelsi · **TDSP 4** (Operationalization)

| Besoin SOC | Réponse technique | Vérification |
|---|---|---|
| Retrouver vite une procédure | segments, embeddings, FAISS | Precision@k, Recall@k, MRR@k |
| Relier logiciel, CVE et incidents | traversée du graphe avec provenance | questions relationnelles |
| Poser une question de suivi, avec une réponse traçable | fusion des preuves, réponse citée | démo conversationnelle, abstention |

**Question → FAISS + graphe → fusion → preuves numérotées → réponse SOC.**

Sections 1 – 6 : architecture validée sur une **démo** (incidents fictifs, sans serveur ni clé ; modes `team` et `hf` optionnels). Section 7 : **passage à l'échelle** sur le corpus réel, le graphe STIX du Notebook 1 et le LLM local du Notebook 3.

<!-- résumé 3b5d8110c282 · Notebook4_PartA_HybridRAG_Pipeline -->
## 1. Contrat de données
Le Notebook 1 fournit un **JSONL** : `doc_id`, `text`, `source` (+ `title`, la question d'origine). Le même `doc_id` sert de provenance dans le graphe. Seule la **réponse** est indexée ; le prompt système du dataset est remplacé par celui de l'application.

Exemple fictif : `{"doc_id":"INC-101","text":"Le logiciel MailGate est affecté par CVE-2099-1001.","source":"rapport-101.pdf#page=2"}`

<!-- résumé 26e812c02129 · Notebook4_PartA_HybridRAG_Pipeline -->
## 2. Chunking et index FAISS
Coupures aux frontières de phrase et de paragraphe, découpage au tokenizer de l'encodeur, léger chevauchement. `IndexFlatIP` sur vecteurs normalisés = **cosinus**. La démo utilise TF-IDF (aucun téléchargement), les modes `team` et `hf` des embeddings multilingues. Index et métadonnées sont exportés ensemble.

<!-- résumé a306a38e15d2 · Notebook4_PartA_HybridRAG_Pipeline -->
### Vérifier le découpage
Le rapport fictif INC-106 dépasse la fenêtre de l'encodeur : chaque chunk garde le `doc_id` du rapport et reçoit son identifiant de segment ; on vérifie que l'adresse IP reste lisible.

<!-- résumé c1dd18ca0dc8 · Notebook4_PartA_HybridRAG_Pipeline -->
## 3. Recherche vectorielle et recherche graphe
- **Vecteurs** : résultats regroupés par document, pour qu'un long rapport n'occupe pas tout le top-k.
- **Graphe** : **faits** structurés, chacun avec un document et un chemin ; les liens observés sont distingués des similarités calculées.

**Mode `team`** : Neo4j (variables `NEO4J_*`, compte **en lecture seule**, procédures APOC) et LLM du Notebook 3 servi par une API compatible OpenAI (variables `SOC_LLM_*`). Chaque ligne Cypher doit renvoyer `doc_id`, `fact`, `path` (+ `source`) : **une relation sans provenance ne devient jamais une preuve**.

<!-- résumé 195500967eb2 · Notebook4_PartA_HybridRAG_Pipeline -->
## 4. Fusion des preuves et réponse conversationnelle
La fusion réserve une place à chaque branche, puis alterne les résultats par rang jusqu'au budget. Le prompt système fixe le rôle, les citations et l'**abstention** ; les preuves sont transmises dans un message séparé des instructions. La mémoire de session complète les questions de suivi courtes, et les preuves sont recherchées à chaque tour. `answer_question` sert d'interface aux autres notebooks.

<!-- résumé 7485c1c415e2 · Notebook4_PartA_HybridRAG_Pipeline -->
### Cas de démonstration : CVE et contrôle après correction
Question composite : la relation **WebRelay → CVE** est dans le graphe, la consigne de vérification de version dans la procédure **SOP-03**. Les trois stratégies sont comparées sur les deux éléments attendus et sur la provenance des citations.

<!-- résumé d0aa34a254dd · Notebook4_PartA_HybridRAG_Pipeline -->
## 5. Évaluation comparative
Mêmes questions et mêmes jugements de pertinence pour les trois stratégies ; mesure **au niveau document**.

| Mesure | Calcul |
|---|---|
| Precision@k | documents pertinents dans le top-k / k |
| Recall@k | documents pertinents retrouvés / attendus |
| MRR@k | inverse du rang du premier document pertinent |
| Temps | recherche + fusion (ms), hors génération |

Ces contrôles valident le **câblage** sur un petit corpus fictif ; l'évaluation sur les données réelles est en section 7.

<!-- résumé 4ee3422cf66e · Notebook4_PartA_HybridRAG_Pipeline -->
### Détail par question et grille de fidélité
Le tableau par question montre où une branche manque un document attendu. Pour la fidélité, chaque affirmation est confrontée à la preuve citée : **étayée**, **partielle**, **contredite** ou **preuve absente**.

<!-- résumé 6a36fc9fba62 · Notebook4_PartA_HybridRAG_Pipeline -->
| Affirmation | Preuve citée (cas fictif) | Verdict |
|---|---|---|
| CVE-2099-2002 affecte WebRelay | INC-102 → CONCERNE → WebRelay ← AFFECTE ← CVE-2099-2002 | Étayée |
| Vérifier le correctif via la version installée | SOP-03, segment SOP-03#0001 | Étayée |

Sur des incidents réels, la même grille s'applique à des questions annotées indépendamment (multi-sources, suivis, sans réponse), en rapportant l'abstention et la part d'affirmations étayées.

<!-- résumé feffa38e630b · Notebook4_PartA_HybridRAG_Pipeline -->
## 6. Intégration dans le dépôt

1. ✅ Chemins résolus depuis la racine du dépôt.
2. ✅ `rag_documents.jsonl` (Notebook 1) : mêmes `doc_id` que la provenance du graphe.
3. ✅ LLM d'équipe : modèle local du Notebook 3 (Qwen2.5-1.5B-Instruct).
4. ⏳ Mode `team` (Neo4j + `GraphCypherQAChain`) : nécessite un serveur Neo4j ; la section 7 utilise le même graphe en mémoire.
5. ✅ Interface pour le Notebook 4B : `answer_question` et `HybridRAG.answer` renvoient `answer`, `evidence` et `trace`.

## 7. Passage à l'échelle : corpus réel, graphe STIX et LLM local

Architecture généralisée dans `cybersec_nlp.rag.hybrid` :

| Démo (sections 1 – 6) | Échelle réelle (section 7) |
| --- | --- |
| 9 documents fictifs | 2 194 réponses du corpus nettoyé |
| TF-IDF dense | **E5 multilingue** (questions en français, corpus en anglais) |
| graphe codé en dur | **graphe STIX 2.1** du Notebook 1 |
| restitution extractive | **Qwen2.5-1.5B local** + contrôle de fidélité phrase par phrase |
| similarité seule | **re-ranking** des 20 meilleurs candidats (cross-encodeur mMARCO) |

<!-- résumé 474bb3a1ea08 · Notebook4_PartA_HybridRAG_Pipeline -->
> **Interprétation.** La première réponse est exacte et appuyée par le **fait du graphe** (CVE-2021-44228 → log4j, [S2]). La question de suivi est complétée par la mémoire de session, et le contrôle de fidélité **retire une phrase non étayée**. La question hors sujet produit une **abstention**. Le contrôle exige désormais que l'identifiant et le produit figurent **dans la même phrase de preuve** (une version antérieure laissait passer « CVE-2021-34527 affecte log4j »).

<!-- résumé ff178b4e140f · Notebook4_PartA_HybridRAG_Pipeline -->
### 7.1 Évaluation de la recherche (corpus réel)
**Protocole known-item** : 300 questions d'origine (jamais indexées) doivent retrouver **leur propre réponse** parmi 2 194 documents. Mêmes questions pour toutes les configurations (dont une ablation du re-ranking), aucun réglage sur ce jeu. Une seule réponse étant pertinente, on rapporte **Recall@4**, **MRR@4**, nDCG@4, la couverture et la latence.

<!-- résumé 6eb46eb1071e · Notebook4_PartA_HybridRAG_Pipeline -->
> **Interprétation.** Les vecteurs seuls (E5 + FAISS) placent la bonne réponse dans le top-4 pour **83 %** des questions (MRR 0,763) ; le **re-ranking** porte ce taux à **87 %** (MRR 0,795) pour ~50 ms de plus. Le graphe seul ne vise pas ce protocole (couverture 37 %, Recall@4 0,08 : une entité comme *windows* est citée par des centaines de documents). **Hybride déployé** (vecteurs re-classés + faits du graphe, vecteurs d'abord) : **Recall@4 0,857 / MRR 0,789**. La fusion « graphe d'abord » faisait chuter le MRR à 0,63 : c'est cette mesure qui a fixé l'ordre actuel.

<!-- résumé 7104f90cb722 · Notebook4_PartA_HybridRAG_Pipeline -->
### 7.2 Abstention et qualité des réponses générées
- **Hors domaine** (12 questions) : une abstention est attendue.
- **Dans le domaine** (30 questions, stratégie hybride, LLM local) : fausses abstentions, phrases **étayées**, citations spontanées, ROUGE-L, latence.

<!-- résumé 340cfb311a7a · Notebook4_PartA_HybridRAG_Pipeline -->
> **Interprétation.** Les **12** questions hors domaine sont refusées, avec **0** fausse abstention sur 30. Après contrôle, **100 %** des phrases conservées sont rattachées à une preuve, alors que le LLM ne cite spontanément ses sources que dans **37 %** des réponses : le contrôle a posteriori est indispensable. ROUGE-L 0,17 (réponses courtes en français vs références de ~400 mots en anglais). Latence : **2,9 s** sur GPU. **Limite** : « étayée » signifie proche d'une preuve, sans identifiant inventé ou mal attribué, pas *vérifiée vraie*.

<!-- résumé 3f220a97f021 · Notebook4_PartA_HybridRAG_Pipeline -->
## 8. Conclusion

- **Architecture** validée sur la démo, puis **mesurée** sur 2 194 documents et le graphe STIX du Notebook 1.
- **Recherche** : hybride + re-ranking Recall@4 0,857 / MRR 0,789 (vecteurs seuls 0,827 / 0,763), ~60 ms.
- **Génération** : abstention hors domaine 100 %, 0 fausse abstention, phrases conservées 100 % étayées, 2,9 s.
- **Intégration** : `cybersec_nlp.rag` sert directement l'API et l'interface de **Vigie**.
- **Limites** : jeu known-item construit automatiquement, mode Neo4j non exécuté, fidélité contrôlée par similarité.
- **Pistes** : questions annotées par des analystes (dont multi-documents), Neo4j en production.

<!-- résumé 763058446c9b · Notebook4_PartB_AgenticRAG_Security_SIEM -->
# Notebook 4B — Agentic RAG (ReAct), sécurité OWASP LLM08 & export SIEM

**Responsable :** Adrian Salvador Ekomo Mesi Obono · **Chapitre 4** (RAG avancé & sécurité) · **TDSP 5** (Security Audit)

Un assistant SOC doit répondre **de façon fiable** sans devenir **un vecteur d'attaque** :

| Problème | Réponse | Code (`src/cybersec_nlp/`) |
| --- | --- | --- |
| Le LLM écrit des requêtes Cypher qui échouent | agent **ReAct** qui les répare + gabarits guidés par le schéma | `rag/agentic.py`, `rag/cypher_templates.py` |
| Le graphe peut être **empoisonné**, l'index vectoriel **fuir** ou être **inversé** | détecteurs GragPoison + contrôles OWASP **LLM08** | `security/` |
| Une réponse doit devenir une **détection durable** | règles Splunk **SPL** et Sentinel **KQL** à partir d'IOC validés | `siem/rules.py` |

**Démarche** : sections 1 – 5 sur un **graphe de démonstration contrôlé** (vérité connue, LLM simulé, reproductible) ; section 6 sur le **graphe réel** (Notebook 1) avec le **LLM local** (Notebook 3). Graphe en mémoire et **lecture seule** (aucun `CREATE/MERGE/DELETE/SET/CALL`). Sorties : `reports/siem/` et `reports/metrics/notebook4b_metrics.json`. Durée : ~5 min (GPU pour la section 6.1).

<!-- résumé f4637253edc7 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
## 1. Graphe de démonstration

Ontologie minimale inspirée de STIX 2.1 / MITRE ATT&CK :

```
(Actor)-[:USES]->(Malware)-[:BEACONS_TO]->(IPAddress | Domain)
(Malware)-[:HAS_HASH]->(FileHash)
(Incident)-[:ATTRIBUTED_TO]->(Actor)
```

Chaque arête porte sa **provenance** (`source`) : c'est elle qui distingue un fait fiable d'un fait injecté. La vérité étant connue, chaque mécanisme est vérifié ici avant d'être mesuré sur le graphe réel.

<!-- résumé 6ebf549a97d7 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
## 2. Agentic RAG — boucle ReAct d'auto-correction

**Pensée → Action → Observation** : l'action exécute la requête Cypher, l'observation est la réponse (ou l'erreur) de la base.

```
question ─► générateur Text-to-Cypher ─► Cypher ─► base de graphe
                  ▲                                     │
                  │  erreur + schéma                    ▼
                  └──────── réparation ◄───────── observation
                                                         │ succès
                                                         ▼
                                              ré-ordonnancement ─► réponse
```

- **Réparation** : l'erreur (`Unknown relationship type 'USES_MALWARE'…`) et le schéma sont renvoyés au réparateur (ici déterministe ; en production, un LLM avec le même contrat).
- **Garde-fous** : budget `max_steps`, arrêt si la réparation ne change rien, lecture seule.
- **Ré-ordonnancement** : recouvrement avec la question, bonus de provenance.

**LLM simulé** (reproductible, sans API) : étiquette inventée (`Threat_Actor`), relations mal nommées (`USES_MALWARE`, `BEACON_TO`) et deux cas **irréparables**, pour mesurer honnêtement les limites.

<!-- résumé a6e865b29ae4 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
La trace montre **deux erreurs successives** (étiquette `Threat_Actor`, puis relation `USES_MALWARE`), corrigées l'une après l'autre jusqu'à une requête valide.

### Évaluation : avec / sans agent
Les 6 questions sont posées avec **1 tentative** (RAG classique) puis avec **4 tentatives** (agent ReAct).

<!-- résumé a7038dead2bf · Notebook4_PartB_AgenticRAG_Security_SIEM -->
**Lecture.** L'agent récupère les erreurs **localisables dans le schéma** et **refuse volontairement** les deux cas irréparables (`EXFILTRATES` n'existe pas, la propriété `title` non plus) : mieux vaut « je ne sais pas » qu'une réponse inventée. Limite : ce réparateur est lexical ; un réparateur LLM couvrirait plus de cas, avec les mêmes garde-fous.

### Ré-ordonnancement
Une arête **sans provenance** est rétrogradée, même si son nom correspond à la question.

<!-- résumé a0acbda5c896 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
## 3. Audit de sécurité — empoisonnement du graphe (GragPoison)

**Menace** : quelques nœuds ou arêtes injectés détournent de nombreuses requêtes ⇒ mauvaise attribution, IOC légitimes bloqués, consignes cachées pour le LLM (*injection de prompt indirecte*).

| # | Attaque | Détecteur |
| --- | --- | --- |
| 1 | arêtes issues d'une source non approuvée (pastebin) | `unprovenanced` |
| 2 | faux malware relié à de nombreuses cibles (*hub*) | `hub_injection` |
| 3 | incident ré-attribué à un autre acteur | `attribution_flip` |
| 4 | consigne cachée dans une propriété texte | `prompt_injection` |

Le graphe est comparé à un **instantané de référence** approuvé ; les statistiques de degré sont calculées sur cette référence (sinon un hub injecté gonflerait l'écart-type et se masquerait lui-même).

<!-- résumé 763e875c93b0 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
Les quatre familles sont détectées. Impact sur le RAG : la même question est posée au graphe empoisonné, puis au graphe assaini.

<!-- résumé 4dae64ca3dd3 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
Le graphe assaini redevient **identique à la référence** et un nouveau scan est propre. **Limite** : un attaquant qui passe par une source approuvée et reste dans les degrés normaux échappe à ces détecteurs ; ils complètent la signature des sources, la revue humaine et la journalisation des écritures.

## 4. Audit OWASP LLM08:2025 — *Vector and Embedding Weaknesses*
Trois risques, trois contrôles, indépendants du modèle d'embedding (ici des n-grammes de caractères hachés, déterministes).

### 4.1 Fuite inter-locataires
Un top-k global filtré après coup peut renvoyer les documents d'un autre client. Contrôle : **filtre de locataire appliqué avant le calcul de similarité**, identifiant obligatoire ; `audit_tenant_isolation` interroge l'index en tant que chaque locataire et liste toute fuite.

<!-- résumé 4a4ced0b2f6e · Notebook4_PartB_AgenticRAG_Security_SIEM -->
### 4.2 Inversion d'embeddings
L'attaquant dispose des vecteurs volés et d'un **dictionnaire de phrases candidates** : on mesure son taux de récupération selon le bruit gaussien et l'arrondi ajoutés avant stockage. Compromis : plus de bruit ⇒ plus de confidentialité, mais moins de précision de recherche.

<!-- résumé 9f63ae5f7bff · Notebook4_PartB_AgenticRAG_Security_SIEM -->
> **Portée** : attaque par dictionnaire sur des embeddings simples. Elle valide la méthode de mesure, pas la résistance d'un modèle de production (à refaire avec l'encodeur E5).

### 4.3 Données sensibles dans l'index
Tout ce qui est embeddé peut être ré-exposé : `scrub_sensitive` masque secrets et données personnelles **avant** l'embedding.

<!-- résumé 424d7139db23 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
## 5. Export SIEM — règles de détection durables
Une réponse (« quels IOC pour APT29 ? ») devient une règle **Splunk SPL** (+ stanza `savedsearches.conf`) et **Microsoft Sentinel KQL** (+ règle analytique en JSON).

**Sécurité** : les IOC viennent d'un graphe potentiellement empoisonné. Chaque valeur est **validée** (IP, domaine, SHA-256) et échappée ; une valeur invalide est **rejetée et journalisée**, jamais corrigée ; une règle sans IOC valide est refusée.

<!-- résumé da6e2d72e5cf · Notebook4_PartB_AgenticRAG_Security_SIEM -->
Le domaine piégé (`x.example.com") | delete index=*`) est **rejeté**. Les IP du faux malware, elles, sont formellement valides : seul l'audit de la section 3 les arrête. On exporte donc depuis le graphe **assaini**.

<!-- résumé 5baeb21493c6 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
## 6. Graphe réel (Notebook 1) et LLM local (Notebook 3)
Les mécanismes validés ci-dessus sont maintenant mesurés sur le graphe STIX 2.1 de Walid Fehry (`knowledge_graph.json`) avec Qwen2.5-1.5B-Instruct en local.

<!-- résumé c3f28bfa73c0 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
### 6.1 Text-to-Cypher : LLM, agent ReAct et gabarits guidés par le schéma

| Jeu de questions | Rôle |
| --- | --- |
| Développement (10) | utilisé pendant la conception de l'agent et des gabarits |
| Validation (11, dont 3 en français) | écrit **avant** toute mesure, jamais utilisé pour régler |
| Formulation libre (4) | hors de la forme « quel(s) <type> … <entité> ? » : teste le repli sur le LLM |

| Configuration | Génération | Réparations |
| --- | --- | --- |
| LLM seul | Qwen2.5-1.5B (schéma + exemples dans le prompt) | aucune |
| Agent + réparation LLM | idem | syntaxe → schéma → liaison d'entités → sens de la relation → LLM |
| **Gabarits + agent** | type demandé + entité liée par le NER + relation du schéma ; LLM sinon | idem |

Métriques : **réponse exacte** (même ensemble que la requête de référence écrite à la main), requête exécutable, nombre d'étapes.

<!-- résumé 0da1da0f1993 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
> **Interprétation.** Le LLM seul n'écrit **aucune requête exacte** sur le jeu de développement (27 % en validation, 25 % en libre) : il invente labels et relations, ou se trompe de sens. L'**agent ReAct** remonte ces taux à 40 % / 45 % / 50 %. Les **gabarits** répondent **exactement à 100 %** en développement **et en validation** (questions en français comprises), en une étape et sans GPU. **Lecture honnête** : ces jeux suivent la forme ciblée par les gabarits ; en formulation libre, le repli LLM + agent reste à **50 %**. Comportement voulu : réponse fiable quand la question est reconnue, effort du LLM sinon, jamais de réponse inventée.

<!-- résumé 84d7bb916433 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
### 6.2 Audit d'empoisonnement sur le graphe réel (vérité terrain connue)
Quatre attaques sont injectées dans une copie du graphe réel ; on mesure la précision, le rappel et les faux positifs de la quarantaine.

| Attaque | Technique | Détection attendue |
| --- | --- | --- |
| A. Hub | faux malware `updatehelper` relié aux 25 entités les plus citées (source pastebin) | `unprovenanced`, `hub_injection` |
| B. Provenance usurpée | 6 relations `AFFECTS` fausses, source « corpus », `doc_ids` qui ne mentionnent pas les deux entités | `provenance_mismatch` |
| C. Injection de prompt | consigne cachée dans le titre d'un document | `prompt_injection` |
| D. Attaque furtive | faux document « propre » + 2 relations qui le citent | **aucune** (limite assumée) |

<!-- résumé a91e84412fa4 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
> **Interprétation.** Sur 34 arêtes injectées, la quarantaine en retire **32, toutes injectées** : **précision 1,00, rappel 0,94, 0 faux positif** sur le graphe sain (2 573 nœuds). Chaque attaque est prise par le détecteur attendu (source non approuvée : 25 ; provenance usurpée : 7 ; entité mentionnée par aucun document : le faux malware ; injection dans un titre : 1). Les 2 arêtes manquées sont celles de l'**attaque furtive** : limite assumée, qui impose de signer les sources. Même avant quarantaine, la **règle de provenance du RAG** empêche les relations sans document source d'atteindre le LLM ; la relation usurpée, en tête des preuves avant quarantaine, disparaît ensuite. L'audit a aussi permis de corriger deux faux positifs (URL, « jailbreak » iOS) et un bug de quarantaine.

<!-- résumé 1b4ed8ddfd1e · Notebook4_PartB_AgenticRAG_Security_SIEM -->
### 6.3 Export SIEM depuis les indicateurs du corpus
Les nœuds `Indicator` (IP, empreintes) passent par la validation stricte. Un corpus pédagogique contient surtout des adresses internes, de documentation ou bénignes, qu'il faut écarter avant qu'une règle ne génère des milliers de faux positifs.

<!-- résumé 124a0b808776 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
> **Interprétation.** Sur 20 indicateurs candidats, **un seul** devient une règle (`89.62.172.13`, serveur C2 décrit dans un rapport d'analyse). Les 18 rejets sont justifiés : adresses internes, de bouclage ou réservées (15), plages de documentation RFC 5737 (2), résolveur DNS public (1). Sans cette validation, la règle déclencherait sur tout le trafic interne et DNS. Les numéros de section (« 3.6.5.2 ») autrefois pris pour des IP sont désormais filtrés dès le NER.

<!-- résumé 7ec6c4b945f9 · Notebook4_PartB_AgenticRAG_Security_SIEM -->
### 6.4 Métriques exportées
`reports/metrics/notebook4b_metrics.json`, lu par la synthèse et la page *Pilotage* de Vigie.

<!-- résumé 55832ae8ad1d · Notebook4_PartB_AgenticRAG_Security_SIEM -->
## 7. Synthèse et limites

| Axe | Démo contrôlée (§ 1 – 5) | Graphe réel (§ 6) |
| --- | --- | --- |
| Fiabilité (gabarits + agent ReAct) | 4/6 questions résolues (dont 2 après réparation), 2 refus justifiés | réponses exactes : LLM seul 27 % → 100 % (validation) ; 50 % en formulation libre |
| Intégrité du graphe (6 détecteurs + quarantaine) | 4 familles détectées, graphe assaini = référence | précision 1,00, rappel 0,94, 0 faux positif |
| LLM08 — isolation | 5 fuites → 0 | — |
| LLM08 — inversion | récupération 100 % → 4 % (σ = 0,4) | — |
| LLM08 — données sensibles | clés, e-mails et jetons masqués | — |
| SIEM (validation + échappement) | IOC piégé rejeté ; SPL, KQL, stanza, JSON | 1 IOC retenu sur 20 candidats |

**Limites** : formulations libres dépendantes du LLM (50 %) ; graphe en mémoire limité à un saut (Neo4j pour le multi-sauts) ; attaque furtive non détectée (signer les sources) ; inversion à refaire avec l'encodeur E5 ; règles SIEM non testées sur un vrai Splunk / Sentinel.

## 8. Intégration avec l'équipe (Jalons 4 et 5)

| Élément | Avec | État |
| --- | --- | --- |
| Graphe STIX 2.1 | Walid Fehry (Notebook 1) | ✅ chargé, importable dans Neo4j ; l'agent ne dépend que de `run(query)` et `schema()` |
| LLM | Khaled Gannoun (Notebook 3) | ✅ Qwen2.5-1.5B local pour générer et réparer le Cypher ; adaptateur LoRA chargeable |
| HybridRAG | Ines Trabelsi (Notebook 4A) | ✅ garde-fou d'entrée + contrôle de fidélité ; audit à lancer avant chaque mise à jour du graphe |
| Audit global (Jalon 5) | équipe | ✅ métriques ci-dessus ; ⏳ tests sur un vrai Splunk / Sentinel |

<!-- résumé 254a07fe1bd7 · Synthese_TDSP -->
# Synthèse TDSP — résultats consolidés, démonstration de Vigie et acceptation

Cette partie lit les métriques exportées par chaque notebook (`reports/metrics/`), rejoue le moteur de **Vigie** (le MVP) et vérifie les critères d'acceptation.

| Étape TDSP | Section | Sources |
| --- | --- | --- |
| 1. Business Understanding | 1 — besoins SOC, objectifs data science | rapport TDSP phases 1 – 2 |
| 2. Data Acquisition & Understanding | 2 — corpus, nettoyage, entités, graphe | Notebook 1 |
| 3. Modeling | 3 — représentations, NER, GNN / HGT, LLM / LoRA, HybridRAG | Notebooks 1, 2A, 2B, 3, 4A |
| 4. Deployment | 4 — démonstration du moteur de **Vigie** | `cybersec_nlp.engine`, `backend/`, `frontend/` |
| 5. Security Audit & Acceptance | 5 — audit et critères d'acceptation | Notebook 4B, tous |

<!-- résumé 7767a9c7c4fc · Synthese_TDSP -->
## 1. Business Understanding

| Besoin du SOC | Réponse data science | Mesure principale |
| --- | --- | --- |
| **Tri & classification** des rapports | catégorisation (8 catégories SOC, supervision faible) + NER cyber | macro-F1, F1 NER |
| **Cartographie des attaques** (menaces → vecteurs → cibles) | graphe STIX 2.1, GNN / HGT, clustering Leiden | macro-F1 vs texte seul, modularité |
| **Assistant QA conversationnel** | HybridRAG (FAISS + graphe) + LLM local, réponses citées | Recall@k, MRR, abstention, phrases étayées |
| **Fiabilité et sécurité** | agent ReAct, garde-fous, audit d'empoisonnement, OWASP LLM08, export SIEM | réponses exactes, précision / rappel, fuites |

**Contrainte clé** : le corpus est un jeu **questions / réponses pédagogique**, sans labels ni incidents réels ⇒ catégories = pseudo-labels, relations du graphe = associations candidates. Tous les résultats se lisent avec cette limite.

<!-- résumé cd1b8d09d2d3 · Synthese_TDSP -->
## 4. Déploiement : démonstration de bout en bout

`SOCEngine` est **le même objet** que celui servi par Vigie (API FastAPI `backend/`, interface Streamlit `frontend/`) : ce qui suit est exactement le comportement du MVP.

<!-- résumé 0fbd8e89502f · Synthese_TDSP -->
> **Lecture.** **Les 15 critères proposés sont atteints.** Deux réserves : (1) les seuils sont des **propositions** à valider avec le SOC, et certaines valeurs en sont proches (triage 0,53 pour 0,50) ; (2) plusieurs métriques viennent de jeux construits par l'équipe et sont **optimistes** (garde-fou : 20 requêtes ; NER : étiquettes *silver* ; Text-to-Cypher : 50 % seulement en formulation libre). Les résultats négatifs comptent aussi : GCN / GAT et HGT ne battent pas le texte seul sur ces pseudo-labels, et LoRA améliore le style mais pas la cohérence factuelle.

<!-- résumé 0b2b377e5214 · Synthese_TDSP -->
## 6. Conclusion et prochaines étapes

**Ce qui fonctionne.** Un corpus propre et traçable, un graphe STIX 2.1 importable dans Neo4j, et un assistant SOC qui **cite ses preuves, s'abstient hors domaine (100 %), ne garde que des phrases étayées (100 %) et répond en ~3 s** sur un GPU de portable, sans qu'aucune donnée ne quitte la machine. La sécurité est **mesurée** : quarantaine de l'empoisonnement (précision 1,00, rappel 0,94, 0 faux positif), isolation des locataires, validation des IOC avant export SIEM.

**Ce que les données limitent.** Corpus pédagogique : pseudo-labels, peu d'IOC réels, relations issues de co-occurrences. L'absence de gain des modèles de graphes est une conclusion scientifique, pas un échec d'implémentation.

**Prochaines étapes.**
1. Fixer avec le SOC les seuils d'acceptation et un jeu de questions annotées (multi-documents, sans réponse).
2. Ajouter un corpus CTI narratif et MITRE ATT&CK (STIX) pour des relations validées et de vrais IOC.
3. Annoter un échantillon pour évaluer le NER et la catégorisation sans biais.
4. Passer à Neo4j et à un LLM plus grand pour les questions libres en Text-to-Cypher (50 % exactes aujourd'hui).
5. Tester les règles SIEM sur une instance Splunk / Sentinel de recette.
