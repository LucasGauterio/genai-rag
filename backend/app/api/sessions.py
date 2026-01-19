"""
Session management API - CRUD operations and document ingestion.
"""

from flask import Blueprint, request, jsonify
import uuid

from rag.session_store import get_session_store
from utils.text import chunk_text
from utils.pdf import extract_pdf_text


sessions_bp = Blueprint("sessions", __name__)


@sessions_bp.route("/sessions", methods=["POST"])
def create_session():
    """Create a new session with its own document collection."""
    store = get_session_store()
    session = store.create_session()
    return jsonify(session), 201


@sessions_bp.route("/sessions", methods=["GET"])
def list_sessions():
    """List all active sessions."""
    store = get_session_store()
    sessions = store.list_sessions()
    return jsonify({"sessions": sessions})


@sessions_bp.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id: str):
    """Get session info including uploaded documents."""
    store = get_session_store()
    session = store.get_session(session_id)
    
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify(session)


@sessions_bp.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id: str):
    """Close a session and delete its collection."""
    store = get_session_store()
    deleted = store.delete_session(session_id)
    
    if not deleted:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify({"message": f"Session {session_id} deleted"}), 200


@sessions_bp.route("/sessions/<session_id>/ingest", methods=["POST"])
def ingest_to_session(session_id: str):
    """
    Upload a document to a session.
    
    The document will be chunked with citation metadata:
    - document_id, page_number, chunk_index
    - start_offset, end_offset, citation_id
    """
    store = get_session_store()
    
    # Verify session exists
    session = store.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    # Check for file
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    filename = file.filename or "unknown"
    
    try:
        document_id = str(uuid.uuid4())
        all_docs = []
        
        if filename.lower().endswith(".pdf"):
            pages = extract_pdf_text(file)
            
            if not pages:
                return jsonify({"error": "No extractable text in PDF"}), 400
            
            for page in pages:
                page_docs = chunk_text(
                    page["text"],
                    source=filename,
                    document_id=document_id,
                    page_number=page["page_number"],
                )
                all_docs.extend(page_docs)
        
        elif filename.lower().endswith((".txt", ".md")):
            text = file.read().decode("utf-8")
            all_docs = chunk_text(
                text,
                source=filename,
                document_id=document_id,
                page_number=None,
            )
        
        else:
            return jsonify({"error": "Unsupported file type. Use PDF, TXT, or MD"}), 400
        
        if not all_docs:
            return jsonify({"error": "No chunks produced"}), 400
        
        # Store in session's collection
        result = store.add_documents(
            session_id=session_id,
            documents=all_docs,
            document_id=document_id,
            filename=filename,
        )
        
        return jsonify(result), 201
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
