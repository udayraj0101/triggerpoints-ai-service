"""
scripts/extract_muscles.py

Extracts every muscle from ebook_data.json.
Uses Gemini to normalize inconsistent page content into clean structured docs.
Cross-references symptoms.xlsx to attach symptoms_caused[] to each muscle.
Upserts into MongoDB `muscles` collection.

Run: python -m scripts.extract_muscles
"""
import json
import time
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from google import genai
from google.genai import types
from pymongo import UpdateOne

from app.config.settings import GEMINI_API_KEY, EBOOK_JSON, EXCEL_FILE
from app.services.mongo_service import muscles as muscles_col
from app.utils.logger import get_logger

log = get_logger("extract_muscles")

client = genai.Client(api_key=GEMINI_API_KEY)

# Known aliases — extend as needed
MUSCLE_ALIASES: dict[str, list[str]] = {
    "Sternocleidomastoid": ["SCM", "sternocleidomastoid", "sterno"],
    "Quadratus Lumborum": ["QL", "quadratus lumborum"],
    "Temporomandibular Joint": ["TMJ"],
    "Iliopsoas": ["Psoas", "psoas major", "iliacus"],
    "Tensor Fasciae Latae": ["TFL", "tensor fasciae latae"],
    "Extensor Digitorum Longus": ["EDL"],
    "Flexor Digitorum Longus": ["FDL"],
    "Fibulares": ["Peroneus", "peroneal muscles", "fibularis"],
    "Gastrocnemius": ["gastroc"],
    "Trapezius": ["trap", "traps"],
    "Pectoralis Major": ["pec major", "pectoralis"],
    "Pectoralis Minor": ["pec minor"],
    "Gluteus Maximus": ["glute max", "gluteus max"],
    "Gluteus Medius": ["glute med", "gluteus med"],
    "Gluteus Minimus": ["glute min", "gluteus min"],
    "Rectus Abdominis": ["abs", "six pack", "rectus"],
    "Levator Scapulae": ["levator scap"],
    "Semispinalis Capitis": ["semispinalis"],
    "Obliquus Capitis Inferior": ["suboccipital"],
}

EXTRACTION_PROMPT = """You are a medical data extractor for a trigger point therapy database.

Extract structured data from this muscle page content. Return ONLY valid JSON, no markdown.

Page title: {title}
Page content:
{content}

Return this exact JSON structure (use null for missing fields):
{{
  "name": "canonical muscle name",
  "origin": "origin attachment text",
  "insertion": "insertion attachment text", 
  "action": "muscle action/function",
  "nerve_supply": "nerve supply details",
  "referred_pain_pattern": "referred pain description and zones",
  "trigger_point_location": "where trigger points are located",
  "clinical_notes": "clinical indications, conditions, differential diagnosis",
  "self_help": "self-help techniques and advice for patients",
  "causes": "common causes of trigger point activation",
  "connections": "related muscles and connections"
}}"""


def extract_muscle_name(title: str) -> str:
    """Clean muscle name from page title."""
    # Remove suffixes like (Overview), (Continued), (Self-Help), etc.
    name = re.sub(r'\s*\(.*?\)', '', title).strip()
    # Remove trailing descriptors
    for suffix in [" Overview", " Details", " Anatomy", " Treatment", " Continued",
                   " Self-Help", " Summary", " Conclusion", " Start"]:
        name = name.replace(suffix, "").strip()
    return name


def get_aliases(muscle_name: str) -> list[str]:
    """Return known aliases for a muscle, always include lowercase variant."""
    aliases = [muscle_name.lower()]
    for canonical, alias_list in MUSCLE_ALIASES.items():
        if canonical.lower() in muscle_name.lower():
            aliases.extend(alias_list)
    return list(set(aliases))


def normalize_with_gemini(title: str, content: str) -> dict | None:
    """Use Gemini to extract structured fields from a muscle page."""
    prompt = EXTRACTION_PROMPT.format(title=title, content=content[:3000])
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
        text = response.text.strip()
        # Strip markdown code fences if present
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return json.loads(text)
    except Exception as e:
        log.warning(f"Gemini extraction failed for '{title}': {e}")
        return None


def build_symptoms_map() -> dict[str, list[str]]:
    """
    Build muscle_name → [symptom_names] map from symptoms.xlsx.
    Returns both primary and secondary associations.
    """
    try:
        xl = pd.ExcelFile(EXCEL_FILE)
        symptom_map: dict[str, list[str]] = {}

        for sheet in xl.sheet_names:
            df = xl.parse(sheet, header=None)
            # Find rows that look like symptom/muscle data
            for _, row in df.iterrows():
                row_vals = [str(v).strip() for v in row if pd.notna(v) and str(v).strip()]
                if len(row_vals) >= 2:
                    symptom = row_vals[0]
                    for muscle in row_vals[1:]:
                        if muscle and muscle != symptom:
                            symptom_map.setdefault(muscle, [])
                            if symptom not in symptom_map[muscle]:
                                symptom_map[muscle].append(symptom)
        return symptom_map
    except Exception as e:
        log.warning(f"Could not build symptoms map from Excel: {e}")
        return {}


def build_symptoms_map_from_json() -> dict[str, list[str]]:
    """
    Fallback: build muscle → symptoms map from processed symptoms.json if it exists.
    """
    processed = Path(__file__).parent.parent / "app" / "data" / "processed" / "symptoms.json"
    if not processed.exists():
        return {}
    data = json.loads(processed.read_text(encoding="utf-8"))
    muscle_map: dict[str, list[str]] = {}
    for symptom_name, info in data.items():
        for m in info.get("primary_muscles", []) + info.get("secondary_muscles", []):
            muscle_map.setdefault(m, [])
            if symptom_name not in muscle_map[m]:
                muscle_map[m].append(symptom_name)
    return muscle_map


def get_region_for_muscle(muscle_name: str, chapter: str) -> str:
    """Infer body region from chapter name."""
    chapter_lower = chapter.lower()
    if "face" in chapter_lower or "head" in chapter_lower or "neck" in chapter_lower:
        return "Face, Head and Neck"
    if "shoulder" in chapter_lower or "upper arm" in chapter_lower:
        return "Shoulder & Upper Arm"
    if "forearm" in chapter_lower or "hand" in chapter_lower:
        return "Forearm & Hand"
    if "trunk" in chapter_lower or "spine" in chapter_lower or "torso" in chapter_lower:
        return "Spine & Torso"
    if "hip" in chapter_lower or "thigh" in chapter_lower or "knee" in chapter_lower:
        return "Hip, Thigh & Knee"
    if "leg" in chapter_lower or "ankle" in chapter_lower or "foot" in chapter_lower:
        return "Leg, Ankle & Foot"
    if "lumbo" in chapter_lower or "pelvic" in chapter_lower:
        return "Lumbo-Pelvic"
    return "General"


def run():
    log.info("=== Starting muscle extraction ===")

    pages = json.loads(EBOOK_JSON.read_text(encoding="utf-8"))
    muscle_pages = [p for p in pages if p.get("type") == "muscle" and p.get("content")]
    log.info(f"Found {len(muscle_pages)} muscle pages")

    # Build symptoms map
    symptoms_map = build_symptoms_map_from_json()
    if not symptoms_map:
        log.warning("No symptoms.json found, symptoms_caused will be empty")

    # Group pages by muscle name to merge multi-page muscles
    grouped: dict[str, list[dict]] = {}
    for page in muscle_pages:
        raw_name = extract_muscle_name(page["title"])
        grouped.setdefault(raw_name, []).append(page)

    log.info(f"Unique muscle names: {len(grouped)}")

    ops = []
    for muscle_name, pages_list in grouped.items():
        # Merge all page content for this muscle
        merged_content = "\n\n".join(
            f"[Page {p['page_number']}]\n{p['content']}"
            for p in pages_list
        )
        chapter = pages_list[0].get("chapter", "")
        region = get_region_for_muscle(muscle_name, chapter)

        log.info(f"Extracting: {muscle_name} ({len(pages_list)} pages)")

        extracted = normalize_with_gemini(muscle_name, merged_content)

        if extracted is None:
            # Fallback: store raw content
            extracted = {
                "name": muscle_name,
                "origin": None,
                "insertion": None,
                "action": None,
                "nerve_supply": None,
                "referred_pain_pattern": None,
                "trigger_point_location": None,
                "clinical_notes": None,
                "self_help": None,
                "causes": None,
                "connections": None,
            }
        else:
            # Use canonical name from extraction if better
            if not extracted.get("name"):
                extracted["name"] = muscle_name

        # Find symptoms this muscle causes
        symptoms_caused = []
        for key, syms in symptoms_map.items():
            if key.lower() in muscle_name.lower() or muscle_name.lower() in key.lower():
                symptoms_caused.extend(syms)
        symptoms_caused = list(set(symptoms_caused))

        doc = {
            "name": extracted.get("name") or muscle_name,
            "aliases": get_aliases(muscle_name),
            "region": region,
            "chapter": chapter,
            "origin": extracted.get("origin"),
            "insertion": extracted.get("insertion"),
            "action": extracted.get("action"),
            "nerve_supply": extracted.get("nerve_supply"),
            "referred_pain_pattern": extracted.get("referred_pain_pattern"),
            "trigger_point_location": extracted.get("trigger_point_location"),
            "clinical_notes": extracted.get("clinical_notes"),
            "self_help": extracted.get("self_help"),
            "causes": extracted.get("causes"),
            "connections": extracted.get("connections"),
            "symptoms_caused": symptoms_caused,
            "source_pages": [p["page_number"] for p in pages_list],
        }

        ops.append(UpdateOne(
            {"name": doc["name"]},
            {"$set": doc},
            upsert=True,
        ))

        # Rate limit: Gemini free tier ~15 RPM
        time.sleep(1.5)

    if ops:
        result = muscles_col().bulk_write(ops)
        log.info(f"✓ Upserted {result.upserted_count} new, modified {result.modified_count} muscles")

    # Create indexes
    muscles_col().create_index("name")
    muscles_col().create_index("aliases")
    muscles_col().create_index("region")
    log.info("✓ Indexes created on muscles collection")
    log.info("=== Muscle extraction complete ===")


if __name__ == "__main__":
    run()
