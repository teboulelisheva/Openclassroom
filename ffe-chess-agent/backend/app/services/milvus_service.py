"""Service d'accès à la base vectorielle Milvus.

Utilise l'API `MilvusClient` de pymilvus, compatible aussi bien avec un
serveur Milvus (Docker) qu'avec Milvus Lite (fichier local, pour les tests).
"""

from functools import lru_cache

from pymilvus import DataType, MilvusClient

from app.core.config import settings

# Champs texte renvoyés par une recherche.
OUTPUT_FIELDS = ["text", "opening", "eco", "source"]


class MilvusError(Exception):
    """Erreur lors de la communication avec Milvus."""


class MilvusService:
    """Client Milvus pour la collection des ouvertures d'échecs."""

    def __init__(
        self,
        uri: str = settings.MILVUS_DB_URI,
        collection: str = settings.MILVUS_COLLECTION,
    ) -> None:
        self.uri = uri
        self.collection = collection
        self._client: MilvusClient | None = None
        self._loaded = False  # collection chargée en mémoire ?

    def get_client(self) -> MilvusClient:
        """Connexion à la demande (lazy)."""
        if self._client is None:
            try:
                self._client = MilvusClient(uri=self.uri)
            except Exception as exc:  # noqa: BLE001
                raise MilvusError(f"Connexion à Milvus impossible ({self.uri}) : {exc}") from exc
        return self._client

    def recreate_collection(self, dim: int) -> None:
        """(Re)crée la collection avec le schéma attendu.

        Supprime la collection existante si elle existe : à utiliser
        uniquement dans le script de build.
        """
        client = self.get_client()
        if client.has_collection(self.collection):
            client.drop_collection(self.collection)

        schema = client.create_schema(auto_id=True, enable_dynamic_field=False)
        schema.add_field("id", DataType.INT64, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=dim)
        schema.add_field("text", DataType.VARCHAR, max_length=4000)
        schema.add_field("opening", DataType.VARCHAR, max_length=200)
        schema.add_field("eco", DataType.VARCHAR, max_length=50)
        schema.add_field("source", DataType.VARCHAR, max_length=500)

        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            metric_type="COSINE",
            index_type="AUTOINDEX",
        )
        client.create_collection(self.collection, schema=schema, index_params=index_params)

    def insert(self, rows: list[dict]) -> None:
        """Insère des lignes (chaque ligne = un chunk vectorisé)."""
        client = self.get_client()
        client.insert(self.collection, rows)
        client.flush(self.collection)

    def search(self, query_vector: list[float], k: int = 3) -> list[dict]:
        """Recherche les k chunks les plus proches d'un vecteur de requête.

        Returns:
            Liste de dicts : {opening, eco, text, source, score}.

        Raises:
            MilvusError: si la collection n'existe pas ou en cas d'échec.
        """
        client = self.get_client()
        if not client.has_collection(self.collection):
            raise MilvusError(
                f"La collection '{self.collection}' n'existe pas. "
                "Lancez d'abord le script d'indexation (scripts/build_index.py)."
            )

        try:
            # Une collection persistée est à l'état "released" à l'ouverture
            # dans un nouveau processus : il faut la charger avant de chercher.
            if not self._loaded:
                client.load_collection(self.collection)
                self._loaded = True

            results = client.search(
                collection_name=self.collection,
                data=[query_vector],
                limit=k,
                output_fields=OUTPUT_FIELDS,
                search_params={"metric_type": "COSINE"},
            )
        except Exception as exc:  # noqa: BLE001
            raise MilvusError(f"Recherche Milvus échouée : {exc}") from exc

        hits = results[0]  # une seule requête → un seul jeu de résultats
        return [
            {
                "opening": hit["entity"].get("opening", ""),
                "eco": hit["entity"].get("eco", ""),
                "text": hit["entity"].get("text", ""),
                "source": hit["entity"].get("source", ""),
                "score": float(hit["distance"]),
            }
            for hit in hits
        ]


@lru_cache(maxsize=1)
def get_milvus_service() -> MilvusService:
    """Instance unique partagée du service Milvus."""
    return MilvusService()
