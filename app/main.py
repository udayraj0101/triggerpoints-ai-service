from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.middleware.rate_limiter import setup_rate_limiter, limiter
from app.routes.chat import router as chat_router
from app.routes.stream import router as stream_router
from app.services.rag_service import _load_index
from app.services.excel_service import load_all
from app.utils.logger import get_logger
from app.utils.env_validation import validate_environment
from fastapi.middleware.cors import CORSMiddleware

log = get_logger("main")



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate environment before loading anything
    log.info("Starting up TriggerPoints AI Service")
    try:
        validate_environment()
    except Exception as e:
        log.critical(f"Environment validation failed: {e}")
        raise
    
    # Pre-load everything into memory at startup
    try:
        load_all()
        log.info("✓ Excel data loaded")
    except Exception as e:
        log.error(f"Failed to load Excel data: {e}")
    
    try:
        _load_index()
        log.info("✓ FAISS index loaded")
    except Exception as e:
        log.error(f"Failed to load FAISS index: {e}")
    
    log.info("Startup complete")
    yield
    
    log.info("Shutting down TriggerPoints AI Service")


app = FastAPI(
    title="TriggerPoints AI Service",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Setup rate limiting
setup_rate_limiter(app)

app.include_router(chat_router)
app.include_router(stream_router)


@app.get("/health")
def health():
    log.debug("Health check requested")
    return {"status": "ok"}


@app.get("/admin/cache-stats")
def cache_stats():
    """Get cache statistics (requires API key in production)."""
    from app.services import cache_service
    log.debug("Cache stats requested")
    return cache_service.get_stats()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    log.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    log.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
