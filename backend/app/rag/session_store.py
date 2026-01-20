"""
Session-based ChromaDB collection management.

Each chat session gets its own ChromaDB collection.
When the session is closed, the collection is deleted.
"""

import chromadb
from chromadb.config import Settings
from typing import Optional, Dict, List
from datetime import datetime
import uuid

from rag.embedding import embed_text
from rag.bm25 import BM25Retriever
from rag.hybrid_search import hybrid_search


class SessionStore:
    """
    Manages ChromaDB collections per session.
    
    Architecture:
    - Each session = one ChromaDB collection
    - Collection name: "session_{session_id}"
    - Documents are isolated per session
    - Cleanup: delete collection when session closes
    """
    
    def __init__(self):
        self.client = chromadb.Client()
        self._sessions: Dict[str, dict] = {}
    
    # --- Session CRUD ---
    
    def create_session(self) -> dict:
        """Create a new session with its own collection."""
        session_id = str(uuid.uuid4())[:8]
        collection_name = f"session_{session_id}"
        collection = self.client.create_collection(
            name=collection_name,
            metadata={"created_at": datetime.utcnow().isoformat()}
        )
        
        self._sessions[session_id] = {
            "collection": collection,
            "bm25": BM25Retriever(),
            "created_at": datetime.utcnow().isoformat(),
            "documents": [],
        }
        
        return {
            "session_id": session_id,
            "created_at": self._sessions[session_id]["created_at"],
            "collection_name": collection_name,
        }
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session info."""
        if session_id not in self._sessions:
            # if not self._recover_session(session_id):
            return None
        
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "created_at": session["created_at"],
            "documents": session["documents"],
            "chunk_count": session["collection"].count(),
        }
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its collection."""
        try:
            self.client.delete_collection(f"session_{session_id}")
            self._sessions.pop(session_id, None)
            return True
        except Exception:
            return False
    
    def list_sessions(self) -> List[dict]:
        """List all active sessions."""
        collections = self.client.list_collections()
        return [
            {
                "session_id": col.name.replace("session_", ""),
                "collection_name": col.name,
                "chunk_count": col.count(),
                "created_at": col.metadata.get("created_at", "unknown"),
            }
            for col in collections
            if col.name.startswith("session_")
        ]
    
    # --- Document Operations ---
    
    def add_documents(
        self,
        session_id: str,
        documents: List,
        document_id: str,
        filename: str,
    ) -> dict:
        """Add documents (chunks) to a session's collection."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        collection = session["collection"]
        bm25 = session["bm25"]
        # Prepare data
        ids, texts, metadatas = [], [], []
        for doc in documents:
            chunk_id = f"{session_id}_{document_id}_p{doc.metadata.get('page_number', 0)}_c{doc.metadata.get('chunk_index', 0)}"
            ids.append(chunk_id)
            texts.append(doc.page_content)
            metadatas.append({**doc.metadata, "session_id": session_id})
       
        # Store in ChromaDB
        embeddings = [embed_text(t) for t in texts]
        collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        
        # Store in BM25
        bm25.add_documents([
            {"text": t, "metadata": m}
            for t, m in zip(texts, metadatas)
        ])
        
        # Track document
        session["documents"].append({
            "document_id": document_id,
            "filename": filename,
            "chunks": len(documents),
        })
        
        return {
            "document_id": document_id,
            "filename": filename,
            "chunks_ingested": len(documents),
        }
    
    def search(
        self,
        session_id: str,
        query: str,
        k: int = 5,
        document_id: Optional[str] = None,
    ) -> List[dict]:
        """Search within a session using hybrid retrieval."""
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        return hybrid_search(
            collection=session["collection"],
            bm25=session["bm25"],
            query=query,
            k=k,
            document_id=document_id,
        )
    
    # --- Private Helpers ---
    
    # def _recover_session(self, session_id: str) -> bool:
    #     """Try to recover session from persistent storage."""
    #     try:
    #         collection = self.client.get_collection(f"session_{session_id}")
    #         self.client._get_collection(f"session_{session_id}")
    #         self._sessions[session_id] = {
    #             "collection": collection,
    #             "bm25": BM25Retriever(),
    #             "created_at": collection.metadata.get("created_at", "unknown"),
    #             "documents": [],
    #         }
    #         return True
    #     except Exception:
    #         return False


# --- Global Instance ---

_session_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get or create the global session store."""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
