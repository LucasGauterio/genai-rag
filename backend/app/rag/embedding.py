import requests
from config import OPENROUTER_API_KEY

EMBEDDING_MODEL = "text-embedding-3-small"
OPENROUTER_URL = "https://openrouter.ai/api/v1/embeddings"


def embed_text(text: str) -> list[float]:
    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": EMBEDDING_MODEL,
            "input": text,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    return data["data"][0]["embedding"]
