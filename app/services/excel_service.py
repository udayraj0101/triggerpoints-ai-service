import json
from functools import lru_cache
from app.config.settings import SYMPTOMS_JSON, MUSCLES_JSON, REGIONS_JSON
from app.utils.logger import get_logger

log = get_logger("excel_service")


@lru_cache(maxsize=1)
def load_all():
    try:
        symptoms = json.loads(SYMPTOMS_JSON.read_text()) if SYMPTOMS_JSON.exists() else {}
        muscles = json.loads(MUSCLES_JSON.read_text()) if MUSCLES_JSON.exists() else {}
        regions = json.loads(REGIONS_JSON.read_text()) if REGIONS_JSON.exists() else {}
        log.info(f"Excel data loaded: {len(symptoms)} symptoms, {len(muscles)} muscles, {len(regions)} regions")
        return symptoms, muscles, regions
    except Exception as e:
        log.error(f"Failed to load Excel data: {e}")
        return {}, {}, {}


def query_excel(query: str) -> dict:
    try:
        symptoms, muscles, regions = load_all()
        q = query.lower()
        result = {}

        # Check muscle name first if query explicitly names one
        for muscle, syms in muscles.items():
            if muscle.lower() in q:
                result["muscle"] = muscle
                result["related_symptoms"] = syms
                log.debug(f"Excel query matched muscle: {muscle}")
                return result

        for symptom, data in symptoms.items():
            if symptom.lower() in q or q in symptom.lower():
                result["symptom"] = symptom
                result.update(data)
                log.debug(f"Excel query matched symptom: {symptom}")
                return result

        for region, syms in regions.items():
            if region.lower() in q:
                result["region"] = region
                result["symptoms"] = syms
                log.debug(f"Excel query matched region: {region}")
                return result

        log.debug("Excel query returned no matches")
        return result
    except Exception as e:
        log.error(f"Excel query failed: {e}")
        return {}
