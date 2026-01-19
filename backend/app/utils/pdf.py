"""
PDF text extraction utilities.
"""

import io


def extract_pdf_text(file) -> list[dict]:
    """
    Extract text from a PDF file, preserving page numbers.
    
    Args:
        file: File object (from Flask request.files)
    
    Returns:
        List of dicts: [{ "page_number": int, "text": str }]
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader
    
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
