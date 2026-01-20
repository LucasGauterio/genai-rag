"""
Markdown Parser - Native structure-aware Markdown parsing.

Parses Markdown files preserving:
- Header hierarchy (H1-H6)
- Code blocks with language
- Lists and tables
- Section context for each chunk
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from langchain_core.documents import Document

from .base_parser import BaseParser


class MarkdownParser(BaseParser):
    """Structure-aware Markdown parser."""
    
    # Regex patterns for Markdown elements
    HEADER_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
    
    def __init__(self, file_path: str | Path):
        super().__init__(file_path)
        self.doc_id = self._generate_doc_id()
    
    def parse(self) -> List[Document]:
        """
        Parse Markdown with structure awareness.
        
        Splits content by headers, preserving section hierarchy
        and maintaining context in metadata.
        
        Returns:
            List of Document objects, one per section
        """
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into sections based on headers
        sections = self._split_by_headers(content)
        
        documents = []
        for section in sections:
            if section["content"].strip():
                metadata = {
                    "source": self.filename,
                    "doc_id": self.doc_id,
                    "section_h1": section.get("h1"),
                    "section_h2": section.get("h2"),
                    "section_h3": section.get("h3"),
                    "section_level": section.get("level", 0),
                    "has_code": section.get("has_code", False),
                    "file_type": "markdown",
                }
                
                documents.append(Document(
                    page_content=section["content"],
                    metadata=metadata
                ))
        
        return documents
    
    def _split_by_headers(self, content: str) -> List[Dict]:
        """
        Split content into sections based on Markdown headers.
        
        Args:
            content: Full Markdown content
            
        Returns:
            List of section dictionaries with content and hierarchy
        """
        sections = []
        current_section = {
            "content": "",
            "h1": None,
            "h2": None,
            "h3": None,
            "level": 0,
            "has_code": False,
        }
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check for code block (preserve as-is)
            if line.startswith('```'):
                code_block = [line]
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_block.append(lines[i])
                    i += 1
                if i < len(lines):
                    code_block.append(lines[i])
                current_section["content"] += '\n'.join(code_block) + '\n'
                current_section["has_code"] = True
                i += 1
                continue
            
            # Check for header
            header_match = self.HEADER_PATTERN.match(line)
            if header_match:
                # Save current section if it has content
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                
                level = len(header_match.group(1))
                header_text = header_match.group(2)
                
                # Update hierarchy based on level
                current_section = {
                    "content": line + '\n',
                    "h1": current_section["h1"] if level > 1 else header_text,
                    "h2": current_section["h2"] if level > 2 else (header_text if level == 2 else None),
                    "h3": header_text if level == 3 else None,
                    "level": level,
                    "has_code": False,
                }
                
                if level == 1:
                    current_section["h1"] = header_text
                    current_section["h2"] = None
                    current_section["h3"] = None
                elif level == 2:
                    current_section["h2"] = header_text
                    current_section["h3"] = None
                elif level == 3:
                    current_section["h3"] = header_text
            else:
                current_section["content"] += line + '\n'
            
            i += 1
        
        # Don't forget the last section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    @staticmethod
    def supported_extensions() -> List[str]:
        return [".md", ".markdown"]
