"""
scripts/seed_symptoms.py

Reads processed symptoms.json -> embeds each symptom -> upserts into MongoDB `symptoms` collection.

Embedding text combines name + region + muscles so semantic queries
("my butt hurts when sitting") can match clinical names ("Anal Pain").

Run: python -m scripts.seed_symptoms
"""
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from google.genai import types
from pymongo import UpdateOne

from app.config.settings import GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, SYMPTOMS_JSON
from app.services.mongo_service import symptoms as symptoms_col
from app.utils.logger import get_logger

log = get_logger("seed_symptoms")

client = genai.Client(api_key=GEMINI_API_KEY)


def build_symptom_text(name: str, info: dict) -> str:
    """Rich semantic text for embedding — improves recall on paraphrased queries."""
    parts = [f"Symptom: {name}"]
    if info.get("region"):
        parts.append(f"Body region: {info['region']}")
    if info.get("primary_muscles"):
        parts.append(f"Primary muscles: {', '.join(info['primary_muscles'])}")
    if info.get("secondary_muscles"):
        parts.append(f"Secondary muscles: {', '.join(info['secondary_muscles'])}")
    return ". ".join(parts)


def embed_text(text: str) -> list[float] | None:
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


def run():
    log.info("=== Starting symptoms seeding ===")

    if not SYMPTOMS_JSON.exists():
        log.error(f"symptoms.json not found: {SYMPTOMS_JSON}")
        return

    data = json.loads(SYMPTOMS_JSON.read_text(encoding="utf-8"))
    log.info(f"Loaded {len(data)} symptoms from symptoms.json")

    ops = []
    embedded = 0
    skipped = 0
    failed = 0

    for name, info in data.items():
        existing = symptoms_col().find_one(
            {"name": name},
            {"embedding": 1, "embedding_text": 1},
        )
        text_for_embedding = build_symptom_text(name, info)

        if existing and existing.get("embedding") and existing.get("embedding_text") == text_for_embedding:
            skipped += 1
            continue

        log.info(f"Embedding: {name}")
        embedding = embed_text(text_for_embedding)

        if embedding is None:
            failed += 1
            continue

        ops.append(UpdateOne(
            {"name": name},
            {"$set": {
                "name": name,
                "region": info.get("region", ""),
                "primary_muscles": info.get("primary_muscles", []),
                "secondary_muscles": info.get("secondary_muscles", []),
                "embedding": embedding,
                "embedding_text": text_for_embedding,
            }},
            upsert=True,
        ))
        embedded += 1

        if len(ops) >= 50:
            symptoms_col().bulk_write(ops)
            log.info(f"  Flushed {len(ops)} symptoms to MongoDB")
            ops = []

        time.sleep(0.1)  # rate limit cushion

    if ops:
        symptoms_col().bulk_write(ops)

    log.info(f"✓ Embedded {embedded} symptoms ({skipped} unchanged, {failed} failed)")

    symptoms_col().create_index("name")
    symptoms_col().create_index("region")
    symptoms_col().create_index("primary_muscles")
    log.info("Standard indexes created on symptoms collection")

    log.info("")
    log.info("=" * 60)
    log.info("NEXT STEP: Create Atlas Vector Search index")
    log.info("  Collection: symptoms")
    log.info("  Index name: symptom_vector_index")
    log.info("  Field: embedding   Dimensions: 3072   Similarity: cosine")
    log.info("=" * 60)
    log.info("=== Symptoms seeding complete ===")


if __name__ == "__main__":
    run()
