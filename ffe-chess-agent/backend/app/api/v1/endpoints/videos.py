"""Endpoint de recherche de vidéos explicatives YouTube pour une ouverture."""

from fastapi import APIRouter, HTTPException

from app.schemas.chess import Video, VideosResponse
from app.services.youtube import YouTubeError, youtube_service

router = APIRouter()


@router.get("/videos/{opening}", response_model=VideosResponse, tags=["videos"])
async def get_videos(opening: str) -> VideosResponse:
    """Retourne des vidéos YouTube pertinentes pour une ouverture donnée.

    Exemple : `/api/v1/videos/Défense sicilienne` (les espaces sont encodés
    automatiquement par Swagger).

    Chaque vidéo inclut son lien `url` (watch) et son `embed_url` (pour un
    lecteur embarqué / streaming dans le front). Si aucune vidéo n'est
    trouvée, la réponse le signale via `message`.
    """
    try:
        raw_videos = youtube_service.search_videos(opening)
    except YouTubeError as exc:
        # Clé absente ou quota dépassé → 503 (service momentanément indisponible)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    videos = [Video(**v) for v in raw_videos]
    return VideosResponse(
        opening=opening,
        count=len(videos),
        videos=videos,
        message=None if videos else f"Aucune vidéo trouvée pour « {opening} ».",
    )
