"""Aide aux tests : retrouve le chemin d'un document du corpus à partir de son identifiant."""
import json
from pathlib import Path


def doc_path(corpus: Path, doc_id: str) -> Path:
    manifest = json.loads((Path(corpus) / "manifest.json").read_text())
    return Path(corpus) / next(m["filename"] for m in manifest if m["document_id"] == doc_id)
