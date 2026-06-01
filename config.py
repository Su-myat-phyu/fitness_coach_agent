import os

from dotenv import load_dotenv


load_dotenv()

BACKEND = os.getenv("BACKEND", "ollama").strip().lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3").strip()
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "30"))


if BACKEND not in {"groq", "ollama"}:
    raise ValueError("BACKEND must be either 'groq' or 'ollama'.")

if BACKEND == "groq" and not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is required when BACKEND=groq.")
