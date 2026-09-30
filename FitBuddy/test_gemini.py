from app.config import get_settings
from google import genai

settings = get_settings()
if not settings.gemini_api_key:
    raise SystemExit("GEMINI_API_KEY is missing in .env")

client = genai.Client(api_key=settings.gemini_api_key)
print("Testing model:", settings.gemini_plan_model)
response = client.models.generate_content(
    model=settings.gemini_plan_model,
    contents="Reply with exactly: FITBUDDY GEMINI OK",
)
print("Gemini response:", response.text)
