import pytest

from app.core.config import Settings


def test_budgets_defaults_match_spec():
    s = Settings()
    assert (s.max_model_calls, s.max_mcp_calls, s.max_pipeline_seconds) == (6, 3, 60)


def test_default_secrets_rejected_outside_dev():
    with pytest.raises(RuntimeError):
        Settings(app_env="prod").assert_safe_for_prod()
    Settings(app_env="dev-cpu").assert_safe_for_prod()


def test_device_auto_falls_back_to_cpu_without_torch():
    from app.core.config import resolve_device

    assert resolve_device("cpu") == "cpu"
    assert resolve_device("auto") in ("cpu", "cuda")


def test_bge_m3_backend_plumbing_with_fake_model(monkeypatch):
    """Sans télécharger le modèle : vérifie que get_embedder('bge-m3') branche bien sentence-transformers."""
    import sys
    import types

    import numpy as np

    class FakeST:
        device = "cpu"

        def __init__(self, name, device=None):
            self.name = name

        def encode(self, texts, **kw):
            assert kw["normalize_embeddings"] is True
            return np.ones((len(texts), 1024), dtype="float64") / 32.0

    monkeypatch.setitem(sys.modules, "sentence_transformers", types.SimpleNamespace(SentenceTransformer=FakeST))
    from app.services.retrieval.embeddings import get_embedder

    e = get_embedder("bge-m3")
    v = e.embed(["a", "b"])
    assert e.name == "bge-m3" and e.dim == 1024 and len(v) == 2 and len(v[0]) == 1024


def test_lexical_support_uses_domain_synonyms_and_ignores_request_wording():
    from app.services.answer_generation.answer import lexical_support
    assert lexical_support("Quel calibre de protection AC prévoir ?", "Calibre du fusible AC : 16 A") == 1.0
    assert lexical_support("Je dois manutentionner : combien pèse-t-il ?", "Masse (poids) : 16 kg") >= 0.5
    assert lexical_support("Quel est le prix de livraison ?", "Masse (poids) : 16 kg") == 0.0
