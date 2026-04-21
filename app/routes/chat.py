from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from google import genai

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
log = get_logger("chat_route")


class ChatRequest(BaseModel):
    user_id: str
    query: str


@router.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, req: ChatRequest, api_key: str = Depends(verify_api_key)):
    try:
        log.info(f"Chat request from user: {req.user_id}")
        query = req.query.strip()

        # 1. Detect intent
        intent = detect_intent(query)
        log.debug(f"Intent: {intent}")

        # 2. Load session context (last known muscle/symptom for follow-up queries)
        context = session_service.get_context(req.user_id)
        history = session_service.get_history(req.user_id)

        # 3. Entity extraction
        muscle_doc = muscle_service.extract_muscle_from_query(query)
        symptom_doc = symptom_service.extract_symptom_from_query(query)

        # 4. Context resolution — use last known entities for follow-up queries
        #    e.g. "show video" after "I have neck pain" → use last_symptom
        if not muscle_doc and not symptom_doc:
            if intent in ("FLOW_B", "HYBRID") and context.get("last_muscle"):
                muscle_doc = muscle_service.find_muscle(context["last_muscle"])
                log.debug(f"Resolved muscle from context: {context['last_muscle']}")
            elif intent == "FLOW_A" and context.get("last_symptom"):
                symptom_doc = symptom_service.find_symptom(context["last_symptom"])
                log.debug(f"Resolved symptom from context: {context['last_symptom']}")

        # 5. If FLOW_A but we found a muscle name, upgrade to FLOW_B
        if intent == "FLOW_A" and muscle_doc and not symptom_doc:
            intent = "FLOW_B"
            log.debug("Upgraded FLOW_A → FLOW_B (muscle found in query)")

        # 6. Build navigation instructions
        navigation = None
        if intent == "FLOW_B" and muscle_doc:
            navigation = build_flow_b(muscle_doc, query)
        elif intent == "HYBRID" and muscle_doc:
            navigation = build_flow_b(muscle_doc, query)
        elif intent == "FLOW_A" and symptom_doc:
            navigation = build_flow_a(symptom_doc)
        elif intent == "FLOW_A" and not symptom_doc:
            navigation = build_flow_a_unknown(query)
        elif intent == "APP_HELP":
            navigation = build_app_help(query)

        # 7. RAG search — always run for knowledge/hybrid, skip for pure app help
        rag_chunks = []
        if intent != "APP_HELP":
            search_query = query
            if muscle_doc:
                search_query = f"{muscle_doc['name']} trigger points referred pain {query}"
            elif symptom_doc:
                search_query = f"{symptom_doc['name']} muscles trigger points {query}"
            rag_chunks = vector_service.search(search_query)

        # 8. Build prompt
        prompt = build_prompt(
            query=query,
            intent=intent,
            history=history,
            muscle_doc=muscle_doc,
            symptom_doc=symptom_doc,
            rag_chunks=rag_chunks,
            navigation=navigation,
        )

        # 9. Call Gemini
        try:
            gemini_response = _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            answer = gemini_response.text.strip()
        except Exception as e:
            log.error(f"Gemini API error: {e}")
            raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")

        # 10. Update session context
        session_service.add_message(req.user_id, "user", req.query)
        session_service.add_message(req.user_id, "assistant", answer)
        session_service.update_context(
            req.user_id,
            muscle=muscle_doc.get("name") if muscle_doc else None,
            symptom=symptom_doc.get("name") if symptom_doc else None,
        )

        # 11. Build response
        muscles_list = []
        if muscle_doc:
            muscles_list = [muscle_doc["name"]]
        elif symptom_doc:
            muscles_list = (
                symptom_doc.get("primary_muscles", []) +
                symptom_doc.get("secondary_muscles", [])
            )

        return {
            "intent": intent,
            "answer": answer,
            "muscles": muscles_list,
            "navigation": navigation or "",
            "muscle_found": muscle_doc.get("name") if muscle_doc else None,
            "symptom_found": symptom_doc.get("name") if symptom_doc else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
