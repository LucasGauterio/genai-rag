from rag.vector_store import ChromaVectorStore
from rag.bm25 import BM25Retriever


class HybridRetriever:
    def __init__(
        self,
        vector_store: ChromaVectorStore,
        bm25: BM25Retriever,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
    ):
        self.vector_store = vector_store
        self.bm25 = bm25
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

    def retrieve(
        self,
        query: str,
        k: int = 5,
        metadata_filter: dict | None = None,
    ) -> list[str]:
        vector_docs = self.vector_store.similarity_search(
            query,
            k,
            metadata_filter=metadata_filter,
        )

        bm25_docs = self.bm25.search(
            query,
            k,
            metadata_filter=metadata_filter,
        )

        scores = {}

        for i, doc in enumerate(vector_docs):
            scores[doc["text"]] = scores.get(doc["text"], 0) + self.vector_weight * (k - i)

        for i, doc in enumerate(bm25_docs):
            scores[doc["text"]] = scores.get(doc["text"], 0) + self.bm25_weight * (k - i)

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        print(ranked)
        return [text for text, _ in ranked[:k]]
