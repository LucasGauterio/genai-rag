"""
Multi-query expansion for improved retrieval.

This module implements query expansion techniques to generate multiple
paraphrased queries and merge their retrieval results.
"""

from typing import List
from llm import call_openrouter


def expand_query(original_query: str, num_queries: int = 3) -> List[str]:
    """
    Generate multiple paraphrased queries using LLM.
    
    Args:
        original_query: The user's original query
        num_queries: Total number of queries to generate (including original)
    
    Returns:
        List of queries: [original_query, paraphrase1, paraphrase2, ...]
    """
    if num_queries <= 1:
        return [original_query]
    
    prompt = f"""Generate {num_queries - 1} alternative phrasings of the following query.
Each phrasing should use different words but maintain the same intent.
Focus on academic/technical terminology variations.
Return only the queries, one per line, without numbering or bullets.

Original query: {original_query}

Alternative phrasings:"""
    
    try:
        response = call_openrouter(prompt)
        # Parse response: split by newlines, clean up
        queries = [
            line.strip()
            for line in response.split('\n')
            if line.strip() and not line.strip().startswith(('#', '-', '*', '•'))
        ]
        
        # Combine with original
        all_queries = [original_query] + queries[:num_queries - 1]
        return all_queries[:num_queries]
    
    except Exception as e:
        # Fallback to original query if expansion fails
        print(f"Query expansion failed: {e}")
        return [original_query]


def multi_query_retrieve(
    retriever,
    query: str,
    k: int = 5,
    num_expansions: int = 3
) -> List[dict]:
    """
    Retrieve using multiple query variations and merge results.
    
    Args:
        retriever: HybridRetriever instance
        query: Original user query
        k: Number of final results to return
        num_expansions: Number of query variations to generate
    
    Returns:
        List of document dicts with aggregated scores
    """
    # Generate query variations
    queries = expand_query(query, num_expansions)
    
    # Retrieve for each query
    all_results = {}
    for q in queries:
        try:
            results = retriever.retrieve(q, k=k * 2)  # Retrieve more per query
            
            for rank, doc in enumerate(results, start=1):
                # Use text as key (or doc ID if available)
                doc_key = doc.get("metadata", {}).get("id") or doc.get("text", "")[:100]
                
                if doc_key not in all_results:
                    all_results[doc_key] = {
                        "text": doc.get("text", doc),
                        "metadata": doc.get("metadata", {}),
                        "ranks": []
                    }
                
                # Store rank (lower is better)
                all_results[doc_key]["ranks"].append(rank)
        
        except Exception as e:
            print(f"Retrieval failed for query '{q}': {e}")
            continue
    
    # Aggregate scores using reciprocal rank fusion
    for doc_key, doc_data in all_results.items():
        ranks = doc_data["ranks"]
        # RRF: sum of 1/(k + rank) for each rank
        rrf_k = 60
        rrf_score = sum(1.0 / (rrf_k + rank) for rank in ranks)
        doc_data["final_score"] = rrf_score
    
    # Sort by final score and return top-k
    ranked = sorted(
        all_results.values(),
        key=lambda x: x["final_score"],
        reverse=True
    )
    
    return [
        {"text": d["text"], "metadata": d["metadata"]}
        for d in ranked[:k]
    ]
