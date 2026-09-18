"""Service d'évaluation de position via le moteur Stockfish.

Encapsule l'usage de la bibliothèque `stockfish` pour évaluer une position
donnée au format FEN. La position est d'abord validée avec python-chess.
"""

from functools import lru_cache

import chess
from stockfish import Stockfish

from app.core.config import settings


class StockfishError(Exception):
    """Erreur lors de l'évaluation avec Stockfish."""


class StockfishService:
    """Wrapper autour du moteur Stockfish."""

    def __init__(
        self,
        path: str = settings.STOCKFISH_PATH,
        depth: int = settings.STOCKFISH_DEPTH,
        threads: int = settings.STOCKFISH_THREADS,
        hash_mb: int = settings.STOCKFISH_HASH_MB,
    ) -> None:
        self.path = path
        self.depth = depth
        self.parameters = {"Threads": threads, "Hash": hash_mb}
        self._engine: Stockfish | None = None

    def _get_engine(self) -> Stockfish:
        """Instancie le moteur à la demande (lazy init)."""
        if self._engine is None:
            try:
                self._engine = Stockfish(
                    path=self.path,
                    depth=self.depth,
                    parameters=self.parameters,
                )
            except Exception as exc:  # binaire introuvable, etc.
                raise StockfishError(
                    f"Impossible de démarrer Stockfish depuis '{self.path}'. "
                    "Vérifiez que le binaire est installé."
                ) from exc
        return self._engine

    def evaluate(self, fen: str) -> dict:
        """Évalue une position et renvoie l'analyse.

        Args:
            fen: la position au format FEN (supposée déjà validée en amont,
                mais revalidée ici par sécurité).

        Returns:
            dict avec 'type', 'value', 'best_move', 'depth', 'interpretation'.

        Raises:
            ValueError: si le FEN est invalide.
            StockfishError: si le moteur échoue.
        """
        # Validation stricte via python-chess (lève ValueError si invalide).
        chess.Board(fen)

        engine = self._get_engine()
        if not engine.is_fen_valid(fen):
            raise ValueError("FEN rejeté par le moteur Stockfish.")

        engine.set_fen_position(fen)
        evaluation = engine.get_evaluation()  # {"type": "cp"|"mate", "value": int}
        best_move = engine.get_best_move()

        eval_type = evaluation["type"]
        value = evaluation["value"]

        return {
            "type": eval_type,
            "value": value,
            "best_move": best_move,
            "depth": self.depth,
            "interpretation": self._interpret(eval_type, value),
        }

    @staticmethod
    def _interpret(eval_type: str, value: int) -> str:
        """Traduit l'évaluation brute en phrase compréhensible."""
        if eval_type == "mate":
            camp = "les Blancs" if value > 0 else "les Noirs"
            return f"Mat forcé pour {camp} en {abs(value)} coup(s)."

        # eval_type == "cp" (centipions) : positif = avantage Blancs.
        pions = value / 100
        if abs(value) < 30:
            return "Position équilibrée."
        camp = "Blancs" if value > 0 else "Noirs"
        return f"Avantage {camp} d'environ {abs(pions):.2f} pion(s)."


@lru_cache(maxsize=1)
def get_stockfish_service() -> StockfishService:
    """Renvoie une instance unique du service (réutilise le moteur)."""
    return StockfishService()
