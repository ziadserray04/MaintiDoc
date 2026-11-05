"""Sortie structurée (PDF §7). Aucun champ de « confiance » inventé par le modèle (PDF §8)."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Citation(BaseModel):
    document_id: str
    version: str
    page: int = Field(ge=1)
    element_id: str
    element_type: str = "text"
    retrieval_score: float | None = None  # similarité brute : PAS une probabilité de vérité


class AnswerResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")  # interdit tout champ non prévu (ex. « confidence »)

    status: Literal["answered", "needs_clarification", "abstained", "conflicting_sources"]
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    clarification_question: str | None = None
    proposed_action: str | None = None
