"""
Symptom lookup service.

Strategy for resolving a free-text query → a symptom doc:
  1. Exact / substring match on symptom name (free, deterministic).
  2. Atlas Vector Search on the symptoms collection (semantic).
     - If the top match is clearly ahead → return it as the resolved symptom.
     - If multiple matches score close together → return the top match plus
       alternative names so the chat layer can ask the user to disambiguate.
  3. No confident match → return (None, []). Caller falls back to generic guidance.
"""
from app.services.mongo_service import symptoms
from app.services.vector_service import embed_query
from app.utils.logger import get_logger

log = get_logger("symptom_service")

VECTOR_INDEX_NAME = "symptom_vector_index"
VECTOR_MIN_SCORE = 0.72          # below this → no confident match at all
AMBIGUITY_GAP = 0.03             # if top-1 minus top-2 score < this → ambiguous
MAX_ALTERNATIVES = 3             # number of alternative names to surface


def find_symptom(query: str) -> dict | None:
    """Find symptom by exact or partial name match."""
    q = query.strip()
    col = symptoms()

    doc = col.find_one({"name": {"$regex": f"^{q}$", "$options": "i"}})
    if doc:
        return doc

    doc = col.find_one({"name": {"$regex": q, "$options": "i"}})
    if doc:
        return doc

    return None


def find_symptom_candidates_by_vector(query: str, top_k: int = 5) -> list[dict]:
    """Top-K semantic candidates from Atlas Vector Search, sorted by score desc."""
    embedding = embed_query(query)
    if not embedding:
        return []

    try:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": VECTOR_INDEX_NAME,
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                }
            },
            {
                "$project": {
                    "name": 1,
                    "region": 1,
                    "primary_muscles": 1,
                    "secondary_muscles": 1,
                    "score": {"$meta": "vectorSearchScore"},
                    "_id": 0,
                }
            },
        ]
        return list(symptoms().aggregate(pipeline))
    except Exception as e:
        log.error(f"Symptom vector search failed: {e}")
        return []


def resolve_symptom_from_query(query: str) -> tuple[dict | None, list[str]]:
    """
    Resolve a user query to a symptom doc plus optional alternatives.

    Returns:
        (doc, alternatives)
        - doc: the best-matching symptom doc (or None if no confident match)
        - alternatives: list of other symptom names worth offering when the
          query is ambiguous (empty list if the match is unambiguous)
    """
    q_lower = query.lower()

    # Pass 1: exact / substring match — symptom name appears verbatim in query
    all_symptoms = list(symptoms().find({}, {"name": 1}))
    all_symptoms.sort(key=lambda s: len(s.get("name", "")), reverse=True)

    for s in all_symptoms:
        name = s.get("name", "")
        if name and name.lower() in q_lower:
            log.debug(f"Symptom substring match: '{name}'")
            return find_symptom(name), []

    # Pass 2: semantic vector match (top-K candidates)
    candidates = find_symptom_candidates_by_vector(query, top_k=MAX_ALTERNATIVES + 1)
    if not candidates:
        return None, []

    top = candidates[0]
    top_score = top.get("score", 0)

    if top_score < VECTOR_MIN_SCORE:
        log.debug(f"Top vector score {top_score:.3f} below threshold for '{query}'")
        return None, []

    # Decide if the result is ambiguous: top-1 and top-2 within AMBIGUITY_GAP
    second_score = candidates[1].get("score", 0) if len(candidates) > 1 else 0
    is_ambiguous = (top_score - second_score) < AMBIGUITY_GAP

    if not is_ambiguous:
        log.debug(f"Symptom vector match: '{top['name']}' (score={top_score:.3f}, clear winner)")
        return top, []

    # Ambiguous: surface alternatives that are also above threshold
    alternatives = [
        c["name"] for c in candidates[1:]
        if c.get("score", 0) >= VECTOR_MIN_SCORE
    ][:MAX_ALTERNATIVES]
    log.debug(
        f"Symptom vector ambiguous: top='{top['name']}' ({top_score:.3f}), "
        f"alternatives={alternatives}"
    )
    return top, alternatives


def extract_symptom_from_query(query: str) -> dict | None:
    """Backwards-compatible accessor — returns just the resolved doc."""
    doc, _ = resolve_symptom_from_query(query)
    return doc


def get_symptoms_for_region(region: str) -> list[dict]:
    """Return all symptoms in a body region."""
    return list(symptoms().find(
        {"region": {"$regex": region, "$options": "i"}},
        {"name": 1, "region": 1, "primary_muscles": 1}
    ))
