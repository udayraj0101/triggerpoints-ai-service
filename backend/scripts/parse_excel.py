"""
Run once to generate:
  app/data/processed/symptoms.json
  app/data/processed/muscles.json
  app/data/processed/regions.json
"""
import sys
import json
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config.settings import EXCEL_FILE, SYMPTOMS_JSON, MUSCLES_JSON, REGIONS_JSON


def split_muscles(val) -> list[str]:
    if pd.isna(val) or str(val).strip() in ("", "(None)"):
        return []
    return [m.strip() for m in str(val).replace("\n", ",").split(",") if m.strip()]


def parse_excel():
    # Read raw without headers so we can detect region block headers ourselves
    df = pd.read_excel(EXCEL_FILE, header=None)

    symptoms, muscles, regions = {}, {}, {}
    current_region = None

    for _, row in df.iterrows():
        cell0 = str(row[0]).strip()
        cell1 = str(row[1]).strip() if not pd.isna(row[1]) else ""

        # Detect region header row: col0 == "S. No." and col1 is the region name
        if cell0 == "S. No.":
            current_region = cell1
            continue

        # Skip empty or non-data rows
        if not cell0.lstrip("-").isdigit() or not cell1 or cell1 == "nan":
            continue

        symptom = cell1
        primary = split_muscles(row[2] if len(row) > 2 else None)
        secondary = split_muscles(row[3] if len(row) > 3 else None)

        symptoms[symptom] = {
            "region": current_region or "",
            "primary_muscles": primary,
            "secondary_muscles": secondary,
        }

        for muscle in primary + secondary:
            muscles.setdefault(muscle, [])
            if symptom not in muscles[muscle]:
                muscles[muscle].append(symptom)

        if current_region:
            regions.setdefault(current_region, [])
            if symptom not in regions[current_region]:
                regions[current_region].append(symptom)

    SYMPTOMS_JSON.parent.mkdir(parents=True, exist_ok=True)
    SYMPTOMS_JSON.write_text(json.dumps(symptoms, indent=2))
    MUSCLES_JSON.write_text(json.dumps(muscles, indent=2))
    REGIONS_JSON.write_text(json.dumps(regions, indent=2))

    print(f"✅ symptoms.json  → {len(symptoms)} entries")
    print(f"✅ muscles.json   → {len(muscles)} entries")
    print(f"✅ regions.json   → {len(regions)} entries")


if __name__ == "__main__":
    parse_excel()
