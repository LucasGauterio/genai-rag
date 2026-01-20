import time
import re
from typing import List, Dict, Set, Union

def calculate_retrieval_metrics(
    retrieved_chunks: List[Dict], 
    relevant_pages: List[int], 
    relevant_doc: str
) -> Dict[str, float]:
    """
    Calculate Precision@K, Recall@K, and MRR for retrieved chunks.
    
    Args:
        retrieved_chunks: List of chunk objects (must have 'metadata' with 'page_number' and 'source').
        relevant_pages: List of page numbers that are considered ground truth.
        relevant_doc: Filename of the relevant document.
        
    Returns:
        Dictionary with precision, recall, and mrr keys.
    """
    if not relevant_pages:
        return {"precision": 0.0, "recall": 0.0, "mrr": 0.0}

    k = len(retrieved_chunks)
    if k == 0:
        return {"precision": 0.0, "recall": 0.0, "mrr": 0.0}

    relevant_retrieved = 0
    relevant_pages_set = set(relevant_pages)
    retrieved_pages_set = set()
    first_relevant_rank = 0
    
    for i, chunk in enumerate(retrieved_chunks):
        # Access metadata safely
        meta = chunk.metadata if hasattr(chunk, "metadata") else chunk.get("metadata", {})
        doc_source = meta.get("source", "")
        page_num = meta.get("page_number")
        
        # Check if this chunk is from the correct doc and page
        # Note: simplistic matching on filename suffix due to potential path differences
        is_correct_doc = doc_source.endswith(relevant_doc) if relevant_doc else False
        
        if is_correct_doc and page_num in relevant_pages_set:
            relevant_retrieved += 1
            retrieved_pages_set.add(page_num)
            
            if first_relevant_rank == 0:
                first_relevant_rank = i + 1

    precision = relevant_retrieved / k
    recall = len(retrieved_pages_set) / len(relevant_pages_set)
    mrr = 1.0 / first_relevant_rank if first_relevant_rank > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "mrr": mrr
    }

def _normalize_for_matching(text: str) -> str:
    """Normalize text for flexible matching: lowercase, collapse whitespace, remove hyphens."""
    text = text.lower()
    text = text.replace("-", " ").replace("_", " ")  # Treat hyphens/underscores as spaces
    text = re.sub(r"\s+", " ", text)  # Collapse multiple spaces
    return text

def _keyword_matches(keyword: str, text: str) -> bool:
    """
    Check if keyword matches in text with flexible matching:
    - Case insensitive
    - Hyphen/space insensitive ("Match-on-Card" matches "match on card")
    - Handles plurals (simple 's' suffix)
    - Handles partial word boundaries
    """
    keyword_norm = _normalize_for_matching(keyword)
    text_norm = _normalize_for_matching(text)

    # Direct substring match (after normalization)
    if keyword_norm in text_norm:
        return True

    # Handle simple plurals: "CNNs" should match "CNN"
    if keyword_norm.endswith("s") and keyword_norm[:-1] in text_norm:
        return True
    # And vice versa: "CNN" should match "CNNs"
    if (keyword_norm + "s") in text_norm:
        return True

    return False

def calculate_keyword_recall(generated_text: str, expected_keywords: List[str]) -> float:
    """
    Calculate the fraction of expected keywords present in the generated text.

    Uses flexible matching:
    - Case insensitive
    - Hyphen/space insensitive ("Match-on-Card" matches "match on card")
    - Simple plural handling ("CNN" matches "CNNs")

    Args:
        generated_text: The string output from the LLM.
        expected_keywords: List of keywords/phrases to look for.

    Returns:
        Float between 0.0 and 1.0.
    """
    if not expected_keywords:
        return 1.0  # No keywords expected, so technically we missed nothing

    if not generated_text:
        return 0.0

    matches = 0

    for keyword in expected_keywords:
        if _keyword_matches(keyword, generated_text):
            matches += 1

    return matches / len(expected_keywords)

class LatencyTimer:
    def __init__(self):
        self.start_time = 0
        self.end_time = 0
        
    def start(self):
        self.start_time = time.time()
        
    def stop(self):
        self.end_time = time.time()
        return (self.end_time - self.start_time) * 1000 # ms
