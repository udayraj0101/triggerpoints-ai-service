import json
from pathlib import Path
from typing import Optional

# Load symptoms data for dynamic navigation
SYMPTOMS_FILE = Path(__file__).parent.parent / "data" / "processed" / "symptoms.json"
REGIONS_FILE = Path(__file__).parent.parent / "data" / "processed" / "regions.json"

# Cache for symptoms data
_symptoms_data: Optional[dict] = None
_regions_data: Optional[dict] = None


def _load_symptoms_data() -> dict:
    """Load symptoms data from JSON file"""
    global _symptoms_data
    if _symptoms_data is None:
        try:
            with open(SYMPTOMS_FILE, 'r', encoding='utf-8') as f:
                _symptoms_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _symptoms_data = {}
    return _symptoms_data


def _load_regions_data() -> dict:
    """Load regions data from JSON file"""
    global _regions_data
    if _regions_data is None:
        try:
            with open(REGIONS_FILE, 'r', encoding='utf-8') as f:
                _regions_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            _regions_data = {}
    return _regions_data


def get_symptom_navigation(symptom_query: str) -> Optional[str]:
    """
    Generate step-by-step navigation guide for a symptom.
    
    Returns a formatted string with:
    - Body region to select
    - Primary muscles (most likely to cause the pain)
    - Secondary muscles (may also contribute)
    """
    symptoms = _load_symptoms_data()
    regions = _load_regions_data()
    
    # Find matching symptom (case-insensitive partial match)
    symptom_query_lower = symptom_query.lower().strip()
    matched_symptom = None
    
    for symptom_name in symptoms.keys():
        if symptom_query_lower in symptom_name.lower():
            matched_symptom = symptom_name
            break
    
    # If no partial match, try to find any keyword match
    if not matched_symptom:
        query_words = symptom_query_lower.split()
        for symptom_name in symptoms.keys():
            symptom_lower = symptom_name.lower()
            # Check if any significant word matches
            for word in query_words:
                if len(word) > 3 and word in symptom_lower:
                    matched_symptom = symptom_name
                    break
            if matched_symptom:
                break
    
    if not matched_symptom:
        return None
    
    symptom_data = symptoms.get(matched_symptom, {})
    region = symptom_data.get("region", "Unknown")
    primary_muscles = symptom_data.get("primary_muscles", [])
    secondary_muscles = symptom_data.get("secondary_muscles", [])
    
    # Build the navigation guide
    guide = []
    guide.append(f"## 🎯 Step-by-Step Guide for: **{matched_symptom}**")
    guide.append("")
    guide.append("### Step 1: Select Body Region")
    guide.append(f"→ Open the app → Go to **Body Map** → Select **{region}**")
    guide.append("")
    
    if primary_muscles:
        guide.append("### Step 2: Check PRIMARY Muscles (Most Likely Cause)")
        guide.append("These muscles are the **most common cause** of your symptom:")
        for muscle in primary_muscles:
            guide.append(f"  • **{muscle}**")
        guide.append("")
    
    if secondary_muscles:
        guide.append("### Step 3: Check SECONDARY Muscles (May Also Contribute)")
        guide.append("These muscles can **sometimes contribute** to your symptoms:")
        for muscle in secondary_muscles:
            guide.append(f"  • **{muscle}**")
        guide.append("")
    
    guide.append("### Step 4: View Trigger Points")
    guide.append("→ Tap on any muscle → View its trigger point locations on the diagram")
    guide.append("")
    
    guide.append("### Step 5: Treatment Information")
    guide.append("→ Each muscle shows:")
    guide.append("  • Exact trigger point locations")
    guide.append("  • Referral pain patterns")
    guide.append("  • Self-treatment tips")
    guide.append("  • Stretching instructions")
    
    return "\n".join(guide)


def get_region_navigation(region_query: str) -> Optional[str]:
    """
    Generate navigation guide for a body region.
    Lists all available muscles in that region.
    """
    regions = _load_regions_data()
    muscles = _load_symptoms_data()
    
    region_query_lower = region_query.lower().strip()
    matched_region = None
    
    # Find matching region
    for region_name in regions.keys():
        if region_query_lower in region_name.lower():
            matched_region = region_name
            break
    
    if not matched_region:
        return None
    
    # Get all unique muscles for this region
    region_symptoms = regions.get(matched_region, [])
    muscles_in_region = set()
    
    for symptom in region_symptoms:
        symptom_data = muscles.get(symptom, {})
        muscles_in_region.update(symptom_data.get("primary_muscles", []))
        muscles_in_region.update(symptom_data.get("secondary_muscles", []))
    
    guide = []
    guide.append(f"## 🏋️ Muscles in **{matched_region}**")
    guide.append("")
    guide.append(f"Found **{len(muscles_in_region)}** muscles in this region:")
    guide.append("")
    
    for muscle in sorted(muscles_in_region):
        guide.append(f"  • {muscle}")
    
    guide.append("")
    guide.append("### How to Use:")
    guide.append("1. Go to Body Map")
    guide.append(f"2. Select **{matched_region}**")
    guide.append("3. Tap on any muscle to see:")
    guide.append("   - Trigger point locations")
    guide.append("   - Pain referral patterns")
    guide.append("   - Treatment instructions")
    
    return "\n".join(guide)


def get_muscle_navigation(muscle_query: str) -> Optional[str]:
    """
    Generate navigation guide for a specific muscle.
    Shows which symptoms that muscle can cause.
    """
    muscles = _load_symptoms_data()
    
    muscle_query_lower = muscle_query.lower().strip()
    
    # Find muscles that match the query
    matched_muscles = []
    for symptom_name, symptom_data in muscles.items():
        all_muscles = (symptom_data.get("primary_muscles", []) + 
                      symptom_data.get("secondary_muscles", []))
        
        for muscle in all_muscles:
            if muscle_query_lower in muscle.lower() and muscle not in matched_muscles:
                matched_muscles.append(muscle)
    
    if not matched_muscles:
        return None
    
    # For simplicity, just use the first match (or combine them)
    muscle_name = matched_muscles[0]
    
    # Find all symptoms this muscle can cause
    symptoms_caused = []
    for symptom_name, symptom_data in muscles.items():
        primary = symptom_data.get("primary_muscles", [])
        secondary = symptom_data.get("secondary_muscles", [])
        
        if muscle_name in primary:
            symptoms_caused.append((symptom_name, "Primary"))
        elif muscle_name in secondary:
            symptoms_caused.append((symptom_name, "Secondary"))
    
    guide = []
    guide.append(f"## 💪 **{muscle_name}**")
    guide.append("")
    
    if symptoms_caused:
        guide.append("### Symptoms This Muscle Can Cause:")
        for symptom, cause_type in symptoms_caused:
            badge = "🔴" if cause_type == "Primary" else "🟡"
            guide.append(f"  {badge} {symptom} ({cause_type})")
        
        guide.append("")
        guide.append("### How to Find Trigger Points:")
        guide.append(f"1. Go to Body Map → Find {muscle_name}")
        guide.append("2. Tap on the muscle to see trigger point locations")
        guide.append("3. View the pain referral diagram")
        guide.append("4. Follow treatment instructions")
    else:
        guide.append("No symptom data available for this muscle.")
    
    return "\n".join(guide)


# Legacy static navigation rules for general queries
NAVIGATION_RULES: dict[str, str] = {
    "find muscle": "Tap the body map → select the affected area → choose the muscle.",
    "find trigger point": "Go to Body Map → tap the muscle → view trigger point locations.",
    "log symptom": "Tap the '+' button on the home screen → select 'Log Symptom' → fill in details.",
    "search symptom": "Use the Search tab → type your symptom → select from results.",
    "view history": "Go to Profile → tap 'History' to see past sessions.",
    "start session": "Tap 'Start Session' on the home screen → follow the guided steps.",
    "settings": "Tap the gear icon (top-right) to open Settings.",
    "contact": "Go to Settings → 'Support' → 'Contact Us'.",
}


def get_navigation(query: str) -> str | None:
    """
    Main navigation function - tries multiple strategies:
    1. Match symptom → provide detailed muscle guide
    2. Match region → list muscles in that region
    3. Match specific muscle → show what symptoms it causes
    4. Fall back to static navigation rules
    """
    q = query.lower()
    
    # First try dynamic navigation based on symptom/region/muscle
    symptom_result = get_symptom_navigation(query)
    if symptom_result:
        return symptom_result
    
    region_result = get_region_navigation(query)
    if region_result:
        return region_result
    
    muscle_result = get_muscle_navigation(query)
    if muscle_result:
        return muscle_result
    
    # Fall back to static navigation rules
    for keyword, steps in NAVIGATION_RULES.items():
        if keyword in q:
            return steps
    
    return None
