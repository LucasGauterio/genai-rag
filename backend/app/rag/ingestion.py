"""
Ingestion service for RAG system.
Handles file processing, text extraction, chunking, and storage.
"""
import uuid
from typing import BinaryIO, Dict, Any, Union

from rag.session_store import get_session_store
from utils.text import chunk_text
from utils.pdf import extract_pdf_text

def ingest_document(
    file_obj: Union[BinaryIO, Any], 
    filename: str, 
    session_id: str
) -> Dict[str, Any]:
    """
    Ingest a document into the specified session.
    
    Args:
        file_obj: File-like object (opened in binary mode for PDF, or compatible stream)
        filename: Name of the file (used for type detection and metadata)
        session_id: ID of the session to add documents to
        
    Returns:
        Dict containing operation result/stats
    """
    store = get_session_store()
    document_id = str(uuid.uuid4())
    all_docs = []
    
    filename_lower = filename.lower()
    
    if filename_lower.endswith(".pdf"):
        # extract_pdf_text expects a binary file stream
        pages = extract_pdf_text(file_obj)
        
        if not pages:
            raise ValueError("No extractable text found in PDF")
        
        for page in pages:
            page_docs = chunk_text(
                page["text"],
                source=filename,
                document_id=document_id,
                page_number=page["page_number"],
            )
            all_docs.extend(page_docs)
            
    elif filename_lower.endswith((".txt", ".md")):
        # Read text content
        # If file_obj is bytes (from open(..., 'rb')), decode it
        # If it's a string buffer, use as is. 
        # Flask FileStorage.read() returns bytes.
        content = file_obj.read()
        if isinstance(content, bytes):
            text = content.decode("utf-8")
        else:
            text = str(content)
            
        all_docs = chunk_text(
            text,
            source=filename,
            document_id=document_id,
            page_number=None,
        )
        
    else:
        raise ValueError("Unsupported file type. Use PDF, TXT, or MD")
    
    if not all_docs:
        raise ValueError("No chunks produced from document")

    # Store in session's collection
    result = store.add_documents(
        session_id=session_id,
        documents=all_docs,
        document_id=document_id,
        filename=filename,
    )
    
    return result
