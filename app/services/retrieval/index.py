"""Index Qdrant versionné + recherche avec FILTRE D'ACCÈS APPLIQUÉ DANS LA REQUÊTE (avant tout accès au contenu)."""
import json
import re
from pathlib import Path

from qdrant_client import QdrantClient, models

from app.schemas.retrieval import SearchHit, UserContext
from app.services.retrieval.embeddings import Embedder

INDEX_VERSION = "v1"
CODE_RE = re.compile(r"\b[eb]\d{3}\b", re.I)   # codes d'erreur (E301, B101…)
CODE_BOOST = 0.5                               # bonus lexical : identifiant exact présent dans le passage
POOL = 100                                     # candidats vectoriels avant ré-ordonnancement hybride


def collection_name(embedder: Embedder) -> str:
    return f"chunks_text_{embedder.name}_{INDEX_VERSION}"


def build_index(chunks_jsonl: Path, client: QdrantClient, embedder: Embedder, batch: int = 128) -> int:
    name = collection_name(embedder)
    if client.collection_exists(name):
        client.delete_collection(name)
    client.create_collection(name, vectors_config=models.VectorParams(size=embedder.dim, distance=models.Distance.COSINE))
    rows = [json.loads(line) for line in chunks_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    for i in range(0, len(rows), batch):
        part = rows[i:i + batch]
        vecs = embedder.embed([f"{r.get('equipment_model') or ''} {r.get('section') or ''}. {r['text']}" for r in part])
        client.upsert(name, points=[models.PointStruct(id=i + j, vector=v, payload=r)
                                    for j, (v, r) in enumerate(zip(vecs, part))])
    return len(rows)


def known_models(client: QdrantClient, embedder: Embedder) -> set[str]:
    seen: set[str] = set()
    offset = None
    while True:
        pts, offset = client.scroll(collection_name(embedder), limit=256, offset=offset, with_payload=["equipment_model"])
        seen |= {p.payload["equipment_model"] for p in pts if p.payload.get("equipment_model")}
        if offset is None:
            return seen


def search(client: QdrantClient, embedder: Embedder, query: str, user: UserContext, *, top_k: int = 5,
           equipment_model: str | None = None, include_obsolete: bool = False) -> list[SearchHit]:
    if not user.groups:
        return []  # aucun droit : aucune récupération
    must = [models.FieldCondition(key="access_groups", match=models.MatchAny(any=user.groups))]
    if not include_obsolete:
        must.append(models.FieldCondition(key="validity_status", match=models.MatchValue(value="valid")))
    if equipment_model:
        # documents du modèle demandé + documents généraux (sans modèle)
        must.append(models.Filter(should=[
            models.FieldCondition(key="equipment_model", match=models.MatchValue(value=equipment_model)),
            models.IsNullCondition(is_null=models.PayloadField(key="equipment_model"))]))
    codes = {c.upper() for c in CODE_RE.findall(query)}
    res = client.query_points(collection_name(embedder), query=embedder.embed([query])[0],
                              query_filter=models.Filter(must=must), limit=POOL if codes else top_k,
                              with_payload=True).points
    hits = []
    for p in res:
        boost = CODE_BOOST if codes and any(re.search(rf"\b{c}\b", p.payload.get("text", ""), re.I) for c in codes) else 0.0
        hits.append(SearchHit(score=p.score + boost, **{k: p.payload.get(k) for k in SearchHit.model_fields if k != "score"}))
    return sorted(hits, key=lambda h: -h.score)[:top_k]
