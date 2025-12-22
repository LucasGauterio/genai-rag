import chromadb
from chromadb.config import Settings
from rag.embedding import embed_text


class ChromaVectorStore:
    def __init__(self, path: str = "./chroma"):
        self.client = chromadb.Client(
            Settings(
                persist_directory=path,
                anonymized_telemetry=False,
            )
        )

        # Create or get collection; do NOT pass embedding_function
        self.collection = self.client.get_or_create_collection(
            name="documents"
        )

    def add(self, ids: list[str], texts: list[str], metadatas: list[dict] | None = None):
        """
        Precompute embeddings and store them in Chroma.
        """
        embeddings = [embed_text(t) for t in texts]  # Ensure all are same dimension
        self.collection.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def similarity_search(self, query: str, k: int = 3) -> list[str]:
        """
        Embed the query and use it for vector search.
        """
        query_embedding = embed_text(query)

        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )

        return result["documents"][0]
