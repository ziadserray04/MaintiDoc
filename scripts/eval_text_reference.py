"""Évalue le RAG texte sur data/evaluation/text_reference.jsonl : Recall@5, nDCG@5, MRR@10 et comportements.
Backend d'embeddings : celui de .env (EMBEDDING_BACKEND). Avec `hashing` (non sémantique), ces chiffres mesurent
la plomberie, pas la qualité d'un vrai modèle. Écrit docs/eval_text_reference_report.md."""
import json
import math
import re
import sys
import tempfile
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.schemas.retrieval import UserContext
from app.services.answer_generation.answer import answer_question, models_in_query
from app.services.ingestion.pipeline import ingest_corpus
from app.services.retrieval.embeddings import get_embedder
from app.services.retrieval.index import build_index, known_models, search

CORPUS, REF = Path("data/samples/corpus"), Path("data/evaluation/text_reference.jsonl")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", s)).strip().lower()


def main(report_path="docs/eval_text_reference_report.md", chunks_jsonl=None):
    scenarios = [json.loads(l) for l in REF.read_text().splitlines() if l.strip()]
    tmp = Path(tempfile.mkdtemp())
    if chunks_jsonl is None:
        ingest_corpus(CORPUS, tmp / "c.jsonl", tmp / "s.json")
        chunks_jsonl = tmp / "c.jsonl"
    chunks = [json.loads(l) for l in Path(chunks_jsonl).read_text().splitlines()]
    backend = get_settings().embedding_backend
    emb, cl = get_embedder(backend), QdrantClient(":memory:")
    build_index(Path(chunks_jsonl), cl, emb)
    known = known_models(cl, emb)

    rec, ndcg, mrr, unresolved = [], [], [], []
    beh = defaultdict(lambda: [0, 0])
    cite_ok = cite_n = 0
    fails = []
    for s in scenarios:
        user = UserContext(user_id="eval", groups=s["user_groups"])
        r = answer_question(s["question"], user, cl, emb, known)
        good = r.status == s["expected_status"]
        text = norm(r.answer)
        if good and s["gold_contains"] and s["expected_status"] in ("answered", "conflicting_sources"):
            good = norm(s["gold_contains"]) in text
        if good and s["must_not_contain"]:
            good = norm(s["must_not_contain"]) not in text
        beh[s["category"]][0] += good
        beh[s["category"]][1] += 1
        if not good:
            fails.append((s["id"], s["category"], s["question"], r.status, r.answer[:90]))
        if s["gold_doc"] and s["expected_status"] == "answered" and s["user_groups"]:
            gold = {c["chunk_id"] for c in chunks if c["document_id"] == s["gold_doc"] and c["element_type"] == s["gold_type"]
                    and norm(s["gold_contains"]) in norm(c["text"])}
            if not gold:
                unresolved.append(s["id"])
                continue
            ms = models_in_query(s["question"])
            hits = search(cl, emb, s["question"], user, top_k=10, equipment_model=ms[0] if len(ms) == 1 else None)
            # un passage est pertinent s'il vient du document attendu, du bon type, et contient la valeur attendue
            rel = [norm(s["gold_contains"]) in norm(h.text) and h.document_id == s["gold_doc"] and h.element_type == s["gold_type"]
                   for h in hits]
            first5 = rel[:5]
            rec.append(min(1.0, sum(first5) / max(len(gold), 1)))
            dcg = sum(1 / math.log2(i + 2) for i, v in enumerate(first5) if v)
            idcg = sum(1 / math.log2(i + 2) for i in range(min(len(gold), 5)))
            ndcg.append(dcg / idcg if idcg else 0.0)
            mrr.append(next((1 / (i + 1) for i, v in enumerate(rel[:10]) if v), 0.0))
            if r.status == "answered":
                cite_n += 1
                c0 = r.citations[0] if r.citations else None
                cite_ok += bool(c0 and c0.document_id == s["gold_doc"] and norm(s["gold_contains"]) in text)

    avg = lambda v: sum(v) / len(v) if v else 0.0  # noqa: E731
    tot_ok, tot_n = sum(v[0] for v in beh.values()), sum(v[1] for v in beh.values())
    lines = [f"# Évaluation du RAG texte sur le jeu de référence\n",
             f"Exécutée le {date.today().isoformat()} - embeddings : `{backend}` - {len(scenarios)} scénarios "
             f"(`data/evaluation/text_reference.jsonl`, graine 2026).\n",
             "Ces scénarios sont **synthétiques**, générés depuis les mêmes faits que le corpus avec des formulations "
             "différentes de celles utilisées pour régler le système. "
             + ("Le backend `hashing` n'est pas sémantique : ces chiffres ne représentent PAS la qualité d'un vrai modèle (BGE-M3).\n"
                if backend == "hashing" else "\n"),
             "La première exécution (avant correctifs) est conservée dans `docs/eval_text_reference_first_run.md` : 53/70. "
             "Les correctifs qui ont suivi ont été décidés après lecture des échecs de ce même jeu : il n'est donc plus "
             "indépendant et ne doit pas être présenté comme une mesure à l'aveugle.\n",
             "## Recherche (questions avec réponse, %d scénarios)\n" % len(rec),
             "| Métrique | Valeur |", "|---|---|",
             f"| Recall@5 | {avg(rec):.3f} |", f"| nDCG@5 | {avg(ndcg):.3f} |", f"| MRR@10 | {avg(mrr):.3f} |",
             f"| Réponses avec bonne citation (document attendu et valeur) | {cite_ok}/{cite_n} |", ""]
    if unresolved:
        lines += [f"Scénarios dont la référence n'a pas pu être résolue dans le corpus : {', '.join(unresolved)}\n"]
    lines += ["## Comportement (statut attendu et valeur attendue)\n", "| Catégorie | Réussis |", "|---|---|"]
    lines += [f"| {k} | {a}/{n} |" for k, (a, n) in sorted(beh.items())]
    lines += [f"| **Total** | **{tot_ok}/{tot_n}** |", ""]
    if fails:
        lines += ["## Échecs\n"] + [f"- {i} ({c}) « {q} » -> {st} : {a}" for i, c, q, st, a in fails] + [""]
    Path(report_path).write_text("\n".join(lines))
    print("\n".join(lines))
    return dict(recall=avg(rec), ndcg=avg(ndcg), mrr=avg(mrr), ok=tot_ok, n=tot_n, fails=fails, cite=(cite_ok, cite_n))


if __name__ == "__main__":
    main()
