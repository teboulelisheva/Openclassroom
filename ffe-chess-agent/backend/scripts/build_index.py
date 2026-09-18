"""Construit l'index vectoriel Milvus à partir des articles d'ouvertures.

Étapes :
    1. charge les articles depuis data/openings.json
    2. découpe chaque article en chunks (avec chevauchement)
    3. vectorise les chunks avec sentence-transformers
    4. (ré)crée la collection Milvus et y insère les vecteurs

Usage (dans le conteneur backend) :
    docker compose exec backend python scripts/build_index.py
"""

import json
import sys
from pathlib import Path

# Rend le package `app` importable quand le script est lancé directement.
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.embedding import get_embedding_service  # noqa: E402
from app.services.milvus_service import get_milvus_service  # noqa: E402

DATA_PATH = BACKEND_DIR / "data" / "openings.json"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Découpe un texte en morceaux d'environ `size` caractères.

    On tente de couper sur une espace pour ne pas casser un mot, et on
    conserve un chevauchement `overlap` entre chunks pour préserver le
    contexte à la frontière.
    """
    text = " ".join(text.split())  # normalise les espaces
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + size
        if end < len(text):
            # recule jusqu'à la dernière espace pour ne pas couper un mot
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        chunks.append(text[start:end].strip())
        start = end - overlap
    return [c for c in chunks if c]


def main() -> None:
    print(f"Lecture des données : {DATA_PATH}")
    articles = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    print(f"{len(articles)} articles chargés.")

    embedding_service = get_embedding_service()
    milvus_service = get_milvus_service()

    print(f"Chargement du modèle d'embedding : {embedding_service.model_name} ...")
    dim = embedding_service.dimension
    print(f"Dimension des vecteurs : {dim}")

    print("(Ré)création de la collection Milvus ...")
    milvus_service.recreate_collection(dim)

    rows: list[dict] = []
    for article in articles:
        chunks = chunk_text(article["content"])
        vectors = embedding_service.embed(chunks)
        for chunk, vector in zip(chunks, vectors):
            rows.append(
                {
                    "vector": vector,
                    "text": chunk,
                    "opening": article["opening"],
                    "eco": article.get("eco", ""),
                    "source": article.get("source", ""),
                }
            )
        print(f"  - {article['opening']}: {len(chunks)} chunk(s)")

    print(f"Insertion de {len(rows)} chunks dans Milvus ...")
    milvus_service.insert(rows)
    print(f"Terminé. Collection '{milvus_service.collection}' prête avec {len(rows)} vecteurs.")


if __name__ == "__main__":
    main()
