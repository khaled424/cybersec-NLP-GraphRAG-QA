# Commandes essentielles

Le projet se pilote avec **[mise](https://mise.jdx.dev)** (`mise.toml` à la racine). Il fixe la version de
Python (3.12), crée la venv `.venv` et définit les commandes. Équivalents : `make <cible>` (Linux / macOS),
`.\run.ps1 <commande>` (Windows).

## Première installation

```bash
mise trust          # autorise le mise.toml du dépôt (une seule fois)
mise install        # installe Python 3.12 et crée .venv
mise run setup      # dépendances + dataset vérifié + artefacts du pipeline (~10 min la première fois)
```

`mise tasks` affiche la liste à jour ; `mise run <tâche> --help` affiche l'aide d'une tâche.

## Commandes

| Commande | Rôle | Durée |
| --- | --- | --- |
| `mise run install` | dépendances (`requirements.txt`), package éditable, modèle spaCy | ~5 min |
| `mise run setup` | `install` + `data` + `pipeline` (première installation) | ~10 min |
| `mise run data` | télécharge le dataset à la révision figée et vérifie son SHA-256 | < 10 s |
| `mise run pipeline` | corpus nettoyé → NER → graphe STIX → scripts Neo4j → index FAISS → classifieur | ~2 min |
| `mise run notebooks` | exécute les notebooks de l'équipe et la synthèse, dans l'ordre (GPU recommandé) | ~1 h |
| `mise run master` | **reconstruit le notebook maître** (livrable) à partir des notebooks puis l'exécute | ~1 h 30 |
| `mise run master-text` | met à jour **le texte seul** du maître (résumés de `scripts/master_summaries.md`) ; code et sorties intacts | < 5 s |
| `mise run notebook 00_Master_Notebook` | exécute un seul notebook (nom sans `.ipynb`) | variable |
| `mise run lab` | ouvre JupyterLab sur `notebooks/` | — |
| `mise run mvp` | **Vigie** complet : API + interface en parallèle (Ctrl+C arrête les deux) | ~15 s |
| `mise run api` | API seule : http://localhost:8000 (documentation : `/docs`) | — |
| `mise run ui` | interface seule : http://localhost:8501 (l'API doit tourner) | — |
| `mise run docker` | Vigie en conteneurs, CPU (après `pipeline`) | build ~10 min |
| `mise run test` | tests unitaires et d'API | ~15 s |
| `mise run lint` | analyse statique (ruff) | < 5 s |
| `mise run format` | corrections automatiques de ruff | < 5 s |
| `mise run check` | `lint` + `test` : à lancer avant chaque push | ~20 s |

## Scénarios courants

```bash
# Démontrer Vigie (soutenance)
mise run pipeline && mise run mvp          # puis ouvrir http://localhost:8501

# Après une modification du package
mise run check

# Après une modification d'un notebook ou du NER : régénérer les résultats et le livrable
mise run pipeline && mise run notebooks && mise run master
```

## Variables d'environnement (définies par `mise.toml`)

| Variable | Valeur par défaut | Rôle |
| --- | --- | --- |
| `PY` | `.venv/bin/python` | interpréteur utilisé par les tâches (indépendant de l'ordre du `PATH`) |
| `CYBERSEC_API_URL` | `http://localhost:8000` | URL de l'API utilisée par l'interface |
| `PYTORCH_CUDA_ALLOC_CONF` | `expandable_segments:True` | limite la fragmentation mémoire GPU (fine-tuning LoRA sur 8 Go) |
| `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` | non définies | optionnelles : import du graphe dans Neo4j (Notebook 1), voir `.env.example` |

## Dépannage

| Symptôme | Cause / solution |
| --- | --- |
| `No module named pytest` (ou autre) | dépendances absentes : `mise run install` |
| Interface : « API hors ligne » | lancer `mise run api` (ou `mise run mvp`) |
| API : erreur 503 « … is missing » | artefacts absents : `mise run pipeline` |
| Réponses « extractives » uniquement | pas de GPU CUDA détecté : comportement normal, sans génération par LLM |
| `CUDA out of memory` dans un notebook | fermer l'API / les autres notebooks qui occupent le GPU, relancer le notebook seul |
| `mise` ignore `mise.toml` | `mise trust` dans le dossier du projet |
