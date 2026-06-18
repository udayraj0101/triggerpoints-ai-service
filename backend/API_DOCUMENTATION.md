# TriggerPoints AI Service — API Documentation

## Base URL
`https://trigger-point-o2nb4.ondigitalocean.app/api`

---

## Endpoints

### 1. Chat
- `POST /api/chat`

### 2. Health check
- `GET /api/health` — returns `{"status":"ok"}`

---

## Authentication

Every request to `/api/chat` must include the backend API key in a request header.

- Header: `X-API-Key`
- Value: the `API_KEY` configured in the backend service environment.

The internal `GEMINI_API_KEY` is server-side only and must never be exposed to the app or front-end.

---

## Rate limit
- `10 requests / minute` per IP. Excess requests get `429 Too Many Requests`.

---

## Chat request

```
POST /api/chat
Content-Type: application/json
X-API-Key: <your-backend-api-key>
```

Body:
```json
{
  "user_id": "string",
  "query": "string"
}
```

### Field semantics

| Field | Required | Notes |
|---|---|---|
| `user_id` | yes | **Must be unique per end-user and stable across that user's requests.** The backend keys conversation history and last-known muscle/symptom by this id. Do NOT hardcode a constant (e.g. `"user123"`) — that pollutes context across users and degrades response quality. Use the auth user id, a stable device id, or a per-install UUID stored in app preferences. |
| `query` | yes | The user's free-text message. |

---

## Chat response

`200 OK`, `application/json`:

```json
{
  "intent": "FLOW_A | FLOW_B | HYBRID | APP_HELP | KNOWLEDGE",
  "answer": "string",
  "should_navigate": true,
  "muscles": ["string", "..."],
  "muscle_found": "string | null",
  "symptom_found": "string | null"
}
```

### Field semantics

| Field | Type | What it means | What the app should do |
|---|---|---|---|
| `answer` | string | The text to render in the chat bubble. May contain a knowledge answer, a clarifying question, or a knowledge answer + step-by-step navigation steps inline. | **Always render this in the chat UI.** |
| `should_navigate` | boolean | `true` when the AI is guiding the user to a screen in the app (navigation steps are already embedded inside `answer`). `false` for general knowledge replies or when the AI is asking the user to clarify their query first. | If `true`, the app can optionally show an in-app navigation button / deep link using `muscle_found` or `muscles`. If `false`, just show `answer`. |
| `muscles` | string[] | Muscles relevant to the user's query. For a specific muscle query → `[that muscle]`. For a symptom → primary + secondary muscles for that symptom. | When `should_navigate` is `true`, use this list to render muscle chips / deep links into the app's muscle screens. |
| `muscle_found` | string \| null | The specific muscle the AI resolved from the query (if any). | Useful for direct deep-link to that muscle. |
| `symptom_found` | string \| null | The specific symptom the AI resolved from the query (if any). | Useful for direct deep-link to that symptom screen. |
| `intent` | string | Internal classification of what the user wants. | Debug / analytics. Not required for rendering. |

### When `should_navigate` is `true`

The `answer` text already contains the step-by-step navigation. Examples of `intent` values that produce this:
- `FLOW_A` — user described a symptom, the AI resolved it confidently, and is guiding them to the right symptom screen + listing the muscles.
- `FLOW_B` — user named a specific muscle, AI is guiding them to that muscle's screen.
- `HYBRID` — user asked about a muscle's anatomy AND wants to find it in the app.
- `APP_HELP` — user is asking how to do something in the app.

### When `should_navigate` is `false`

The `answer` is a normal conversational reply with no navigation steps:
- `KNOWLEDGE` — user is asking a general question (e.g. "what causes trigger points?"). `answer` is informational only.
- `FLOW_A` with an ambiguous query — user said something general like "neck pain" that matches multiple symptoms. `answer` will list close matches and ask the user to clarify before any navigation is offered.

---

## Example — confident symptom query

Request:
```json
{ "user_id": "user_abc123", "query": "I have pain in my heel after long standing" }
```

Response:
```json
{
  "intent": "FLOW_A",
  "answer": "Heel pain after standing is most often caused by trigger points in the Soleus and Gastrocnemius muscles ... Step 1: Tap the Symptoms screen ...",
  "should_navigate": true,
  "muscles": ["Soleus", "Gastrocnemius", "Quadratus Plantae"],
  "muscle_found": null,
  "symptom_found": "Heel Pain"
}
```

The app:
- Shows `answer` in the chat bubble (navigation steps are inline).
- Optionally surfaces `muscles` as tappable chips that deep-link into the app's muscle screens.

---

## Example — ambiguous query

Request:
```json
{ "user_id": "user_abc123", "query": "neck pain" }
```

Response:
```json
{
  "intent": "FLOW_A",
  "answer": "Your query 'neck pain' could mean several things. Could you tell me whether it's the back of your neck, the front, stiffness on waking, or pain extending into the throat?",
  "should_navigate": false,
  "muscles": ["Trapezius", "Multifidi", "Levator Scapulae", "Splenius Cervicis"],
  "muscle_found": null,
  "symptom_found": "Back of Neck Pain"
}
```

The app:
- Shows `answer`. No navigation, no deep links — wait for the user to reply with a clarification before showing app navigation.

---

## Example — general knowledge query

Request:
```json
{ "user_id": "user_abc123", "query": "what is a trigger point?" }
```

Response:
```json
{
  "intent": "KNOWLEDGE",
  "answer": "A trigger point is a tight, irritable spot in muscle fibers ...",
  "should_navigate": false,
  "muscles": [],
  "muscle_found": null,
  "symptom_found": null
}
```

The app:
- Shows `answer` as a plain conversational reply.

---

## Example fetch call

```js
const response = await fetch("https://trigger-point-o2nb4.ondigitalocean.app/api/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-API-Key": "YOUR_BACKEND_API_KEY",
  },
  body: JSON.stringify({
    user_id: currentUser.id,          // stable per-user id, NOT a hardcoded string
    query: "Where is the pain map for shoulder pain?",
  }),
});

if (!response.ok) {
  throw new Error(`Chat API error: ${response.status}`);
}

const data = await response.json();

renderAssistantBubble(data.answer);

if (data.should_navigate && data.muscles.length > 0) {
  showMuscleDeepLinkChips(data.muscles);   // optional in-app navigation UX
}
```

---

## Error responses

| Status | Body | Meaning |
|---|---|---|
| 401 | `{"detail": "Invalid API key"}` | Wrong / missing `X-API-Key` |
| 422 | `{"detail": "..."}` | Missing `user_id` or `query`, or malformed JSON |
| 429 | `{"detail": "Rate limit exceeded ..."}` | More than 10 requests/min from this IP |
| 500 | `{"detail": "Internal server error"}` | Backend failure |
| 502 | `{"detail": "AI service error: ..."}` | Google Gemini call failed |

---

## Integrator checklist

- [ ] Use a **stable, unique `user_id`** per real end-user. Never hardcode `"user123"`.
- [ ] Send `X-API-Key` on every `/api/chat` request.
- [ ] Render `data.answer` in the chat UI — it always contains the full assistant reply, including navigation steps when present.
- [ ] When `data.should_navigate === true`, optionally render in-app navigation affordances using `data.muscles` / `data.muscle_found` / `data.symptom_found`.
- [ ] When `data.should_navigate === false`, do **not** show navigation buttons — the AI is either having a normal conversation or asking the user to clarify.
- [ ] Use `/api/health` as an uptime probe.
- [ ] Respect the rate limit (≤ 10 requests / minute).
