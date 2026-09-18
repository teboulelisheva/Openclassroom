"""Endpoint de recherche vectorielle (RAG) sur les ouvertures d'échecs."""

from fastapi import APIRouter, HTTPException, Query

from app.schemas.chess import VectorSearchResponse, VectorSearchResult
from app.services.embedding import get_embedding_service
from app.services.milvus_service import MilvusError, get_milvus_service

router = APIRouter()


@router.get("/vector-search", response_model=VectorSearchResponse, tags=["rag"])
async def vector_search(
    query: str = Query(..., description="Question ou nom d'ouverture (ex: 'à quoi sert la sicilienne ?').", min_length=2),
    k: int = Query(3, ge=1, le=10, description="Nombre d'extraits à retourner."),
) -> VectorSearchResponse:
    """Recherche des informations pertinentes sur une ouverture.

    La requête textuelle est vectorisée puis comparée aux extraits indexés
    dans Milvus par similarité sémantique. Retourne les k extraits les plus
    proches, avec leur ouverture, leur code ECO et un score de similarité.
    """
    embedding_service = get_embedding_service()
    milvus_service = get_milvus_service()

    # 1. Vectorisation de la requête.
    try:
        query_vector = embedding_service.embed([query])[0]
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"Modèle d'embedding indisponible : {exc}",
        ) from exc

    # 2. Recherche dans Milvus.
    try:
        hits = milvus_service.search(query_vector, k=k)
    except MilvusError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    results = [VectorSearchResult(**hit) for hit in hits]
    return VectorSearchResponse(query=query, results=results)
