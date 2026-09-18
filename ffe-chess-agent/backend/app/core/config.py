"""Configuration de l'application, chargée depuis les variables d'environnement."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de l'application.

    Chaque champ peut être surchargé par une variable d'environnement
    du même nom (ex: ENVIRONMENT=production).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- API ---
    PROJECT_NAME: str = "FFE Chess Agent API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Origines autorisées pour le front Angular (CORS), séparées par des virgules.
    CORS_ORIGINS: str = "http://localhost:4200,http://localhost"

    # --- Services externes (préparés pour les étapes suivantes) ---
    MONGO_URI: str = "mongodb://root:changeme@mongodb:27017"
    MONGO_DB: str = "ffe_chess"
    MILVUS_HOST: str = "milvus-standalone"
    MILVUS_PORT: int = 19530

    # --- RAG : recherche vectorielle ---
    # ⚠️ NE PAS nommer cette variable "MILVUS_URI" : pymilvus lit lui-même
    # la variable d'environnement MILVUS_URI à l'import et exige une forme
    # http://... — un chemin de fichier la ferait planter. D'où "MILVUS_DB_URI".
    #   - Milvus Lite (par défaut) : chemin de fichier .db, moteur embarqué.
    #   - Serveur Milvus (Docker) : "http://milvus-standalone:19530".
    MILVUS_DB_URI: str = "/vectorstore/milvus.db"
    MILVUS_COLLECTION: str = "chess_openings"
    # Modèle d'embedding léger et multilingue (gère le français).
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # --- YouTube Data API v3 ---
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_MAX_RESULTS: int = 5
    YOUTUBE_RELEVANCE_LANGUAGE: str = "fr"

    # --- Lichess (Opening Explorer) ---
    LICHESS_EXPLORER_URL: str = "https://explorer.lichess.ovh/lichess"
    LICHESS_TIMEOUT: float = 10.0
    LICHESS_MAX_MOVES: int = 12
    # User-Agent recommandé par Lichess pour identifier l'application
    LICHESS_USER_AGENT: str = "FFE-Chess-Agent/0.1 (POC OpenClassrooms)"

    # --- Stockfish ---
    # Chemin du binaire dans l'image Docker Debian (apt install stockfish)
    STOCKFISH_PATH: str = "/usr/games/stockfish"
    STOCKFISH_DEPTH: int = 15
    STOCKFISH_THREADS: int = 1
    STOCKFISH_HASH_MB: int = 128


settings = Settings()
