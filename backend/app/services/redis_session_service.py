"""
Redis Session Storage for conversation history.
Stores full conversation history in Redis with TTL-based expiration.
"""
import json
import redis
from datetime import datetime
from typing import List, Dict, Optional
from app.config.settings import REDIS_URL, SESSION_MEMORY_LIMIT
from app.utils.logger import get_logger

log = get_logger("redis_session_service")


class RedisSessionService:
    """
    Store and retrieve conversation history from Redis.
    Uses Redis hashes for efficient storage and retrieval.
    """
    
    def __init__(self):
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        self.ttl_seconds = 30 * 24 * 3600  # 30 days
    
    def _get_session_key(self, user_id: str) -> str:
        """Generate Redis key for user session."""
        return f"session:{user_id}"
    
    def get_session(self, user_id: str) -> Optional[Dict]:
        """
        Retrieve full conversation session for a user.
        Returns None if no session exists.
        """
        session_key = self._get_session_key(user_id)
        session_data = self.redis_client.get(session_key)
        
        if session_data:
            log.debug(f"Redis session found for user: {user_id}")
            return json.loads(session_data)
        
        log.debug(f"No Redis session for user: {user_id}")
        return None
    
    def create_session(self, user_id: str) -> Dict:
        """Create a new session for a user."""
        session = {
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat()
        }
        self._save_session(user_id, session)
        log.info(f"New Redis session created for user: {user_id}")
        return session
    
    def add_message(self, user_id: str, role: str, content: str) -> None:
        """
        Add a message to the user's conversation history.
        Creates new session if one doesn't exist.
        """
        session = self.get_session(user_id)
        
        if not session:
            session = self.create_session(user_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        session["messages"].append(message)
        session["last_updated"] = datetime.utcnow().isoformat()
        
        self._save_session(user_id, session)
        log.debug(f"Message added to Redis session for user: {user_id}")
    
    def get_history(self, user_id: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get conversation history for a user.
        By default returns all messages (unlimited), but can be limited.
        """
        session = self.get_session(user_id)
        
        if not session:
            return []
        
        messages = session.get("messages", [])
        
        if limit:
            return messages[-limit:]
        
        return messages
    
    def _save_session(self, user_id: str, session: Dict) -> None:
        """Persist session to Redis with TTL."""
        session_key = self._get_session_key(user_id)
        self.redis_client.set(
            session_key,
            json.dumps(session),
            ex=self.ttl_seconds
        )
    
    def delete_session(self, user_id: str) -> bool:
        """Delete a user's session."""
        session_key = self._get_session_key(user_id)
        result = self.redis_client.delete(session_key)
        log.info(f"Redis session deleted for user: {user_id}")
        return result > 0
    
    def get_session_count(self) -> int:
        """Get total number of active sessions (for debugging)."""
        keys = self.redis_client.keys("session:*")
        return len(keys)


# Global instance
_session_service = None


def get_session_service() -> RedisSessionService:
    """Get or create the Redis session service instance."""
    global _session_service
    if _session_service is None:
        _session_service = RedisSessionService()
        log.info("Redis Session Service initialized")
    return _session_service


def add_message(user_id: str, role: str, content: str) -> None:
    """Convenience function to add a message."""
    get_session_service().add_message(user_id, role, content)


def get_history(user_id: str, limit: Optional[int] = None) -> List[Dict]:
    """Convenience function to get conversation history."""
    return get_session_service().get_history(user_id, limit)


def get_session(user_id: str) -> Optional[Dict]:
    """Convenience function to get full session."""
    return get_session_service().get_session(user_id)