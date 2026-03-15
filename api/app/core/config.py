import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "SCT Extractor API"
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

settings = Settings()

# Global initialization of GenAI client
def setup_ai():
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
    else:
        print("Warning: Could not initialize GenAI client. Ensure GOOGLE_API_KEY or GEMINI_API_KEY is set.")

setup_ai()
