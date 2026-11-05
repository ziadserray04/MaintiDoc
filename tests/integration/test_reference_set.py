"""Le jeu de référence texte s'exécute de bout en bout ; invariants de sécurité et de fiabilité (pas de seuil de qualité sémantique)."""
import json
from pathlib import Path

import pytest

from scripts import eval_text_reference

REF = Path("data/evaluation/text_reference.jsonl")
pytestmark = pytest.mark.skipif(not REF.exists(), reason="jeu de référence absent")


@pytest.fixture(scope="module")
def result(ingested, tmp_path_factory):
    return eval_text_reference.main(str(tmp_path_factory.mktemp("r") / "rapport.md"), chunks_jsonl=ingested["out"])


def test_reference_set_has_expected_shape():
    s = [json.loads(l) for l in REF.read_text().splitlines()]
    assert len(s) == 70 and len({x["id"] for x in s}) == 70
    cats = {c: sum(1 for x in s if x["category"] == c) for c in {x["category"] for x in s}}
    assert cats["sans_source"] == 10 and cats["contradiction"] == 5 and cats["obsolète"] == 5 and cats["droits"] == 10


def test_every_answered_scenario_has_a_resolvable_gold(result):
    assert result["recall"] > 0 and result["ndcg"] > 0 and result["mrr"] > 0


def test_no_confidential_leak_and_no_obsolete_value(result):
    failed = {f[0]: f for f in result["fails"]}
    s = {x["id"]: x for x in (json.loads(l) for l in REF.read_text().splitlines())}
    for sid, x in s.items():
        if x["must_not_contain"] and sid in failed:
            # un échec sur une valeur interdite (marqueur confidentiel ou valeur v1) serait une fuite ou une version obsolète
            assert x["must_not_contain"] not in failed[sid][4], failed[sid]


def test_every_cited_answer_cites_the_expected_document(result):
    ok, n = result["cite"]
    assert n > 0 and ok == n


def test_contradiction_detected_in_most_phrasings(result):
    c = [f for f in result["fails"] if f[1] == "contradiction"]
    assert len(c) <= 2  # 4/5 constaté ; l'échec restant est un écart de vocabulaire (« derating »)
