import os
from langchain_ollama import OllamaEmbeddings

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini"
)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
# Embedding model for semantic chunking and retrieval
OLLAMA_EMBEDDINGS = OllamaEmbeddings(
    model=EMBEDDING_MODEL,
    base_url=OLLAMA_BASE_URL,
)

# =============================================================================
# GENERATION CONFIGURATION
# =============================================================================
LLM_MODEL = "gemini-flash-latest"
LLM_TEMPERATURE = 0.1
VALID_TAGS = ["definition", "concept", "procedure", "comparison", "application"]

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    # Warn but don't fail immediately to allow offline dev if not generating
    print("WARNING: GOOGLE_API_KEY not found. Flashcard generation will fail.")

MAX_FLASHCARDS = 10