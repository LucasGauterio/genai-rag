import fitz  # PyMuPDF
import hashlib
import os
from langchain_core.documents import Document

def get_pdf_documents(file_path):
    """
    Extracts text from a PDF file page-by-page and returns LangChain Document objects.
    """
    documents = []
    file_name = os.path.basename(file_path)
    
    # Generate a unique doc_id based on file content (or filename if preferred)
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    
    doc = fitz.open(file_path)
    
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        
        metadata = {
            "source": file_name,
            "page_number": page_num,
            "doc_id": file_hash
        }
        
        documents.append(Document(page_content=text, metadata=metadata))
    
    doc.close()
    return documents
