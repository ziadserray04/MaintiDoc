import unicodedata
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ElementType = Literal["text", "ocr", "table", "figure"]


class DocumentMeta(BaseModel):
    document_id: str
    title: str
    version: str
    validity_status: Literal["valid", "obsolete", "unknown"] = "unknown"
    equipment_family: str | None = None
    equipment_model: str | None = None
    access_groups: list[str] = Field(default_factory=list)
    provenance: str = "unknown"
    document_date: str | None = None  # AAAA-MM-JJ, si connue


class Chunk(BaseModel):
    """Passage indexable avec provenance exploitable (document, version, page, élément)."""

    chunk_id: str
    document_id: str
    version: str
    page: int = Field(ge=1)
    element_id: str
    element_type: ElementType
    section: str | None = None
    text: str
    validity_status: str = "unknown"
    equipment_family: str | None = None
    equipment_model: str | None = None
    access_groups: list[str] = Field(default_factory=list)
    ocr_lang: str | None = None

    @field_validator("text", "section")
    @classmethod
    def _nfkc(cls, v: str | None) -> str | None:
        """Normalise l'Unicode extrait (ex. symbole ohm U+2126 -> oméga U+03A9, espaces insécables) pour que
        une valeur tapée par l'utilisateur (« 480 kΩ ») corresponde à celle du document."""
        return unicodedata.normalize("NFKC", v) if v is not None else None


class IngestionReport(BaseModel):
    document_id: str
    sha256: str
    status: Literal["ok", "skipped_duplicate", "error"]
    pages: int = 0
    chunks: int = 0
    ocr_pages: list[int] = Field(default_factory=list)
    blank_pages: list[int] = Field(default_factory=list)
    tables: int = 0
    figures: int = 0
    error: str | None = None
