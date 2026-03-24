"""
Rate Limiting middleware using SlowAPI.
Prevents API abuse and controls costs.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from starlette.responses import JSONResponse

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "error": "Too many requests. Please try again later.",
            "retry_after": str(exc.headers.get("Retry-After", "60"))
        }
    )


def setup_rate_limiter(app):
    """
    Setup rate limiting on the FastAPI app.
    
    Call this in main.py after creating the app instance.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)