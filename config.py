import os

from dotenv import load_dotenv


load_dotenv()

BACKEND = "groq"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "30"))

MISSING_GROQ_KEYS = {"", "replace_with_your_groq_api_key", "your_groq_api_key_here"}


if GROQ_API_KEY in MISSING_GROQ_KEYS:
    raise ValueError("GROQ_API_KEY is required. Add your Groq key to .env.")
