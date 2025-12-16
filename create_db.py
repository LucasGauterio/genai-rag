# create_database.py
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# 1. Load Environment Variables
load_dotenv()

DATA_PATH = "data/lectures"
CHROMA_PATH = "chroma_db"

def main():
    print("Loading documents...")
    # Initialize loader to read PDFs from the data folder
    loader = DirectoryLoader(DATA_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    
    print(f"Loaded {len(documents)} pages.")

    # 2. Split Text into Chunks
    # We split text because models can't read entire books at once.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=500,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")

    # 3. Create Vector Store (The "Brain")
    # This sends text to Google to get "embeddings" (numbers representing meaning)
    # and saves them to a local folder named 'chroma_db'
    print("Creating database...")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    db = Chroma.from_documents(
        chunks, 
        embedding_function, 
        persist_directory=CHROMA_PATH
    )
    print(f"Saved to {CHROMA_PATH}.")

if __name__ == "__main__":
    main()