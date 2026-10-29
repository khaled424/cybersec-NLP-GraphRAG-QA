# Guide pour construire et déployer une solution Graph-RAG fiable

Ce guide s'appuie sur le [rapport TDSP au format PDF](./rapport-projet-cybersecurity-tdsp-v2.pdf)
et sa [transcription Markdown](./rapport-projet-cybersecurity-tdsp.md). Il
traduit leurs recommandations en étapes concrètes : valider le périmètre,
construire la solution, la tester, puis la déployer et l'exploiter en sécurité.
Il distingue l'état actuel du dépôt de la cible décrite dans le rapport.

> **État actuel du dépôt : prototype de démarrage.** L'API FastAPI expose
> uniquement `GET /health`. Le frontend est un placeholder et les workflows
> NLP, graphe de connaissances et Graph-RAG complets restent à implémenter.
> Le Docker Compose actuel ne lance que l'API. Les métriques expérimentales
> mentionnées dans le rapport (par exemple les scores HybridRAG) sont des
> objectifs ou résultats rapportés, pas des performances mesurées par le code
> présent dans ce dépôt. Ne présentez donc pas ce prototype comme un outil SOC
> opérationnel avant d'avoir réalisé les étapes de ce guide.

## 1. Définir ce que signifie « réussir »

Avant le développement, convenez avec les analystes SOC des critères
d'acceptation et d'un jeu d'évaluation représentatif. Mesurez au minimum :

- la précision, le rappel et le score F1 de l'extraction d'entités (CVE,
  logiciels, techniques MITRE ATT&CK, indicateurs, etc.) ;
- la justesse des réponses, la qualité des citations vers les sources et le
  taux de réponses non étayées ;
- la réussite des questions multi-sauts, la latence (p50/p95), le taux
  d'erreur et le coût par requête ;
- les résultats par type de source, période, langue et catégorie de question.

Conservez un jeu de test indépendant des données d'entraînement et d'indexation.
Faites évaluer les réponses sensibles par des analystes ; un score moyen ne
remplace pas une vérification des erreurs à fort impact. Définissez les seuils
de mise en production avec le SOC : les chiffres du rapport ne sont pas une
garantie applicable à votre corpus.

## 2. Construire une base de connaissances traçable

1. **Valider les sources et leurs droits d'usage.** Documentez le propriétaire,
   la licence, la date d'acquisition, la classification et les règles de
   conservation pour chaque corpus. Vérifiez le contenu avant ingestion.
2. **Séparer les faits observés des inférences.** Enregistrez la provenance,
   l'horodatage, la source et, si disponible, le niveau de confiance sur chaque
   entité et relation du graphe. Ne présentez pas une attribution inférée comme
   un fait confirmé.
3. **Normaliser et contrôler les données.** Dédupliquez, nettoyez les documents,
   validez les identifiants (par exemple CVE et MITRE ATT&CK), et conservez un
   lien vers le passage source de chaque élément indexé.
4. **Versionner et rejouer l'ingestion.** Gardez une version identifiable du
   corpus, des transformations, du modèle d'embedding, du schéma de graphe et
   des index. Une ingestion doit pouvoir être auditée, comparée et annulée.
5. **Comparer les architectures.** Établissez une référence vectorielle, puis
   mesurez les gains et coûts d'une recherche hybride vecteur + graphe. N'ajoutez
   un agent ou un GNN que si une évaluation contrôlée montre une amélioration
   utile.

Le dataset actuellement mentionné dans le README contient des paires
instruction-réponse sans labels de classes explicites. Il ne suffit donc pas, à
lui seul, à certifier un modèle de classification ou de NER supervisé.

## 3. Préparer l'application avant la production

Complétez le prototype avant de viser un déploiement SOC :

- implémenter les routes de questions/réponses, le chargement du modèle et la
  gestion explicite des erreurs ;
- réaliser les pipelines d'ingestion, d'indexation vectorielle et de
  construction/interrogation du graphe ;
- fournir une réponse avec extraits/citations, provenance et possibilité de
  s'abstenir lorsque les preuves sont insuffisantes ;
- choisir et documenter les services de données, leur stratégie de sauvegarde
  et de restauration ; ils ne sont pas encore configurés dans le Compose actuel ;
- implémenter le frontend et l'authentification avant toute exposition à des
  utilisateurs ;
- ajouter des tests d'intégration et d'évaluation de bout en bout, ainsi que des
  contrôles de disponibilité et de préparation adaptés aux dépendances.

Ne renvoyez pas une réponse présentée comme certaine lorsque la recherche échoue,
qu'aucun document fiable n'est trouvé ou que le modèle ne peut pas répondre.
Exposez un état dégradé et journalisez l'erreur sans inclure de secrets ou de
contenu sensible inutile.

## 4. Installer et vérifier le prototype en local

Depuis la racine du dépôt, avec Python 3.10 ou supérieur :

```powershell
.\run.ps1 install
.\run.ps1 test
.\run.ps1 lint
.\run.ps1 api
```

L'API de démarrage répond sur `http://127.0.0.1:8000/health`. Elle ne fournit
pas encore de fonction de questions-réponses. Le téléchargement de données est
optionnel et peut nécessiter un accès réseau :

```powershell
.\run.ps1 data
.\run.ps1 explore
```

Pour construire et lancer le conteneur API avec Docker Compose, depuis la
racine :

```powershell
docker compose -f infra/docker-compose.yml config
docker compose -f infra/docker-compose.yml up --build
```

Vérifiez `http://localhost:8000/health`, puis arrêtez les conteneurs avec
`Ctrl+C`. Le Compose existant ne lance ni frontend, ni base vectorielle, ni base
graphe. Le Dockerfile frontend n'est pas référencé par ce Compose et le
frontend actuel affiche seulement un message placeholder.

## 5. Sécuriser le système Graph-RAG

Avant d'exposer le service, mettez en place les contrôles suivants :

- **Accès** : authentification, autorisation par rôle, TLS, limitation de débit
  et réseau privé pour les bases. N'exposez jamais directement les interfaces
  d'administration ou les ports des bases de données.
- **Identifiants** : utilisez un gestionnaire de secrets en déploiement. Ne
  stockez ni clés API ni mots de passe dans le dépôt, l'image, les journaux ou
  les fichiers Compose versionnés. `.env.example` est actuellement un
  placeholder.
- **Requêtes générées** : limitez l'accès du compte graphe au strict nécessaire,
  validez le schéma et les requêtes, appliquez des limites de temps et de
  résultats. Une requête produite par un LLM ne doit jamais pouvoir modifier ou
  supprimer les données.
- **Empoisonnement et prompt injection** : traitez les documents récupérés
  comme des données non fiables, pas comme des instructions. Contrôlez les
  sources, les relations anormales et les changements de nœuds centraux ;
  exigez une revue humaine pour les ajouts sensibles.
- **Confidentialité** : réduisez et masquez les données personnelles ou
  confidentielles avant l'indexation. Limitez les droits de lecture des index,
  définissez la rétention et contrôlez les accès aux embeddings et aux
  citations.
- **Réponses et actions** : citez les éléments justificatifs et signalez
  l'incertitude. Toute règle KQL ou recommandation générée doit être revue et
  testée par un analyste avant son activation dans un SIEM. Le système ne doit
  pas exécuter automatiquement une action de réponse à incident.
- **Chaîne logicielle** : verrouillez les dépendances, reconstruisez des images
  minimales et non-root, analysez les dépendances et images, et publiez des
  images identifiées par version ou digest.

## 6. Déployer progressivement

1. **Environnement de développement** : exécutez les tests, l'analyse statique
   et les évaluations avec des données synthétiques ou autorisées.
2. **Préproduction** : déployez une image immuable avec configuration et
   secrets séparés. Testez les parcours API, les dépendances, la charge,
   l'authentification, les scénarios d'échec et la restauration des sauvegardes.
3. **Mode observation** : confrontez les résultats à ceux des analystes sans
   déclencher d'action opérationnelle. Relevez les erreurs factuelles, les
   réponses non sourcées, les latences et le coût.
4. **Pilote limité** : ouvrez l'accès à un groupe d'utilisateurs défini,
   maintenez une validation humaine et fixez des seuils d'arrêt/retour arrière.
5. **Production** : élargissez progressivement après validation des critères
   d'acceptation, de sécurité, de capacité, de sauvegarde et de support.

En production, surveillez la disponibilité, les erreurs, les latences, la
fraîcheur des index, les échecs d'ingestion et la qualité des réponses. Les
journaux doivent permettre l'audit sans recopier inutilement les documents
sensibles. Prévoyez un responsable de service, une procédure d'incident, une
rotation des secrets, une sauvegarde testée et un mécanisme de retour à la
version précédente.

## 7. Liste de contrôle de mise en production

- [ ] Le cas d'usage, les utilisateurs, les données et les critères de réussite
  sont validés par le SOC.
- [ ] Les métriques sont calculées sur un jeu de test indépendant ; les réponses
  critiques ont été revues par des humains.
- [ ] Chaque résultat important est justifiable par des sources traçables et le
  système peut s'abstenir.
- [ ] Les accès, secrets, données, journaux et requêtes générées sont protégés.
- [ ] Les tests automatisés, tests d'intégration, tests de charge et contrôles
  de sécurité passent.
- [ ] Les sauvegardes et la restauration ont été testées ; le retour arrière est
  documenté.
- [ ] L'exploitation, la supervision, le support et les seuils d'arrêt sont
  définis.
- [ ] Le pilote n'active aucune règle ou action SOC sans revue et autorisation
  explicites.

## État des fonctions vérifiables dans ce dépôt

| Fonction | État observé |
| --- | --- |
| Vérification de santé FastAPI | Implémentée (`GET /health`) |
| Téléchargement et exploration du dataset | Scripts présents |
| Modèles NLP/NER et évaluation | À compléter et valider |
| Indexation vectorielle et Graph-RAG complet | À compléter |
| Base graphe et orchestration d'ingestion | Non configurées dans Compose |
| Interface utilisateur | Placeholder |
| Déploiement de production | Non défini |

Le déploiement du prototype est donc un contrôle technique initial, pas une
preuve que les objectifs métier, les résultats du rapport ou les exigences de
sécurité sont satisfaits.
