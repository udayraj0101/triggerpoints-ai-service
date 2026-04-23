import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Authentication
API_KEY = os.getenv("API_KEY", "")

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "")
MONGODB_DB = os.getenv("MONGODB_DB", "triggerpoints")

# Query Classification
ENABLE_ML_CLASSIFIER = os.getenv("ENABLE_ML_CLASSIFIER", "true").lower() == "true"
CLASSIFIER_MODEL = os.getenv("CLASSIFIER_MODEL", "gemini-2.5-flash")

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
SESSION_MEMORY_LIMIT = 6
EMBEDDING_DIMENSIONS = 3072  # gemini-embedding-004 output size
