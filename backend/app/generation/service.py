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
    store = get_session_store()
    
    chunks = store.search(
        session_id=session_id,
        query=question,
        k=k,
        document_id=document_id,
    )
    
    if not chunks:
        return {
            "answer": "I couldn't find relevant information in the uploaded documents.",
            "citations": {},
            "chunks_used": 0
        }
    
    context, citations = build_context_with_citations(chunks)
    prompt = build_chat_prompt(context, question, mode)
    
    answer = call_openrouter(prompt)
    
    return {
        "answer": answer,
        "citations": citations,
        "chunks_used": len(chunks),
        "retrieved_chunks": chunks 
    }
