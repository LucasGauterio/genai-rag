"""
Vector Store - ChromaDB management for document embeddings.

Handles:
- Creating and persisting the vector store
- Adding documents with metadata
- Similarity search operations
"""

from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from langchain_chroma import Chroma

from .embeddings import get_embedding_function

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import CHROMA_PATH


class VectorStore:
    """ChromaDB vector store wrapper for flashcard generation."""
    
    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = "flashcard_docs",
    ):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the Chroma collection
        """
        self.persist_directory = persist_directory or str(CHROMA_PATH)
        self.collection_name = collection_name
        self.embedding_function = get_embedding_function()
        self._db = None
    
    @property
    def db(self) -> Chroma:
        """Lazy-load the database connection."""
        if self._db is None:
            self._db = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function,
                collection_name=self.collection_name,
            )
        return self._db
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        return self.db.add_documents(documents)
    
    def create_from_documents(
        self,
        documents: List[Document],
        clear_existing: bool = True,
    ) -> "VectorStore":
        """
        Create a new vector store from documents.
        
        Args:
            documents: Documents to index
            clear_existing: Whether to clear existing data
            
        Returns:
            Self for chaining
        """
        if clear_existing:
            self.clear()
        
        # Create new database from documents
        self._db = Chroma.from_documents(
            documents=documents,
            embedding=self.embedding_function,
            persist_directory=self.persist_directory,
            collection_name=self.collection_name,
        )
        
        return self
    
    def clear(self):
        """Clear all documents from the vector store."""
        import shutil
        persist_path = Path(self.persist_directory)
        if persist_path.exists():
            shutil.rmtree(persist_path)
        self._db = None
    
    def similarity_search(
        self,
        query: str,
        k: int = 10,
        filter_dict: Optional[dict] = None,
    ) -> List[Document]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of matching documents
        """
        search_kwargs = {"k": k}
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        
        return self.db.similarity_search(query, **search_kwargs)
    
    def as_retriever(self, k: int = 10, filter_dict: Optional[dict] = None):
        """
        Get as a LangChain retriever.
        
        Args:
            k: Number of results
            filter_dict: Optional metadata filter
            
        Returns:
            Retriever instance
        """
        search_kwargs = {"k": k}
        if filter_dict:
            search_kwargs["filter"] = filter_dict
        
        return self.db.as_retriever(search_kwargs=search_kwargs)
    
    def get_all_documents(self) -> List[Document]:
        """
        Retrieve all documents from the store.
        
        Returns:
            List of all stored documents
        """
        collection = self.db.get()
        
        documents = []
        for i in range(len(collection['ids'])):
            doc = Document(
                page_content=collection['documents'][i],
                metadata=collection['metadatas'][i]
            )
            documents.append(doc)
        
        return documents
    
    @property
    def count(self) -> int:
        """Return the number of documents in the store."""
        try:
            return len(self.db.get()['ids'])
        except Exception:
            return 0
