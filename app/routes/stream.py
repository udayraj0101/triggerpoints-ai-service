"""
SSE Streaming endpoint — mirrors chat route logic with streaming output.
"""
import json
import asyncio
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from google import genai
from typing import AsyncGenerator

from app.config.settings import GEMINI_API_KEY, GEMINI_MODEL
from app.middleware.rate_limiter import limiter
from app.services import session_service, vector_service, muscle_service, symptom_service
from app.utils.intent_detector import detect_intent
from app.utils.navigation_builder import (
    build_flow_a, build_flow_b, build_flow_a_unknown, build_app_help
)
from app.utils.prompt_builder import build_prompt
from app.utils.auth import verify_api_key
from app.utils.logger import get_logger

router = APIRouter()
_client = genai.Client(api_key=GEMINI_API_KEY)
log = get_logger("stream_route")


async def generate_stream(user_id: str, query: str) -> AsyncGenerator[str, None]:
    try:
        intent = detect_intent(query)
        context = session_service.get_context(user_id)
        history = session_service.get_history(user_id)

        muscle_doc = muscle_service.extract_muscle_from_query(query)
        symptom_doc = symptom_service.extract_symptom_from_query(query)

        if not muscle_doc and not symptom_doc:
            if intent in ("FLOW_B", "HYBRID") and context.get("last_muscle"):
                muscle_doc = muscle_service.find_muscle(context["last_muscle"])
            elif intent == "FLOW_A" and context.get("last_symptom"):
                symptom_doc = symptom_service.find_symptom(context["last_symptom"])

        if intent == "FLOW_A" and muscle_doc and not symptom_doc:
            intent = "FLOW_B"

        navigation = None
        if intent == "FLOW_B" and muscle_doc:
            navigation = build_flow_b(muscle_doc, query)
        elif intent == "HYBRID" and muscle_doc:
            navigation = build_flow_b(muscle_doc, query)
        elif intent == "FLOW_A" and symptom_doc:
            navigation = build_flow_a(symptom_doc)
        elif intent == "FLOW_A":
            navigation = build_flow_a_unknown(query)
        elif intent == "APP_HELP":
            navigation = build_app_help(query)

        rag_chunks = []
        if intent != "APP_HELP":
            search_query = query
            if muscle_doc:
                search_query = f"{muscle_doc['name']} trigger points {query}"
            elif symptom_doc:
                search_query = f"{symptom_doc['name']} muscles {query}"
            rag_chunks = vector_service.search(search_query)

        prompt = build_prompt(
            query=query,
            intent=intent,
            history=history,
            muscle_doc=muscle_doc,
            symptom_doc=symptom_doc,
            rag_chunks=rag_chunks,
            navigation=navigation,
        )

        full_answer = ""
        response = _client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        for chunk in response:
            if hasattr(chunk, "text") and chunk.text:
                full_answer += chunk.text
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.text})}\n\n"
                await asyncio.sleep(0.01)

        session_service.add_message(user_id, "user", query)
        session_service.add_message(user_id, "assistant", full_answer)
        session_service.update_context(
            user_id,
            muscle=muscle_doc.get("name") if muscle_doc else None,
            symptom=symptom_doc.get("name") if symptom_doc else None,
        )

        yield f"data: {json.dumps({'type': 'done', 'intent': intent, 'navigation': navigation or ''})}\n\n"

    except Exception as e:
        log.error(f"Stream error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/stream-chat")
@limiter.limit("10/minute")
async def stream_chat(request: Request, api_key: str = Depends(verify_api_key)):
    try:
        body = await request.json()
        user_id = body.get("user_id")
        query = body.get("query")
    except Exception:
        raise HTTPException(status_code=400, detail="user_id and query required")

    if not user_id or not query:
        raise HTTPException(status_code=400, detail="user_id and query required")

    return StreamingResponse(
        generate_stream(user_id, query.strip()),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
