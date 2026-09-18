"""Route de vérification de l'état du service."""

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/healthcheck", tags=["health"])
async def healthcheck() -> dict:
    """Vérifie que l'API répond correctement.

    Utilisé par Docker / la supervision pour s'assurer que le
    conteneur est opérationnel.
    """
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
