"""
Generation service for RAG system.
Handles retrieval, prompting, and LLM interaction for chat.
"""
from typing import Dict, Any, Optional

from rag.session_store import get_session_store
from llm import call_openrouter
from utils.prompts import (
    build_context_with_citations,
    build_chat_prompt,
)

def generate_chat_answer(
    session_id: str, 
    question: str, 
    k: int = 5, 
    document_id: Optional[str] = None,
    mode: str = "chat"
) -> Dict[str, Any]:
    """
    Generate an answer for a chat query using RAG.
    
    Args:
        session_id: ID of the session to retrieve documents from
        question: User query
        k: Number of chunks to retrieve
        document_id: Optional filter for a specific document
        mode: Prompt mode ("chat", etc.)
        
    Returns:
        Dict containing answer, citations, and retrieval stats.
    """
    store = get_session_store()
    
    # Retrieve from session
    chunks = store.search(
        session_id=session_id,
        query=question,
        k=k,
        document_id=document_id,
    )
    
    if not chunks:
        # Standardized empty response
        return {
            "answer": "I couldn't find relevant information in the uploaded documents.",
            "citations": {},
            "chunks_used": 0
        }
    
    # Build context and prompt
    context, citations = build_context_with_citations(chunks)
    prompt = build_chat_prompt(context, question, mode)
    
    # Generate response
    answer = call_openrouter(prompt)
    
    return {
        "answer": answer,
        "citations": citations,
        "chunks_used": len(chunks),
        "retrieved_chunks": chunks # Returning chunks too for evaluation purposes
    }
