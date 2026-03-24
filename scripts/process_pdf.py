"""
Run once to build the FAISS index from ebook_data.json.
Requires GEMINI_API_KEY in .env

Usage:
    python scripts/process_pdf.py
"""
import sys
import re
import json
import time
from pathlib import Path

import numpy as np
import faiss
from google import genai
from google.genai import types

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.config.settings import (
    DATA_RAW, FAISS_INDEX_DIR, GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL, CHUNK_SIZE_WORDS,
)

_client = genai.Client(api_key=GEMINI_API_KEY)

EBOOK_JSON = DATA_RAW / "ebook_data.json"
SKIP_TYPES = {"boilerplate"}


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------
def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if s.strip()]


def chunk_prose(text: str, chunk_words: int = CHUNK_SIZE_WORDS, overlap_words: int = 50) -> list[str]:
    sentences = split_sentences(text)
    chunks, current, overlap = [], [], []

    for sentence in sentences:
        current.extend(sentence.split())
        if len(current) >= chunk_words:
            chunk = " ".join(current)
            if len(current) >= 80:
                chunks.append(chunk)
            overlap = current[-overlap_words:]
            current = overlap[:]

    if len(current) >= 80:
        chunks.append(" ".join(current))

    return chunks


# ---------------------------------------------------------------------------
# Build chunks from JSON
# ---------------------------------------------------------------------------
def build_chunks(data: list[dict]) -> list[str]:
    chunks = []

    for entry in data:
        if entry["type"] in SKIP_TYPES or not entry["content"]:
            continue

        page = entry["page_number"]
        chapter = entry["chapter"] or ""
        title = entry["title"] or ""
        page_type = entry["type"]
        content = entry["content"]

        # Metadata prefix for every chunk — improves embedding relevance
        meta = f"[Page {page} | {chapter} | {title}]"

        if page_type == "muscle":
            # Each muscle page is one self-contained chunk
            chunks.append(f"{meta}\n{content}")

        else:
            # Prose, table, protocol — chunk with overlap
            for chunk in chunk_prose(content):
                chunks.append(f"{meta}\n{chunk}")

    return chunks


# ---------------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------------
def embed_chunks(chunks: list[str], batch_size: int = 20) -> np.ndarray:
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        result = _client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
        )
        all_embeddings.extend([e.values for e in result.embeddings])
        print(f"  Embedded {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")
        time.sleep(1)
    return np.array(all_embeddings, dtype="float32")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def build_index():
    print(f"Loading {EBOOK_JSON.name}...")
    data = json.loads(EBOOK_JSON.read_text(encoding="utf-8"))
    print(f"  {len(data)} pages loaded")

    print("Building chunks...")
    chunks = build_chunks(data)
    print(f"  {len(chunks)} chunks created")

    by_type = {}
    for entry in data:
        if entry["type"] not in SKIP_TYPES and entry["content"]:
            by_type[entry["type"]] = by_type.get(entry["type"], 0) + 1
    for t, count in by_type.items():
        print(f"    {t}: {count} pages")

    print("\nGenerating embeddings...")
    embeddings = embed_chunks(chunks)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(FAISS_INDEX_DIR / "index.faiss"))
    (FAISS_INDEX_DIR / "chunks.json").write_text(
        json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\nFAISS index saved -> {FAISS_INDEX_DIR / 'index.faiss'}")
    print(f"Chunks saved      -> {FAISS_INDEX_DIR / 'chunks.json'}")
    print(f"Done. {len(chunks)} chunks indexed.")


if __name__ == "__main__":
    build_index()
