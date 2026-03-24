import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Authentication
API_KEY = os.getenv("API_KEY", "")

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-004")

# Redis Cache Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL = int(os.getenv("CACHE_TTL", "86400"))  # 24 hours default
USE_REDIS = os.getenv("USE_REDIS", "true").lower() == "true"

# Query Classification
ENABLE_ML_CLASSIFIER = os.getenv("ENABLE_ML_CLASSIFIER", "true").lower() == "true"
CLASSIFIER_MODEL = os.getenv("CLASSIFIER_MODEL", "gemini-2.0-flash")

DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"
FAISS_INDEX_DIR = BASE_DIR / "data" / "faiss_index"

EXCEL_FILE = DATA_RAW / "symptoms.xlsx"
EBOOK_JSON = DATA_RAW / "ebook_data.json"

SYMPTOMS_JSON = DATA_PROCESSED / "symptoms.json"
MUSCLES_JSON = DATA_PROCESSED / "muscles.json"
REGIONS_JSON = DATA_PROCESSED / "regions.json"

CHUNK_SIZE_WORDS = 350
TOP_K_RESULTS = 5
SESSION_MEMORY_LIMIT = 3
