"""Enregistre le corpus : fichiers -> MinIO (ou dossier local), métadonnées -> PostgreSQL (ou SQLite).
Le choix dépend de .env (MINIO_ENDPOINT, DATABASE_URL). Usage : python -m scripts.register_corpus [dossier]"""
import sys
from pathlib import Path

from app.core.config import get_settings
from app.services.storage.file_store import build_file_store
from app.services.storage.metadata_store import MetadataStore, register_corpus

if __name__ == "__main__":
    s = get_settings()
    corpus = Path(sys.argv[1] if len(sys.argv) > 1 else "data/samples/corpus")
    n = register_corpus(corpus, build_file_store(s), MetadataStore(s.database_url))
    print(f"{n} documents enregistrés ({'MinIO' if s.minio_endpoint else 'stockage local'}, {s.database_url.split(':')[0]})")
