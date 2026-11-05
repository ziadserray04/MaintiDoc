"""Vérification de l'extraction sur un échantillon (feuille de route, phase 3).
Échantillon tiré avec une graine fixe ; chaque contrôle compare l'extraction à une vérité connue.
  - lignes de tableau des codes d'erreur : comparées à facts.json (titre, cause, action)
  - figures : la légende existe dans le texte de la page d'origine
  - pages OCR : texte OCR comparé au texte du même PDF avant dégradation (ressemblance de séquence)
Écrit docs/extraction_sample_report.md avec les résultats RÉELS de l'exécution."""
import difflib
import json
import random
import re
import sys
import tempfile
import unicodedata
from datetime import date
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.services.ingestion.pipeline import available_ocr_lang, ingest_corpus  # noqa: E402

CORPUS = Path("data/samples/corpus")
SEED, N_TABLE, N_FIG = 7, 60, 30


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).strip().lower()


def main():
    facts = json.loads((CORPUS / "facts.json").read_text())["models"]
    manifest = json.loads((CORPUS / "manifest.json").read_text())
    tmp = Path(tempfile.mkdtemp())
    ingest_corpus(CORPUS, tmp / "c.jsonl", tmp / "s.json")
    chunks = [json.loads(l) for l in (tmp / "c.jsonl").read_text().splitlines()]
    rnd = random.Random(SEED)

    # 1. lignes de tableau des guides de codes
    rows = [c for c in chunks if c["element_type"] == "table" and c["document_id"].startswith("codes_")]
    sample = rnd.sample(rows, min(N_TABLE, len(rows)))
    ok_t, bad_t = 0, []
    for c in sample:
        model = c["equipment_model"]
        code = re.search(r"\b[EB]\d{3}\b", c["text"])
        ref = next((e for e in facts[model]["error_codes"] if code and e["code"] == code.group(0)), None)
        t = norm(c["text"])
        if ref and all(norm(ref[k]).rstrip(".") in t for k in ("title", "cause", "action")):
            ok_t += 1
        else:
            bad_t.append((c["chunk_id"], c["text"][:100]))

    # 2. figures
    figs = [c for c in chunks if c["element_type"] == "figure"]
    sample_f = rnd.sample(figs, min(N_FIG, len(figs)))
    ok_f, bad_f = 0, []
    for c in sample_f:
        page = pymupdf.open(CORPUS / next(m["filename"] for m in manifest if m["document_id"] == c["document_id"]))[c["page"] - 1]
        if norm(c["text"]) in norm(page.get_text()):
            ok_f += 1
        else:
            bad_f.append(c["chunk_id"])

    # 3. OCR : comparaison avec le PDF avant dégradation
    sys.path.insert(0, "scripts")
    from corpus_data import battery_facts, inverter_facts, BATTERIES, INVERTERS  # noqa: E402
    from corpus_flows import procedure_flow  # noqa: E402
    from corpus_helpers import build  # noqa: E402
    allf = {f["model"]: f for f in [inverter_facts(i, s) for i, s in enumerate(INVERTERS)] +
            [battery_facts(i, s) for i, s in enumerate(BATTERIES)]}
    ocr_res = []
    for model in ("HN-S3", "HN-B5"):
        doc_id = f"procedure_{model.lower().replace('-', '')}_v1"
        ref_pdf = tmp / f"{doc_id}_ref.pdf"
        build(ref_pdf, f"Procédure de maintenance {model}", procedure_flow(allf[model]))
        for pno in sorted({c["page"] for c in chunks if c["document_id"] == doc_id and c["element_type"] == "ocr"}):
            ref_txt = norm(pymupdf.open(ref_pdf)[pno - 1].get_text())
            ocr_txt = norm(" ".join(c["text"] for c in chunks if c["document_id"] == doc_id and c["page"] == pno
                                    and c["element_type"] == "ocr"))
            ocr_res.append((doc_id, pno, difflib.SequenceMatcher(None, ref_txt, ocr_txt, autojunk=False).ratio()))
    mean_ocr = sum(r[2] for r in ocr_res) / len(ocr_res) if ocr_res else 0.0
    worst = min(ocr_res, key=lambda r: r[2]) if ocr_res else None

    lines = [f"# Vérification de l'extraction sur un échantillon\n", f"Exécutée le {date.today().isoformat()}, graine {SEED}, "
             f"OCR : Tesseract `{available_ocr_lang()}`.\n",
             "| Contrôle | Échantillon | Conformes | Taux |", "|---|---|---|---|",
             f"| Lignes de tableau des codes d'erreur (titre, cause et action comparés à `facts.json`) | {len(sample)} | {ok_t} | {ok_t / max(len(sample), 1):.0%} |",
             f"| Légendes de figures retrouvées sur la bonne page | {len(sample_f)} | {ok_f} | {ok_f / max(len(sample_f), 1):.0%} |",
             f"| Pages OCR : ressemblance avec le texte d'origine (moyenne) | {len(ocr_res)} pages | - | {mean_ocr:.1%} |", ""]
    if worst:
        lines.append(f"Page OCR la moins bonne : `{worst[0]}` page {worst[1]}, ressemblance {worst[2]:.1%}.\n")
    if bad_t:
        lines.append("Lignes de tableau non conformes :\n" + "\n".join(f"- `{a}` : {b}" for a, b in bad_t[:10]) + "\n")
    if bad_f:
        lines.append("Figures non retrouvées : " + ", ".join(bad_f[:10]) + "\n")
    lines.append("Limites : l'échantillon vient du corpus synthétique ; la ressemblance OCR mesure la lecture de scans "
                 "simulés, pas celle de vrais documents numérisés. Le texte de référence contient le pied de page, que "
                 "l'ingestion retire volontairement : la ressemblance est donc légèrement sous-estimée.\n")
    Path("docs/extraction_sample_report.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return ok_t == len(sample) and ok_f == len(sample_f)


if __name__ == "__main__":
    main()
