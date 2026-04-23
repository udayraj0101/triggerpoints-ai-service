"""
Navigation builder.
Generates step-by-step app navigation instructions per the App Workflow Chatbot Guide.

FLOW A — Symptom-based (user doesn't know muscle):
  Go to Symptoms screen → Select region → Select symptom → Select muscle → Split view

FLOW B — Direct muscle (user knows muscle):
  Tap rotate/switch button → Landscape mode → Select region → Search/select muscle → Split view
"""


def build_flow_a(symptom_doc: dict) -> str:
    """
    Build Flow A navigation steps for a known symptom.
    symptom_doc: { name, region, primary_muscles[], secondary_muscles[] }
    """
    name = symptom_doc.get("name", "your symptom")
    region = symptom_doc.get("region", "the relevant region")
    primary = symptom_doc.get("primary_muscles", [])
    secondary = symptom_doc.get("secondary_muscles", [])

    lines = [
        f"To find muscles related to {name}, follow these steps in the app:",
        "",
        "Step 1: Tap the Symptoms screen from the main menu.",
        f"Step 2: Select the body region — {region}.",
        f"Step 3: Select the symptom — {name}.",
        "Step 4: The app will show a list of muscles. Tap any muscle to open the split view.",
        "  In split view:",
        "  - Left side shows the pain map (referred pain zones in red)",
        "  - Right side shows the trigger point locations (blue dots)",
    ]

    if primary:
        lines.append("")
        lines.append(f"Primary muscles (most likely cause): {', '.join(primary)}")
    if secondary:
        lines.append(f"Secondary muscles (may also contribute): {', '.join(secondary)}")

    lines += [
        "",
        "Step 5: Tap the Play button to watch the needling or self-help video.",
        "Step 6: Tap Self Help and Advice (bottom right) for causes, advice, and techniques.",
    ]

    return "\n".join(lines)


def build_flow_b(muscle_doc: dict, intent: str = "") -> str:
    """
    Build Flow B navigation steps for a known muscle.
    muscle_doc: { name, region, ... }
    intent: optional hint about what user wants (pain map, trigger points, video, self-help)
    """
    name = muscle_doc.get("name", "the muscle")
    region = muscle_doc.get("region", "the relevant region")

    lines = [
        f"To navigate directly to {name} in the app:",
        "",
        "Step 1: Tap the rotate/switch button to enter landscape mode.",
        "  The app opens the split view automatically:",
        "  - Left side: pain map",
        "  - Right side: trigger point locations",
        f"Step 2: Select the body region — {region}.",
        f"Step 3: Search for and select {name}.",
    ]

    intent_lower = intent.lower()

    if "pain map" in intent_lower:
        lines += [
            "",
            "The pain map is shown on the left side of the split view.",
            "Red zones indicate referred pain areas.",
        ]
    elif "trigger point" in intent_lower:
        lines += [
            "",
            "Trigger points appear as blue dots on the right side of the split view.",
            "Tap each dot to see the specific trigger point location.",
        ]
    elif "video" in intent_lower or "needling" in intent_lower:
        lines += [
            "",
            "Step 4: Tap the Play button.",
            "Step 5: Choose the video type:",
            "  - Safety (contraindications and warnings)",
            "  - Needling (dry needling technique demonstration)",
            "  - Functional Anatomy",
            "  - TP Overview",
        ]
    elif "self help" in intent_lower or "self-help" in intent_lower or "advice" in intent_lower:
        lines += [
            "",
            "Step 4: In the split view, tap the Self Help and Advice button (bottom right).",
            "  This shows:",
            "  - Common causes of trigger point activation",
            "  - Self-massage techniques",
            "  - Stretching and advice",
        ]
    else:
        # General — show all options
        lines += [
            "",
            "From the split view you can:",
            "  - View the pain map (left side)",
            "  - View trigger point locations (right side, blue dots)",
            "  - Tap Play to watch videos (Safety, Needling, Functional Anatomy, TP Overview)",
            "  - Tap Self Help and Advice (bottom right) for causes and self-treatment",
        ]

    return "\n".join(lines)


def build_flow_a_unknown(query: str) -> str:
    """Flow A when symptom is not in database — guide user to browse."""
    return (
        f"I couldn't find an exact match for your symptom in the database. "
        f"Here's how to find it in the app:\n\n"
        f"Step 1: Tap the Symptoms screen from the main menu.\n"
        f"Step 2: Browse the body regions to find the area closest to your pain.\n"
        f"Step 3: Select the symptom that best matches your description.\n"
        f"Step 4: Tap a muscle from the list to open the split view.\n"
        f"Step 5: Use the pain map and trigger point view to identify your issue."
    )


def build_app_help(query: str) -> str:
    """Static app help for UI navigation questions."""
    q = query.lower()

    if "pain map" in q:
        return (
            "To view a pain map:\n"
            "If you know the muscle: Tap the rotate/switch button → enter landscape mode → "
            "select region → select muscle. The pain map appears on the left side.\n"
            "If you don't know the muscle: Go to Symptoms screen → select region → "
            "select symptom → select muscle. Pain map appears on the left side of split view."
        )
    if "trigger point" in q:
        return (
            "To view trigger points:\n"
            "Tap the rotate/switch button → enter landscape mode → select region → select muscle.\n"
            "Trigger points appear as blue dots on the right side of the split view."
        )
    if "video" in q or "watch" in q:
        return (
            "To watch videos:\n"
            "Navigate to a muscle (rotate button → landscape → select region → select muscle).\n"
            "Tap the Play button, then choose: Safety, Needling, Functional Anatomy, or TP Overview."
        )
    if "self help" in q or "self-help" in q or "advice" in q:
        return (
            "To access Self Help and Advice:\n"
            "Navigate to a muscle in landscape mode (rotate button → select region → select muscle).\n"
            "Tap the Self Help and Advice button at the bottom right of the split view."
        )
    if "rotate" in q or "landscape" in q or "switch" in q:
        return (
            "The rotate/switch button enters landscape mode.\n"
            "In landscape mode, the app shows a split view:\n"
            "  - Left side: pain map (referred pain zones)\n"
            "  - Right side: trigger point locations\n"
            "This is the main view for exploring individual muscles."
        )
    if "cloth" in q or "layer" in q or "skeleton" in q:
        return (
            "The Cloth button (bottom left) toggles between anatomical layers:\n"
            "  1. Clothed model\n"
            "  2. Muscle layer\n"
            "  3. Skeletal view\n"
            "Use this to see deeper anatomy."
        )
    if "region" in q or "body map" in q:
        return (
            "Body regions available in the app:\n"
            "  - Face, Head and Neck\n"
            "  - Shoulder & Upper Arm\n"
            "  - Forearm & Hand\n"
            "  - Spine & Torso\n"
            "  - Lumbo-Pelvic\n"
            "  - Hip, Thigh & Knee\n"
            "  - Leg, Ankle & Foot\n"
            "Select a region from the top-left dropdown on the main screen."
        )

    # Generic app help
    return (
        "Here is how to use the TriggerPoints3D app:\n\n"
        "Main navigation:\n"
        "  - Rotate/switch button: enters landscape split view for muscle detail\n"
        "  - Symptoms screen: find muscles by symptom (Flow A)\n"
        "  - Body region dropdown (top-left): filter by body area\n"
        "  - Cloth button (bottom-left): toggle between skin, muscle, and skeleton layers\n\n"
        "In split view (landscape mode):\n"
        "  - Left: pain map (referred pain zones in red)\n"
        "  - Right: trigger point locations (blue dots)\n"
        "  - Play button: watch Safety, Needling, Functional Anatomy, or TP Overview videos\n"
        "  - Self Help and Advice (bottom right): causes, self-massage, stretching"
    )
