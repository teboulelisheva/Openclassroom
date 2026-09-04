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

    # --- Services externes (préparés pour les étapes suivantes) ---
    MONGO_URI: str = "mongodb://root:changeme@mongodb:27017"
    MONGO_DB: str = "ffe_chess"
    MILVUS_HOST: str = "milvus-standalone"
    MILVUS_PORT: int = 19530


settings = Settings()
