"""Point d'entrée de l'application FastAPI (POC Agent IA ouvertures échecs - FFE)."""

from fastapi import FastAPI

from app.api.v1.endpoints import health
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="POC d'un agent IA d'accompagnement à l'apprentissage des ouvertures aux échecs.",
)

# Routes versionnées : tout est monté sous /api/v1
app.include_router(health.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"])
async def root() -> dict:
    """Message d'accueil et lien vers la documentation interactive."""
    return {
        "message": f"Bienvenue sur l'API {settings.PROJECT_NAME}",
        "docs": "/docs",
        "healthcheck": f"{settings.API_V1_PREFIX}/healthcheck",
    }
