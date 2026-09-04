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
├── backend/                # API FastAPI
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py         # Point d'entrée
│       ├── core/config.py  # Configuration (variables d'env)
│       └── api/v1/endpoints/health.py
└── frontend/               # Application Angular (étape ultérieure)
```

## Prérequis

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/products/docker-desktop/) et Docker Compose

## Démarrage rapide

```bash
# 1. Cloner le dépôt
git clone <url-du-depot>
cd ffe-chess-agent

# 2. Créer le fichier de configuration
cp .env.example .env

# 3. Lancer uniquement le backend (rapide, étape 1)
docker compose up --build backend

# ou l'ensemble des services
docker compose up --build
```

## Vérification

Une fois le backend démarré :

- Healthcheck : http://localhost:8000/api/v1/healthcheck
- Documentation interactive (Swagger) : http://localhost:8000/docs

```bash
curl http://localhost:8000/api/v1/healthcheck
# {"status":"ok","service":"FFE Chess Agent API","version":"0.1.0","environment":"development"}
```

## Configuration

Toute la configuration passe par des variables d'environnement définies dans
`.env` (voir `.env.example`). Cela évite de coder en dur les ports, identifiants
et hôtes de services.

## Feuille de route

- [x] **Étape 1** — Poste de travail : structure, Git, `docker-compose`, backend FastAPI + healthcheck
- [ ] Étape 2 — Intégration Stockfish et lecture des positions (FEN)
- [ ] Étape 3 — Connexion aux APIs Lichess
- [ ] Étape 4 — Base vectorielle Milvus (données WikiChess)
- [ ] Étape 5 — Vidéos YouTube pertinentes
- [ ] Étape 6 — Orchestration de l'agent avec LangGraph
- [ ] Étape 7 — Interface Angular (échiquier interactif)
