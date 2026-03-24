"""
ML-based query classification using Gemini API.
Classifies queries into: navigation, symptom, or knowledge
with higher accuracy than keyword matching (~90% vs 70%).
"""
from google import genai
from app.config.settings import GEMINI_API_KEY, ENABLE_ML_CLASSIFIER, CLASSIFIER_MODEL
from app.utils.logger import get_logger

log = get_logger("classifier_service")

_client = genai.Client(api_key=GEMINI_API_KEY)

# Classification system prompt
CLASSIFICATION_PROMPT = """You are a query classifier for a TriggerPoints mobile app chatbot.

Classify the following user query into ONE of these categories:

1. **navigation** - Questions about how to use the app, UI features, settings, account management
   Examples: "How do I find a muscle?", "Where is the settings page?", "How do I log symptoms?"

2. **symptom** - Questions about symptoms, pain, muscles, trigger points, referred pain
   Examples: "What causes neck pain?", "What are trigger points for trapezius?", "I have shoulder pain"

3. **knowledge** - General questions about health, anatomy, therapy concepts
   Examples: "What is myofascial pain?", "How does trigger point therapy work?"

IMPORTANT: Respond with ONLY the category name (navigation | symptom | knowledge), nothing else.
No explanation, no markdown, just the single word."""


def classify(query: str) -> str:
    """
    Classify a query using Gemini API.
    Returns: "navigation", "symptom", or "knowledge"
    """
    if not ENABLE_ML_CLASSIFIER:
        log.debug("ML classifier disabled, using fallback")
        from app.utils.query_router import route
        return route(query)
    
    try:
        log.debug(f"Classifying query using Gemini")
        response = _client.models.generate_content(
            model=CLASSIFIER_MODEL,
            contents=[
                {"role": "user", "parts": [{"text": CLASSIFICATION_PROMPT}]},
                {"role": "model", "parts": [{"text": "I understand. I will classify queries into navigation, symptom, or knowledge categories."}]},
                {"role": "user", "parts": [{"text": f"Classify: {query}"}]},
            ],
        )
        
        classification = response.text.strip().lower().split()[0]  # Get first word
        
        # Validate response
        if classification not in ("navigation", "symptom", "knowledge"):
            log.warning(f"Invalid classification: {classification}, falling back to keyword routing")
            from app.utils.query_router import route
            return route(query)
        
        log.debug(f"Query classified as: {classification}")
        return classification
        
    except Exception as e:
        log.error(f"Classification error: {e}, falling back to keyword routing")
        from app.utils.query_router import route
        return route(query)
