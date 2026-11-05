import importlib.util
import json
from pathlib import Path

import pymupdf
import pytest

from tests.corpus_paths import doc_path  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "generate_corpus.py"


@pytest.fixture(scope="module")
def corpus(tmp_path_factory):
    spec = importlib.util.spec_from_file_location("gen", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path_factory.mktemp("corpus")
    manifest = mod.main(str(out))
    facts = json.loads((out / "facts.json").read_text())
    return out, manifest, facts


def text_of(path):
    """Texte du PDF avec espaces normalisés (les retours à la ligne du PDF ne comptent pas)."""
    return " ".join("".join(p.get_text() for p in pymupdf.open(path)).split())


def test_size_within_spec(corpus):
    out, manifest, _ = corpus
    photos = json.loads((out / "photos_manifest.json").read_text())
    assert 30 <= len(manifest) + sum(p["in_corpus"] for p in photos) <= 50  # les photos du corpus comptent dans les 30 à 50
    assert len({m["document_id"] for m in manifest}) == len(manifest)


def test_two_families_many_models(corpus):
    _, manifest, facts = corpus
    fams = {m["equipment_family"] for m in manifest}
    assert fams == {"onduleur", "batterie"}
    models = facts["models"]
    assert sum(1 for m in models.values() if m["family"] == "onduleur") >= 7
    assert sum(1 for m in models.values() if m["family"] == "batterie") >= 7


def test_every_model_has_rich_error_guide(corpus):
    out, manifest, facts = corpus
    for m in manifest:
        if m["kind"] == "codes_erreur":
            assert not m["scanned"]
            txt = text_of(out / m["filename"])
            n = sum(1 for c in facts["models"][m["equipment_model"]]["error_codes"] if c["code"] in txt)
            assert n >= 25, (m["document_id"], n)


def test_scanned_docs_have_no_text_layer(corpus):
    out, manifest, _ = corpus
    scans = [m for m in manifest if m["scanned"]]
    assert len(scans) == 2
    for m in scans:
        assert len(text_of(out / m["filename"]).strip()) == 0


def test_obsolete_and_contradiction_have_different_values(corpus):
    out, manifest, facts = corpus
    s8 = facts["special"]["contradiction"]
    assert s8["manual_value"] != s8["bulletin_value"]
    assert f"{s8['manual_value']} °C" in text_of(doc_path(out, "manuel_hns8_v2"))
    assert f"{s8['bulletin_value']} °C" in text_of(doc_path(out, "bulletin_hns8_contradictoire"))
    obs = [m for m in manifest if m["validity_status"] == "obsolete"]
    assert len(obs) == 2


def test_confidential_group_isolated(corpus):
    _, manifest, _ = corpus
    conf = [m for m in manifest if m["access_groups"] == ["grp_engineering"]]
    assert [m["document_id"] for m in conf] == ["note_confidentielle_engineering"]
    assert all("grp_engineering" not in m["access_groups"] for m in manifest if m not in conf)


def test_injection_doc_and_photos(corpus):
    out, _, facts = corpus
    assert facts["special"]["injection"]["text"] in text_of(doc_path(out, "annexe_hnt15_piegee"))
    assert (out / "images" / "photo_panneau_hns5.png").exists()
    assert (out / "images" / "photo_panneau_hns5_floue.png").exists()


def test_same_orange_led_means_different_things(corpus):
    _, _, facts = corpus
    def orange_fixed(model):
        return next(l["meaning"] for l in facts["models"][model]["leds"] if l["led"] == "Orange fixe")
    assert orange_fixed("HN-S5") != orange_fixed("HN-T15")
    assert orange_fixed("HN-S5") != orange_fixed("HN-B10")


def test_manuals_are_long_documents_with_numbered_chapters_and_figures(corpus):
    out, manifest, _ = corpus
    manuals = [m for m in manifest if m["kind"] == "manuel"]
    assert len(manuals) == 16 and all(m["pages"] >= 10 for m in manuals)
    for m in manuals:
        txt = text_of(out / m["filename"])
        assert "12. Annexes" in txt and "Figure 3.1" in txt and "Figure 3.2" in txt and "Figure 7.1" in txt


def test_error_guides_have_one_diagnostic_sheet_per_code(corpus):
    out, manifest, facts = corpus
    for m in manifest:
        if m["kind"] == "codes_erreur":
            assert m["pages"] >= 8
            txt = text_of(out / m["filename"])
            for c in facts["models"][m["equipment_model"]]["error_codes"]:
                assert f"Fiche {c['code']} -" in txt, (m["document_id"], c["code"])


def test_compatibility_matrix_is_consistent_in_facts_and_documents(corpus):
    out, _, facts = corpus
    assert len(facts["compatibility"]) == 49
    ok = {(c["inverter"], c["battery"]): c["compatible"] for c in facts["compatibility"]}
    assert ok[("HN-S5", "HN-B10")] is True and ok[("HN-S5", "HN-B13")] is False and ok[("HN-S10", "HN-B30")] is False
    assert ok[("HN-T20", "HN-B30")] is True
    inv_txt = text_of(doc_path(out, "manuel_hns5_v2"))
    assert "HN-B13 13 kWh Non" in inv_txt and "HN-B10 10 kWh Oui" in inv_txt
    assert "HN-S5 5 kW Oui" in text_of(doc_path(out, "manuel_hnb10_v2")) and "HN-S3 3 kW Non" in text_of(doc_path(out, "manuel_hnb10_v2"))


def test_photos_have_ground_truth_and_ambiguity_cases(corpus):
    out, _, _ = corpus
    photos = json.loads((out / "photos_manifest.json").read_text())
    assert len(photos) == 22 and sum(p["in_corpus"] for p in photos) == 7
    assert all((out / p["file"]).exists() for p in photos)
    assert all(p["file"].startswith("images/" if p["in_corpus"] else "eval_images/") for p in photos)
    normal = [p for p in photos if p["variant"] == "normale"]
    assert len(normal) == 14 and all(p["model_identifiable"] and p["plate_legible"] for p in normal)
    hard = [p for p in photos if p["variant"] in ("floue", "plaque_masquee")]
    assert hard and all(not p["model_identifiable"] and not p["plate_legible"] for p in hard)
    assert {p["variant"] for p in photos} == {"normale", "floue", "plaque_masquee", "sombre"}


def test_dates_vary_and_obsolete_is_older(corpus):
    _, manifest, _ = corpus
    dates = {m["document_date"] for m in manifest}
    assert len(dates) > 20 and all(len(d) == 10 for d in dates)
    for m in manifest:
        if m["validity_status"] == "obsolete":
            v2 = next(x for x in manifest if x["document_id"] == m["document_id"].replace("_v1", "_v2"))
            assert m["document_date"] < v2["document_date"]


def test_blank_page_is_really_blank(corpus):
    out, _, facts = corpus
    b = facts["special"]["blank_page"]
    page = pymupdf.open(doc_path(out, b["document_id"]))[b["page"] - 1]
    assert page.get_text().replace("HelioNova (fictif) - Page 2", "").strip() == "" and not page.get_images()


def test_inventory_matches_files_and_consignes(corpus):
    import sys
    sys.path.insert(0, str(SCRIPT.parent))
    from corpus_inventory import check_inventory
    out, _, _ = corpus
    assert check_inventory(out) == []


def test_all_models_have_equipment_ids_consistent_with_history(corpus):
    out, _, facts = corpus
    park = json.loads((out / "equipment_history.json").read_text())
    assert set(park) == {f"{m}-01" for m in facts["models"]}
    assert all(d["history"] for d in park.values()) and any(d["open_tickets"] for d in park.values())
