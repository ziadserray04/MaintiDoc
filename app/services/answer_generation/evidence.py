"""Vérifie qu'une source SOUTIENT réellement l'affirmation (une citation présente ne prouve rien à elle seule)."""
import re

from pydantic import BaseModel

from app.services.retrieval.embeddings import normalize

NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
STOP = {"pour", "dans", "avec", "sans", "cette", "sont", "peut", "elle", "leur", "plus", "mais", "tout", "tous"}


class EvidenceVerification(BaseModel):
    supported: bool
    reason: str
    missing_numbers: list[str] = []
    word_overlap: float = 0.0


def _numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in NUM_RE.findall(text)}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", normalize(text)) if len(w) > 3 and w not in STOP}


def verify_support(claim: str, passage: str, min_overlap: float = 0.6) -> EvidenceVerification:
    missing = sorted(_numbers(claim) - _numbers(passage))
    if missing:
        return EvidenceVerification(supported=False, reason="valeur numérique absente de la source", missing_numbers=missing)
    cw = _words(claim)
    overlap = len(cw & _words(passage)) / len(cw) if cw else 0.0
    if overlap < min_overlap:
        return EvidenceVerification(supported=False, reason="recouvrement lexical insuffisant", word_overlap=round(overlap, 2))
    return EvidenceVerification(supported=True, reason="valeurs et termes retrouvés dans la source", word_overlap=round(overlap, 2))
