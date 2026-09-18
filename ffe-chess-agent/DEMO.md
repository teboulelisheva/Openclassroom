# Guide de démonstration — FFE Chess Agent

Scénario de démonstration client du POC. Durée indicative : **10-15 min**.

---

## 0. Avant la démo (à faire à l'avance)

```bash
cp .env.example .env      # renseigner LICHESS_TOKEN et YOUTUBE_API_KEY
docker compose up --build
```

Laissez ce **premier lancement se terminer entièrement** (téléchargement du
modèle d'embedding + construction de l'index Milvus) pour que tout soit en
cache. Vérifiez ensuite :

- http://localhost:4200 → l'échiquier s'affiche
- http://localhost:8000/docs → la doc Swagger répond

Gardez un onglet sur l'interface et un onglet sur Swagger.

---

## 1. Le pitch (1 min)

> « Cet agent accompagne les jeunes joueurs dans l'apprentissage des ouvertures.
> À chaque coup joué, il combine quatre sources : la théorie issue de millions
> de parties (Lichess), un moteur d'analyse (Stockfish), une base de
> connaissances sur les ouvertures (recherche vectorielle Milvus), et des
> vidéos explicatives (YouTube) — le tout orchestré par un agent LangGraph. »

---

## 2. Démonstration sur l'interface (5 min)

Jouez les coups directement sur l'échiquier. À chaque coup, le panneau de
droite se met à jour.

### a) Une ouverture classique — la Sicilienne
Jouez **1.e4 c5**.
- L'ouverture est identifiée (« Sicilian Defense »).
- Les coups théoriques les plus joués s'affichent.
- Le panneau « Le savais-tu ? » donne le contexte (contre-jeu aile dame…).
- Des vidéos explicatives apparaissent.

### b) Continuer dans la théorie
Jouez **2.Cf3 d6 3.d4** : l'agent suit et met à jour ouverture + contexte.

### c) Sortir de la théorie
Jouez un coup inhabituel (ex. **1.e4 e5 2.Da5?!**).
- L'agent détecte que la position est **hors théorie**.
- Il bascule sur **Stockfish** : évaluation en centipions + meilleur coup.

Message clé : *l'agent adapte automatiquement sa réponse selon que la position
est connue de la théorie ou non.*

---

## 3. Démonstration technique sur Swagger (3 min)

Sur http://localhost:8000/docs, montrez que chaque brique est un service
indépendant et testable.

### Positions FEN prêtes à coller

**Position de départ**
```
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1
```

**Défense sicilienne (après 1.e4 c5)**
```
rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2
```

**Ouverture italienne (après 1.e4 e5 2.Cf3 Cc6 3.Fc4)**
```
r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3
```

**Position hors théorie (déclenche Stockfish)**
```
rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2
```

### Endpoints à montrer
- `GET /api/v1/moves/{fen}` → coups théoriques (Lichess).
- `GET /api/v1/evaluate/{fen}` → évaluation Stockfish.
- `GET /api/v1/vector-search?query=ouverture combative contre 1.e4` → RAG Milvus.
- `GET /api/v1/videos/Défense sicilienne` → vidéos YouTube.
- `GET /api/v1/assistant/{fen}` → **l'agent complet** qui agrège tout.

---

## 4. Points d'architecture à souligner (2 min)

- **Agent LangGraph** : orchestration avec aiguillage conditionnel (théorie →
  Stockfish ignoré ; hors théorie → Stockfish appelé) et robustesse (un outil
  en panne n'interrompt pas l'agent, cf. champ `errors`).
- **Containerisation** : tout démarre avec `docker compose up`, données
  persistées dans des volumes.
- **Arbitrages assumés** : Milvus Lite (contrainte de registre Docker),
  `ngx-chess-board` épinglé, torch CPU-only, adaptation à l'API Lichess.

---

## 5. Limites et perspectives (1 min)

- Jeu de données réduit à 8 ouvertures (rédigées pour le POC) → à étendre.
- L'agent **agrège** les données ; une évolution naturelle est un **nœud de
  synthèse LLM** qui rédigerait une explication pédagogique (le graphe est déjà
  prêt à l'accueillir).
- Extension possible : historique de partie, multi-langues, plus de sources.
