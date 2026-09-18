# Plan de monitoring — Pipeline ETL CheckIt.AI

**Livrable étape 5** — stratégie de surveillance du pipeline en production,
alignée sur les automatisations en place (DAG Airflow `etl_checkit_multimodal`,
planifié toutes les 6 heures, soit 4 exécutions par jour).

## 1. Ce que l'on surveille : les KPI

| Famille | KPI | Source de mesure | Objectif |
|---|---|---|---|
| Précision | Taux de validité (valides / collectées) | fichiers JSONL + dashboard | ≥ 70 % |
| Précision | Rejets par cause (image, texte, doublon) | pipeline.log | suivi de tendance |
| Précision | Publications collectées par run | XCom / logs tâche extract | > 0 |
| Rapidité | Durée de chaque tâche | base de métadonnées Airflow | extract < 15 min |
| Rapidité | Taux de succès des runs | Airflow (états des tâches) | 100 % sur 7 j |
| Coût | Appels API NewsData consommés / jour | 4 runs × 3 pages = 12 max | < 200 (quota) |
| Coût | Stockage images + table publications | disque + pg_total_relation_size | croissance linéaire |

Ces KPI sont visualisés dans le tableau de bord Streamlit
(`dashboard/dashboard_kpi.py`), conçu pour être lisible par un public non
technique : trois gros indicateurs par famille, messages en clair
(✅ conforme / ⚠️ seuil dépassé), pas de jargon.

## 2. Seuils d'alerte et réactions

| Événement détecté | Seuil | Gravité | Réaction |
|---|---|---|---|
| Tâche en échec après ses 2 retries | 1 occurrence | Critique | Notification immédiate (email Airflow), intervention le jour même |
| Extraction retourne 0 publication | 2 runs consécutifs | Critique | Vérifier les sources (flux RSS modifiés ? clé API révoquée ?) |
| Taux de validité < 70 % | 1 run | Majeure | Analyser les causes de rejet dans pipeline.log (ex. : un média a changé son format d'image) |
| Durée extract > 15 min | 1 run | Majeure | Vérifier la disponibilité des sources et le réseau |
| HTTP 429 (quota API) dans les logs | 1 occurrence | Mineure | Normalement impossible (12 appels/jour « 200) : réviser NEWSDATA_MAX_PAGES si cela survient |
| Base PostgreSQL inaccessible | 1 occurrence | Critique | Vérifier le service, les identifiants, l'espace disque |
| Croissance anormale du stockage | > +20 % vs semaine précédente | Mineure | Vérifier l'absence de doublons d'images, envisager une purge/archivage |

Mise en œuvre des notifications : Airflow permet d'attacher un
`on_failure_callback` ou une configuration SMTP au DAG pour envoyer un
email à chaque échec définitif de tâche — c'est l'évolution prévue en
production (en local, l'UI et les logs suffisent).

## 3. Fréquence des vérifications (alignée sur l'automatisation)

| Quand | Quoi | Qui / comment |
|---|---|---|
| À chaque run (toutes les 6 h) | Contrôles automatiques : retries (2×), validation texte/image, idempotence du chargement, journalisation | Automatique (Airflow + code du pipeline) |
| Quotidien (5 min) | Coup d'œil au dashboard : 4 runs verts ? taux de validité ? volumes cohérents ? | Ingénieur data, via Streamlit |
| Hebdomadaire (30 min) | Revue des tendances : durées, causes de rejet, croissance du stockage, taux de succès sur 7 j | Ingénieur data |
| Mensuel | Vérification des sources (flux RSS toujours actifs, CGU API inchangées), rotation du mot de passe applicatif, purge des logs anciens | Équipe data |

La fréquence quotidienne est cohérente avec la planification 6 h : un
incident nocturne est vu au plus tard le lendemain matin, et les retries
automatiques couvrent les indisponibilités transitoires entre deux
vérifications humaines.

## 4. Gestion des erreurs (déjà implémentée dans le pipeline)

- **Retries Airflow** : 2 tentatives espacées de 5 min par tâche — absorbe
  les indisponibilités ponctuelles des sources.
- **Dégradation contrôlée** : une source en panne (ex. clé API absente,
  un flux RSS illisible) est journalisée et ignorée ; le pipeline continue
  avec les autres sources plutôt que d'échouer entièrement.
- **Idempotence** : relancer un run (ou une seule tâche via « Clear task »)
  ne crée jamais de doublon — déduplication par hash à l'écriture JSONL et
  clé primaire `ON CONFLICT DO NOTHING` en base.
- **Quarantaine implicite** : les entrées invalides ne sont pas supprimées
  silencieusement, elles restent visibles dans le brut (publications.jsonl)
  et leurs causes de rejet sont comptabilisées dans les logs, ce qui
  alimente le KPI « rejets par cause ».
- **Traçabilité** : double journalisation (logs Airflow par tâche et par
  run + pipeline.log applicatif), permettant l'audit a posteriori de
  n'importe quelle exécution.

## 5. Limites connues et évolutions

- Les alertes sont aujourd'hui « pull » (on consulte le dashboard) ; le
  passage en « push » (email/Slack via callbacks Airflow) est la première
  évolution de production.
- Le coût est mesuré en ressources locales (stockage, quota API) ; sur un
  déploiement cloud, ajouter le coût monétaire (instance, stockage objet).
- À terme, exporter les métriques vers un outil dédié (Prometheus +
  Grafana) si le nombre de pipelines augmente.
