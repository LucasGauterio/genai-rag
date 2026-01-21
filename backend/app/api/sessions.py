from flask import Blueprint, request, jsonify
import uuid

from rag.session_store import get_session_store


sessions_bp = Blueprint("sessions", __name__)


from rag.ingestion import ingest_document

@sessions_bp.route("/sessions", methods=["POST"])
def create_session():
    store = get_session_store()
    session = store.create_session()
    return jsonify(session), 201


@sessions_bp.route("/sessions", methods=["GET"])
def list_sessions():
    store = get_session_store()
    sessions = store.list_sessions()
    return jsonify({"sessions": sessions})


@sessions_bp.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id: str):
    store = get_session_store()
    session = store.get_session(session_id)
    
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify(session)


@sessions_bp.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id: str):
    store = get_session_store()
    deleted = store.delete_session(session_id)
    
    if not deleted:
        return jsonify({"error": "Session not found"}), 404
    
    return jsonify({"message": f"Session {session_id} deleted"}), 200


@sessions_bp.route("/sessions/<session_id>/ingest", methods=["POST"])
def ingest_to_session(session_id: str):

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    filename = file.filename or "unknown"
    
    try:
        result = ingest_document(file, filename, session_id)
        return jsonify(result), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
