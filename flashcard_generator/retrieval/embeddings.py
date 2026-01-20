"""
Embedding Functions - Using BGE-large for state-of-the-art embeddings.

BGE (BAAI General Embedding) is currently one of the best open-source
embedding models, outperforming many commercial alternatives on MTEB benchmarks.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from functools import lru_cache

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embedding_function(model_name: str = None) -> HuggingFaceEmbeddings:
    """
    Get the embedding function (cached for efficiency).
    
    Uses BGE-large by default for best retrieval quality.
    The model is cached to avoid reloading on every call.
    
    Args:
        model_name: Optional override for embedding model
        
    Returns:
        HuggingFaceEmbeddings instance
    """
    model = model_name or EMBEDDING_MODEL
    
    # Normalized embeddings work better for similarity search
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}
    
    return HuggingFaceEmbeddings(
        model_name=model,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )


def embed_query(text: str, model_name: str = None) -> list:
    """
    Embed a single query text.
    
    Args:
        text: Text to embed
        model_name: Optional model override
        
    Returns:
        Embedding vector as list of floats
    """
    embeddings = get_embedding_function(model_name)
    return embeddings.embed_query(text)


def embed_documents(texts: list, model_name: str = None) -> list:
    """
    Embed multiple document texts.
    
    Args:
        texts: List of texts to embed
        model_name: Optional model override
        
    Returns:
        List of embedding vectors
    """
    embeddings = get_embedding_function(model_name)
    return embeddings.embed_documents(texts)
