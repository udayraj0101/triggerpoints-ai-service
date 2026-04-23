# TriggerPoints AI Service - Technical Explanation for Clients

## Overview
The TriggerPoints AI Service is a backend API that powers a mobile app for trigger point therapy. It uses AI (Google Gemini) to answer user questions about muscle trigger points, pain patterns, and treatment.

---

## How It Works (Simple Flow)

```
User Query → Classification → Data Retrieval → AI Response → User
```

### 1. User Sends a Query
The user asks a question through the mobile app (e.g., "What causes shoulder pain?")

### 2. Query Classification (ML-Based)
The system automatically classifies the query into one of three types:
- **Symptom** - Questions about pain/symptoms
- **Navigation** - Questions about app features
- **General** - Other health-related questions

### 3. Data Retrieval (Knowledge Base)
The system pulls relevant information from multiple sources:

| Source | Content |
|--------|---------|
| **Excel Database** | 50+ muscles with trigger points, symptoms |
| **FAISS Index** | Searchable knowledge base (ebook content) |
| **Redis Cache** | Speeds up repeated queries |

### 4. AI Processing (Gemini)
The system sends to Google Gemini:
- The user's question
- Relevant data from the knowledge base
- Last 3 conversation messages (for context)
- Special instructions (plain text, medical accuracy)

### 5. Response to User
The AI generates a personalized response with:
- The answer
- Related muscles/t trigger points
- Navigation hints (if needed)

---

## Key Features

### 🔄 Conversation Memory
- Remembers last 3 messages per user
- Stored in Redis for 30 days
- Provides contextual responses

### ⚡ Performance
- **Rate Limiting**: 10 requests/minute per user
- **Caching**: 24-hour cache for common queries
- **Fast Search**: FAISS vector database for instant lookups

### 🛡️ Security
- API key authentication required
- Environment-based configuration
- No sensitive data stored

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI (Python) |
| AI Model | Google Gemini 1.5 Flash |
| Vector Search | FAISS (Facebook) |
| Cache/Session | Redis |
| Data Storage | Excel + JSON files |

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /chat` | Main chat interface |
| `GET /health` | Service health check |

---

## Data Sources

1. **symptoms.xlsx** - Medical symptoms database
2. **ebook_data.pdf** - Trigger point reference book
3. **muscles.json** - Muscle anatomy data
4. **regions.json** - Body region mappings

---

## Example Conversation

**User**: "What trigger points cause headaches?"

**System**:
1. Classifies as "symptom" query
2. Searches Excel for headache-related muscles
3. Finds relevant RAG chunks about trigger points
4. Sends to Gemini with context
5. Returns: "Temporalis and suboccipital muscles often refer pain to the head..."

---

## Configuration (Environment Variables)

- `GEMINI_API_KEY` - Google AI API key
- `GEMINI_MODEL` - Model version (default: gemini-1.5-flash)
- `REDIS_URL` - Cache server URL
- `API_KEY` - Client authentication

---

## Scalability

The service is designed to handle:
- Multiple concurrent users
- Growing knowledge base (easy to add new data)
- High request volumes through caching