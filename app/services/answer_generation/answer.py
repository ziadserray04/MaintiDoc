"""Décision réponse / clarification / abstention + réponse extractive citée (backend sans LLM, CPU).

Le VLM/LLM (Qwen2.5-VL) remplacera `compose_answer` en profil gpu-demo ; les garde-fous (droits, abstention,
vérification de support) restent identiques.
"""
import re

from qdrant_client import QdrantClient

from app.schemas.answer import AnswerResponse, Citation
from app.schemas.retrieval import SearchHit, UserContext
from app.services.answer_generation.evidence import verify_support
from app.services.retrieval.embeddings import Embedder, normalize
from app.services.retrieval.index import CODE_RE, search

MODEL_RE = re.compile(r"\bhn[\s-]?([a-z]\d{1,3})\b", re.I)
# Seuil de similarité cosinus PROPRE au backend `hashing` (à recalibrer avec un vrai modèle d'embeddings).
MIN_SCORE = 0.12
FR_STOP = {"comment", "faire", "quelle", "quel", "quels", "quelles", "est", "sont", "que", "qui", "quoi", "pour",
           "dans", "avec", "sans", "cette", "cet", "les", "des", "une", "aux", "sur", "par", "est-ce", "signifie",
           "faut", "partir", "combien", "helionova", "peut", "puis", "elle", "lui", "leur", "mon", "son", "ses", "mes", "tout", "tous", "plus", "il"}
CONFLICT_MIN_LEXICAL = 0.6  # part des mots-clés de la question que CHAQUE passage comparé doit contenir
MIN_LEXICAL = 0.5  # part des mots-clés de la question qui doivent figurer dans la source
NO_SOURCE = "Je n'ai pas de source accessible et suffisante pour répondre à cette question."


def models_in_query(question: str) -> list[str]:
    return sorted({f"HN-{m.upper()}" for m in MODEL_RE.findall(question)})


def lexical_support(question: str, text: str) -> float:
    """Garde-fou indépendant du modèle d'embeddings : la source doit contenir les mots-clés de la question."""
    q = {w for w in re.findall(r"[a-z0-9]+", normalize(MODEL_RE.sub(" ", question))) if len(w) > 2 and w not in FR_STOP}
    if not q:
        return 0.0
    t = normalize(text)
    # radical de 4 lettres pour les mots longs : « serrer » ~ « serrage », « limite » ~ « limitation »
    return sum(1 for w in q if (w[:4] if len(w) > 5 else w) in t) / len(q)


def _content_words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", normalize(MODEL_RE.sub(" ", text))) if len(w) > 2 and w not in FR_STOP}


def best_segment(text: str, question: str, n: int = 2) -> str:
    parts = [p.strip() for p in re.split(r"(?<=\.) ", text) if p.strip()]
    q = _content_words(question)
    ranked = sorted(parts, key=lambda p: -len(q & _content_words(p)))
    return " ".join(ranked[:n])


UNIT_NUM_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(°C|N\.m|kΩ|kWh|kW|mm2|mV|kg|V|A|%)")


def _quantities(text: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for num, unit in UNIT_NUM_RE.findall(text):
        out.setdefault(unit, set()).add(num.replace(",", "."))
    return out


def _quantity_segment(text: str, question: str) -> str:
    """Phrase qui contient une valeur chiffrée avec unité et qui ressemble le plus à la question."""
    parts = [p.strip() for p in re.split(r"(?<=\.) ", text) if UNIT_NUM_RE.search(p)]
    q = _content_words(question)
    return max(parts, key=lambda p: len(q & _content_words(p)), default="")


def find_conflict(question: str, top: SearchHit, pool: list[SearchHit]) -> SearchHit | None:
    """Autre document VALIDE du même modèle qui répond à la même question avec une valeur différente (même unité).
    Les deux passages comparés doivent chacun reprendre l'essentiel des mots de la question : sans cela, deux grandeurs
    différentes (alarme haute vs seuil de charge basse, par exemple) ne sont pas une contradiction."""
    if not top.equipment_model:
        return None

    def seg(h: SearchHit) -> str:
        t = h.text if h.element_type == "table" else _quantity_segment(h.text, question)
        return f"{t} température degrés" if "°C" in t else t  # l'unité vaut le mot : « 58 °C » répond à « quelle température »

    mine_seg = seg(top)
    if lexical_support(question, mine_seg) < CONFLICT_MIN_LEXICAL:
        return None
    mine = _quantities(mine_seg)
    for h in pool:
        if h.document_id == top.document_id or h.validity_status != "valid" or h.equipment_model != top.equipment_model:
            continue
        s_h = seg(h)
        if lexical_support(question, s_h) < CONFLICT_MIN_LEXICAL:
            continue
        theirs = _quantities(s_h)
        if any(theirs.get(u) and not (theirs[u] & vals) for u, vals in mine.items()):
            return h
    return None


def _cite(h: SearchHit) -> Citation:
    return Citation(document_id=h.document_id, version=h.version, page=h.page, element_id=h.element_id,
                    element_type=h.element_type, retrieval_score=round(h.score, 3))


def answer_question(question: str, user: UserContext, client: QdrantClient, embedder: Embedder,
                    known: set[str]) -> AnswerResponse:
    mentioned = models_in_query(question)
    if len(mentioned) == 2 and sum(m.startswith("HN-B") for m in mentioned) == 1:
        return _answer_compat(question, mentioned, user, client, embedder, known)
    if len(mentioned) > 1:
        return AnswerResponse(status="needs_clarification", answer="Plusieurs modèles sont mentionnés.",
                              clarification_question="Sur quel modèle exact intervenez-vous ? (voir la plaque signalétique)")
    model = mentioned[0] if mentioned else None
    if model and model not in known:
        # même message qu'une absence de droit : on ne révèle pas ce qui existe ou non
        return AnswerResponse(status="abstained", answer=NO_SOURCE,
                              uncertainties=[f"Aucune documentation disponible pour le modèle {model}."])
    pool = search(client, embedder, question, user, top_k=10, equipment_model=model)
    hits = pool  # reclassement lexical sur tout le pool (10) : le passage exact peut être hors des 5 premiers vecteurs
    if not hits or hits[0].score < MIN_SCORE or max(lexical_support(question, h.text) for h in hits) < MIN_LEXICAL:
        return AnswerResponse(status="abstained", answer=NO_SOURCE)
    # le passage retenu est celui qui contient le plus de mots-clés de la question (évite les titres/fragments génériques)
    hits = sorted(hits, key=lambda h: -(lexical_support(question, h.text) + 0.5 * h.score))
    if model is None:
        specific = {h.equipment_model for h in hits if h.equipment_model}
        if hits[0].equipment_model and len(specific) > 1:
            return AnswerResponse(
                status="needs_clarification",
                answer="Les codes et seuils diffèrent d'un modèle à l'autre ; le modèle exact est nécessaire.",
                uncertainties=["Modèle d'équipement non identifié."],
                clarification_question="Quel est le modèle exact de l'équipement ? Pouvez-vous photographier la plaque signalétique ?")
    top = hits[0]
    codes = {c.upper() for c in CODE_RE.findall(question)}
    if codes:
        # question sur un code d'erreur : la ligne du tableau (code, titre, cause, action) est l'unité de réponse
        with_code = [h for h in hits if h.element_type == "table" and any(re.search(rf"\b{c}\b", h.text, re.I) for c in codes)]
        code_table = [h for h in with_code if (h.section or "").startswith("Tableau (Code")]
        top = (code_table or with_code or [top])[0]
    if not codes and lexical_support(question, top.text) < MIN_LEXICAL:
        return AnswerResponse(status="abstained", answer=NO_SOURCE)
    claim = top.text if top.element_type == "table" else best_segment(top.text, question)  # une ligne de tableau est l'unité de réponse
    other = find_conflict(question, top, pool)
    if other is not None:
        a = claim if top.element_type == "table" else _quantity_segment(top.text, question)
        b = other.text if other.element_type == "table" else _quantity_segment(other.text, question)
        return AnswerResponse(
            status="conflicting_sources",
            answer=(f"Deux sources valides donnent des valeurs différentes : « {a} » ({top.document_id}, p. {top.page}) "
                    f"et « {b} » ({other.document_id}, p. {other.page}). Je ne tranche pas entre elles."),
            citations=[_cite(top), _cite(other)],
            uncertainties=["Sources contradictoires : faire valider la valeur par le responsable documentaire avant d'intervenir."])
    check = verify_support(claim, top.text)
    if not check.supported:
        return AnswerResponse(status="abstained", answer=NO_SOURCE, uncertainties=[check.reason])
    return AnswerResponse(status="answered", answer=claim, citations=[_cite(top)])


def _answer_compat(question, mentioned, user, client, embedder, known) -> AnswerResponse:
    """Question onduleur + batterie : la ligne de la matrice de compatibilité du manuel de l'onduleur fait foi."""
    battery = next(m for m in mentioned if m.startswith("HN-B"))
    inverter = next(m for m in mentioned if m != battery)
    if inverter not in known or battery not in known:
        return AnswerResponse(status="abstained", answer=NO_SOURCE)
    hits = search(client, embedder, f"Matrice de compatibilité batterie {battery}", user, top_k=20, equipment_model=inverter)
    row = next((h for h in hits if h.element_type == "table" and h.equipment_model == inverter
                and re.search(rf"\b{battery}\b", h.text) and "Compatible" in h.text), None)
    if row is None:
        return AnswerResponse(status="abstained", answer=NO_SOURCE)
    return AnswerResponse(status="answered", answer=row.text, citations=[_cite(row)])
