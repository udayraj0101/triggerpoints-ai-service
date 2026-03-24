"""
SSE Streaming endpoint for real-time response streaming.
"""
import json
import asyncio
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from google import genai
from typing import AsyncGenerator

from app.config.settings import GEMINI_API_KEY, GEMINI_MODEL
from app.middleware.rate_limiter import limiter
from app.services import cache_service, excel_service, rag_service, classifier_service
from app.services.redis_session_service import add_message as redis_add_message
from app.services.navigation_service import get_navigation
from app.utils.prompt_builder import build_prompt
from app.utils.auth import verify_api_key
from app.utils.logger import get_logger

router = APIRouter()
_client = genai.Client(api_key=GEMINI_API_KEY)
log = get_logger("stream_route")


class StreamChatRequest:
    def __init__(self, user_id: str, query: str):
        self.user_id = user_id
        self.query = query


async def generate_stream(user_id: str, query: str) -> AsyncGenerator[str, None]:
    """
    Generate response stream using SSE format.
    Yields JSONPUSH events with answer chunks.
    """
    try:
        query = query.strip().lower()
        
        # Check cache first
        cached = cache_service.get(query)
        if cached:
            log.info(f"Cache hit for query: {query}")
            yield f"data: {json.dumps({'type': 'cached', 'answer': cached['answer']})}\n\n"
            redis_add_message(user_id, "user", query)
            redis_add_message(user_id, "assistant", cached['answer'])
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return
        
        # Classify query
        query_type = classifier_service.classify(query)
        log.debug(f"Query classified as: {query_type}")
        
        nav_answer = None
        excel_data = {}
        rag_chunks = []
        
        if query_type == "navigation":
            nav_answer = get_navigation(query)
            if nav_answer:
                response = {
                    "type": "navigation",
                    "answer": nav_answer,
                }
                yield f"data: {json.dumps(response)}\n\n"
                redis_add_message(user_id, "user", query)
                redis_add_message(user_id, "assistant", nav_answer)
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return
        
        if query_type == "symptom":
            excel_data = excel_service.query_excel(query)
        
        rag_chunks = rag_service.search(query)
        
        # Build prompt
        prompt = build_prompt(query, [], excel_data, rag_chunks, nav_answer)
        
        # Stream from Gemini API
        log.debug("Calling Gemini API for streaming response")
        
        try:
            # Use generate_content with streaming enabled
            response = _client.models.generate_content_stream(
                model=GEMINI_MODEL,
                contents=prompt,
                config={"temperature": 0.3}
            )
            
            full_answer = ""
            for chunk in response:
                if hasattr(chunk, 'text'):
                    text_chunk = chunk.text
                    full_answer += text_chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': text_chunk})}\n\n"
                    await asyncio.sleep(0.01)  # Small delay for smoother streaming
            
            # Store complete response
            muscles = (
                excel_data.get("primary_muscles", []) + excel_data.get("secondary_muscles", [])
                if excel_data
                else []
            )
            
            cache_service.set(query, {
                "type": query_type,
                "answer": full_answer,
                "muscles": muscles,
            })
            
            redis_add_message(user_id, "user", query)
            redis_add_message(user_id, "assistant", full_answer)
            
            yield f"data: {json.dumps({'type': 'done', 'muscles': muscles})}\n\n"
            
            log.info(f"Streaming response completed for user: {user_id}")
            
        except Exception as e:
            log.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
    except Exception as e:
        log.error(f"Stream generation error: {e}", exc_info=True)
        yield f"data: {json.dumps({'type': 'error', 'message': 'Stream generation failed'})}\n\n"


@router.post("/stream-chat")
@limiter.limit("10/minute")
async def stream_chat(request: Request, user_id: str = None, query: str = None, api_key: str = Depends(verify_api_key)):
    """
    SSE streaming chat endpoint.
    Returns Server-Sent Events stream with response chunks.
    """
    if not user_id or not query:
        try:
            body = await request.json()
            user_id = body.get("user_id")
            query = body.get("query")
        except:
            raise HTTPException(status_code=400, detail="user_id and query required")
    
    if not user_id or not query:
        raise HTTPException(status_code=400, detail="user_id and query required")
    
    log.info(f"Stream chat request from user: {user_id}")
    
    return StreamingResponse(
        generate_stream(user_id, query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )