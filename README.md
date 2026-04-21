# TriggerPoints AI — Backend

FastAPI backend for the TriggerPoints3D AI chatbot. Powered by Google Gemini, MongoDB Atlas (vector search + data storage), and PM2 + Uvicorn for process management.

**Python 3.11+** | **FastAPI** | **MongoDB Atlas** | **Gemini API** | **PM2 + Uvicorn**

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI |
| AI Model | Google Gemini 2.5 Flash |
| Embeddings | Gemini Embedding 004 |
| Vector Search | MongoDB Atlas Vector Search |
| Database | MongoDB Atlas |
| Server | Uvicorn |
| Process Manager | PM2 |
| Rate Limiting | SlowAPI |

---

## Project Structure

```
app/
├── main.py                  # FastAPI app entry point
├── config/settings.py       # All configuration
├── routes/
│   ├── chat.py              # POST /chat endpoint
│   └── stream.py            # POST /stream-chat endpoint
├── services/
│   ├── mongo_service.py     # MongoDB connection + collections
│   ├── muscle_service.py    # Muscle lookup + alias resolution
│   ├── symptom_service.py   # Symptom lookup
│   ├── vector_service.py    # Atlas Vector Search (RAG)
│   └── session_service.py   # Conversation history + context
├── utils/
│   ├── intent_detector.py   # Flow A / Flow B / Hybrid / App Help / Knowledge
│   ├── navigation_builder.py # Step-by-step app navigation instructions
│   └── prompt_builder.py    # Gemini prompt construction

scripts/
├── seed_all.py              # Run full data pipeline (one command)
├── seed_symptoms.py         # symptoms.xlsx → MongoDB
├── extract_muscles.py       # ebook_data.json → MongoDB (Gemini-normalized)
└── seed_knowledge.py        # ebook chunks + embeddings → MongoDB
```

---

## Local Development Setup

### 1. Clone & install

```bash
git clone https://github.com/YOUR_REPO/triggerpoints-ai-service.git
cd triggerpoints-ai-service
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_gemini_key
API_KEY=your_api_key
MONGODB_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=triggerpoints
```

### 3. Run data pipeline (one time only)

```bash
python -m scripts.seed_all
```

This runs three steps:
- `seed_symptoms` — reads `symptoms.xlsx` → MongoDB `symptoms` collection
- `extract_muscles` — reads `ebook_data.json`, uses Gemini to normalize each muscle page → MongoDB `muscles` collection
- `seed_knowledge` — chunks all prose/table/protocol pages, embeds with Gemini → MongoDB `knowledge_chunks` collection

Takes ~5 minutes. Re-runs are safe — already-embedded chunks are skipped.

### 4. Create Atlas Vector Search index (one time, in Atlas UI)

1. Go to MongoDB Atlas → your cluster → **Atlas Search**
2. Click **Create Search Index** → **JSON Editor**
3. Collection: `triggerpoints.knowledge_chunks`
4. Index name: `vector_index`
5. Paste:

```json
{
  "fields": [{
    "type": "vector",
    "path": "embedding",
    "numDimensions": 3072,
    "similarity": "cosine"
  }]
}
```

### 5. Run locally

```bash
uvicorn app.main:app --reload --port 8010
```

API docs: http://localhost:8010/docs

---

## Server Deployment with PM2 + Uvicorn

### Prerequisites on server

```bash
# Python 3.11+
sudo apt update && sudo apt install python3.11 python3.11-venv python3-pip -y

# Node.js + PM2
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y
sudo npm install -g pm2
```

### Deploy steps

```bash
# 1. Clone repo
git clone https://github.com/YOUR_REPO/triggerpoints-ai-service.git
cd triggerpoints-ai-service

# 2. Create virtualenv and install dependencies
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Create .env
cp .env.example .env
nano .env   # fill in GEMINI_API_KEY, API_KEY, MONGODB_URI

# 4. Run data pipeline (only needed once)
python -m scripts.seed_all

# 5. Create logs directory
mkdir -p logs

# 6. Update ecosystem.config.cjs with correct server paths, then start
pm2 start ecosystem.config.cjs --only triggerpoints-backend

# 7. Save PM2 process list and enable startup on reboot
pm2 save
pm2 startup   # follow the printed command
```

### PM2 commands

```bash
pm2 status                          # check running processes
pm2 logs triggerpoints-backend      # view backend logs
pm2 restart triggerpoints-backend   # restart backend
pm2 stop triggerpoints-backend      # stop backend
pm2 reload triggerpoints-backend    # zero-downtime reload
```

### Update deployed code

```bash
cd triggerpoints-ai-service
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pm2 restart triggerpoints-backend
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Main chat endpoint |
| POST | `/stream-chat` | SSE streaming chat |
| GET | `/health` | Health check |

All endpoints except `/health` require header: `X-API-Key: your_api_key`

### Chat example

```bash
curl -X POST http://localhost:8010/chat \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user1","query":"I have neck pain"}'
```

Response:
```json
{
  "intent": "FLOW_A",
  "answer": "Neck pain is commonly caused by...",
  "muscles": ["Trapezius", "Levator Scapulae"],
  "navigation": "Step 1: Tap the Symptoms screen...",
  "muscle_found": null,
  "symptom_found": "Back of Neck Pain"
}
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `API_KEY` | Yes | Auth key for all endpoints |
| `MONGODB_URI` | Yes | MongoDB Atlas connection string |
| `MONGODB_DB` | No | Database name (default: triggerpoints) |
| `GEMINI_MODEL` | No | Chat model (default: gemini-2.5-flash) |
| `GEMINI_EMBEDDING_MODEL` | No | Embedding model (default: gemini-embedding-004) |
| `SESSION_MEMORY_LIMIT` | No | Messages per session (default: 6) |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| MongoDB connection failed | Check `MONGODB_URI` in `.env` |
| 401 Unauthorized | Check `API_KEY` matches in `.env` |
| Port 8010 in use | `lsof -i :8010` then kill the process |
| Vector search returns nothing | Create Atlas Vector Search index (step 4 above) |
| Import errors | `pip install -r requirements.txt --upgrade` |
| PM2 not found | `npm install -g pm2` |
