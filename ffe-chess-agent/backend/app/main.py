"""Point d'entrée de l'application FastAPI (POC Agent IA ouvertures échecs - FFE)."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import assistant, evaluate, health, moves, vector_search, videos
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="POC d'un agent IA d'accompagnement à l'apprentissage des ouvertures aux échecs.",
)

# CORS : autorise le front Angular à appeler l'API depuis le navigateur.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes versionnées : tout est monté sous /api/v1
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(moves.router, prefix=settings.API_V1_PREFIX)
app.include_router(evaluate.router, prefix=settings.API_V1_PREFIX)
app.include_router(vector_search.router, prefix=settings.API_V1_PREFIX)
app.include_router(videos.router, prefix=settings.API_V1_PREFIX)
app.include_router(assistant.router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["root"])
async def root() -> dict:
    """Message d'accueil et lien vers la documentation interactive."""
    return {
        "message": f"Bienvenue sur l'API {settings.PROJECT_NAME}",
        "docs": "/docs",
        "healthcheck": f"{settings.API_V1_PREFIX}/healthcheck",
    }
