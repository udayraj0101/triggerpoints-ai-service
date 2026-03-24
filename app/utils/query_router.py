NAVIGATION_KEYWORDS = {
    "how do i", "where is", "how to", "navigate", "find", "open", "go to",
    "settings", "log", "start session", "contact", "history", "search",
}

SYMPTOM_KEYWORDS = {
    "symptom", "pain", "ache", "muscle", "region", "trigger point",
    "stiffness", "soreness", "tension", "spasm", "tightness",
}


def route(query: str) -> str:
    """Returns 'navigation', 'symptom', or 'knowledge'."""
    q = query.lower()
    if any(kw in q for kw in NAVIGATION_KEYWORDS):
        return "navigation"
    if any(kw in q for kw in SYMPTOM_KEYWORDS):
        return "symptom"
    return "knowledge"
