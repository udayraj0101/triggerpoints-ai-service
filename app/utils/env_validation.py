from app.config.settings import GEMINI_API_KEY, API_KEY, MONGODB_URI
from app.utils.logger import get_logger

log = get_logger("env_validation")


def validate_environment():
    errors = []
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set")
    if not API_KEY:
        errors.append("API_KEY is not set")
    if not MONGODB_URI or "<user>" in MONGODB_URI:
        errors.append("MONGODB_URI is not configured")
    if errors:
        for e in errors:
            log.error(e)
        raise ValueError(f"Environment validation failed: {'; '.join(errors)}")
    log.info("Environment validation passed")
