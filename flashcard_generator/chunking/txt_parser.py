"""
TXT Parser - Plain text parsing with semantic boundary detection.

Parses text files by detecting:
- Paragraph boundaries (double newlines)
- Sentence boundaries for smaller chunks
- Potential section breaks (lines with all caps, numbering)
"""

import re
from pathlib import Path
from typing import List
from langchain_core.documents import Document

from .base_parser import BaseParser


class TxtParser(BaseParser):
    """Plain text parser with semantic boundary detection."""
    
    # Patterns for detecting structure in plain text
    SECTION_HEADER_PATTERN = re.compile(
        r'^(?:'
        r'[A-Z][A-Z\s]{2,}$|'  # ALL CAPS lines
        r'\d+\.\s+[A-Z]|'      # Numbered sections (1. Title)
        r'[IVXLCDM]+\.\s+|'    # Roman numerals (I. II. III.)
        r'Chapter\s+\d+|'      # Chapter headers
        r'Section\s+\d+'       # Section headers
        r')',
        re.MULTILINE
    )
    
    def __init__(self, file_path: str | Path):
        super().__init__(file_path)
        self.doc_id = self._generate_doc_id()
    
    def parse(self) -> List[Document]:
        """
        Parse plain text with semantic boundary detection.
        
        Splits by paragraphs and detects section headers
        to provide structure context.
        
        Returns:
            List of Document objects, one per semantic section
        """
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', content)
        
        documents = []
        current_section = None
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            
            # Check if this paragraph looks like a section header
            if self._is_section_header(para):
                current_section = para
            
            metadata = {
                "source": self.filename,
                "doc_id": self.doc_id,
                "paragraph_index": i,
                "section": current_section,
                "file_type": "txt",
            }
            
            documents.append(Document(
                page_content=para,
                metadata=metadata
            ))
        
        return documents
    
    def _is_section_header(self, text: str) -> bool:
        """
        Detect if text appears to be a section header.
        
        Args:
            text: Text to check
            
        Returns:
            True if text appears to be a header
        """
        # Short lines that match header patterns
        if len(text) < 100 and self.SECTION_HEADER_PATTERN.match(text):
            return True
        
        # ALL CAPS short lines
        if len(text) < 60 and text.isupper():
            return True
        
        return False
    
    @staticmethod
    def supported_extensions() -> List[str]:
        return [".txt", ".text"]
