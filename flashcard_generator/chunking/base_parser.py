"""
Base Parser - Abstract base class for all document parsers.

All parsers must implement the parse() method which returns
LangChain Document objects with proper metadata.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from langchain_core.documents import Document


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    def __init__(self, file_path: str | Path):
        """
        Initialize parser with file path.
        
        Args:
            file_path: Path to the document file
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
    
    @abstractmethod
    def parse(self) -> List[Document]:
        """
        Parse the document and return list of Document objects.
        
        Each Document should have:
        - page_content: The text content
        - metadata: Dict with 'source', 'doc_id', and format-specific fields
        
        Returns:
            List of LangChain Document objects
        """
        pass
    
    def _generate_doc_id(self) -> str:
        """Generate a unique document ID based on file content hash."""
        import hashlib
        with open(self.file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    
    @property
    def filename(self) -> str:
        """Return the filename without path."""
        return self.file_path.name
    
    @staticmethod
    def supported_extensions() -> List[str]:
        """Return list of supported file extensions."""
        return []
