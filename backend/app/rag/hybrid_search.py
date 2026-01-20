"""
Hybrid search with Reciprocal Rank Fusion (RRF).

Combines dense (vector) and sparse (BM25) retrieval.
"""

from typing import List, Dict, Optional

from rag.embedding import embed_text
from rag.bm25 import BM25Retriever


def hybrid_search(
    collection,
    bm25: BM25Retriever,
    query: str,
    k: int = 5,
    document_id: Optional[str] = None,
    rrf_k: int = 60,
) -> List[Dict]:
    """
    Search using hybrid retrieval with RRF fusion.
    
    Args:
        collection: ChromaDB collection
        bm25: BM25Retriever instance
        query: Search query
        k: Number of results to return
        document_id: Optional filter to specific document
        rrf_k: RRF smoothing constant (default 60)
    
    Returns:
        List of results with text, metadata, and scores
    """
    # Build filter
    where_filter = None
    if document_id:
        where_filter = {"document_id": document_id}
    
    # Dense search (ChromaDB)
    query_embedding = embed_text(query)
    dense_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k * 3,
        where=where_filter,
    )
    
    # Sparse search (BM25)
    bm25_results = bm25.search(
        query,
        k=k * 3,
        metadata_filter={"document_id": document_id} if document_id else None,
    )
    
    # RRF Fusion
    doc_map = _fuse_results(dense_results, bm25_results, rrf_k)
    
    # Sort and return top-k
    ranked = sorted(doc_map.values(), key=lambda x: x["score"], reverse=True)
    
    return [
        {
            "text": d["text"],
            "metadata": d["metadata"],
            "score": d["score"],
        }
        for d in ranked[:k]
    ]


def _fuse_results(
    dense_results: Dict,
    bm25_results: List[Dict],
    rrf_k: int = 60,
) -> Dict[str, Dict]:
    """
    Fuse dense and sparse results using RRF.
    
    RRF formula: score = Σ 1/(k + rank)
    
    Args:
        dense_results: ChromaDB query results
        bm25_results: BM25 search results
        rrf_k: RRF smoothing constant
    
    Returns:
        Dict mapping doc_key to result with fused score
    """
    doc_map = {}
    
    # Process dense results
    if dense_results["documents"] and dense_results["documents"][0]:
        for rank, (text, meta) in enumerate(
            zip(dense_results["documents"][0], dense_results["metadatas"][0]),
            start=1
        ):
            doc_key = meta.get("citation_id", text[:50])
            if doc_key not in doc_map:
                doc_map[doc_key] = {
                    "text": text,
                    "metadata": meta,
                    "dense_rank": rank,
                    "sparse_rank": None,
                }
            else:
                doc_map[doc_key]["dense_rank"] = rank
    
    # Process sparse results
    for rank, doc in enumerate(bm25_results, start=1):
        doc_key = doc["metadata"].get("citation_id", doc["text"][:50])
        if doc_key not in doc_map:
            doc_map[doc_key] = {
                "text": doc["text"],
                "metadata": doc["metadata"],
                "dense_rank": None,
                "sparse_rank": rank,
            }
        else:
            doc_map[doc_key]["sparse_rank"] = rank
    
    # Calculate RRF scores
    for doc_data in doc_map.values():
        score = 0.0
        if doc_data["dense_rank"] is not None:
            score += 1.0 / (rrf_k + doc_data["dense_rank"])
        if doc_data["sparse_rank"] is not None:
            score += 1.0 / (rrf_k + doc_data["sparse_rank"])
        doc_data["score"] = score
    
    return doc_map
