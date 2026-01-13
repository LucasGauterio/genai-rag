import argparse
import os
from dotenv import load_dotenv

# Core LangChain
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Google & Embeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

# Advanced Retrieval
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers.contextual_compression import ContextualCompressionRetriever
from langchain_community.document_compressors.flashrank_rerank import FlashrankRerank

# Custom Modules
from generation import get_prompt_template

load_dotenv()

CHROMA_PATH = "chroma_db"

def format_docs(docs):
    return "\n\n".join([f"Source: {doc.metadata.get('source', 'Unknown')}, Page: {doc.metadata.get('page_number', 'Unknown')}\nContent: {doc.page_content}" for doc in docs])

def get_hybrid_retriever(db, doc_ids=None):
    """
    Creates a Hybrid retriever with optional doc_id filtering.
    """
    # 1. Vector (Dense) Retriever
    search_kwargs = {"k": 10}
    if doc_ids:
        if len(doc_ids) == 1:
            search_kwargs["filter"] = {"doc_id": doc_ids[0]}
        else:
            search_kwargs["filter"] = {"doc_id": {"$in": doc_ids}}
    
    vector_retriever = db.as_retriever(search_kwargs=search_kwargs)

    # 2. BM25 (Sparse) Retriever
    all_docs = db.get()
    
    docs_for_bm25 = []
    for i in range(len(all_docs['ids'])):
        metadata = all_docs['metadatas'][i]
        content = all_docs['documents'][i]
        from langchain_core.documents import Document
        if not doc_ids or metadata['doc_id'] in doc_ids:
            docs_for_bm25.append(Document(page_content=content, metadata=metadata))
    
    if not docs_for_bm25:
        return vector_retriever
        
    bm25_retriever = BM25Retriever.from_documents(docs_for_bm25)
    bm25_retriever.k = 10

    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5]
    )
    return ensemble_retriever

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The question text.")
    parser.add_argument("--mode", type=str, choices=["summary", "story", "flashcards"], default="summary", help="Generation mode.")
    parser.add_argument("--doc_ids", type=str, nargs="*", help="Optional doc_ids to filter by.")
    args = parser.parse_args()
    
    # Setup Vector DB
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # 1. Create Hybrid Retriever with Scope Control
    print(f"Initializing Hybrid Retriever (Mode: {args.mode}, Scope: {args.doc_ids if args.doc_ids else 'Full Content'})...")
    hybrid_retriever = get_hybrid_retriever(db, doc_ids=args.doc_ids)

    # 2. Add Re-Ranking
    print("Initializing Re-ranker...")
    try:
        compressor = FlashrankRerank(model="ms-marco-MiniLM-L-12-v2")
    except Exception as e:
        print(f"Warning: Flashrank failed to initialize ({e}). Falling back to no re-ranking.")
        compressor = None
    if compressor:
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, 
            base_retriever=hybrid_retriever
        )
    else:
        compression_retriever = hybrid_retriever

    # 3. Generation with Master Prompts
    model = ChatGoogleGenerativeAI(model="gemini-flash-latest")
    prompt_template = get_prompt_template(args.mode)

    chain = (
        {"context": compression_retriever | format_docs, "question": RunnablePassthrough()}
        | prompt_template
        | model
        | StrOutputParser()
    )

    print(f"\nProcessing Query: '{args.query_text}'")
    response = chain.invoke(args.query_text)
    
    print("\n--- Answer ---")
    print(response)

if __name__ == "__main__":
    main()