"""Évaluation de fumée du RAG textuel : 64 questions générées depuis facts.json (vérité de terrain connue).
Mesure UNIQUEMENT la plomberie avec le backend d'embeddings `hashing` ; ce n'est pas une évaluation de qualité sémantique."""
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.schemas.retrieval import UserContext
from app.services.answer_generation.answer import answer_question
from app.services.ingestion.pipeline import ingest_corpus
from app.services.retrieval.embeddings import get_embedder
from app.services.retrieval.index import build_index, known_models

CORPUS = Path("data/samples/corpus")


def questions(facts):
    qs = []
    M = facts["models"]
    for m, f in M.items():
        mid = m.lower().replace("-", "")
        qs.append(("couple", f"Quel est le couple de serrage des bornes du {m} ?", f"{f['terminal_torque_nm']} N.m", f"manuel_{mid}_v2"))
        qs.append(("masse", f"Quelle est la masse du {m} ?", f"{f['weight_kg']} kg", f"manuel_{mid}_v2"))
        if f["family"] == "onduleur":
            qs.append(("câble AC", f"Quelle section de câble AC faut-il utiliser pour le {m} ?", f"{f['ac_cable_mm2']} mm2", f"manuel_{mid}_v2"))
            qs.append(("fusible", f"Quel est le calibre du fusible AC du {m} ?", f"{f['fuse_a']} A", f"manuel_{mid}_v2"))
            qs.append(("rendement", f"Quel est le rendement maximal du {m} ?", f"{f['efficiency_pct']} %", f"manuel_{mid}_v2"))
        else:
            qs.append(("stockage", f"Après combien de mois faut-il recharger la batterie {m} stockée ?", f"{f['storage_recharge_months']} mois", f"manuel_{mid}_v2"))
    pairs = [("HN-S5", "HN-B13"), ("HN-S5", "HN-B10"), ("HN-S3", "HN-B7"), ("HN-S10", "HN-B30"),
             ("HN-T20", "HN-B30"), ("HN-T15", "HN-B20"), ("HN-S8", "HN-B20"), ("HN-S6", "HN-B5")]
    ok = {(c["inverter"], c["battery"]): c["compatible"] for c in facts["compatibility"]}
    for i, b in pairs:
        qs.append(("compatibilité", f"La batterie {b} est-elle compatible avec l'onduleur {i} ?", f"Compatible : {'Oui' if ok[(i, b)] else 'Non'}", None))
    return qs


def main():
    facts = json.loads((CORPUS / "facts.json").read_text())
    d = Path(tempfile.mkdtemp())
    ingest_corpus(CORPUS, d / "c.jsonl", d / "s.json")
    cl, em = QdrantClient(":memory:"), get_embedder(get_settings().embedding_backend)
    build_index(d / "c.jsonl", cl, em)
    known = known_models(cl, em)
    user = UserContext(user_id="eval", groups=["grp_sav"])
    res, fails = defaultdict(lambda: [0, 0]), []
    for cat, q, value, doc in questions(facts):
        r = answer_question(q, user, cl, em, known)
        good = r.status == "answered" and value in r.answer and (doc is None or (r.citations and r.citations[0].document_id == doc))
        res[cat][0] += good
        res[cat][1] += 1
        if not good:
            fails.append((cat, q, r.status, r.answer[:90]))
    tot = sum(v[0] for v in res.values()), sum(v[1] for v in res.values())
    for k, (a, n) in res.items():
        print(f"{k:14s} {a:2d}/{n}")
    print(f"TOTAL          {tot[0]}/{tot[1]}")
    if "-v" in sys.argv:
        for f in fails:
            print("ÉCHEC:", f)
    return tot


if __name__ == "__main__":
    main()
