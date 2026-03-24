# TriggerPoints AI Service (Backend)

FastAPI microservice powering the TriggerPoints AI chatbot with Gemini AI integration.

## Features

- 🤖 AI-powered chatbot using Google Gemini
- 🧠 Session memory with Redis
- 📊 Excel-based symptom/muscle data lookup
- 📚 RAG (Retrieval Augmented Generation) with FAISS
- 🚀 Rate limiting and caching
- 🔐 API Key authentication

## Prerequisites

- Python 3.10+
- Redis (for session memory)
- Docker (optional, for Redis)

## Local Development Setup

### 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/triggerpoints-ai-service.git
cd triggerpoints-ai-service

# Create virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Required - Get from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Optional - Defaults shown
GEMINI_MODEL=gemini-2.0-flash
API_KEY=my-api-key
REDIS_URL=redis://localhost:6379
SESSION_MEMORY_LIMIT=10
CACHE_TTL=3600
```

### 3. Start Redis

#### Option A: Using Docker (Recommended)
```bash
docker-compose up -d redis
```

#### Option B: Local Redis Installation
```bash
# Windows (using Chocolatey)
choco install redis-64

# Mac
brew install redis
brew services start redis

# Linux
sudo apt install redis-server
redis-server
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 5. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: my-api-key" \
  -d '{"user_id": "test123", "query": "What muscles cause neck pain?"}'
```

## Production Deployment

### Option 1: Render.com (Recommended for Python)

1. Push code to GitHub
2. Create account on [Render](https://render.com)
3. Create new Web Service
4. Connect your GitHub repository
5. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add Environment Variables in Render dashboard:
   - `GEMINI_API_KEY` = your_api_key
   - `API_KEY` = your_custom_api_key
   - `REDIS_URL` = your_redis_url (use Render's managed Redis or Upstash)
7. Deploy!

### Option 2: Railway

1. Push code to GitHub
2. Create account on [Railway](https://railway.app)
3. Create new project → Deploy from GitHub repo
4. Add Environment Variables:
   - `GEMINI_API_KEY`
   - `API_KEY`
   - `REDIS_URL` (Railway provides Redis plugin)
5. Deploy!

### Option 3: DigitalOcean App Platform

1. Push code to GitHub
2. Create app on DigitalOcean
3. Connect GitHub repository
4. Add database (Redis)
5. Add Environment Variables
6. Deploy!

### Option 4: Docker Deployment

```bash
# Build the image
docker build -t triggerpoints-ai .

# Run with Redis
docker run -d -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e API_KEY=your_api_key \
  -e REDIS_URL=redis://host:6379 \
  triggerpoints-ai
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

#### POST /chat
```json
{
  "user_id": "user123",
  "query": "What muscles are related to neck pain?"
}
```

Response:
```json
{
  "type": "symptom",
  "answer": "The sternocleidomastoid and trapezius muscles...",
  "muscles": ["Sternocleidomastoid", "Trapezius"],
  "navigation": ""
}
```

#### GET /health
Returns `{"status": "ok"}`

#### GET /stream/chat
Streaming chat endpoint for real-time responses.

## Architecture

```
Query → Normalize → Cache check
                        ↓ miss
              Route (navigation / symptom / knowledge)
                        ↓
         navigation → rules-based answer
         symptom    → Excel JSON lookup + FAISS
         knowledge  → FAISS search only
                        ↓
              Build prompt → Gemini API → Response
                        ↓
                  Cache + Session memory
```

## Troubleshooting

### Redis Connection Error
```bash
# Check if Redis is running
redis-cli ping

# If not running, start it
docker-compose up -d redis
```

### API Key Error
Make sure `GEMINI_API_KEY` is set in your `.env` file and you have quota available.

### Port Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000
# Then kill it or use a different port
```

## License

MIT
