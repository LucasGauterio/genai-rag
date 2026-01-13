from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

CHROMA_PATH = "chroma_db"

def inspect_db():
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    
    all_docs = db.get()
    unique_docs = {}
    
    for metadata in all_docs['metadatas']:
        doc_id = metadata['doc_id']
        source = metadata['source']
        if doc_id not in unique_docs:
            unique_docs[doc_id] = source
            
    print("Available Documents in Vector Store:")
    for doc_id, source in unique_docs.items():
        print(f"ID: {doc_id} | Source: {source}")

if __name__ == "__main__":
    inspect_db()
