from collections import defaultdict, deque
from app.config.settings import SESSION_MEMORY_LIMIT
from app.utils.logger import get_logger

log = get_logger("memory_service")

_sessions: dict[str, deque] = defaultdict(lambda: deque(maxlen=SESSION_MEMORY_LIMIT))


def get_history(user_id: str) -> list[dict]:
    history = list(_sessions[user_id])
    log.debug(f"Retrieved {len(history)} messages for user: {user_id}")
    return history


def add_message(user_id: str, role: str, content: str) -> None:
    _sessions[user_id].append({"role": role, "content": content})
    log.debug(f"Added {role} message for user: {user_id}")
