"""
scripts/seed_symptoms.py

Reads processed symptoms.json -> upserts into MongoDB `symptoms` collection.

Run: python -m scripts.seed_symptoms
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pymongo import UpdateOne

from app.config.settings import SYMPTOMS_JSON
from app.services.mongo_service import symptoms as symptoms_col
from app.utils.logger import get_logger

log = get_logger("seed_symptoms")


def run():
    log.info("=== Starting symptoms seeding ===")

    if not SYMPTOMS_JSON.exists():
        log.error(f"symptoms.json not found: {SYMPTOMS_JSON}")
        return

    data = json.loads(SYMPTOMS_JSON.read_text(encoding="utf-8"))
    log.info(f"Loaded {len(data)} symptoms from symptoms.json")

    ops = [
        UpdateOne(
            {"name": name},
            {"$set": {
                "name": name,
                "region": info.get("region", ""),
                "primary_muscles": info.get("primary_muscles", []),
                "secondary_muscles": info.get("secondary_muscles", []),
            }},
            upsert=True,
        )
        for name, info in data.items()
    ]

    result = symptoms_col().bulk_write(ops)
    log.info(f"Upserted {result.upserted_count} new, modified {result.modified_count} symptoms")

    symptoms_col().create_index("name")
    symptoms_col().create_index("region")
    symptoms_col().create_index("primary_muscles")
    log.info("Indexes created on symptoms collection")
    log.info("=== Symptoms seeding complete ===")


if __name__ == "__main__":
    run()
