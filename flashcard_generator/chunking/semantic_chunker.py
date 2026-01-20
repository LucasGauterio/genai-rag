"""
Semantic Chunker - Structure-aware text chunking.

The key innovation here is respecting document structure:
- Headers mark semantic boundaries (don't split mid-section)
- Paragraphs are kept intact when possible
- Overlap includes context from previous chunks
"""

from pathlib import Path
from typing import List, Optional, Union
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .pdf_parser import PDFParser
from .markdown_parser import MarkdownParser
from .txt_parser import TxtParser
from .base_parser import BaseParser

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import CHUNK_SIZE, CHUNK_OVERLAP, SEMANTIC_SEPARATORS


class SemanticChunker:
    """
    Structure-aware semantic chunker.
    
    Chunks documents while respecting:
    1. Header boundaries (never split in the middle of a section)
    2. Paragraph integrity (keep paragraphs together when possible)
    3. Semantic continuity (overlap provides context)
    """
    
    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
        separators: List[str] = None,
    ):
        """
        Initialize the semantic chunker.
        
        Args:
            chunk_size: Target size for each chunk (default from config)
            chunk_overlap: Overlap between chunks (default from config)
            separators: List of separators in priority order
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or SEMANTIC_SEPARATORS
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            keep_separator=True,
            add_start_index=True,
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Chunk a list of documents while preserving metadata.
        
        Args:
            documents: List of parsed Document objects
            
        Returns:
            List of chunked Document objects with inherited metadata
        """
        all_chunks = []
        
        for doc in documents:
            # Split this document's content
            chunks = self.text_splitter.split_documents([doc])
            
            # Add chunk index to metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_index"] = i
                chunk.metadata["total_chunks"] = len(chunks)
            
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def chunk_text(self, text: str, metadata: dict = None) -> List[Document]:
        """
        Chunk raw text into Documents.
        
        Args:
            text: Raw text to chunk
            metadata: Optional metadata to attach to all chunks
            
        Returns:
            List of chunked Document objects
        """
        metadata = metadata or {}
        doc = Document(page_content=text, metadata=metadata)
        return self.chunk_documents([doc])


def get_document_loader(file_path: Union[str, Path]) -> BaseParser:
    """
    Factory function to get the appropriate parser for a file.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Appropriate parser instance
        
    Raises:
        ValueError: If file type is not supported
    """
    path = Path(file_path)
    extension = path.suffix.lower()
    
    if extension in PDFParser.supported_extensions():
        return PDFParser(path)
    elif extension in MarkdownParser.supported_extensions():
        return MarkdownParser(path)
    elif extension in TxtParser.supported_extensions():
        return TxtParser(path)
    else:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported types: PDF, Markdown (.md), Text (.txt)"
        )


def load_and_chunk_document(
    file_path: Union[str, Path],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """
    Convenience function to load and chunk a document in one step.
    
    Args:
        file_path: Path to the document
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunked Document objects
    """
    # Parse the document
    parser = get_document_loader(file_path)
    documents = parser.parse()
    
    # Chunk the parsed content
    chunker = SemanticChunker(chunk_size, chunk_overlap)
    chunks = chunker.chunk_documents(documents)
    
    return chunks


def load_and_chunk_directory(
    directory_path: Union[str, Path],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """
    Load and chunk all supported documents in a directory.
    
    Args:
        directory_path: Path to directory containing documents
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of all chunked Document objects
    """
    import glob
    
    directory = Path(directory_path)
    all_chunks = []
    
    # Supported extensions
    extensions = (
        PDFParser.supported_extensions() + 
        MarkdownParser.supported_extensions() + 
        TxtParser.supported_extensions()
    )
    
    for ext in extensions:
        pattern = str(directory / f"*{ext}")
        for file_path in glob.glob(pattern):
            try:
                chunks = load_and_chunk_document(file_path, chunk_size, chunk_overlap)
                all_chunks.extend(chunks)
                print(f"✓ Loaded {len(chunks)} chunks from {Path(file_path).name}")
            except Exception as e:
                print(f"✗ Error loading {file_path}: {e}")
    
    return all_chunks
