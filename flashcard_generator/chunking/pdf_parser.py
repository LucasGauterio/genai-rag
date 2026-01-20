"""
PDF Parser - Structure-aware PDF parsing with header detection.

Uses PyMuPDF (fitz) to extract text with structural awareness:
- Detects headers based on font size
- Preserves section hierarchy
- Maintains page boundaries
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.documents import Document

from .base_parser import BaseParser


class PDFParser(BaseParser):
    """Structure-aware PDF parser using PyMuPDF."""
    
    # Font size thresholds for header detection
    H1_MIN_SIZE = 16
    H2_MIN_SIZE = 14
    H3_MIN_SIZE = 12
    
    def __init__(self, file_path: str | Path):
        super().__init__(file_path)
        self.doc_id = self._generate_doc_id()
    
    def parse(self) -> List[Document]:
        """
        Parse PDF with structure awareness.
        
        Extracts text page by page, detecting headers based on font size
        and preserving section context in metadata.
        
        Returns:
            List of Document objects, one per page with section context
        """
        documents = []
        doc = fitz.open(self.file_path)
        
        current_section = {
            "h1": None,
            "h2": None,
            "h3": None,
        }
        
        try:
            for page_num, page in enumerate(doc, start=1):
                # Extract text with block information for structure analysis
                blocks = page.get_text("dict")["blocks"]
                page_text = []
                
                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        block_text = self._process_text_block(block, current_section)
                        if block_text:
                            page_text.append(block_text)
                
                full_text = "\n".join(page_text)
                
                if full_text.strip():
                    metadata = {
                        "source": self.filename,
                        "doc_id": self.doc_id,
                        "page_number": page_num,
                        "total_pages": len(doc),
                        "section_h1": current_section["h1"],
                        "section_h2": current_section["h2"],
                        "section_h3": current_section["h3"],
                        "file_type": "pdf",
                    }
                    
                    documents.append(Document(
                        page_content=full_text,
                        metadata=metadata
                    ))
        finally:
            doc.close()
        
        return documents
    
    def _process_text_block(
        self, 
        block: Dict[str, Any], 
        current_section: Dict[str, str]
    ) -> str:
        """
        Process a text block and update section headers if detected.
        
        Args:
            block: PyMuPDF text block dictionary
            current_section: Current section hierarchy (modified in place)
            
        Returns:
            Processed text from the block
        """
        lines_text = []
        
        for line in block.get("lines", []):
            line_text = ""
            max_font_size = 0
            
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                font_size = span.get("size", 0)
                
                if text:
                    line_text += text + " "
                    max_font_size = max(max_font_size, font_size)
            
            line_text = line_text.strip()
            
            if line_text:
                # Detect headers based on font size and update section context
                if max_font_size >= self.H1_MIN_SIZE:
                    current_section["h1"] = line_text
                    current_section["h2"] = None
                    current_section["h3"] = None
                    lines_text.append(f"\n# {line_text}\n")
                elif max_font_size >= self.H2_MIN_SIZE:
                    current_section["h2"] = line_text
                    current_section["h3"] = None
                    lines_text.append(f"\n## {line_text}\n")
                elif max_font_size >= self.H3_MIN_SIZE:
                    current_section["h3"] = line_text
                    lines_text.append(f"\n### {line_text}\n")
                else:
                    lines_text.append(line_text)
        
        return " ".join(lines_text)
    
    @staticmethod
    def supported_extensions() -> List[str]:
        return [".pdf"]
