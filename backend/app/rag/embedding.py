import os
import requests
from typing import List
from config import OLLAMA_BASE_URL, EMBEDDING_MODEL

def embed_text(text: str) -> List[float]:
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={
            "model": EMBEDDING_MODEL,
            "prompt": text,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    
    return data["embedding"]


def embed_batch(texts: List[str]) -> List[List[float]]:
    return [embed_text(t) for t in texts]
