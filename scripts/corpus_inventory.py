"""Inventaire du corpus (inventaire.csv) au format des consignes du livrable 1, et contrôle de cohérence."""
import csv
import re
from pathlib import Path

import pymupdf

COLUMNS = ["document_id", "fichier", "titre", "famille_equipement", "equipement_id", "type_document", "version", "nb_pages",
           "langue", "format", "elements_visuels", "provenance", "licence", "genere_par_ia", "outil_ia", "verifie_par",
           "corrections", "groupe_acces", "usage_test", "remarques"]
TYPES = {"manuel", "procedure", "fiche_securite", "schema", "codes_alarme", "photo", "historique"}
USAGES = {"normal", "contradictoire", "injection", "ambigu"}
KIND_TO_TYPE = {"manuel": "manuel", "guide": "manuel", "faq": "manuel", "codes_erreur": "codes_alarme", "procedure": "procedure",
                "bulletin": "procedure", "annexe": "procedure", "interne": "procedure", "fiche_securite": "fiche_securite",
                "securite": "fiche_securite", "historique": "historique", "retour_terrain": "historique"}
FAMILLE = {"onduleur": "onduleurs", "batterie": "batteries"}
REVIEWER = "A_COMPLETER"  # prénom du relecteur humain, à renseigner par l'équipe
FIGURE_LINE = re.compile(r"^Figure\s+(\d+\.\d+)\b")

# Renvois aux prompts décrits dans prompts_corpus.md
PROMPTS_BY_KIND = {"manuel": "P01", "codes_erreur": "P01", "procedure": "P01", "guide": "P01", "bulletin": "P01", "interne": "P01",
                   "annexe": "P01, P03", "fiche_securite": "P04", "historique": "P04", "securite": "P04", "faq": "P02",
                   "retour_terrain": "P02"}


def visuals_of(pdf_path: Path) -> str:
    """Figures (légende « Figure x.y ») et tableaux d'un PDF numérique, avec leur page. À appeler AVANT numérisation."""
    figs, tables = [], []
    for pno, page in enumerate(pymupdf.open(pdf_path), start=1):
        for line in page.get_text("text").splitlines():
            m = FIGURE_LINE.match(line.strip())
            if m:
                figs.append(f"fig {m.group(1)} p.{pno}")
        if len(tables) < 2 and page.find_tables().tables:
            tables.append(f"tableau p.{pno}")
    return " ; ".join(dict.fromkeys(figs + tables)) or "aucun"


def _date_ym(d: str | None) -> str:
    return (d or "2025-01-01")[:7]


def _equipment_ids(model, family, park):
    if model:
        return f"{model}-01"
    return ";".join(eid for eid, d in park.items() if d["family"] == family)


def _usage(m: dict) -> str:
    if m["document_id"] in ("bulletin_hns8_contradictoire", "manuel_hns8_v2", "manuel_hns5_v1", "manuel_hns5_v2",
                            "manuel_hnb10_v1", "manuel_hnb10_v2"):
        return "contradictoire"
    return "injection" if m["kind"] == "annexe" else "normal"


def _remarque(m: dict) -> str:
    notes = {"bulletin_hns8_contradictoire": "contredit manuel_hns8_v2 (seuil de limitation de puissance)",
             "manuel_hns8_v2": "contredit bulletin_hns8_contradictoire (seuil de limitation de puissance)",
             "manuel_hns5_v1": "obsolète : valeurs différentes de manuel_hns5_v2", "manuel_hnb10_v1": "obsolète : valeurs différentes de manuel_hnb10_v2",
             "manuel_hns5_v2": "version valide ; la v1 est obsolète", "manuel_hnb10_v2": "version valide ; la v1 est obsolète",
             "annexe_hnt15_piegee": "contient une instruction malveillante p.1 ; page 2 volontairement vide",
             "note_confidentielle_engineering": "réservé au groupe engineering : test de fuite entre groupes"}
    return notes.get(m["document_id"], m.get("note", "") or ("voyant orange fixe : sens propre à chaque modèle" if m["kind"] == "manuel" else ""))


def write_inventory(out: Path, manifest: list[dict], photos: list[dict], park: dict, reviewer: str = REVIEWER) -> int:
    rows = []
    for m in manifest:
        rows.append({
            "document_id": m["document_id"], "fichier": m["filename"], "titre": m["title"],
            "famille_equipement": FAMILLE[m["equipment_family"]],
            "equipement_id": _equipment_ids(m["equipment_model"], m["equipment_family"], park),
            "type_document": KIND_TO_TYPE[m["kind"]], "version": f"v{m['version']} ({_date_ym(m.get('document_date'))})",
            "nb_pages": m["pages"], "langue": "fr", "format": "pdf_scanne" if m["scanned"] else "pdf_texte",
            "elements_visuels": m.get("visuals", "aucun"), "provenance": "synthetique", "licence": "synthetique",
            "genere_par_ia": "oui", "outil_ia": f"Claude (prompt {PROMPTS_BY_KIND.get(m['kind'], 'P01')})", "verifie_par": reviewer,
            "corrections": "valeurs contrôlées automatiquement contre facts.json (tests) ; relecture humaine à faire",
            "groupe_acces": " ; ".join(m["access_groups"]), "usage_test": _usage(m), "remarques": _remarque(m)})
    for p in photos:
        if not p["in_corpus"]:
            continue
        ambiguous = p["variant"] != "normale"
        rows.append({
            "document_id": p["document_id"], "fichier": p["file"], "titre": f"Panneau de commande {p['model']} ({p['variant'].replace('_', ' ')})",
            "famille_equipement": FAMILLE[p["equipment_family"]], "equipement_id": p["equipment_id"], "type_document": "photo",
            "version": "v1.0 (2025-01)", "nb_pages": 1, "langue": "fr", "format": "image",
            "elements_visuels": f"voyant {p['led_lit'].lower()} ; code {p['displayed_code']} à l'écran ; plaque signalétique",
            "provenance": "synthetique", "licence": "synthetique", "genere_par_ia": "oui", "outil_ia": "Claude (prompt P02)",
            "verifie_par": reviewer, "corrections": "image contrôlée visuellement par l'IA ; relecture humaine à faire",
            "groupe_acces": " ; ".join(p["access_groups"]), "usage_test": "ambigu" if ambiguous else "normal",
            "remarques": (f"modèle identifiable : {'oui' if p['model_identifiable'] else 'non'} ; plaque lisible : "
                          f"{'oui' if p['plate_legible'] else 'non'}")})
    with (out / "inventaire.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def check_inventory(corpus_dir: Path) -> list[str]:
    """Contrôles des consignes : inventaire ↔ fichiers, colonnes, valeurs autorisées, volumétrie. Renvoie les problèmes."""
    corpus_dir = Path(corpus_dir)
    problems = []
    with (corpus_dir / "inventaire.csv").open(encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        rows = list(rd)
        if rd.fieldnames != COLUMNS:
            problems.append(f"colonnes inattendues : {rd.fieldnames}")
    ids = [r["document_id"] for r in rows]
    if len(set(ids)) != len(ids):
        problems.append("document_id en double")
    if not 30 <= len(rows) <= 50:
        problems.append(f"{len(rows)} lignes (30 à 50 attendues)")
    listed = {r["fichier"] for r in rows}
    on_disk = {p.relative_to(corpus_dir).as_posix() for sub in ("documents", "images") for p in (corpus_dir / sub).rglob("*") if p.is_file()}
    problems += [f"fichier absent de l'inventaire : {f}" for f in sorted(on_disk - listed)]
    problems += [f"ligne sans fichier : {f}" for f in sorted(listed - on_disk)]
    for r in rows:
        if not re.fullmatch(r"[a-z0-9_]+", r["document_id"]):
            problems.append(f"document_id invalide : {r['document_id']}")
        if Path(r["fichier"]).stem != r["document_id"]:
            problems.append(f"le fichier doit s'appeler <document_id> : {r['fichier']}")
        if r["type_document"] not in TYPES:
            problems.append(f"type_document invalide : {r['document_id']}")
        if r["usage_test"] not in USAGES:
            problems.append(f"usage_test invalide : {r['document_id']}")
        if r["format"] not in ("pdf_texte", "pdf_scanne", "image"):
            problems.append(f"format invalide : {r['document_id']}")
        if r["provenance"] != "synthetique" and not r["provenance"].startswith("http"):
            problems.append(f"provenance invalide : {r['document_id']}")
        if not all(r[c].strip() for c in COLUMNS if c not in ("outil_ia", "remarques")):
            problems.append(f"colonne vide : {r['document_id']}")
    if len({r["famille_equipement"] for r in rows}) != 2:
        problems.append("deux familles attendues")
    if sum(r["elements_visuels"] != "aucun" for r in rows) < 10:
        problems.append("moins de 10 documents avec éléments visuels")
    if sum(r["format"] == "pdf_scanne" for r in rows) < 2:
        problems.append("moins de 2 documents scannés")
    if sum(r["usage_test"] == "contradictoire" for r in rows) < 2:
        problems.append("moins de 2 documents contradictoires")
    if sum(r["usage_test"] == "injection" for r in rows) < 1:
        problems.append("aucun document piégé")
    if len({g.strip() for r in rows for g in r["groupe_acces"].split(";")}) < 2:
        problems.append("moins de 2 groupes d'accès")
    return problems
