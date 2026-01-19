"""
Generation API - Chat and flashcard generation.
"""

from flask import Blueprint, request, jsonify

from rag.session_store import get_session_store
from llm import call_openrouter
from utils.prompts import (
    build_context_with_citations,
    build_chat_prompt,
    build_flashcard_prompt,
    parse_flashcards,
)


generation_bp = Blueprint("generation", __name__)


@generation_bp.route("/sessions/<session_id>/chat", methods=["POST"])
def chat_in_session(session_id: str):
    """
    Chat within a session, retrieving only from that session's documents.
    
    Request:
        {
            "question": "What is attention?",
            "mode": "chat" | "flashcards" | "summary",
            "document_id": "optional - filter to specific doc",
            "k": 5
        }
    
    Returns:
        {
            "answer": "Attention is... [1]",
            "citations": { "[1]": { page, source, text, citation_id } }
        }
    """
    store = get_session_store()
    
    session = store.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    data = request.get_json()
    question = data.get("question", "")
    mode = data.get("mode", "chat")
    document_id = data.get("document_id")
    k = data.get("k", 5)
    
    if not question:
        return jsonify({"error": "Missing question"}), 400
    
    try:
        # Retrieve from session
        chunks = store.search(
            session_id=session_id,
            query=question,
            k=k,
            document_id=document_id,
        )
        
        if not chunks:
            return jsonify({
                "answer": "I couldn't find relevant information in the uploaded documents.",
                "citations": {}
            })
        
        # Build context and prompt
        context, citations = build_context_with_citations(chunks)
        prompt = build_chat_prompt(context, question, mode)
        
        # Generate response
        answer = call_openrouter(prompt)
        
        return jsonify({
            "answer": answer,
            "citations": citations,
            "chunks_used": len(chunks),
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@generation_bp.route("/sessions/<session_id>/flashcards", methods=["POST"])
def generate_flashcards(session_id: str):
    """
    Generate flashcards from session documents.
    
    Request:
        {
            "topic": "attention mechanism",
            "document_id": "optional - filter to specific doc",
            "count": 10
        }
    
    Returns:
        {
            "flashcards": [{ "question", "answer", "citation" }],
            "citations": { ... }
        }
    """
    store = get_session_store()
    
    session = store.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    data = request.get_json()
    topic = data.get("topic", "")
    document_id = data.get("document_id")
    count = data.get("count", 10)
    
    if not topic:
        return jsonify({"error": "Missing topic"}), 400
    
    try:
        # Retrieve relevant chunks
        chunks = store.search(
            session_id=session_id,
            query=topic,
            k=min(count * 2, 20),
            document_id=document_id,
        )
        
        if not chunks:
            return jsonify({
                "flashcards": [],
                "citations": {},
                "message": "No relevant content found"
            })
        
        # Build context and prompt
        context, citations = build_context_with_citations(chunks)
        prompt = build_flashcard_prompt(context, topic, count)
        
        # Generate flashcards
        response = call_openrouter(prompt)
        flashcards = parse_flashcards(response)
        
        return jsonify({
            "flashcards": flashcards,
            "citations": citations,
            "topic": topic,
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
