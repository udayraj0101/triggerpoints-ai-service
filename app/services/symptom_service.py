"""
Symptom lookup service.
"""
from app.services.mongo_service import symptoms
from app.utils.logger import get_logger

log = get_logger("symptom_service")


def find_symptom(query: str) -> dict | None:
    """Find symptom by exact or partial name match."""
    q = query.strip()
    col = symptoms()

    # Exact match
    doc = col.find_one({"name": {"$regex": f"^{q}$", "$options": "i"}})
    if doc:
        return doc

    # Partial match — query is substring of symptom name
    doc = col.find_one({"name": {"$regex": q, "$options": "i"}})
    if doc:
        return doc

    return None


def extract_symptom_from_query(query: str) -> dict | None:
    """
    Scan query text for any known symptom name.
    Also does reverse match — checks if key query words appear in symptom names.
    Returns best match found.
    """
    col = symptoms()
    q_lower = query.lower()

    all_symptoms = list(col.find({}, {"name": 1}))
    # Sort by length descending for greedy matching
    all_symptoms.sort(key=lambda s: len(s.get("name", "")), reverse=True)

    # Pass 1: symptom name is substring of query (exact)
    for s in all_symptoms:
        name = s.get("name", "")
        if name.lower() in q_lower:
            return find_symptom(name)

    # Pass 2: meaningful query words appear in symptom name
    stop_words = {"i", "have", "my", "a", "an", "the", "is", "are", "feel", "feeling",
                  "some", "bad", "very", "really", "bit", "little", "lot", "of", "in",
                  "at", "on", "with", "and", "or", "do", "does", "can", "get"}
    query_words = [w for w in q_lower.split() if w not in stop_words and len(w) > 2]

    best_match = None
    best_score = 0
    for s in all_symptoms:
        name = s.get("name", "").lower()
        matched_words = [w for w in query_words if w in name]
        # Score = matched words / total symptom words (precision)
        symptom_words = [w for w in name.split() if w not in stop_words and len(w) > 2]
        if not symptom_words:
            continue
        score = len(matched_words) / len(symptom_words)
        if score > best_score and len(matched_words) >= 1:
            best_score = score
            best_match = s.get("name")

    if best_score >= 0.4 and best_match:
        return find_symptom(best_match)

    # Pass 3: single meaningful word substring match for short queries
    if len(query_words) <= 2:
        for s in all_symptoms:
            name = s.get("name", "").lower()
            if any(w in name for w in query_words if len(w) >= 4):
                return find_symptom(s.get("name"))

    return None


def get_symptoms_for_region(region: str) -> list[dict]:
    """Return all symptoms in a body region."""
    return list(symptoms().find(
        {"region": {"$regex": region, "$options": "i"}},
        {"name": 1, "region": 1, "primary_muscles": 1}
    ))
