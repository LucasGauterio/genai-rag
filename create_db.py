# create_database.py
import os
import glob
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from custom_parser import get_pdf_documents

# 1. Load Environment Variables
load_dotenv()

DATA_PATH = "data/lectures"
CHROMA_PATH = "chroma_db"

def main():
    print("Loading documents using structure-aware parser...")
    
    # Load PDFs using custom parser
    all_documents = []
    pdf_files = glob.glob(os.path.join(DATA_PATH, "*.pdf"))
    
    for pdf_file in pdf_files:
        docs = get_pdf_documents(pdf_file)
        all_documents.extend(docs)
    
    print(f"Loaded {len(all_documents)} pages from {len(pdf_files)} files.")

    # 2. Split Text into Chunks within Boundaries
    # Parameters: chunk_size=500, chunk_overlap=50
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        add_start_index=True,
    )
    
    chunks = []
    for doc in all_documents:
        # Split each page individually to ensure it stays within boundaries
        page_chunks = text_splitter.split_documents([doc])
        # Each page_chunk already inherits metadata from 'doc'
        chunks.extend(page_chunks)
        
    print(f"Split into {len(chunks)} chunks.")

    # 3. Create Vector Store
    print("Creating/Updating database...")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Empty existing DB if needed or just add to it. 
    # For this implementation, we'll recreate it for clean testing if CHROMA_PATH exists
    if os.path.exists(CHROMA_PATH):
        print(f"Clearing existing database at {CHROMA_PATH}...")
        import shutil
        shutil.rmtree(CHROMA_PATH)

    db = Chroma.from_documents(
        chunks, 
        embedding_function, 
        persist_directory=CHROMA_PATH
    )
    print(f"Saved to {CHROMA_PATH}.")

if __name__ == "__main__":
    main()