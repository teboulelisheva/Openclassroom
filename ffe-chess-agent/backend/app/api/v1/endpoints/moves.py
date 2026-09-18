"""Endpoint des coups théoriques (théorie des ouvertures via Lichess)."""

import chess
from fastapi import APIRouter, HTTPException

from app.schemas.chess import MovesResponse, OpeningInfo, TheoreticalMove
from app.services.lichess import LichessError, lichess_service

router = APIRouter()


@router.get("/moves/{fen:path}", response_model=MovesResponse, tags=["chess"])
async def get_theoretical_moves(fen: str) -> MovesResponse:
    """Retourne les coups théoriques possibles depuis une position FEN.

    Le convertisseur `{fen:path}` permet de capturer les `/` présents dans
    un FEN. Les espaces doivent être encodés (%20) — Swagger le fait
    automatiquement.

    - Si des coups théoriques existent, ils sont renvoyés avec leurs
      statistiques (victoires Blancs / nulles / Noirs).
    - Sinon, la position est « hors théorie » : on invite à utiliser
      l'endpoint /evaluate.
    """
    # 1. Validation de la position avec python-chess.
    try:
        chess.Board(fen)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"FEN invalide : {exc}") from exc

    # 2. Appel à Lichess (erreurs réseau/timeout/429 → 502 Bad Gateway).
    try:
        data = await lichess_service.get_opening_moves(fen)
    except LichessError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    # 3. Mise en forme de la réponse.
    raw_moves = data.get("moves", [])
    moves = [
        TheoreticalMove(
            uci=m["uci"],
            san=m["san"],
            white=m.get("white", 0),
            draws=m.get("draws", 0),
            black=m.get("black", 0),
            total=m.get("white", 0) + m.get("draws", 0) + m.get("black", 0),
        )
        for m in raw_moves
    ]

    opening_raw = data.get("opening")
    opening = OpeningInfo(**opening_raw) if opening_raw else None
    total_games = sum(m.total for m in moves)
    is_theoretical = len(moves) > 0

    return MovesResponse(
        fen=fen,
        is_theoretical=is_theoretical,
        opening=opening,
        total_games=total_games,
        moves=moves,
        message=(
            None
            if is_theoretical
            else "Position hors théorie : aucun coup connu. Utilisez /api/v1/evaluate pour une analyse Stockfish."
        ),
    )
