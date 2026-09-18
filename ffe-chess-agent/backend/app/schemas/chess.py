"""Schémas de réponse (Pydantic) pour les endpoints liés aux échecs."""

from pydantic import BaseModel, Field


class TheoreticalMove(BaseModel):
    """Un coup théorique renvoyé par l'explorateur d'ouvertures Lichess."""

    uci: str = Field(..., description="Coup au format UCI (ex: 'e2e4')", examples=["e2e4"])
    san: str = Field(..., description="Coup en notation algébrique (ex: 'e4')", examples=["e4"])
    white: int = Field(..., description="Nombre de parties gagnées par les Blancs")
    draws: int = Field(..., description="Nombre de parties nulles")
    black: int = Field(..., description="Nombre de parties gagnées par les Noirs")
    total: int = Field(..., description="Nombre total de parties où ce coup a été joué")


class OpeningInfo(BaseModel):
    """Nom et code ECO de l'ouverture identifiée."""

    eco: str | None = Field(None, description="Code ECO de l'ouverture (ex: 'B01')")
    name: str | None = Field(None, description="Nom de l'ouverture (ex: 'Scandinavian Defense')")


class MovesResponse(BaseModel):
    """Réponse de l'endpoint /moves : coups théoriques pour une position."""

    fen: str
    is_theoretical: bool = Field(
        ...,
        description="True si au moins un coup théorique existe pour cette position.",
    )
    opening: OpeningInfo | None = None
    total_games: int = Field(0, description="Nombre total de parties dans la base pour cette position.")
    moves: list[TheoreticalMove] = Field(default_factory=list)
    message: str | None = Field(
        None,
        description="Indication complémentaire (ex: position hors théorie → utiliser /evaluate).",
    )


class EvaluationResponse(BaseModel):
    """Réponse de l'endpoint /evaluate : évaluation Stockfish d'une position."""

    fen: str
    type: str = Field(..., description="'cp' (centipions) ou 'mate' (mat en N coups)", examples=["cp"])
    value: int = Field(
        ...,
        description="Valeur de l'évaluation. En 'cp', positif = avantage Blancs. "
        "En 'mate', N = mat forcé en N coups (signe = camp qui mate).",
        examples=[26],
    )
    best_move: str | None = Field(None, description="Meilleur coup selon Stockfish (UCI).", examples=["e2e4"])
    depth: int = Field(..., description="Profondeur de recherche utilisée.")
    interpretation: str = Field(..., description="Interprétation en français de l'évaluation.")


class VectorSearchResult(BaseModel):
    """Un extrait textuel pertinent renvoyé par la recherche vectorielle."""

    opening: str = Field(..., description="Ouverture concernée.")
    eco: str = Field("", description="Code ECO de l'ouverture.")
    text: str = Field(..., description="Extrait de texte (chunk) pertinent.")
    source: str = Field("", description="Source du texte.")
    score: float = Field(..., description="Score de similarité cosinus (proche de 1 = très pertinent).")


class VectorSearchResponse(BaseModel):
    """Réponse de l'endpoint /vector-search."""

    query: str
    results: list[VectorSearchResult] = Field(default_factory=list)


class Video(BaseModel):
    """Une vidéo YouTube pertinente."""

    video_id: str = Field(..., description="Identifiant YouTube de la vidéo.")
    title: str = Field(..., description="Titre de la vidéo.")
    channel: str = Field("", description="Nom de la chaîne.")
    description: str = Field("", description="Description courte.")
    published_at: str = Field("", description="Date de publication (ISO 8601).")
    url: str = Field(..., description="Lien de la vidéo (watch).", examples=["https://www.youtube.com/watch?v=..."])
    embed_url: str = Field(..., description="Lien d'intégration (pour lecteur embarqué / streaming).")
    thumbnail: str = Field("", description="URL de la miniature.")


class VideosResponse(BaseModel):
    """Réponse de l'endpoint /videos."""

    opening: str
    count: int = Field(0, description="Nombre de vidéos trouvées.")
    videos: list[Video] = Field(default_factory=list)
    message: str | None = Field(None, description="Indication si aucune vidéo n'est trouvée.")
