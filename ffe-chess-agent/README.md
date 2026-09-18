# FFE Chess Agent — POC Agent IA ouvertures d'échecs

Proof of Concept d'un agent intelligent qui accompagne les jeunes espoirs de la
**Fédération Française des Échecs (FFE)** dans l'apprentissage des ouvertures.

L'agent guide l'utilisateur en s'appuyant sur :

- l'identification de la position en cours via son identifiant **FEN** ;
- un moteur d'analyse spécialisé (**Stockfish**) ;
- les **APIs Lichess** (bibliothèque d'ouvertures et parties de référence) ;
- une base vectorielle **Milvus** alimentée par des données type WikiChess ;
- des **vidéos explicatives YouTube** pertinentes.

> ⚠️ Ce dépôt est en cours de construction. Cette version correspond à
> **l'étape 1 : mise en place du poste de travail** (structure, dépôt Git,
> `docker-compose` de base avec un backend FastAPI fonctionnel).

## Stack technique cible

| Composant            | Technologie          |
| -------------------- | -------------------- |
| Orchestration agent  | LangGraph            |
| API backend          | FastAPI              |
| Base documentaire    | MongoDB              |
| Recherche vectorielle| Milvus               |
| Interface            | Angular + ngx-chessboard |
| Conteneurisation     | Docker Compose       |

## Structure du dépôt

```
ffe-chess-agent/
├── docker-compose.yml      # Orchestration des services
├── .env.example            # Modèle de configuration (à copier en .env)
├── backend/                # API FastAPI + agent LangGraph
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── data/openings.json  # Jeu de données RAG (ouvertures)
│   ├── scripts/build_index.py
│   └── app/
│       ├── main.py         # App FastAPI (CORS + routes)
│       ├── core/config.py  # Configuration (variables d'env)
│       ├── services/       # lichess, stockfish, milvus, embedding, youtube
│       ├── agent/graph.py  # Orchestration LangGraph
│       └── api/v1/endpoints/
└── frontend/               # Application Angular (échiquier + panneau agent)
    ├── Dockerfile
    ├── nginx.conf
    └── src/app/            # composant, service, modèles
```

## Prérequis

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/products/docker-desktop/) et Docker Compose

## Démarrage rapide (démo)

Trois étapes, une seule commande de lancement :

```bash
# 1. Récupérer le projet
git clone <url-du-depot> && cd ffe-chess-agent

# 2. Créer et compléter la configuration
cp .env.example .env
#   -> renseigner LICHESS_TOKEN et YOUTUBE_API_KEY dans .env (voir Configuration)

# 3. Tout lancer
docker compose up --build
```

Cela démarre **backend + MongoDB + frontend**. Au **premier** démarrage, le
backend télécharge le modèle d'embedding puis construit automatiquement l'index
Milvus (quelques minutes ; mis en cache ensuite). Les démarrages suivants sont
quasi immédiats.

Une fois lancé :

- **Interface** : http://localhost:4200
- **API / Swagger** : http://localhost:8000/docs

> 💡 Pour une démo fluide, lancez `docker compose up --build` **une première
> fois à l'avance** afin que les téléchargements et l'index soient déjà en
> cache le jour J.

## Vérification

```bash
curl http://localhost:8000/api/v1/healthcheck
# {"status":"ok","service":"FFE Chess Agent API","version":"0.1.0","environment":"development"}
```

- Healthcheck : http://localhost:8000/api/v1/healthcheck
- Documentation interactive (Swagger) : http://localhost:8000/docs
- Interface Angular : http://localhost:4200

## Endpoints disponibles

| Méthode | Route                        | Description                                             |
| ------- | ---------------------------- | ------------------------------------------------------- |
| GET     | `/api/v1/healthcheck`        | État du service                                         |
| GET     | `/api/v1/moves/{fen}`        | Coups théoriques depuis Lichess (Opening Explorer)      |
| GET     | `/api/v1/evaluate/{fen}`     | Évaluation Stockfish de la position                     |
| GET     | `/api/v1/vector-search`      | Recherche RAG sur les ouvertures (Milvus + embeddings)  |
| GET     | `/api/v1/videos/{opening}`   | Vidéos YouTube explicatives pour une ouverture          |
| GET     | `/api/v1/assistant/{fen}`    | Agent complet (LangGraph) : coups + éval + contexte + vidéos |

### ⚠️ Passer un FEN dans l'URL

Un FEN contient des `/` et des espaces, incompatibles avec une URL brute.
Deux points à retenir :

- Les endpoints utilisent le convertisseur `{fen:path}` de FastAPI, qui
  capture les `/`.
- Les **espaces doivent être encodés en `%20`**. L'interface Swagger
  (`/docs`) et Postman le font automatiquement.

Exemple avec la position de départ :

```
FEN brut :   rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
URL       :   /api/v1/evaluate/rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR%20w%20KQkq%20-%200%201
```

```bash
# Évaluation de la position de départ
curl "http://localhost:8000/api/v1/evaluate/rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR%20w%20KQkq%20-%200%201"
```

Le plus simple pour tester reste **Swagger** : http://localhost:8000/docs
(colle le FEN brut dans le champ, l'encodage est géré).

## Recherche vectorielle (RAG) — construire l'index

Le POC utilise **Milvus Lite** : le moteur Milvus est embarqué directement dans
le backend (fichier local persistant), donc **aucun service Milvus séparé** à
lancer et aucune image supplémentaire à télécharger. La stack Milvus standalone
complète reste définie dans le `docker-compose.yml` (profil `milvus-server`)
pour un usage ultérieur.

Milvus Lite étant mono-processus, l'index est construit **automatiquement au
premier démarrage** du backend (voir `entrypoint.sh`), puis persiste dans le
volume `vectorstore`. Vous n'avez donc rien à faire pour la démo.

Pour le (re)construire manuellement si besoin (le backend étant arrêté) :

```bash
docker compose run --rm --no-deps backend python scripts/build_index.py
```

Le script lit `backend/data/openings.json`, découpe les articles en chunks,
les vectorise avec sentence-transformers, puis les insère dans Milvus.

> ⚠️ Le **premier build de l'image** télécharge PyTorch (CPU) et, au premier
> lancement du script, le modèle d'embedding (~470 Mo). C'est mis en cache
> ensuite (volumes `hf_cache` et `vectorstore`), donc les fois suivantes sont
> rapides.

Exemple de requête une fois l'index prêt :

```bash
curl "http://localhost:8000/api/v1/vector-search?query=ouverture%20combative%20contre%201.e4&k=3"
```

### Repasser au serveur Milvus (optionnel)

Si l'accès au registre Docker le permet, la stack Milvus standalone peut être
activée :

```bash
docker compose --profile milvus-server up
```

Il faut alors remettre la variable `MILVUS_DB_URI` du backend sur
`http://milvus-standalone:19530` (dans `docker-compose.yml`).

> Note : la variable s'appelle `MILVUS_DB_URI` et non `MILVUS_URI`, car
> pymilvus réserve `MILVUS_URI` (lue à l'import, elle doit être une URL http).

## Vidéos YouTube

L'endpoint `/videos/{opening}` recherche des vidéos explicatives via l'API
**YouTube Data v3**. Il faut une clé API (gratuite) : créez-la sur
[Google Cloud Console](https://console.cloud.google.com/apis/credentials),
activez « YouTube Data API v3 », puis renseignez `YOUTUBE_API_KEY` dans `.env`.

Chaque vidéo renvoie son lien `url` (watch) et son `embed_url` (lecteur
embarqué / streaming). Sans clé, l'endpoint répond `503` avec un message clair.

```bash
curl "http://localhost:8000/api/v1/videos/D%C3%A9fense%20sicilienne"
```

## Agent complet (LangGraph)

L'endpoint `/assistant/{fen}` orchestre tous les outils via **LangGraph** :

```
identify_moves (Lichess) ──► [théorique ?]
                               ├─ oui ─────────────► rag_context (Milvus) ─► videos (YouTube) ─► fin
                               └─ non ─► evaluate (Stockfish) ─► rag_context ─► videos ─► fin
```

Chaque nœud capture ses erreurs : si un outil est indisponible (ex. clé
YouTube absente), l'agent renvoie quand même une réponse partielle et liste le
problème dans `errors`. Exemple (position de départ) :

```bash
curl "http://localhost:8000/api/v1/assistant/rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR%20w%20KQkq%20-%200%201"
```

## Frontend Angular (interface + échiquier)

L'interface (Angular 17 + `ngx-chess-board`) affiche un échiquier interactif et
un panneau de recommandations de l'agent (coups théoriques, évaluation,
contexte, vidéos). À chaque coup joué, elle appelle `/api/v1/assistant/{fen}`.

> ℹ️ On utilise `ngx-chess-board@2.2.3` (dernière version correctement
> compilée ; la 3.0.0 publiée sur npm est cassée). D'où `--legacy-peer-deps`.

**En développement (rapide) :**

```bash
cd frontend
npm install --legacy-peer-deps
npm start          # ng serve → http://localhost:4200
```

**Via Docker (avec le reste du système) :**

```bash
docker compose up --build          # backend + mongodb + frontend
# front : http://localhost:4200   |   API : http://localhost:8000/docs
```

Le backend autorise le front via CORS (origines dans `CORS_ORIGINS`). L'URL de
l'API côté front est dans `frontend/src/environments/environment.ts`.

## Configuration

Toute la configuration passe par des variables d'environnement définies dans
`.env` (voir `.env.example`). Cela évite de coder en dur les ports, identifiants
et hôtes de services.

## Volumes persistants

Les données qui doivent survivre au redémarrage des conteneurs sont stockées
dans des volumes Docker nommés :

| Volume        | Contenu                                      |
| ------------- | -------------------------------------------- |
| `mongo_data`  | Base MongoDB                                 |
| `vectorstore` | Index Milvus Lite (ouvertures vectorisées)   |
| `hf_cache`    | Modèle d'embedding téléchargé                |

Vérifier qu'ils existent :

```bash
docker volume ls | findstr ffe-chess-agent      # Windows
docker volume ls | grep ffe-chess-agent          # macOS / Linux
docker volume inspect ffe-chess-agent_vectorstore
```

Tester la persistance (les données survivent à la recréation des conteneurs) :

```bash
docker compose down          # arrête et supprime les conteneurs (garde les volumes)
docker compose up            # au redémarrage : l'index n'est PAS reconstruit
```

> `docker compose down` conserve les volumes. Pour tout remettre à zéro (index,
> base, cache), utilisez `docker compose down -v` — le prochain démarrage
> reconstruira l'index automatiquement.

## Dépannage

| Symptôme | Cause probable / solution |
| --- | --- |
| `pull access denied` sur minio/etcd/milvus | Registre restreint aux images officielles. Normal : le POC utilise Milvus Lite, ces services ne démarrent pas (profil `milvus-server`). |
| `/moves` renvoie 502 | `LICHESS_TOKEN` absent ou invalide dans `.env`. |
| `videos` vide, `errors` mentionne YouTube | `YOUTUBE_API_KEY` absente/quota dépassé. Le reste de l'agent fonctionne quand même. |
| `port is already allocated` | Un service occupe déjà 4200/8000/27017. Fermez-le ou changez les ports dans `.env`. |
| Front affiche une erreur réseau | Le backend n'est pas démarré, ou CORS : vérifiez `CORS_ORIGINS`. |

## Feuille de route

- [x] **Étape 1** — Poste de travail : structure, Git, `docker-compose`, backend FastAPI + healthcheck
- [x] **Étape 2** — Endpoints `/moves` (Lichess) et `/evaluate` (Stockfish), validation FEN via python-chess
- [x] **Étape 3** — RAG : index Milvus (données ouvertures) + embeddings + endpoint `/vector-search`
- [x] **Étape 4** — Vidéos YouTube (`/videos`) + orchestration LangGraph (`/assistant`)
- [x] **Étape 5** — Interface Angular : échiquier interactif + panneau de recommandations de l'agent
- [x] **Étape 6** — Containerisation complète, index auto-construit, doc d'installation et guide de démo
- [ ] Étape 4 — Base vectorielle Milvus (données WikiChess)
- [ ] Étape 5 — Vidéos YouTube pertinentes
- [ ] Étape 6 — Orchestration de l'agent avec LangGraph
- [ ] Étape 7 — Interface Angular (échiquier interactif)
