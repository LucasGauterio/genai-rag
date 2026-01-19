from flask import Blueprint, request, jsonify
import uuid
import io

from rag.vector_store import ChromaVectorStore
from rag.bm25 import BM25Retriever
from utils.text import chunk_text

ingest_bp = Blueprint("ingest", __name__)
vector_store = ChromaVectorStore()
bm25_retriever = BM25Retriever()

# keeping it for reference, also for bm25 and so on.
# @ingest_bp.route("/ingest-file", methods=["POST"])
# def ingest_file():
#     """Handle file uploads including PDFs."""
#     if "file" not in request.files:
#         return jsonify({"error": "No file provided"}), 400

#     file = request.files["file"]
#     print(request)
#     filename = file.filename or "unknown"
    
#     try:
#         # Extract text based on file type
#         if filename.lower().endswith(".pdf"):
#             text = extract_pdf_text(file)
#         elif filename.lower().endswith((".txt", ".md")):
#             text = file.read().decode("utf-8")
#         else:
#             return jsonify({"error": "Unsupported file type. Use PDF, TXT, or MD"}), 400
        
#         if not text or not text.strip():
#             return jsonify({"error": "Could not extract text from file"}), 400

#         chunks = chunk_text(text)
#         ids = [str(uuid.uuid4()) for _ in chunks]
#         metadatas = [{"source": filename} for _ in chunks]

#         vector_store.add(
#             ids=ids,
#             texts=chunks,
#             metadatas=metadatas,
#         )

#         bm25_docs = [
#         {"text": chunk, "metadata": meta}
#         for chunk, meta in zip(chunks, metadatas)
#         ]
#         bm25_retriever.add_documents(bm25_docs)

#         return jsonify({
#             "chunks_ingested": len(chunks),
#             "filename": filename
#         })
#     except Exception as e:
#         return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

@ingest_bp.route("/ingest-file", methods=["POST"])
def ingest_file():
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
            return jsonify(
                {"error": "Unsupported file type. Use PDF, TXT, or MD"},
                400,
            )

        if not all_docs:
            return jsonify({"error": "No chunks produced"}), 400

        # all_docs is a list of LangChain Document objects:
        # Document(page_content=str, metadata=dict)
        # metadata={
        #   "document_id": str: uuid,
        #   "source": str: filename,
        #   "page_number": int | None,
        #   "chunk_index": int,
        #   "start_offset": int,
        #   "end_offset": int,
        #   "citation_id": str: 'docId:pPageNumber:cChunkIndex'
        # }

        # Prepare data for storage
        ids = [
            f"{document_id}_{doc.metadata.get('chunk_index', i)}"
            for i, doc in enumerate(all_docs)
        ]
        texts = [doc.page_content for doc in all_docs]
        metadatas = [doc.metadata for doc in all_docs]

        # Store in ChromaDB (vector store)
        vector_store.add(
            ids=ids,
            texts=texts,
            metadatas=metadatas,
        )

        # Store in BM25 (sparse retriever)
        bm25_docs = [
            {"text": text, "metadata": meta}
            for text, meta in zip(texts, metadatas)
        ]
        bm25_retriever.add_documents(bm25_docs)

        return jsonify({
            "document_id": document_id,
            "filename": filename,
            "chunks_ingested": len(all_docs),
            "pages": max((doc.metadata.get("page_number") or 0) for doc in all_docs),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def extract_pdf_text(file) -> list[dict]:
    """
    Extract text from a PDF file, preserving page numbers.
    Returns: [{ "page_number": int, "text": str }]
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    import io

    reader = PdfReader(io.BytesIO(file.read()))
    pages = []

    for idx, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        if page_text and page_text.strip():
            pages.append({
                "page_number": idx,
                "text": page_text
            })

    return pages


