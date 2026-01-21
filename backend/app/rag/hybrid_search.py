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
    where_filter = None
    if document_id:
        where_filter = {"document_id": document_id}
    
    query_embedding = embed_text(query)
    dense_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k * 3,
        where=where_filter,
    )
    
    bm25_results = bm25.search(
        query,
        k=k * 3,
        metadata_filter={"document_id": document_id} if document_id else None,
    )
    
    doc_map = _fuse_results(dense_results, bm25_results, rrf_k)
    
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
    doc_map = {}
    
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
    
    for doc_data in doc_map.values():
        score = 0.0
        if doc_data["dense_rank"] is not None:
            score += 1.0 / (rrf_k + doc_data["dense_rank"])
        if doc_data["sparse_rank"] is not None:
            score += 1.0 / (rrf_k + doc_data["sparse_rank"])
        doc_data["score"] = score
    
    return doc_map
