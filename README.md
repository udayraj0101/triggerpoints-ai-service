# TriggerPoints AI Service

FastAPI microservice for AI-powered trigger point therapy chatbot. Powered by Google Gemini, FAISS vector search, and Redis.

**Python 3.10+** | **FastAPI** | **Docker** | **Redis** | **Gemini API**

## Features

- 🤖 AI responses via Google Gemini 1.5 Flash
- 💾 Redis session memory & query caching
- 📊 50+ muscle database with trigger points
- 📚 FAISS vector search for knowledge retrieval
- 🔐 API key auth + rate limiting
- ⚡ Fast responses (<10ms cached, 2-5s new)
- 🐳 Docker & Docker Compose included
- 📡 Streaming endpoint support

## 📋 Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| API Framework | FastAPI | 0.111+ |
| AI Model | Google Gemini | 1.5 Flash |
| Vector Search | FAISS | 1.8.0+ |
| Session/Cache | Redis | 5.0+ |
| Data Processing | Pandas | 2.0+ |
| Server | Uvicorn | 0.29+ |
| Rate Limiting | SlowAPI | 0.1.9+ |

## Prerequisites

- Python 3.10+
- Redis 5.0+
- Google Gemini API Key (free at https://aistudio.google.com/app/apikey)
- Docker (optional, for Redis)

## Setup (5 minutes)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_REPO/triggerpoints-ai-service.git
cd triggerpoints-ai-service
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add:
# GEMINI_API_KEY=your_key_here
# API_KEY=your_api_key_here
```

### 3. Start Redis

```bash
# Docker (recommended)
docker-compose up -d

# Or install locally: brew install redis (macOS) / apt install redis-server (Linux)
redis-cli ping  # Should return PONG
```

### 4. Run Server

```bash
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for API documentation

## Data Processing

Before deployment, process your data files:

### Parse Excel Database

```bash
python scripts/parse_excel.py
```

This extracts muscle and symptom data from `app/data/raw/symptoms.xlsx` and creates:
- `app/data/processed/muscles.json`
- `app/data/processed/symptoms.json`
- `app/data/processed/regions.json`

### Process PDF & Build FAISS Index

```bash
python scripts/process_pdf.py
```

This:
- Reads trigger point data from `app/data/raw/ebook_data.json`
- Generates embeddings via Gemini API
- Builds FAISS vector index at `app/data/faiss_index/index.faiss`
- Creates chunks metadata at `app/data/faiss_index/chunks.json`

**Note**: Requires GEMINI_API_KEY in .env

### Full Data Pipeline

```bash
# Parse Excel
python scripts/parse_excel.py

# Build vector index
python scripts/process_pdf.py

# Verify
ls -la app/data/processed/
ls -la app/data/faiss_index/
```

## API Endpoints

### Chat

```bash
curl -X POST http://localhost:8000/chat \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user1","query":"What causes shoulder pain?"}'
```

Response:
```json
{
  "response": "Shoulder pain typically originates from...",
  "related_muscles": ["Trapezius", "Rotator Cuff"],
  "confidence": 0.95
}
```

### Stream

```bash
curl -X POST http://localhost:8000/stream \
  -H "X-API-Key: your_api_key" \
  -d '{"user_id":"user1","query":"question here"}'
```

### Health

```bash
curl http://localhost:8000/health
```

### Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

**Required:**
```env
GEMINI_API_KEY=your_gemini_key
API_KEY=your_api_key
```

**Optional:**
```env
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=86400
SESSION_MEMORY_LIMIT=3
GEMINI_MODEL=gemini-1.5-flash
```

See `.env.example` for all options.

## Deployment

### Docker

```bash
docker build -t triggerpoints-ai .
docker run -d -p 8000:8000 \
  -e GEMINI_API_KEY=xxx \
  -e API_KEY=xxx \
  -e REDIS_URL=redis://redis:6379 \
  triggerpoints-ai
```

### Production (local)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Cloud Options

- **Render**: Connect GitHub → Deploy
- **Railway**: Connect GitHub → Add Redis add-on → Deploy
- **Google Cloud Run**: `gcloud run deploy --source .`
- **AWS**: Deploy to EC2/ECS with RDS Redis

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Redis connection refused | `docker-compose up -d` |
| 401 API key error | Check `.env` file |
| Port 8000 in use | `lsof -i :8000` and kill process |
| Import errors | `pip install -r requirements.txt --upgrade` |
| FAISS index missing | Run `python scripts/process_pdf.py` |

## Project Structure

```
app/
├── main.py              # FastAPI app
├── config/settings.py   # Configuration
├── routes/              # API endpoints
├── services/            # Business logic
├── middleware/          # Rate limiting
└── utils/              # Helper functions

data/
├── raw/                 # Excel & JSON data
├── processed/          # Processed outputs
└── faiss_index/        # Vector database

scripts/
├── parse_excel.py      # Extract Excel data
└── process_pdf.py      # Build vector index

requirements.txt        # Dependencies
docker-compose.yml      # Docker setup
.env.example           # Configuration template
```

## Architecture

```
Request → Auth → Rate Limit → Cache Check
                        ↓ miss
Classify → Retrieve Data → Build Prompt → Gemini API
                        ↓
Cache → Memory → Response
```

Query types:
- **Symptom** (80%) - Excel + FAISS lookup
- **Navigation** (10%) - Rules-based 
- **General** (10%) - FAISS only

## Security

- API key required for all endpoints
- Rate limit: 10 req/min per user
- Configure secrets in `.env` (never commit)
- Use HTTPS in production
- Rotate API keys monthly

## License

MIT - See [LICENSE](LICENSE)

## Support

- **Issues**: GitHub Issues
- **Docs**: See EXPLANATION.md for technical details
- **Health Check**: `GET /health`
