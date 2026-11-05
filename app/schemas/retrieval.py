from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """Identité et droits VÉRIFIÉS côté serveur (jamais lus depuis le navigateur)."""

    user_id: str
    groups: list[str] = Field(default_factory=list)


class SearchHit(BaseModel):
    chunk_id: str
    document_id: str
    version: str
    page: int
    element_id: str
    element_type: str
    section: str | None
    text: str
    equipment_model: str | None
    equipment_family: str | None
    validity_status: str
    score: float
