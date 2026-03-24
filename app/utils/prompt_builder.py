def build_prompt(
    query: str,
    history: list[dict],
    excel_data: dict,
    rag_chunks: list[str],
    nav_answer: str | None,
) -> str:
    parts = [
        "You are a helpful AI assistant for the TriggerPoints mobile app, specializing in trigger point therapy and muscle anatomy.",
        "Answer thoroughly and accurately using the provided context. Include specific details about muscles, trigger point locations, referred pain patterns, and clinical notes where relevant.",
        "Write in plain text only. Do not use markdown, bullet points, bold, italics, headers, or citation numbers like [1].",
        "If the context does not contain enough information, say so clearly.",
        "",
    ]

    if history:
        parts.append("## Conversation History")
        for msg in history:
            parts.append(f"{msg['role'].capitalize()}: {msg['content']}")
        parts.append("")

    if nav_answer:
        parts.append(f"## App Navigation\n{nav_answer}\n")

    if excel_data:
        parts.append("## Structured Data")
        for k, v in excel_data.items():
            parts.append(f"{k}: {v}")
        parts.append("")

    if rag_chunks:
        parts.append("## Reference Knowledge")
        for i, chunk in enumerate(rag_chunks, 1):
            parts.append(f"[{i}] {chunk}")
        parts.append("")

    parts.append(f"## User Question\n{query}")
    return "\n".join(parts)
