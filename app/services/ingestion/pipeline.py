"""Extraction PDF -> chunks avec provenance. Idempotent (hash), reprise possible, erreurs isolées."""
import hashlib
import io
import json
import re
from pathlib import Path

import pymupdf

from app.schemas.ingestion import Chunk, DocumentMeta, IngestionReport

MIN_TEXT_CHARS = 20          # en dessous : page considérée comme scannée
WARNING_RE = re.compile(r"^(AVERTISSEMENT|ATTENTION|DANGER|WARNING|CAUTION)\b", re.I)
FIGURE_RE = re.compile(r"^Figure\s*[:.\d]", re.I)
HEADING_MAX = 60
MIN_WORDS = 5   # un passage « texte » plus court est un fragment (étiquettes de figure, titres seuls)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def available_ocr_lang() -> str:
    """'fra' si installé, sinon 'eng' (documenté comme limite)."""
    try:
        import pytesseract

        langs = pytesseract.get_languages(config="")
        return "fra" if "fra" in langs else "eng"
    except Exception:
        return "eng"


def ocr_page(page: pymupdf.Page, lang: str) -> str:
    import pytesseract
    from PIL import Image

    pix = page.get_pixmap(dpi=200)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    return pytesseract.image_to_string(img, lang=lang)


def _table_rows(page: pymupdf.Page, table) -> list[list[str]]:
    rows = []
    for row in table.rows:
        rows.append([page.get_text("text", clip=pymupdf.Rect(c)).strip().replace("\n", " ") if c else ""
                     for c in row.cells])
    return rows


def _split_sections(text: str) -> list[tuple[str | None, str]]:
    """Découpe en sections (titre court + corps). Un avertissement reste avec l'étape qui suit."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    sections: list[tuple[str | None, list[str]]] = []
    for ln in lines:
        is_heading = len(ln) <= HEADING_MAX and not ln.endswith((".", ":", ";")) and not ln[0].islower()
        if is_heading and (not sections or sections[-1][1] or WARNING_RE.match(ln)):
            sections.append((ln, []))
        elif sections:
            sections[-1][1].append(ln)
        else:
            sections.append((None, [ln]))
    merged: list[tuple[str | None, str]] = []
    for title, body in sections:
        body_txt = " ".join(body).strip()
        if merged and merged[-1][0] and WARNING_RE.match(merged[-1][0]):
            # avertissement : rattaché à la section suivante pour ne pas être séparé de la procédure
            prev_t, prev_b = merged.pop()
            merged.append((title, f"[{prev_t}] {prev_b} {body_txt}".strip()))
        elif body_txt or title:
            merged.append((title, body_txt))
    return merged


def _norm_line(line: str) -> str:
    return re.sub(r"\d+", "#", line.strip().lower())


def _running_lines(doc: pymupdf.Document) -> set[str]:
    """Lignes répétées sur la plupart des pages (en-têtes, pieds de page, numéros) : à ne pas indexer."""
    pages = [[_norm_line(l) for l in pg.get_text("text").splitlines() if l.strip()] for pg in doc]
    pages = [p for p in pages if p]
    if len(pages) < 3:
        return set()
    counts: dict[str, int] = {}
    for p in pages:
        for l in set(p):
            counts[l] = counts.get(l, 0) + 1
    return {l for l, n in counts.items() if n >= 0.6 * len(pages)}


def _strip_running(text: str, running: set[str]) -> str:
    return "\n".join(l for l in text.splitlines() if _norm_line(l) not in running)


def ingest_pdf(path: Path, meta: DocumentMeta, ocr_lang: str | None = None) -> tuple[list[Chunk], IngestionReport]:
    digest = sha256_file(path)
    report = IngestionReport(document_id=meta.document_id, sha256=digest, status="ok")
    chunks: list[Chunk] = []
    common = dict(document_id=meta.document_id, version=meta.version, validity_status=meta.validity_status,
                  equipment_family=meta.equipment_family, equipment_model=meta.equipment_model,
                  access_groups=meta.access_groups)
    try:
        doc = pymupdf.open(path)
        report.pages = len(doc)
        running = _running_lines(doc)
        for pno, page in enumerate(doc, start=1):
            text = page.get_text("text")
            etype, lang = "text", None
            page_tables = []
            if len(text.strip()) < MIN_TEXT_CHARS and page.get_images():
                lang = ocr_lang or available_ocr_lang()
                text = ocr_page(page, lang)
                etype = "ocr"
                report.ocr_pages.append(pno)
            if etype == "text":
                page_tables = page.find_tables().tables
                if page_tables:  # le contenu des tableaux n'est lisible que dans les chunks « table » (lignes intactes)
                    boxes = [pymupdf.Rect(t.bbox) for t in page_tables]
                    text = "\n".join(b[4].strip() for b in page.get_text("blocks", sort=True) if b[6] == 0 and not any(
                        bb.contains(pymupdf.Point((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)) for bb in boxes))
            text = _strip_running(text, running)
            if not text.strip() and not page_tables:
                report.blank_pages.append(pno)  # page vide (ou seulement en-tête/pied de page) : rien à indexer
                continue
            n = 0
            for section, body in _split_sections(text):
                if FIGURE_RE.match(section or "") or FIGURE_RE.match(body):
                    continue
                if etype == "text" and len(f"{section or ''} {body}".split()) < MIN_WORDS:
                    continue  # fragment (étiquette de figure, titre seul)
                n += 1
                chunks.append(Chunk(chunk_id=f"{meta.document_id}:p{pno}:c{n}", page=pno,
                                    element_id=f"p{pno}_c{n}", element_type=etype, section=section,
                                    text=f"{section}. {body}" if section and body else (body or section or ""),
                                    ocr_lang=lang, **common))
            if etype == "text":
                for t_i, tbl in enumerate(page_tables, start=1):
                    rows = _table_rows(page, tbl)
                    header = rows[0] if rows else []
                    report.tables += 1
                    for r_i, row in enumerate(rows[1:], start=1):  # un passage par ligne : le code et sa cause restent ensemble
                        if not any(row):
                            continue
                        flat = " : ".join(row) if len(row) == 2 else " ; ".join(f"{h} : {v}" for h, v in zip(header, row))
                        chunks.append(Chunk(chunk_id=f"{meta.document_id}:p{pno}:t{t_i}:r{r_i}", page=pno,
                                            element_id=f"table_{pno}_{t_i}_r{r_i}", element_type="table",
                                            section=f"Tableau ({' | '.join(header)})", text=flat, **common))
            for f_i, ln in enumerate([l.strip() for l in text.splitlines() if FIGURE_RE.match(l.strip())], 1):
                report.figures += 1
                chunks.append(Chunk(chunk_id=f"{meta.document_id}:p{pno}:f{f_i}", page=pno,
                                    element_id=f"figure_{pno}_{f_i}", element_type="figure",
                                    section="Figure", text=ln, ocr_lang=lang, **common))
        report.chunks = len(chunks)
    except Exception as exc:  # document corrompu, OCR indisponible, etc. : isolé, jamais fatal pour le lot
        report.status, report.error = "error", f"{type(exc).__name__}: {exc}"[:300]
        return [], report
    return chunks, report


def ingest_corpus(corpus_dir: Path, out_jsonl: Path, state_file: Path | None = None) -> list[IngestionReport]:
    """Ingère tout le manifest. Réexécutable : les documents déjà vus (même hash) sont ignorés."""
    manifest = json.loads((corpus_dir / "manifest.json").read_text())
    seen = set(json.loads(state_file.read_text())) if state_file and state_file.exists() else set()
    reports, lang = [], available_ocr_lang()
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if seen else "w"
    with out_jsonl.open(mode, encoding="utf-8") as fh:
        for m in manifest:
            path = corpus_dir / m["filename"]
            digest = sha256_file(path)
            if digest in seen:
                reports.append(IngestionReport(document_id=m["document_id"], sha256=digest,
                                               status="skipped_duplicate"))
                continue
            meta = DocumentMeta(**{k: m[k] for k in DocumentMeta.model_fields if k in m})
            chunks, rep = ingest_pdf(path, meta, lang)
            for c in chunks:
                fh.write(c.model_dump_json() + "\n")
            reports.append(rep)
            if rep.status == "ok":
                seen.add(digest)
    if state_file:
        state_file.write_text(json.dumps(sorted(seen)))
    return reports
