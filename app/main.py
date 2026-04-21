from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.middleware.rate_limiter import setup_rate_limiter, limiter
from app.routes.chat import router as chat_router
from app.services.mongo_service import ping as mongo_ping
from app.utils.logger import get_logger
from app.utils.env_validation import validate_environment

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting TriggerPoints AI Service")
    try:
        validate_environment()
    except Exception as e:
        log.critical(f"Environment validation failed: {e}")
        raise

    try:
        mongo_ping()
    except Exception as e:
        log.error(f"MongoDB connection failed: {e}")
        raise

    log.info("Startup complete")
    yield
    log.info("Shutting down")


app = FastAPI(title="TriggerPoints AI Service", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_rate_limiter(app)
app.include_router(chat_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    log.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
