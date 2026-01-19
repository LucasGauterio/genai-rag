"""
Embedding utilities using Ollama (local, free).

Uses the same embedding model as semantic chunking for consistency.
"""

import os
import requests
from typing import List
from config import OLLAMA_BASE_URL, EMBEDDING_MODEL

def embed_text(text: str) -> List[float]:
    """
    Embed a single text using Ollama.
    
    Args:
        text: Text to embed
    
    Returns:
        Embedding vector as list of floats
    """
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
    """
    Embed multiple texts (calls embed_text for each).
    
    Note: Ollama doesn't support batch embeddings natively,
    so this is a simple loop. For large batches, consider
    using a different embedding service.
    """
    return [embed_text(t) for t in texts]
