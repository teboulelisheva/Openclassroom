"""Service d'accès à l'explorateur d'ouvertures de Lichess.

Encapsule les appels HTTP vers l'API publique de Lichess afin de garder
les endpoints FastAPI propres. Gère les timeouts, les erreurs réseau et
la limite de requêtes (HTTP 429).
"""

import httpx

from app.core.config import settings


class LichessError(Exception):
    """Erreur lors de la communication avec l'API Lichess."""


class LichessService:
    """Client pour l'endpoint 'Opening Explorer' de Lichess."""

    def __init__(
        self,
        base_url: str = settings.LICHESS_EXPLORER_URL,
        timeout: float = settings.LICHESS_TIMEOUT,
        max_moves: int = settings.LICHESS_MAX_MOVES,
        user_agent: str = settings.LICHESS_USER_AGENT,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.max_moves = max_moves
        self.headers = {"User-Agent": user_agent}

    async def get_opening_moves(self, fen: str) -> dict:
        """Interroge Lichess pour les coups théoriques d'une position.

        Args:
            fen: la position au format FEN (supposée déjà validée).

        Returns:
            Le JSON brut renvoyé par Lichess (clés 'opening', 'moves', ...).

        Raises:
            LichessError: en cas de timeout, d'erreur réseau ou de rate-limit.
        """
        params = {"fen": fen, "moves": self.max_moves}
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                response = await client.get(self.base_url, params=params)
        except httpx.TimeoutException as exc:
            raise LichessError("Délai dépassé lors de l'appel à Lichess.") from exc
        except httpx.HTTPError as exc:
            raise LichessError(f"Erreur réseau vers Lichess : {exc}") from exc

        # Lichess limite le nombre de requêtes : renvoie 429 si dépassé.
        if response.status_code == 429:
            raise LichessError(
                "Limite de requêtes Lichess atteinte (HTTP 429). Réessayez plus tard."
            )
        if response.status_code >= 400:
            raise LichessError(
                f"Réponse inattendue de Lichess (HTTP {response.status_code})."
            )

        try:
            return response.json()
        except ValueError as exc:
            raise LichessError("Réponse Lichess illisible (JSON invalide).") from exc


# Instance partagée réutilisée par les endpoints.
lichess_service = LichessService()
