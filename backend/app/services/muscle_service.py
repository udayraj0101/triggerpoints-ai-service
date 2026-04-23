"""
Muscle lookup service.
Handles exact match, alias match, and fuzzy substring match.
"""
from app.services.mongo_service import muscles
from app.utils.logger import get_logger

log = get_logger("muscle_service")


def find_muscle(query: str) -> dict | None:
    """
    Find a muscle by name, alias, or fuzzy substring.
    Returns the full muscle document or None.
    """
    q = query.strip()
    col = muscles()

    # 1. Exact name match (case-insensitive)
    doc = col.find_one({"name": {"$regex": f"^{q}$", "$options": "i"}})
    if doc:
        return doc

    # 2. Alias match
    doc = col.find_one({"aliases": {"$regex": f"^{q}$", "$options": "i"}})
    if doc:
        return doc

    # 3. Substring match on name
    doc = col.find_one({"name": {"$regex": q, "$options": "i"}})
    if doc:
        return doc

    # 4. Substring match on aliases
    doc = col.find_one({"aliases": {"$regex": q, "$options": "i"}})
    if doc:
        return doc

    return None


def extract_muscle_from_query(query: str) -> dict | None:
    """
    Scan query text for any known muscle name or alias.
    Returns first match found.
    """
    col = muscles()
    q_lower = query.lower()

    # Fetch all muscle names and aliases (lightweight — ~100 muscles)
    all_muscles = list(col.find({}, {"name": 1, "aliases": 1}))

    # Sort by name length descending so longer names match first
    all_muscles.sort(key=lambda m: len(m.get("name", "")), reverse=True)

    for m in all_muscles:
        name = m.get("name", "")
        if name.lower() in q_lower:
            return find_muscle(name)
        for alias in m.get("aliases", []):
            if alias.lower() in q_lower:
                return find_muscle(name)

    return None


def get_muscles_for_region(region: str) -> list[dict]:
    """Return all muscles in a body region."""
    return list(muscles().find({"region": {"$regex": region, "$options": "i"}}, {"name": 1, "region": 1}))
