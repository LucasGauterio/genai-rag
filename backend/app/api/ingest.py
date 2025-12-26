from flask import Blueprint, request, jsonify
import uuid
import io

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


@ingest_bp.route("/ingest-file", methods=["POST"])
def ingest_file():
    """Handle file uploads including PDFs."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    filename = file.filename or "unknown"
    
    try:
        # Extract text based on file type
        if filename.lower().endswith(".pdf"):
            text = extract_pdf_text(file)
        elif filename.lower().endswith((".txt", ".md")):
            text = file.read().decode("utf-8")
        else:
            return jsonify({"error": "Unsupported file type. Use PDF, TXT, or MD"}), 400
        
        if not text or not text.strip():
            return jsonify({"error": "Could not extract text from file"}), 400

        chunks = chunk_text(text)
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [{"source": filename} for _ in chunks]

        vector_store.add(
            ids=ids,
            texts=chunks,
            metadatas=metadatas,
        )

        return jsonify({
            "chunks_ingested": len(chunks),
            "filename": filename
        })
    except Exception as e:
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500


def extract_pdf_text(file) -> str:
    """Extract text from a PDF file using PyPDF2."""
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    
    reader = PdfReader(io.BytesIO(file.read()))
    text_parts = []
    
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    
    return "\n\n".join(text_parts)

