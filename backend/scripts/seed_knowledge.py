"""
scripts/seed_knowledge.py

Reads ebook_data.json → chunks all meaningful content → embeds with Gemini
→ stores in MongoDB `knowledge_chunks` collection.

After running this script, create an Atlas Vector Search index on the collection:
  Field: "embedding"
  Dimensions: 3072
  Similarity: cosine

Run: python -m scripts.seed_knowledge
"""
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai import types
from pymongo import UpdateOne

from app.config.settings import GEMINI_API_KEY, EBOOK_JSON, CHUNK_SIZE_WORDS

GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
from app.services.mongo_service import knowledge_chunks as chunks_col
from app.utils.logger import get_logger

log = get_logger("seed_knowledge")

client = genai.Client(api_key=GEMINI_API_KEY)

# Page types worth indexing
INDEXABLE_TYPES = {"prose", "table", "protocol", "muscle"}


def split_into_chunks(text: str, max_words: int = CHUNK_SIZE_WORDS) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    if len(words) <= max_words:
        return [text]

    chunks = []
    overlap = max_words // 5  # 20% overlap for context continuity
    step = max_words - overlap
    i = 0
    while i < len(words):
        chunk_words = words[i: i + max_words]
        chunks.append(" ".join(chunk_words))
        i += step
    return chunks


def embed_text(text: str) -> list[float] | None:
    """Embed a single text string using Gemini embedding model."""
    try:
        result = client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        return result.embeddings[0].values
    except Exception as e:
        log.error(f"Embedding failed: {e}")
        return None


def build_chunk_text(page: dict) -> str:
    """
    Build rich text for a chunk by prepending metadata as context.
    This improves retrieval quality significantly.
    """
    parts = []
    if page.get("chapter"):
        parts.append(f"Chapter: {page['chapter']}")
    if page.get("title"):
        parts.append(f"Topic: {page['title']}")
    if page.get("content"):
        parts.append(page["content"])
    return "\n".join(parts)


def run():
    log.info("=== Starting knowledge seeding ===")

    pages = json.loads(EBOOK_JSON.read_text(encoding="utf-8"))
    indexable = [
        p for p in pages
        if p.get("type") in INDEXABLE_TYPES and p.get("content")
    ]
    log.info(f"Indexable pages: {len(indexable)} / {len(pages)} total")

    ops = []
    total_chunks = 0
    skipped = 0

    for page in indexable:
        full_text = build_chunk_text(page)
        chunks = split_into_chunks(full_text)

        for chunk_idx, chunk_text in enumerate(chunks):
            chunk_id = f"page_{page['page_number']}_chunk_{chunk_idx}"

            # Check if already embedded (avoid re-embedding on re-runs)
            existing = chunks_col().find_one({"chunk_id": chunk_id}, {"_id": 1, "embedding": 1})
            if existing and existing.get("embedding"):
                skipped += 1
                continue

            log.info(f"Embedding {chunk_id} ({len(chunk_text.split())} words)")
            embedding = embed_text(chunk_text)

            if embedding is None:
                log.warning(f"Skipping {chunk_id} — embedding failed")
                continue

            doc = {
                "chunk_id": chunk_id,
                "page_number": page["page_number"],
                "page_type": page["type"],
                "chapter": page.get("chapter"),
                "title": page.get("title"),
                "text": chunk_text,
                "embedding": embedding,
            }

            ops.append(UpdateOne(
                {"chunk_id": chunk_id},
                {"$set": doc},
                upsert=True,
            ))
            total_chunks += 1

            # Flush every 50 to avoid memory buildup
            if len(ops) >= 50:
                chunks_col().bulk_write(ops)
                log.info(f"  Flushed 50 chunks to MongoDB")
                ops = []

            # Rate limit: gemini-embedding-004 allows ~1500 RPM but be safe
            time.sleep(0.1)

    # Flush remaining
    if ops:
        chunks_col().bulk_write(ops)

    log.info(f"✓ Embedded and stored {total_chunks} new chunks ({skipped} already existed)")

    # Create standard indexes (Vector Search index must be created in Atlas UI or API)
    chunks_col().create_index("chunk_id", unique=True)
    chunks_col().create_index("page_type")
    chunks_col().create_index("chapter")
    log.info("✓ Standard indexes created on knowledge_chunks collection")

    log.info("")
    log.info("=" * 60)
    log.info("NEXT STEP: Create Atlas Vector Search index")
    log.info("  Collection: knowledge_chunks")
    log.info("  Index name: vector_index")
    log.info("  Field: embedding")
    log.info("  Dimensions: 3072")
    log.info("  Similarity: cosine")
    log.info("=" * 60)
    log.info("=== Knowledge seeding complete ===")


if __name__ == "__main__":
    run()
