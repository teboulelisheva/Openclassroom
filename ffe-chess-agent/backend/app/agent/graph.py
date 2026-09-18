"""Orchestration de l'agent d'ouvertures via LangGraph.

Le graphe prend une position (FEN) et enchaîne les outils du projet :

    identify_moves (Lichess)
        │
        ├─ si position théorique ─────────────┐
        │                                     ▼
        └─ sinon ─► evaluate (Stockfish) ─► rag_context (Milvus) ─► videos (YouTube) ─► END

Chaque nœud capture ses propres erreurs et remplit un champ `errors`, afin que
l'agent renvoie toujours une réponse partielle utile même si un outil externe
(clé YouTube absente, quota, etc.) est indisponible.
"""

import asyncio
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.services.lichess import LichessError, lichess_service
from app.services.milvus_service import MilvusError, get_milvus_service
from app.services.stockfish_engine import StockfishError, get_stockfish_service
from app.services.youtube import YouTubeError, youtube_service


class AgentState(TypedDict, total=False):
    """État partagé qui circule entre les nœuds du graphe."""

    fen: str
    opening: str | None
    is_theoretical: bool
    moves: list[dict]
    evaluation: dict | None
    context: list[dict]
    videos: list[dict]
    errors: list[str]


async def node_identify_moves(state: AgentState) -> AgentState:
    """Interroge Lichess : coups théoriques + nom de l'ouverture."""
    errors = state.get("errors", [])
    try:
        data = await lichess_service.get_opening_moves(state["fen"])
        opening_info = data.get("opening") or {}
        raw = data.get("moves", [])
        state["opening"] = opening_info.get("name")
        state["moves"] = [
            {"san": m.get("san"), "uci": m.get("uci")} for m in raw
        ]
        state["is_theoretical"] = len(raw) > 0
    except LichessError as exc:
        state["moves"] = []
        state["is_theoretical"] = False
        state["opening"] = state.get("opening")
        errors.append(f"lichess: {exc}")
    state["errors"] = errors
    return state


async def node_evaluate(state: AgentState) -> AgentState:
    """Évalue la position avec Stockfish (seulement si hors théorie)."""
    errors = state.get("errors", [])
    try:
        service = get_stockfish_service()
        state["evaluation"] = await asyncio.to_thread(service.evaluate, state["fen"])
    except (StockfishError, ValueError) as exc:
        state["evaluation"] = None
        errors.append(f"stockfish: {exc}")
    state["errors"] = errors
    return state


async def node_rag_context(state: AgentState) -> AgentState:
    """Recherche du contexte textuel dans Milvus sur l'ouverture identifiée."""
    errors = state.get("errors", [])
    query = state.get("opening") or "ouverture d'échecs"
    try:
        # Import local pour éviter de charger le modèle si ce nœud n'est pas utilisé.
        from app.services.embedding import get_embedding_service

        vector = await asyncio.to_thread(
            lambda: get_embedding_service().embed([query])[0]
        )
        hits = await asyncio.to_thread(get_milvus_service().search, vector, 3)
        state["context"] = hits
    except (MilvusError, Exception) as exc:  # noqa: BLE001
        state["context"] = []
        errors.append(f"rag: {exc}")
    state["errors"] = errors
    return state


async def node_videos(state: AgentState) -> AgentState:
    """Propose automatiquement des vidéos YouTube sur l'ouverture."""
    errors = state.get("errors", [])
    opening = state.get("opening") or "chess opening"
    try:
        state["videos"] = await asyncio.to_thread(youtube_service.search_videos, opening)
    except YouTubeError as exc:
        state["videos"] = []
        errors.append(f"youtube: {exc}")
    state["errors"] = errors
    return state


def _route_after_moves(state: AgentState) -> str:
    """Aiguillage : si la position est hors théorie, on passe par Stockfish."""
    return "rag_context" if state.get("is_theoretical") else "evaluate"


def build_agent_graph():
    """Construit et compile le graphe de l'agent."""
    graph = StateGraph(AgentState)
    graph.add_node("identify_moves", node_identify_moves)
    graph.add_node("evaluate", node_evaluate)
    graph.add_node("rag_context", node_rag_context)
    graph.add_node("videos", node_videos)

    graph.set_entry_point("identify_moves")
    graph.add_conditional_edges(
        "identify_moves",
        _route_after_moves,
        {"evaluate": "evaluate", "rag_context": "rag_context"},
    )
    graph.add_edge("evaluate", "rag_context")
    graph.add_edge("rag_context", "videos")
    graph.add_edge("videos", END)
    return graph.compile()


# Graphe compilé une seule fois, réutilisé par l'endpoint.
agent_graph = build_agent_graph()
