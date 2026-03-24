import json
import numpy as np
import faiss
from google import genai
from google.genai import types
from functools import lru_cache
from app.config.settings import (
    FAISS_INDEX_DIR, GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, TOP_K_RESULTS
)
from app.utils.logger import get_logger

_client = genai.Client(api_key=GEMINI_API_KEY)
log = get_logger("rag_service")


@lru_cache(maxsize=1)
def _load_index():
    try:
        index_path = FAISS_INDEX_DIR / "index.faiss"
        chunks_path = FAISS_INDEX_DIR / "chunks.json"
        if not index_path.exists() or not chunks_path.exists():
            log.warning(f"FAISS index not found at {FAISS_INDEX_DIR}")
            return None, []
        index = faiss.read_index(str(index_path))
        chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
        log.info(f"FAISS index loaded: {len(chunks)} chunks")
        return index, chunks
    except Exception as e:
        log.error(f"Failed to load FAISS index: {e}")
        return None, []


def _embed_query(text: str) -> np.ndarray:
    try:
        result = _client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
        return np.array([result.embeddings[0].values], dtype="float32")
    except Exception as e:
        log.error(f"Failed to embed query: {e}")
        return np.array([], dtype="float32")


def search(query: str, top_k: int = TOP_K_RESULTS) -> list[str]:
    try:
        index, chunks = _load_index()
        if index is None:
            log.debug("FAISS index not available, returning empty results")
            return []
        vec = _embed_query(query)
        if len(vec[0]) == 0:
            log.warning("Failed to embed query, returning empty results")
            return []
        _, indices = index.search(vec, top_k)
        results = [chunks[i] for i in indices[0] if i < len(chunks)]
        log.debug(f"RAG search returned {len(results)} results for query")
        return results
    except Exception as e:
        log.error(f"RAG search failed: {e}")
        return []
