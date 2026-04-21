"""
Vector search service using MongoDB Atlas Vector Search.
Replaces FAISS. Requires Atlas Vector Search index named 'vector_index'
on the knowledge_chunks collection with field 'embedding', 3072 dims, cosine.
"""
from google import genai
from google.genai import types

from app.config.settings import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, TOP_K_RESULTS
from app.services.mongo_service import knowledge_chunks
from app.utils.logger import get_logger

log = get_logger("vector_service")

_client = genai.Client(api_key=GEMINI_API_KEY)


def embed_query(text: str) -> list[float] | None:
    """Embed a query string for retrieval."""
    try:
        result = _client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
        return result.embeddings[0].values
    except Exception as e:
        log.error(f"Query embedding failed: {e}")
        return None


def search(query: str, top_k: int = TOP_K_RESULTS) -> list[str]:
    """
    Semantic search over knowledge_chunks using Atlas Vector Search.
    Returns list of relevant text chunks.
    """
    embedding = embed_query(query)
    if not embedding:
        return []

    try:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": embedding,
                    "numCandidates": top_k * 10,
                    "limit": top_k,
                }
            },
            {
                "$project": {
                    "text": 1,
                    "chapter": 1,
                    "title": 1,
                    "score": {"$meta": "vectorSearchScore"},
                    "_id": 0,
                }
            },
        ]

        results = list(knowledge_chunks().aggregate(pipeline))
        log.debug(f"Vector search returned {len(results)} results")

        # Return text chunks, filtering low-confidence results
        return [r["text"] for r in results if r.get("score", 0) > 0.6]

    except Exception as e:
        log.error(f"Vector search failed: {e}")
        # Fallback: text search
        return _text_search_fallback(query, top_k)


def _text_search_fallback(query: str, top_k: int) -> list[str]:
    """Simple text search fallback when vector search is unavailable."""
    try:
        results = list(knowledge_chunks().find(
            {"$text": {"$search": query}},
            {"text": 1, "score": {"$meta": "textScore"}},
        ).sort([("score", {"$meta": "textScore"})]).limit(top_k))
        return [r["text"] for r in results]
    except Exception:
        return []
