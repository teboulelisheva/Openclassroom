"""Endpoint d'évaluation de position via Stockfish."""

from fastapi import APIRouter, HTTPException

from app.schemas.chess import EvaluationResponse
from app.services.stockfish_engine import StockfishError, get_stockfish_service

router = APIRouter()


@router.get("/evaluate/{fen:path}", response_model=EvaluationResponse, tags=["chess"])
async def evaluate_position(fen: str) -> EvaluationResponse:
    """Évalue une position FEN avec Stockfish.

    Utile lorsque la partie s'écarte de la théorie : on renvoie une
    évaluation en centipions (ou un mat forcé) et le meilleur coup trouvé.

    Le convertisseur `{fen:path}` capture les `/` du FEN ; les espaces
    doivent être encodés (%20).
    """
    service = get_stockfish_service()
    try:
        result = service.evaluate(fen)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"FEN invalide : {exc}") from exc
    except StockfishError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return EvaluationResponse(fen=fen, **result)
