"""
Environment validation at startup.
Checks required env vars and data files exist.
"""
from pathlib import Path
from app.config.settings import (
    GEMINI_API_KEY, API_KEY,
    SYMPTOMS_JSON, MUSCLES_JSON, REGIONS_JSON,
    FAISS_INDEX_DIR
)
from app.utils.logger import get_logger

log = get_logger("env_validation")


class EnvironmentError(Exception):
    """Raised when environment validation fails."""
    pass


def validate_environment() -> None:
    """
    Validate all required environment variables and data files.
    Raises EnvironmentError with detailed message if validation fails.
    """
    errors = []

    # Check environment variables
    log.info("Validating environment variables...")
    
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY not set in .env file (required for AI responses)")
    else:
        log.info("✓ GEMINI_API_KEY is configured")
    
    if not API_KEY:
        log.warning("API_KEY not set in .env file (authentication will not work)")
        errors.append("API_KEY not set in .env file (required for authentication)")
    else:
        log.info("✓ API_KEY is configured")

    # Check data files
    log.info("Validating data files...")
    
    data_files = {
        "Symptoms data": SYMPTOMS_JSON,
        "Muscles data": MUSCLES_JSON,
        "Regions data": REGIONS_JSON,
    }
    
    for name, path in data_files.items():
        if not path.exists():
            errors.append(f"{name} not found at {path}")
            log.warning(f"✗ {name} missing")
        else:
            log.info(f"✓ {name} found")
    
    # Check FAISS index (non-critical)
    if not (FAISS_INDEX_DIR / "index.faiss").exists():
        log.warning(f"✗ FAISS index not found at {FAISS_INDEX_DIR}")
        log.warning("  RAG search will not work. Run: python scripts/process_pdf.py")
    else:
        log.info(f"✓ FAISS index found")
    
    # Raise error if critical items missing
    if errors:
        error_msg = "\n".join([f"  • {e}" for e in errors])
        msg = f"Environment validation failed:\n{error_msg}\n\nSetup instructions:\n" \
              f"  1. Copy .env file and add GEMINI_API_KEY\n" \
              f"  2. Add API_KEY for authentication\n" \
              f"  3. Run: python scripts/parse_excel.py\n" \
              f"  4. Run: python scripts/process_pdf.py"
        log.critical(msg)
        raise EnvironmentError(msg)
    
    log.info("✓ Environment validation passed")
