"""
Generation API - Chat and flashcard generation.
"""

from flask import Blueprint, request, jsonify

from rag.session_store import get_session_store
from utils.prompts import build_context_with_citations


generation_bp = Blueprint("generation", __name__)


@generation_bp.route("/sessions/<session_id>/chat", methods=["POST"])
def chat_in_session(session_id: str):
    """
    Chat within a session, retrieving only from that session's documents.
    Delegates to shared service in generation.service.
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
        from generation.service import generate_chat_answer
        result = generate_chat_answer(
            session_id=session_id,
            question=question,
            k=k,
            document_id=document_id,
            mode=mode
        )
        
        # Filter out 'retrieved_chunks' from API response if not needed, 
        # or leave it. The original didn't return chunks, but it returned 'chunks_used'.
        # The service returns 'retrieved_chunks'.
        # I'll construct the response to match the original API contract exactly.
        
        response = {
            "answer": result["answer"],
            "citations": result["citations"],
            "chunks_used": result["chunks_used"]
        }
        return jsonify(response)
    
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
