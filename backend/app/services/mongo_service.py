"""
MongoDB connection and collection accessors.
Single client instance shared across the app.
"""
from pymongo import MongoClient
from pymongo.collection import Collection
from app.config.settings import MONGODB_URI, MONGODB_DB
from app.utils.logger import get_logger

log = get_logger("mongo_service")

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
        log.info("MongoDB client created")
    return _client


def get_db():
    return get_client()[MONGODB_DB]


def muscles() -> Collection:
    return get_db()["muscles"]


def symptoms() -> Collection:
    return get_db()["symptoms"]


def knowledge_chunks() -> Collection:
    return get_db()["knowledge_chunks"]


def sessions() -> Collection:
    return get_db()["sessions"]


def ping():
    """Test connection — call at startup."""
    get_client().admin.command("ping")
    log.info(f"✓ MongoDB connected → db: {MONGODB_DB}")
