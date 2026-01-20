"""
Hybrid Retriever - Dense Vectors + BM25 for comprehensive retrieval.

This is critical for flashcard generation because:
1. Dense vectors catch semantic relationships ("What is polymorphism?")
2. BM25 catches exact terminology ("Define __init__ method")

The ensemble combines both with configurable weights and optional re-ranking.
"""

from typing import List, Optional
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever

from .vector_store import VectorStore

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import RETRIEVAL_K, BM25_WEIGHT, DENSE_WEIGHT, RERANK_MODEL


class HybridRetriever:
    """
    Hybrid retriever combining dense vectors and BM25.
    
    Architecture:
    Query ──┬──> Dense Retriever (semantic)
            │     └──> BGE embeddings → ChromaDB
            │
            └──> Sparse Retriever (keyword)
                  └──> BM25 algorithm
                  
    Results merged via Reciprocal Rank Fusion (RRF)
    Optional re-ranking with FlashrankRerank
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        k: int = RETRIEVAL_K,
        bm25_weight: float = BM25_WEIGHT,
        dense_weight: float = DENSE_WEIGHT,
        use_reranker: bool = True,
    ):
        """
        Initialize the hybrid retriever.
        
        Args:
            vector_store: VectorStore instance with indexed documents
            k: Number of final results to return
            bm25_weight: Weight for BM25 results (0-1)
            dense_weight: Weight for dense vector results (0-1)
            use_reranker: Whether to apply re-ranking
        """
        self.vector_store = vector_store
        self.k = k
        self.bm25_weight = bm25_weight
        self.dense_weight = dense_weight
        self.use_reranker = use_reranker
        
        # Initialize BM25 with all documents
        self._bm25_retriever = None
        self._reranker = None
    
    @property
    def bm25_retriever(self) -> BM25Retriever:
        """Lazy-load BM25 retriever."""
        if self._bm25_retriever is None:
            documents = self.vector_store.get_all_documents()
            if documents:
                self._bm25_retriever = BM25Retriever.from_documents(documents)
                self._bm25_retriever.k = self.k * 2  # Get more for ensemble
        return self._bm25_retriever
    
    @property
    def reranker(self):
        """Lazy-load reranker."""
        if self._reranker is None and self.use_reranker:
            try:
                from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank
                self._reranker = FlashrankRerank(model=RERANK_MODEL)
            except Exception as e:
                print(f"Warning: Reranker initialization failed: {e}")
                self._reranker = False  # Mark as unavailable
        return self._reranker if self._reranker is not False else None
    
    def retrieve(
        self,
        query: str,
        doc_ids: Optional[List[str]] = None,
    ) -> List[Document]:
        """
        Retrieve documents using hybrid search.
        
        Args:
            query: Search query
            doc_ids: Optional list of doc_ids to filter by
            
        Returns:
            Ranked list of relevant documents
        """
        # 1. Dense vector search
        filter_dict = None
        if doc_ids:
            if len(doc_ids) == 1:
                filter_dict = {"doc_id": doc_ids[0]}
            else:
                filter_dict = {"doc_id": {"$in": doc_ids}}
        
        dense_results = self.vector_store.similarity_search(
            query, 
            k=self.k * 2,
            filter_dict=filter_dict
        )
        
        # 2. BM25 keyword search
        bm25_results = []
        if self.bm25_retriever:
            all_bm25 = self.bm25_retriever.invoke(query)
            
            # Apply doc_id filter if specified
            if doc_ids:
                bm25_results = [
                    doc for doc in all_bm25 
                    if doc.metadata.get("doc_id") in doc_ids
                ]
            else:
                bm25_results = all_bm25
        
        # 3. Combine using Reciprocal Rank Fusion
        combined = self._reciprocal_rank_fusion(
            [dense_results, bm25_results],
            [self.dense_weight, self.bm25_weight]
        )
        
        # 4. Apply re-ranking if available
        if self.reranker and combined:
            try:
                reranked = self.reranker.compress_documents(combined[:self.k * 2], query)
                combined = list(reranked)
            except Exception as e:
                print(f"Reranking failed, using original order: {e}")
        
        return combined[:self.k]
    
    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[Document]],
        weights: List[float],
        k: int = 60,  # RRF constant
    ) -> List[Document]:
        """
        Combine multiple ranked lists using Reciprocal Rank Fusion.
        
        RRF Score = Σ (weight / (rank + k))
        
        Args:
            result_lists: List of ranked document lists
            weights: Weight for each list
            k: RRF constant (higher = less emphasis on top ranks)
            
        Returns:
            Combined and re-ranked document list
        """
        # Track scores by document content (use as unique key)
        doc_scores = {}
        doc_map = {}  # content -> Document
        
        for results, weight in zip(result_lists, weights):
            for rank, doc in enumerate(results, start=1):
                content_key = doc.page_content[:200]  # Use first 200 chars as key
                
                if content_key not in doc_scores:
                    doc_scores[content_key] = 0.0
                    doc_map[content_key] = doc
                
                # RRF formula
                doc_scores[content_key] += weight / (rank + k)
        
        # Sort by combined score
        sorted_keys = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)
        
        return [doc_map[key] for key in sorted_keys]


def create_hybrid_retriever(
    vector_store: VectorStore,
    k: int = RETRIEVAL_K,
    use_reranker: bool = True,
) -> HybridRetriever:
    """
    Factory function to create a configured hybrid retriever.
    
    Args:
        vector_store: Initialized vector store
        k: Number of results to return
        use_reranker: Whether to use re-ranking
        
    Returns:
        Configured HybridRetriever instance
    """
    return HybridRetriever(
        vector_store=vector_store,
        k=k,
        use_reranker=use_reranker,
    )


def format_retrieved_docs(docs: List[Document]) -> str:
    """
    Format retrieved documents for LLM context.
    
    Args:
        docs: List of retrieved documents
        
    Returns:
        Formatted string with source citations
    """
    formatted = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get('source', 'Unknown')
        page = doc.metadata.get('page_number', 'N/A')
        section = doc.metadata.get('section_h1') or doc.metadata.get('section', 'N/A')
        
        formatted.append(
            f"[{i}] Source: {source} | Page: {page} | Section: {section}\n"
            f"{doc.page_content}\n"
        )
    
    return "\n---\n".join(formatted)
