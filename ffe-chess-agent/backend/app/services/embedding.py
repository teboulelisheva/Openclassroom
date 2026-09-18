"""Service de vectorisation de texte via sentence-transformers.

Le modèle est chargé à la demande (lazy) et réutilisé, car son chargement
initial (téléchargement + mise en mémoire) est coûteux.
"""

from functools import lru_cache

from app.core.config import settings


class EmbeddingService:
    """Encapsule un modèle sentence-transformers pour produire des vecteurs."""

    def __init__(self, model_name: str = settings.EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._model = None  # chargé au premier appel

    def _get_model(self):
        if self._model is None:
            # Import local : évite de charger torch tant qu'on n'embarque rien.
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    @property
    def dimension(self) -> int:
        """Dimension des vecteurs produits par le modèle."""
        return self._get_model().get_sentence_embedding_dimension()

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Vectorise une liste de textes.

        Les vecteurs sont normalisés (norme 1) pour être cohérents avec la
        métrique COSINE utilisée dans Milvus.
        """
        model = self._get_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings.tolist()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    """Instance unique partagée du service d'embeddings."""
    return EmbeddingService()
