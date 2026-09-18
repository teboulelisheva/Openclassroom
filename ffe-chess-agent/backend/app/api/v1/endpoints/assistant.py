"""Endpoint de l'agent complet : orchestration LangGraph de tous les outils."""

import chess
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.graph import agent_graph

router = APIRouter()


class AssistantResponse(BaseModel):
    """Réponse agrégée de l'agent pour une position."""

    fen: str
    opening: str | None = None
    is_theoretical: bool = False
    moves: list[dict] = Field(default_factory=list)
    evaluation: dict | None = None
    context: list[dict] = Field(default_factory=list)
    videos: list[dict] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list, description="Outils indisponibles (réponse partielle).")


@router.get("/assistant/{fen:path}", response_model=AssistantResponse, tags=["agent"])
async def assistant(fen: str) -> AssistantResponse:
    """Agent complet : pour une position FEN, orchestre via LangGraph les coups
    théoriques (Lichess), l'évaluation (Stockfish si hors théorie), le contexte
    (Milvus) et les vidéos explicatives (YouTube), puis renvoie le tout.

    Les erreurs d'un outil (ex: clé YouTube absente) n'interrompent pas
    l'agent : elles sont listées dans `errors` et la réponse reste utilisable.
    """
    try:
        chess.Board(fen)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"FEN invalide : {exc}") from exc

    result = await agent_graph.ainvoke({"fen": fen})
    return AssistantResponse(fen=fen, **{k: v for k, v in result.items() if k != "fen"})
