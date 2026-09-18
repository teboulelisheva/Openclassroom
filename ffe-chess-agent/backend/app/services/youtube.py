"""Service de recherche de vidéos explicatives via l'API YouTube Data v3.

Encapsule les appels à l'API YouTube. Gère l'absence de clé, les erreurs de
quota et le cas « aucune vidéo trouvée ».
"""

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings


class YouTubeError(Exception):
    """Erreur lors de la communication avec l'API YouTube."""


class YouTubeService:
    """Client de recherche de vidéos YouTube pertinentes pour une ouverture."""

    def __init__(
        self,
        api_key: str = settings.YOUTUBE_API_KEY,
        max_results: int = settings.YOUTUBE_MAX_RESULTS,
        relevance_language: str = settings.YOUTUBE_RELEVANCE_LANGUAGE,
    ) -> None:
        self.api_key = api_key
        self.max_results = max_results
        self.relevance_language = relevance_language

    def _build_query(self, opening: str) -> str:
        """Construit une requête de recherche ciblée pour une ouverture."""
        return f"{opening} chess opening tutorial explanation échecs"

    def search_videos(self, opening: str) -> list[dict]:
        """Recherche des vidéos YouTube pertinentes pour une ouverture.

        Returns:
            Liste de vidéos (dicts) : titre, chaîne, url, url d'intégration
            (embed), miniature, date, description.

        Raises:
            YouTubeError: clé absente, quota dépassé ou erreur API.
        """
        if not self.api_key:
            raise YouTubeError(
                "Clé API YouTube manquante. Renseignez YOUTUBE_API_KEY dans le .env."
            )

        youtube = build("youtube", "v3", developerKey=self.api_key, cache_discovery=False)

        try:
            response = (
                youtube.search()
                .list(
                    q=self._build_query(opening),
                    part="snippet",
                    type="video",  # uniquement des vidéos (pas de chaînes/playlists)
                    maxResults=self.max_results,
                    order="relevance",
                    relevanceLanguage=self.relevance_language,
                    safeSearch="strict",  # contenu approprié (public jeune)
                    videoEmbeddable="true",  # seulement les vidéos intégrables (streaming)
                )
                .execute()
            )
        except HttpError as exc:
            # 403 + quotaExceeded = quota journalier épuisé
            reason = getattr(exc, "reason", "") or str(exc)
            if exc.resp.status == 403 and "quota" in str(exc).lower():
                raise YouTubeError(
                    "Quota de l'API YouTube dépassé. Réessayez demain ou augmentez le quota."
                ) from exc
            raise YouTubeError(f"Erreur de l'API YouTube : {reason}") from exc

        items = response.get("items", [])
        videos: list[dict] = []
        for item in items:
            video_id = item.get("id", {}).get("videoId")
            if not video_id:
                continue
            snippet = item.get("snippet", {})
            thumbnails = snippet.get("thumbnails", {})
            videos.append(
                {
                    "video_id": video_id,
                    "title": snippet.get("title", ""),
                    "channel": snippet.get("channelTitle", ""),
                    "description": snippet.get("description", ""),
                    "published_at": snippet.get("publishedAt", ""),
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "embed_url": f"https://www.youtube.com/embed/{video_id}",
                    "thumbnail": thumbnails.get("high", {}).get("url", ""),
                }
            )
        return videos


# Instance partagée réutilisée par les endpoints et le graphe.
youtube_service = YouTubeService()
