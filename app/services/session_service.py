"""
Session service using MongoDB.
Stores conversation history + last_muscle / last_symptom for context resolution.
"""
from datetime import datetime, timezone
from app.services.mongo_service import sessions
from app.config.settings import SESSION_MEMORY_LIMIT
from app.utils.logger import get_logger

log = get_logger("session_service")


def get_history(user_id: str) -> list[dict]:
    """Return last N messages for a user."""
    doc = sessions().find_one({"user_id": user_id}, {"messages": 1})
    if not doc:
        return []
    messages = doc.get("messages", [])
    return messages[-SESSION_MEMORY_LIMIT:]


def add_message(user_id: str, role: str, content: str) -> None:
    """Append a message and update timestamp."""
    sessions().update_one(
        {"user_id": user_id},
        {
            "$push": {"messages": {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()},
        },
        upsert=True,
    )


def get_context(user_id: str) -> dict:
    """Return last_muscle and last_symptom for context resolution."""
    doc = sessions().find_one({"user_id": user_id}, {"last_muscle": 1, "last_symptom": 1})
    if not doc:
        return {"last_muscle": None, "last_symptom": None}
    return {
        "last_muscle": doc.get("last_muscle"),
        "last_symptom": doc.get("last_symptom"),
    }


def update_context(user_id: str, muscle: str | None = None, symptom: str | None = None) -> None:
    """Update last known muscle/symptom for follow-up query resolution."""
    update = {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
    if muscle:
        update["$set"]["last_muscle"] = muscle
    if symptom:
        update["$set"]["last_symptom"] = symptom
    sessions().update_one({"user_id": user_id}, update, upsert=True)
