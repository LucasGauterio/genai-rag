import os

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini"
)
OLLAMA_EMBEDDINGS = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434",
)