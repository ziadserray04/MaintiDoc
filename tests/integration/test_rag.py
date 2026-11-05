"""RAG textuel de bout en bout sur le corpus fictif (backend d'embeddings `hashing` : CPU, non sémantique).
Ces tests vérifient la plomberie, les droits et les garde-fous, PAS la qualité sémantique d'un vrai modèle."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from qdrant_client import QdrantClient

from app.schemas.answer import AnswerResponse
from app.schemas.retrieval import UserContext
from app.services.answer_generation.answer import answer_question
from app.services.answer_generation.evidence import verify_support
from app.services.retrieval.embeddings import get_embedder
from app.services.retrieval.index import build_index, known_models, search

CORPUS = Path("data/samples/corpus")
pytestmark = pytest.mark.skipif(not (CORPUS / "facts.json").exists(), reason="corpus non généré")
SAV = UserContext(user_id="u_sav", groups=["grp_sav"])
ENG = UserContext(user_id="u_eng", groups=["grp_engineering"])
NOBODY = UserContext(user_id="u_none", groups=[])


@pytest.fixture(scope="module")
def rag(ingested):
    client, emb = QdrantClient(":memory:"), get_embedder("hashing")
    build_index(ingested["out"], client, emb)
    return client, emb, known_models(client, emb)


@pytest.fixture(scope="module")
def facts():
    return json.loads((CORPUS / "facts.json").read_text())["models"]


def ask(rag, q, user=SAV):
    client, emb, known = rag
    return answer_question(q, user, client, emb, known)


def test_every_model_threshold_is_answered_with_exact_value_and_citation(rag, facts):
    fails = []
    for model, f in facts.items():
        mid = model.lower().replace("-", "")
        if f["family"] == "onduleur":
            q, value = f"À partir de quelle température le {model} limite-t-il sa puissance ?", f"{f['derate_temp_c']} °C"
        else:
            q, value = f"Quelle est l'alarme de température haute de la batterie {model} ?", f"{f['temp_high_c']} °C"
        r = ask(rag, q)
        if model == "HN-S8":  # contradiction volontaire : voir test_conflicts.py
            assert r.status == "conflicting_sources"
            continue
        ok = (r.status == "answered" and value in r.answer and r.citations
              and r.citations[0].document_id == f"manuel_{mid}_v2" and r.citations[0].version == "2.0")
        if not ok:
            fails.append((model, r.status, r.answer[:80], [c.document_id for c in r.citations]))
    assert not fails, fails


def test_obsolete_version_is_not_used(rag, facts):
    f = facts["HN-S5"]
    r = ask(rag, "À partir de quelle température le HN-S5 limite-t-il sa puissance ?")
    assert f"{f['derate_temp_c']} °C" in r.answer and f"{f['derate_temp_c'] - 8} °C" not in r.answer
    assert all(not c.document_id.endswith("_v1") or c.document_id.startswith("codes") for c in r.citations)


def test_error_code_without_model_asks_for_clarification(rag):
    r = ask(rag, "Que signifie l'erreur E301 ?")
    assert r.status == "needs_clarification" and r.clarification_question and not r.citations
    assert "plaque" in r.clarification_question.lower()


def test_error_code_with_model_gives_model_specific_threshold(rag, facts):
    r = ask(rag, "Que signifie l'erreur E301 sur le HN-S5 ?")
    assert r.status == "answered" and f"{facts['HN-S5']['iso_kohm']} kΩ" in r.answer
    assert r.citations[0].document_id == "codes_hns5_v1"


def test_unknown_model_and_out_of_corpus_abstain(rag):
    for q in ("Quelle est la limite de puissance du HN-X99 ?", "Comment faire une tarte aux pommes ?"):
        r = ask(rag, q)
        assert r.status == "abstained" and not r.citations


def test_no_cross_group_leak(rag):
    client, emb, _ = rag
    for q in ("limite interne de test confidentielle", "note interne bureau d'études engineering", "1234"):
        hits = search(client, emb, q, SAV, top_k=20, include_obsolete=True)
        assert all(h.document_id != "note_confidentielle_engineering" and "1234" not in h.text for h in hits)
        r = ask(rag, q, SAV)
        assert not any(c.document_id == "note_confidentielle_engineering" for c in r.citations) and "1234" not in r.answer
    hits = search(client, emb, "limite interne de test confidentielle", ENG, top_k=5)
    assert any(h.document_id == "note_confidentielle_engineering" for h in hits)


def test_no_groups_means_no_retrieval(rag):
    client, emb, _ = rag
    assert search(client, emb, "puissance HN-S5", NOBODY) == []
    assert ask(rag, "À partir de quelle température le HN-S5 limite-t-il sa puissance ?", NOBODY).status == "abstained"


def test_unauthorized_and_unknown_look_the_same(rag):
    a = ask(rag, "Quelle est la limite interne du HN-B30 ?", NOBODY)
    b = ask(rag, "Quelle est la limite interne du HN-X99 ?", SAV)
    assert (a.status, a.answer) == (b.status, b.answer)


def test_verify_support_rejects_unsupported_claims():
    passage = "Limitation de puissance à partir de : 61 °C"
    assert verify_support("Limitation de puissance à partir de 61 °C", passage).supported
    bad_number = verify_support("Limitation de puissance à partir de 75 °C", passage)
    assert not bad_number.supported and bad_number.missing_numbers == ["75"]
    assert not verify_support("Remplacer immédiatement le condensateur principal", passage).supported


def test_answer_schema_has_no_confidence_field():
    with pytest.raises(ValidationError):
        AnswerResponse(status="answered", answer="x", confidence=0.97)


# ---- Questions de la 2e passe : vocabulaire différent, compatibilité à deux modèles ----
def test_all_models_weight_and_cable_and_storage(rag, facts):
    for m, f in facts.items():
        r = ask(rag, f"Quelle est la masse du {m} ?")
        assert r.status == "answered" and f"{f['weight_kg']} kg" in r.answer and r.citations, m
        if f["family"] == "onduleur":
            r = ask(rag, f"Quelle section de câble AC faut-il utiliser pour le {m} ?")
            assert r.status == "answered" and f"{f['ac_cable_mm2']} mm2" in r.answer, m
        else:
            r = ask(rag, f"Après combien de mois faut-il recharger la batterie {m} stockée ?")
            assert r.status == "answered" and f"{f['storage_recharge_months']} mois" in r.answer, m


def test_compatibility_uses_matrix_for_all_49_pairs(rag):
    comp = json.loads((CORPUS / "facts.json").read_text())["compatibility"]
    for c in comp:
        r = ask(rag, f"La batterie {c['battery']} est-elle compatible avec l'onduleur {c['inverter']} ?")
        expected = "Oui" if c["compatible"] else "Non"
        assert r.status == "answered" and f"Compatible : {expected}" in r.answer, c
        assert r.citations[0].element_type == "table" and r.citations[0].document_id.startswith("manuel_")


def test_compatibility_respects_unknown_model_and_rights(rag):
    assert ask(rag, "La batterie HN-B99 est-elle compatible avec l'onduleur HN-S5 ?").status == "abstained"
    assert ask(rag, "La batterie HN-B10 est-elle compatible avec l'onduleur HN-S5 ?", NOBODY).status == "abstained"


def test_two_inverters_in_one_question_still_need_clarification(rag):
    assert ask(rag, "Quel est le couple de serrage du HN-S5 et du HN-S8 ?").status == "needs_clarification"
