"""Régénère le corpus fictif s'il est absent (il est reproductible et n'est pas versionné dans Git)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data" / "samples" / "corpus"


def _ensure_corpus():
    if (CORPUS / "manifest.json").exists() and (CORPUS / "photos_manifest.json").exists():
        return
    spec = importlib.util.spec_from_file_location("gen_corpus", ROOT / "scripts" / "generate_corpus.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.main(str(CORPUS))


_ensure_corpus()


import pytest  # noqa: E402


@pytest.fixture(scope="session")
def ingested(tmp_path_factory):
    """Ingestion complète du corpus, exécutée une seule fois par session de tests."""
    from app.services.ingestion.pipeline import ingest_corpus

    d = tmp_path_factory.mktemp("ingested")
    out, state = d / "chunks.jsonl", d / "state.json"
    reports = ingest_corpus(CORPUS, out, state)
    return dict(out=out, state=state, reports=reports)
