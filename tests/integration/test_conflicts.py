"""Contradictions : le système signale deux sources valides en désaccord, sans trancher, et ne les invente pas ailleurs."""
import json
from pathlib import Path

import pytest

from tests.integration.test_rag import SAV, ask, rag  # noqa: F401

CORPUS = Path("data/samples/corpus")


@pytest.mark.parametrize("q", [
    "À quelle température la limitation de puissance du HN-S8 débute-t-elle ?",
    "Quel est le seuil de limitation de puissance du HN-S8 ?",
    "Le HN-S8 limite sa puissance à partir de quelle température ?",
])
def test_conflict_between_manual_and_bulletin_is_reported(rag, q):  # noqa: F811
    r = ask(rag, q)
    facts = json.loads((CORPUS / "facts.json").read_text())["special"]["contradiction"]
    assert r.status == "conflicting_sources"
    assert {c.document_id for c in r.citations} == {"manuel_hns8_v2", "bulletin_hns8_contradictoire"}
    assert f"{facts['manual_value']} °C" in r.answer and f"{facts['bulletin_value']} °C" in r.answer
    assert r.uncertainties


def test_no_false_conflict_on_other_models(rag):  # noqa: F811
    facts = json.loads((CORPUS / "facts.json").read_text())["models"]
    for m, f in facts.items():
        if f["family"] != "onduleur" or m == "HN-S8":
            continue
        r = ask(rag, f"Quel est le seuil de limitation de puissance du {m} ?")
        assert r.status == "answered" and f"{f['derate_temp_c']} °C" in r.answer, m


def test_obsolete_value_never_appears_as_conflict(rag):  # noqa: F811
    old = json.loads((CORPUS / "facts.json").read_text())["special"]["obsolete"]["HN-S5"]
    r = ask(rag, "Quel est le seuil de limitation de puissance du HN-S5 ?")
    assert r.status == "answered" and f"{old['v2_derate_temp_c']} °C" in r.answer
    assert f"{old['v1_derate_temp_c']} °C" not in r.answer
