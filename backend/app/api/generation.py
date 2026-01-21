import random
from flask import Blueprint, request, jsonify

from rag.session_store import get_session_store
from utils.prompts import build_context_with_citations

from generation.service import generate_chat_answer


from config import MAX_FLASHCARDS
from generation import ExtractorChain
from generation import TransformationChain


generation_bp = Blueprint("generation", __name__)


@generation_bp.route("/sessions/<session_id>/chat", methods=["POST"])
def chat_in_session(session_id: str):
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
        result = generate_chat_answer(
            session_id=session_id,
            question=question,
            k=k,
            document_id=document_id,
            mode=mode
        )

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
        extractor = ExtractorChain()
        extracted = extractor.extract(context)

        # Limit the extracted concepts to the requested count or MAX_FLASHCARDS
        limit = min(count, MAX_FLASHCARDS)
        if len(extracted.concepts) > limit:
            extracted.concepts = random.sample(extracted.concepts, limit)
        
        # 3. Transform to flashcards
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
