import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (two directories up from backend/app)
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"  # Free model for OpenRouter free tier

