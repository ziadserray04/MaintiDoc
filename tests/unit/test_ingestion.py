import json
from pathlib import Path

import pytest

from app.schemas.ingestion import DocumentMeta
from app.services.ingestion.pipeline import ingest_corpus, ingest_pdf
from tests.corpus_paths import doc_path

CORPUS = Path("data/samples/corpus")
pytestmark = pytest.mark.skipif(not (CORPUS / "manifest.json").exists(), reason="corpus non généré")


def meta(doc_id, model, version="1.0", family="onduleur"):
    return DocumentMeta(document_id=doc_id, title=doc_id, version=version, validity_status="valid",
                        equipment_family=family, equipment_model=model, access_groups=["grp_sav"])


def test_digital_pdf_keeps_page_version_and_metadata():
    chunks, rep = ingest_pdf(doc_path(CORPUS, "manuel_hns5_v2"), meta("manuel_hns5_v2", "HN-S5", "2.0"))
    assert rep.status == "ok" and rep.pages >= 1
    seuil = [c for c in chunks if "61 °C" in c.text]  # seuil de limitation de puissance du HN-S5
    assert seuil and seuil[0].page >= 1 and seuil[0].version == "2.0"
    assert seuil[0].access_groups == ["grp_sav"] and seuil[0].equipment_model == "HN-S5"


def test_error_code_table_is_extracted_with_meaning():
    chunks, rep = ingest_pdf(doc_path(CORPUS, "codes_hns5_v1"), meta("codes_hns5_v1", "HN-S5"))
    tables = [c for c in chunks if c.element_type == "table"]
    assert rep.tables >= 1 and tables
    joined = " ".join(c.text for c in tables)
    assert "E301" in joined and "Défaut d'isolement" in joined
    assert sum(1 for code in (f"E{n}" for n in (101, 205, 301, 401, 501, 603, 802)) if code in joined) >= 6


def test_figures_are_referenced_with_page_and_element_id():
    chunks, rep = ingest_pdf(doc_path(CORPUS, "manuel_hns5_v2"), meta("manuel_hns5_v2", "HN-S5", "2.0"))
    figs = [c for c in chunks if c.element_type == "figure"]
    assert rep.figures >= 2 and len(figs) == rep.figures
    assert all(f.page >= 1 and f.element_id.startswith("figure_") for f in figs)
    assert any("Plaque signalétique" in f.text for f in figs)


def test_warning_stays_with_procedure_step():
    chunks, _ = ingest_pdf(doc_path(CORPUS, "procedure_hnt15_v1"), meta("procedure_hnt15_v1", "HN-T15"))
    assert any("AVERTISSEMENT" in c.text and "Étape" in c.text for c in chunks)


def test_running_footer_is_not_indexed_and_chapters_are_sections():
    chunks, rep = ingest_pdf(doc_path(CORPUS, "manuel_hns5_v2"), meta("manuel_hns5_v2", "HN-S5", "2.0"))
    assert rep.pages >= 10
    assert not any("(fictif) - Page" in c.text or "(fictif) - Page" in (c.section or "") for c in chunks)
    sections = {c.section for c in chunks if c.section}
    assert any(s.startswith("5. Installation") or "Installation" in s for s in sections)
    assert max(c.page for c in chunks) >= 10  # les citations couvrent maintenant tout le document


def test_scanned_pdf_goes_through_ocr():
    chunks, rep = ingest_pdf(doc_path(CORPUS, "procedure_hns3_v1"), meta("procedure_hns3_v1", "HN-S3"))
    assert rep.status == "ok" and rep.ocr_pages
    assert chunks and all(c.element_type in ("ocr", "figure") for c in chunks)
    assert any("bornes" in c.text.lower() or "hors tension" in c.text.lower() for c in chunks)


def test_corrupt_pdf_is_isolated(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"pas un pdf")
    chunks, rep = ingest_pdf(bad, meta("bad", "X"))
    assert chunks == [] and rep.status == "error" and rep.error


def test_rerun_is_idempotent(ingested):
    out, state, first = ingested["out"], ingested["state"], ingested["reports"]
    n_lines = len(out.read_text().splitlines())
    second = ingest_corpus(CORPUS, out, state)
    assert sum(r.status == "ok" for r in first) >= 30
    assert not [r for r in first if r.status == "error"]
    assert all(r.status == "skipped_duplicate" for r in second)
    assert len(out.read_text().splitlines()) == n_lines
    assert json.loads(state.read_text())


def test_extracted_text_is_unicode_normalized():
    """Le PDF contient le symbole ohm U+2126 ; l'utilisateur tape l'oméga U+03A9."""
    chunks, _ = ingest_pdf(doc_path(CORPUS, "codes_hns5_v1"), meta("codes_hns5_v1", "HN-S5"))
    txt = " ".join(c.text for c in chunks)
    assert "Ω" not in txt and "kΩ" in txt


def test_ocr_keeps_french_accents_when_fra_is_installed(ingested):
    import json
    from app.services.ingestion.pipeline import available_ocr_lang
    if available_ocr_lang() != "fra":
        pytest.skip("modèle OCR fra non installé")
    txt = " ".join(json.loads(l)["text"] for l in ingested["out"].read_text().splitlines()
                   if json.loads(l)["document_id"] == "procedure_hns3_v1")
    assert "Étape" in txt and "côté" in txt


def test_blank_page_in_corpus_is_reported_and_not_indexed(ingested):
    import json
    rep = next(r for r in ingested["reports"] if r.document_id == "annexe_hnt15_piegee")
    assert rep.status == "ok" and rep.blank_pages == [2]
    pages = {json.loads(l)["page"] for l in ingested["out"].read_text().splitlines()
             if json.loads(l)["document_id"] == "annexe_hnt15_piegee"}
    assert 2 not in pages and 1 in pages


def test_fully_blank_pdf_gives_zero_chunk_without_error(tmp_path):
    import pymupdf
    doc = pymupdf.open()
    doc.new_page()
    doc.new_page()
    p = tmp_path / "vide.pdf"
    doc.save(p)
    chunks, rep = ingest_pdf(p, meta("vide", None))
    assert rep.status == "ok" and chunks == [] and rep.blank_pages == [1, 2]


def test_exact_duplicate_file_is_skipped_by_hash(tmp_path):
    import shutil
    src = doc_path(CORPUS, "guide_general_onduleur")
    shutil.copyfile(src, tmp_path / "a.pdf")
    shutil.copyfile(src, tmp_path / "b.pdf")
    base = json.loads((CORPUS / "manifest.json").read_text())[0]
    manifest = [dict(base, document_id="doc_a", filename="a.pdf"), dict(base, document_id="doc_b", filename="b.pdf")]
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    reps = ingest_corpus(tmp_path, tmp_path / "out.jsonl", tmp_path / "state.json")
    assert [r.status for r in reps] == ["ok", "skipped_duplicate"]
