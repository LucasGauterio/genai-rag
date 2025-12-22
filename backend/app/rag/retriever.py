from rag.vector_store import ChromaVectorStore

vector_store = ChromaVectorStore()

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


def retrieve_context(query: str, k: int = 3) -> str:
    documents = vector_store.similarity_search(query, k)
    return "\n".join(documents)
