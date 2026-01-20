"""
Generation API - Chat and flashcard generation.
"""

import random
from flask import Blueprint, request, jsonify

from rag.session_store import get_session_store
from llm import call_openrouter
from utils.prompts import (
    build_context_with_citations,
    build_chat_prompt,
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
    Generate flashcards from session documents using advanced pipeline.
    
    Request:
        {
            "topic": "attention mechanism",
            "document_id": "optional - filter to specific doc",
            "count": 10,
            "validate": true (default)
        }
    
    Returns:
        {
            "flashcards": [{ "question", "answer", "citation", "tag" }],
            "citations": { ... },
            "stats": { ... }
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
    should_validate = data.get("validate", True)
    
    if not topic:
        return jsonify({"error": "Missing topic"}), 400
    
    try:
        # 1. Retrieve relevant chunks
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
        
        # Build context and citations
        context, citations = build_context_with_citations(chunks)
        
        # 2. Extract concepts
        # We pass the formatted context string directly to preserve [1] markers
        from generation import ExtractorChain
        extractor = ExtractorChain()
        extracted = extractor.extract(context)

        from config import MAX_FLASHCARDS
        # Limit the extracted concepts to the requested count or MAX_FLASHCARDS
        limit = min(count, MAX_FLASHCARDS)
        if len(extracted.concepts) > limit:
            extracted.concepts = random.sample(extracted.concepts, limit)
        
        # 3. Transform to flashcards
        from generation import TransformationChain
        transformer = TransformationChain()
        card_set = transformer.transform(extracted)
        
        # 4. Self-Correction (Optional)
        stats = {}
        if should_validate:
            from validation import validate_and_correct_cards
            card_set, stats = validate_and_correct_cards(card_set, context)
            
        # Limit to requested count
        if len(card_set.cards) > count:
            from generation.structured_output import FlashcardSet
            card_set = FlashcardSet(cards=card_set.cards[:count])
        
        return jsonify({
            "flashcards": [c.model_dump() for c in card_set.cards],
            "citations": citations,
            "topic": topic,
            "stats": stats
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
