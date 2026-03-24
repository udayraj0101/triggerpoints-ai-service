from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from google import genai

from app.config.settings import GEMINI_API_KEY, GEMINI_MODEL, SESSION_MEMORY_LIMIT
from app.middleware.rate_limiter import limiter
from app.services import cache_service, memory_service, excel_service, rag_service, classifier_service
from app.services.redis_session_service import get_history as redis_get_history, add_message as redis_add_message
from app.services.navigation_service import get_navigation
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
        query = req.query.strip().lower()

        # Cache check
        cached = cache_service.get(query)
        if cached:
            log.info(f"Cache hit for query")
            return cached

        # ML-based query classification (with fallback to keyword matching)
        query_type = classifier_service.classify(query)
        log.debug(f"Query classified as: {query_type}")
        history = redis_get_history(req.user_id, limit=SESSION_MEMORY_LIMIT)

        nav_answer = None
        excel_data = {}
        rag_chunks = []

        if query_type == "navigation":
            nav_answer = get_navigation(query)
            if nav_answer:
                response = {
                    "type": "navigation",
                    "answer": nav_answer,
                    "muscles": [],
                    "navigation": nav_answer,
                }
                cache_service.set(query, response)
                redis_add_message(req.user_id, "user", req.query)
                redis_add_message(req.user_id, "assistant", nav_answer)
                log.info(f"Navigation answer provided")
                return response

        if query_type == "symptom":
            excel_data = excel_service.query_excel(query)

        rag_chunks = rag_service.search(query)

        prompt = build_prompt(query, history, excel_data, rag_chunks, nav_answer)

        try:
            log.debug(f"Calling Gemini API for response")
            gemini_response = _client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
            answer = gemini_response.text.strip()
            log.debug(f"Gemini response received ({len(answer)} chars)")
        except Exception as e:
            log.error(f"Gemini API error: {e}")
            raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")

        muscles = (
            excel_data.get("primary_muscles", []) + excel_data.get("secondary_muscles", [])
            if excel_data
            else []
        )

        response = {
            "type": query_type,
            "answer": answer,
            "muscles": muscles,
            "navigation": "",
        }

        cache_service.set(query, response)
        redis_add_message(req.user_id, "user", req.query)
        redis_add_message(req.user_id, "assistant", answer)
        
        log.info(f"Response generated successfully for user: {req.user_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")