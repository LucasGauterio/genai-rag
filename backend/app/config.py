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
LLM_MODEL = OPENROUTER_MODEL
LLM_TEMPERATURE = 0.1
VALID_TAGS = ["definition", "concept", "procedure", "comparison", "application"]

MAX_FLASHCARDS = 10