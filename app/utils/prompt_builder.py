"""
Flow-aware prompt builder.
Constructs the Gemini prompt based on detected intent and available data.
"""


def build_prompt(
    query: str,
    intent: str,
    history: list[dict],
    muscle_doc: dict | None,
    symptom_doc: dict | None,
    rag_chunks: list[str],
    navigation: str | None,
) -> str:
    parts = [
        "You are the AI assistant for the TriggerPoints3D app — a clinical trigger point therapy tool.",
        "You help users understand trigger points, muscles, referred pain, and how to use the app.",
        "Write in clear, plain text. No markdown, no bullet symbols, no bold, no headers.",
        "Be concise and clinically accurate. Always prioritize safety.",
        "",
    ]

    # Conversation history
    if history:
        parts.append("Conversation so far:")
        for msg in history:
            parts.append(f"{msg['role'].capitalize()}: {msg['content']}")
        parts.append("")

    # Structured muscle data from MongoDB
    if muscle_doc:
        parts.append(f"Muscle: {muscle_doc.get('name')}")
        parts.append(f"Region: {muscle_doc.get('region')}")
        if muscle_doc.get("origin"):
            parts.append(f"Origin: {muscle_doc['origin']}")
        if muscle_doc.get("insertion"):
            parts.append(f"Insertion: {muscle_doc['insertion']}")
        if muscle_doc.get("action"):
            parts.append(f"Action: {muscle_doc['action']}")
        if muscle_doc.get("nerve_supply"):
            parts.append(f"Nerve Supply: {muscle_doc['nerve_supply']}")
        if muscle_doc.get("referred_pain_pattern"):
            parts.append(f"Referred Pain Pattern: {muscle_doc['referred_pain_pattern']}")
        if muscle_doc.get("trigger_point_location"):
            parts.append(f"Trigger Point Location: {muscle_doc['trigger_point_location']}")
        if muscle_doc.get("clinical_notes"):
            parts.append(f"Clinical Notes: {muscle_doc['clinical_notes']}")
        if muscle_doc.get("self_help"):
            parts.append(f"Self-Help: {muscle_doc['self_help']}")
        if muscle_doc.get("symptoms_caused"):
            parts.append(f"Symptoms this muscle can cause: {', '.join(muscle_doc['symptoms_caused'])}")
        parts.append("")

    # Structured symptom data from MongoDB
    if symptom_doc:
        parts.append(f"Symptom: {symptom_doc.get('name')}")
        parts.append(f"Region: {symptom_doc.get('region')}")
        if symptom_doc.get("primary_muscles"):
            parts.append(f"Primary muscles (most likely cause): {', '.join(symptom_doc['primary_muscles'])}")
        if symptom_doc.get("secondary_muscles"):
            parts.append(f"Secondary muscles (may contribute): {', '.join(symptom_doc['secondary_muscles'])}")
        parts.append("")

    # RAG knowledge chunks
    if rag_chunks:
        parts.append("Reference knowledge from the trigger point therapy book:")
        for chunk in rag_chunks:
            parts.append(chunk)
        parts.append("")

    # Navigation instructions
    if navigation:
        parts.append("App navigation instructions:")
        parts.append(navigation)
        parts.append("")

    # Intent-specific instructions for Gemini
    if intent == "FLOW_B":
        parts.append(
            "The user wants to navigate to a specific muscle. "
            "Provide a brief explanation of the muscle if relevant, "
            "then include the navigation steps above exactly as written."
        )
    elif intent == "FLOW_A":
        parts.append(
            "The user has a symptom and needs to find the causing muscle. "
            "Explain which muscles are most likely responsible and why, "
            "then include the navigation steps above to guide them in the app."
        )
    elif intent == "HYBRID":
        parts.append(
            "The user wants both an explanation and navigation. "
            "First explain the muscle, its trigger points, and referred pain. "
            "Then include the navigation steps above."
        )
    elif intent == "APP_HELP":
        parts.append(
            "The user needs help using the app. "
            "Provide the navigation steps above clearly and concisely."
        )
    else:  # KNOWLEDGE
        parts.append(
            "Answer the question using the reference knowledge above. "
            "Be thorough and clinically accurate."
        )

    parts.append(f"\nUser question: {query}")
    return "\n".join(parts)
