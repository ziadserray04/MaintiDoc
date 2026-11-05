"""Métadonnées des documents dans une base SQL (SQLite en dev, PostgreSQL via DATABASE_URL).
Le filtrage par groupes d'accès existe aussi ici : un document non autorisé n'est jamais listé."""
import json
from pathlib import Path

from sqlalchemy import JSON, Boolean, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class DocumentRow(Base):
    __tablename__ = "documents"
    document_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    filename: Mapped[str] = mapped_column(String(256))
    title: Mapped[str] = mapped_column(String(256))
    version: Mapped[str] = mapped_column(String(16))
    validity_status: Mapped[str] = mapped_column(String(16))
    document_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    equipment_family: Mapped[str | None] = mapped_column(String(32), nullable=True)
    equipment_model: Mapped[str | None] = mapped_column(String(32), nullable=True)
    access_groups: Mapped[list] = mapped_column(JSON)
    kind: Mapped[str] = mapped_column(String(32))
    scanned: Mapped[bool] = mapped_column(Boolean, default=False)
    pages: Mapped[int] = mapped_column(Integer, default=0)
    provenance: Mapped[str] = mapped_column(String(32), default="unknown")
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    object_key: Mapped[str] = mapped_column(String(128))
    ingestion_status: Mapped[str] = mapped_column(String(24), default="pending")
    blank_pages: Mapped[list] = mapped_column(JSON, default=list)
    ocr_pages: Mapped[list] = mapped_column(JSON, default=list)


class MetadataStore:
    def __init__(self, database_url: str):
        if database_url.startswith("sqlite:///"):
            Path(database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)

    def upsert(self, **fields) -> None:
        with Session(self.engine) as s:
            s.merge(DocumentRow(**fields))
            s.commit()

    def get(self, document_id: str) -> DocumentRow | None:
        with Session(self.engine) as s:
            return s.get(DocumentRow, document_id)

    def visible_documents(self, groups: list[str]) -> list[DocumentRow]:
        """Seuls les documents dont au moins un groupe d'accès appartient à l'utilisateur."""
        with Session(self.engine) as s:
            rows = s.scalars(select(DocumentRow).order_by(DocumentRow.document_id)).all()
        allowed = set(groups)
        return [r for r in rows if allowed & set(r.access_groups)]


def register_corpus(corpus_dir: Path, file_store, meta_store: MetadataStore, reports=None) -> int:
    """Envoie chaque PDF dans le stockage de fichiers et enregistre ses métadonnées. Réexécutable."""
    manifest = json.loads((Path(corpus_dir) / "manifest.json").read_text())
    by_id = {r.document_id: r for r in (reports or [])}
    for m in manifest:
        key = file_store.put(Path(corpus_dir) / m["filename"])
        rep = by_id.get(m["document_id"])
        meta_store.upsert(
            document_id=m["document_id"], filename=m["filename"], title=m["title"], version=m["version"],
            validity_status=m["validity_status"], document_date=m.get("document_date"),
            equipment_family=m.get("equipment_family"), equipment_model=m.get("equipment_model"),
            access_groups=m["access_groups"], kind=m["kind"], scanned=m["scanned"], pages=m["pages"],
            provenance=m["provenance"], sha256=m["sha256"], object_key=key,
            ingestion_status=rep.status if rep else "pending",
            blank_pages=rep.blank_pages if rep else [], ocr_pages=rep.ocr_pages if rep else [])
    return len(manifest)
