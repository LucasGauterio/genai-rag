import argparse
import os
from dotenv import load_dotenv

# Core LangChain
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
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

# Document Loading (Needed for BM25)
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

CHROMA_PATH = "chroma_db"
DATA_PATH = "data/lectures"

def get_hybrid_retriever(db_vector_retriever):
    """
    Creates a 'Hybrid' retriever that combines:
    1. Semantic Search (Chroma) - Finds meaning (e.g., "fast car" matches "speedy vehicle")
    2. Keyword Search (BM25) - Finds exact words (e.g., "Id: 123" matches "Id: 123")
    """
    print("Initializing BM25 (Keyword) Retriever...")
    
    # We need to re-load chunks for BM25 because it runs in-memory
    # (In large production, you'd use a DB like Elasticsearch, but this works for small projects)
    loader = DirectoryLoader(DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    raw_docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=500)
    chunks = text_splitter.split_documents(raw_docs)
    
    bm25_retriever = BM25Retriever.from_documents(chunks)
    bm25_retriever.k = 10  # Get top 10 keyword matches

    # Combine them! (50% Vector, 50% Keyword)
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, db_vector_retriever],
        weights=[0.5, 0.5]
    )
    return ensemble_retriever

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The question text.")
    args = parser.parse_args()
    query_text = args.query_text

    # 1. Setup Vector DB (Same as before)
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    # Get the basic vector retriever
    vector_retriever = db.as_retriever(search_kwargs={"k": 10})

    # 2. UPGRADE: Create Hybrid Retriever
    # This combines keyword search + vector search
    hybrid_retriever = get_hybrid_retriever(vector_retriever)

    # 3. UPGRADE: Add Re-Ranking
    # This takes the top 10/20 results from the Hybrid search and strictly filters them.
    print("Re-ranking results...")
    compressor = FlashrankRerank()
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor, 
        base_retriever=hybrid_retriever
    )

    # 4. Define the Chat Chain
    # Using Gemini 1.5 Flash
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    
    prompt_template = ChatPromptTemplate.from_template("""
    Answer the question based ONLY on the following context:
    {context}
    
    Question: {question}
    """)

    # 5. Build the Pipeline (The "Chain")
    chain = (
        {"context": compression_retriever, "question": RunnablePassthrough()}
        | prompt_template
        | model
        | StrOutputParser()
    )

    # 6. Run it
    print(f"\nProcessing Query: '{query_text}'")
    response = chain.invoke(query_text)
    
    print("\n--- Answer ---")
    print(response)

if __name__ == "__main__":
    main()