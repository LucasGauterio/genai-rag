import os
from dotenv import load_dotenv, find_dotenv
from langchain_ollama import OllamaEmbeddings

# Load environment variables
load_dotenv(find_dotenv())

# LLM Provider: 'openrouter' or 'gemini'
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini"
)

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# Local Embeddings (Ollama)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_EMBEDDINGS = OllamaEmbeddings(
    model=EMBEDDING_MODEL,
    base_url=OLLAMA_BASE_URL,
)


if LLM_PROVIDER == "gemini":
    LLM_MODEL = GEMINI_MODEL
else:
    LLM_MODEL = OPENROUTER_MODEL

LLM_TEMPERATURE = 0.1
VALID_TAGS = ["definition", "concept", "procedure", "comparison", "application"]

MAX_FLASHCARDS = 10