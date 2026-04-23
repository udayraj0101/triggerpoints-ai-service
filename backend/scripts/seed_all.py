"""
scripts/seed_all.py

Runs the full data pipeline in order:
  1. seed_symptoms  — symptoms.xlsx → MongoDB symptoms collection
  2. extract_muscles — ebook_data.json muscle pages → MongoDB muscles collection
  3. seed_knowledge  — ebook_data.json prose/table pages → MongoDB knowledge_chunks (with embeddings)

Run: python -m scripts.seed_all

Note: seed_knowledge embeds ~200+ chunks via Gemini API.
      At 0.1s delay per chunk this takes ~3-5 minutes.
      Re-runs are safe — already-embedded chunks are skipped.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.logger import get_logger

log = get_logger("seed_all")


def main():
    log.info("=" * 60)
    log.info("TRIGGERPOINTS DATA PIPELINE")
    log.info("=" * 60)

    log.info("\n[1/3] Seeding symptoms...")
    from scripts.seed_symptoms import run as seed_symptoms
    seed_symptoms()

    log.info("\n[2/3] Extracting muscles...")
    from scripts.extract_muscles import run as extract_muscles
    extract_muscles()

    log.info("\n[3/3] Seeding knowledge chunks with embeddings...")
    from scripts.seed_knowledge import run as seed_knowledge
    seed_knowledge()

    log.info("\n" + "=" * 60)
    log.info("ALL DONE")
    log.info("=" * 60)
    log.info("")
    log.info("IMPORTANT: Create Atlas Vector Search index manually:")
    log.info("  1. Go to MongoDB Atlas → your cluster → Search")
    log.info("  2. Create Search Index → JSON editor")
    log.info("  3. Collection: triggerpoints.knowledge_chunks")
    log.info("  4. Index name: vector_index")
    log.info("  5. Paste this definition:")
    log.info("""  {
    "fields": [{
      "type": "vector",
      "path": "embedding",
      "numDimensions": 3072,
      "similarity": "cosine"
    }]
  }""")


if __name__ == "__main__":
    main()
