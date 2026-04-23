"""
Intent detector.
Classifies every query into one of 5 intents per the App Workflow Chatbot Guide:

  FLOW_B      — user knows the muscle (direct landscape navigation)
  FLOW_A      — user has a symptom, doesn't know muscle (symptoms screen)
  HYBRID      — user has both muscle + wants explanation (text + Flow B)
  APP_HELP    — user asking how to use the app
  KNOWLEDGE   — general question about trigger points / therapy (RAG only)
"""
from google import genai
from google.genai import types
from app.config.settings import GEMINI_API_KEY, CLASSIFIER_MODEL
from app.utils.logger import get_logger

log = get_logger("intent_detector")

_client = genai.Client(api_key=GEMINI_API_KEY)

INTENT_PROMPT = """You are an intent classifier for the TriggerPoints3D mobile app chatbot.

Classify the user query into EXACTLY ONE of these intents:

FLOW_B   — User mentions a specific muscle by name AND wants to see/navigate to it
           (pain map, trigger points, video, self-help, anatomy info about that muscle)
           Examples: "show pain map of SCM", "where is trapezius", "show deltoid trigger points",
                     "open self help for QL", "show video for infraspinatus"

FLOW_A   — User describes a symptom or pain WITHOUT knowing which muscle causes it
           Examples: "I have neck pain", "my jaw hurts", "I have dizziness",
                     "what causes shoulder pain", "which muscle causes headaches"

HYBRID   — User mentions a specific muscle AND wants an explanation/treatment info
           Examples: "how to treat SCM trigger points", "explain trapezius and show pain map",
                     "what does infraspinatus do and where are its trigger points"

APP_HELP — User asking how to use the app UI
           Examples: "how do I see pain map", "how to watch videos", "how to use self help",
                     "how do I navigate the app", "what does the rotate button do"

KNOWLEDGE — General question about trigger point therapy, anatomy concepts, not app-specific
           Examples: "what is a trigger point", "how does dry needling work",
                     "what is myofascial pain", "tell me about referred pain"

User query: {query}

Respond with ONLY the intent word (FLOW_B, FLOW_A, HYBRID, APP_HELP, or KNOWLEDGE). Nothing else."""


def detect_intent(query: str) -> str:
    """
    Detect intent using Gemini. Falls back to keyword rules on failure.
    Returns one of: FLOW_B, FLOW_A, HYBRID, APP_HELP, KNOWLEDGE
    """
    try:
        response = _client.models.generate_content(
            model=CLASSIFIER_MODEL,
            contents=INTENT_PROMPT.format(query=query),
            config=types.GenerateContentConfig(temperature=0.0),
        )
        intent = response.text.strip().upper().split()[0]
        if intent in ("FLOW_B", "FLOW_A", "HYBRID", "APP_HELP", "KNOWLEDGE"):
            log.debug(f"Intent detected: {intent}")
            return intent
    except Exception as e:
        log.warning(f"Intent detection failed: {e}, using keyword fallback")

    return _keyword_fallback(query)


def _keyword_fallback(query: str) -> str:
    q = query.lower()

    app_help_kw = {"how do i", "how to", "how can i", "where is the", "what is the button",
                   "navigate", "rotate button", "landscape mode", "split view", "settings"}
    visual_kw = {"pain map", "trigger point", "show", "view", "open", "see", "display",
                 "video", "self help", "self-help", "needling", "anatomy"}
    symptom_kw = {"pain", "ache", "hurt", "sore", "stiff", "numb", "tingling", "dizziness",
                  "headache", "cramp", "spasm", "tightness", "weakness", "i have", "i feel",
                  "which muscle", "what causes", "what muscle"}

    if any(kw in q for kw in app_help_kw):
        return "APP_HELP"
    if any(kw in q for kw in visual_kw):
        return "FLOW_B"
    if any(kw in q for kw in symptom_kw):
        return "FLOW_A"
    return "KNOWLEDGE"
