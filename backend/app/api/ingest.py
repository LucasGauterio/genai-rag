from flask import Blueprint, request, jsonify
import uuid

from rag.vector_store import ChromaVectorStore
from utils.text import chunk_text

ingest_bp = Blueprint("ingest", __name__)
vector_store = ChromaVectorStore()


@ingest_bp.route("/ingest", methods=["POST"])
def ingest():
    payload = request.get_json()
    text = payload.get("text")

    if not text:
        return jsonify({"error": "Missing text"}), 400

    chunks = chunk_text(text)

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": "manual"} for _ in chunks]

    vector_store.add(
        ids=ids,
        texts=chunks,
        metadatas=metadatas,
    )

    return jsonify({
        "chunks_ingested": len(chunks)
    })
