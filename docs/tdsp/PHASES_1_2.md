# TDSP — Compte rendu des phases 1 et 2

Ce document transmet à l'équipe l'avancement initial du projet selon les deux
premières phases du **Team Data Science Process (TDSP)**. Il sépare les faits
vérifiés, les décisions de cadrage prises pour démarrer et les points qui
nécessitent encore une validation collective.

## Résumé

- **Cas d'usage retenu pour le pilote :** assistant de questions-réponses pour
  les analystes SOC, avec réponses justifiées par des sources et validation
  humaine.
- **Corpus initial du dépôt :** dataset public Hugging Face de 2 411 exemples
  `system` / `user` / `assistant`. Il n'a pas de labels de classification et
  n'est pas, à lui seul, un corpus de documents CTI permettant de justifier les
  réponses d'un Graph-RAG.
- **Complément exploratoire :** MITRE ATT&CK Enterprise, release 20.0, au format
  STIX 2.1. Ce corpus structuré apporte des techniques et des relations, mais
  ne remplace pas des rapports CTI narratifs.
- **À retenir :** les phases 1 et 2 sont amorcées, mais elles ne sont pas encore
  validées par toute l'équipe. Les seuils de réussite, la licence du dataset
  Hugging Face et le besoin éventuel d'un corpus narratif restent à confirmer.

## Phase 1 — Compréhension métier

### Cadrage de départ

| Élément | Proposition pour le pilote |
| --- | --- |
| Utilisateurs | Analystes SOC |
| Besoin | Retrouver et relier des informations de cybersécurité plus rapidement |
| Cas d'usage | Poser une question et recevoir une réponse accompagnée de sources vérifiables |
| Mode d'utilisation initial | Aide à l'analyse ; un analyste vérifie les résultats |
| Hors périmètre initial | Activation automatique de règles SIEM ou actions de réponse à incident |

Ce choix correspond à l'objectif d'assistant QA SOC décrit dans le rapport
TDSP. Il ne signifie pas que les performances de l'assistant sont déjà
démontrées.

### Critères à valider avec les collègues et le SOC

Avant la modélisation, convenir ensemble :

1. des questions prioritaires et des types de sources attendues ;
2. de ce qui constitue une réponse correcte, suffisamment sourcée ou
   insuffisamment étayée ;
3. des critères d'évaluation : qualité factuelle et des citations, taux
   d'abstention approprié, latence, taux d'erreur et coût ;
4. d'un jeu de test indépendant des données servant à construire ou indexer la
   solution ;
5. des responsabilités de revue humaine et des règles de confidentialité.

Les chiffres de performance cités dans le rapport sont des objectifs ou
résultats rapportés dans ce document ; ils ne sont pas des résultats mesurés
sur les données de ce dépôt.

## Phase 2 — Acquisition et compréhension des données

### Dataset Hugging Face du dépôt

- Identifiant utilisé par le script : `AlicanKiraz0/Cybersecurity-Dataset-v1`.
- Taille observée : **2 411 exemples**, dans un seul split `train`.
- Colonnes observées : `system`, `user`, `assistant`.
- Aucun label explicite de classe ou d'entité n'a été trouvé.
- Deux exemples comportent des champs vides : un exemple où les trois champs
  sont vides et un autre où la réponse `assistant` est vide.
- La vérification des métadonnées Hugging Face n'a pas retourné de licence.
  Le README du projet mentionne Apache 2.0, mais cette mention n'a pas été
  confirmée par les métadonnées consultées. **Vérifier la licence et les
  conditions d'utilisation à la source avant réutilisation, redistribution ou
  publication de résultats.**

Ce dataset peut aider à explorer le format des échanges et à prototyper des
questions-réponses. En revanche, il ne fournit pas nécessairement les documents
de référence permettant de vérifier chaque réponse. Il ne suffit pas non plus
à entraîner et évaluer un modèle supervisé de classification ou de NER sans
annotations appropriées.

### Complément MITRE ATT&CK

- Corpus : **MITRE ATT&CK Enterprise, release 20.0**, représentation STIX 2.1.
- Source : [dépôt officiel MITRE ATT&CK STIX](https://github.com/mitre-attack/attack-stix-data).
- Fichier versionné :
  [enterprise-attack-20.0.json](https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-20.0.json).
- Conditions : [MITRE ATT&CK Terms of Use](https://attack.mitre.org/resources/legal-and-branding/terms-of-use/).
- Attribution requise lors de la reproduction ou distribution :
  `© 2026 The MITRE Corporation. This work is reproduced and distributed with the permission of The MITRE Corporation.`
- Résultat du contrôle local : fichier JSON lisible, **26 690 objets**, dont
  **21 819 relations** ; 24 345 objets contiennent au moins une référence
  externe avec URL.

ATT&CK est une base structurée de connaissances sur les tactiques et techniques,
pas un corpus de rapports d'incidents narratifs. Il convient pour explorer les
entités et relations MITRE ; l'équipe devra décider si des rapports CTI
narratifs, publics et autorisés sont également nécessaires pour le cas d'usage
Q/R avec citations documentaires.

### Emplacement des données et reproductibilité

Les données téléchargées se trouvent localement sous `data/raw/`. Le dépôt
ignore ce répertoire : les corpus volumineux ne doivent pas être ajoutés au
dépôt Git. Chaque membre de l'équipe peut reproduire les téléchargements depuis
la racine du dépôt.

1. Télécharger le dataset Hugging Face, après installation des dépendances du
   projet :

   ```powershell
   .\run.ps1 install
   .\run.ps1 data
   .\run.ps1 explore
   ```

2. Télécharger le même fichier ATT&CK versionné :

   ```powershell
   $target = "data\raw\corpora\mitre_attack"
   New-Item -ItemType Directory -Force -Path $target | Out-Null
   curl.exe -L --fail --silent --show-error `
     "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-20.0.json" `
     --output "$target\enterprise-attack-20.0.json"
   ```

3. Vérifier que le fichier téléchargé est du JSON valide :

   ```powershell
   python -c "import json; json.load(open(r'data\raw\corpora\mitre_attack\enterprise-attack-20.0.json', encoding='utf-8')); print('JSON valide')"
   ```

Les commandes d'exploration affichent des exemples de conversations : ne
copiez pas de contenu sensible dans des tickets, captures ou documents partagés
sans en vérifier la classification.

## Décisions et prochaines actions de l'équipe

- [ ] Valider le cas d'usage Q/R SOC et les utilisateurs pilotes.
- [ ] Définir les critères de réussite, les questions d'évaluation et les
  critères de qualité des citations.
- [ ] Vérifier à la source la licence et les conditions du dataset Hugging Face.
- [ ] Décider si ATT&CK seul est suffisant pour le premier prototype ou si des
  rapports CTI narratifs licenciés sont nécessaires.
- [ ] Documenter les sources retenues : propriétaire, URL/version, licence,
  date d'acquisition, classification et conditions de conservation.
- [ ] Définir le traitement des lignes vides, doublons et informations sensibles.
- [ ] Construire un jeu d'évaluation indépendant et faire valider les exemples
  par des analystes SOC.
- [ ] Ne commencer la phase 3 (modélisation) qu'après accord sur le périmètre et
  les données minimales.

## Préparer un commit et un push

Les fichiers de données sous `data/raw/` sont exclus par `.gitignore` et ne
doivent pas être poussés. Ce document contient les constats, les sources et les
instructions permettant aux collègues de refaire l'acquisition.

Depuis la racine du dépôt, examiner d'abord les changements :

```powershell
git status --short
git diff --check
```

Ajouter explicitement uniquement les documents que l'équipe souhaite partager
— ne pas utiliser `git add .` pour éviter d'inclure les données locales ou
d'autres fichiers non suivis :

```powershell
git add README.md GUIDE_DEPLOIEMENT.md docs\tdsp\PHASES_1_2.md
git diff --cached --stat
git diff --cached
```

Après revue des changements indexés et accord de l'équipe, créer le commit et
pousser la branche :

```powershell
git commit -m "docs: document TDSP phases 1 and 2"
git push
```

Les rapports PDF et Markdown présents à la racine peuvent être des fichiers
non suivis dans le dépôt courant. Vérifier `git status` et se mettre d'accord
avec l'équipe avant de les ajouter à un commit.
