from rag.vector_store import ChromaVectorStore
from rag.bm25 import BM25Retriever
from rag.hybrid_retriever import HybridRetriever

vector_store = ChromaVectorStore()
bm25 = BM25Retriever()

# Seed data (only for initial testing)
# if vector_store.collection.count() == 0:
#     vector_store.add(
#         ids=["1", "2", "3"],
#         texts=[
#             "Flask is a lightweight Python web framework.",
#             "Nuxt is a Vue-based framework used for frontend applications.",
#             "RAG combines retrieval with generation using LLMs.",
#         ],
#     )
hybrid = HybridRetriever(
    vector_store=vector_store,
    bm25=bm25,
    vector_weight=0.5,
    bm25_weight=0.5,
)

def retrieve_context(query: str, k: int = 5) -> str:
    documents = hybrid.retrieve(query, k)
    return "\n".join(documents)
