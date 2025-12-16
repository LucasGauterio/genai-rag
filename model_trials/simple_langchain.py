from langchain_community.document_loaders import DirectoryLoader

DATA_PATH = "data/books"

def load_documents():
    loader = DirectoryLoader(
        DATA_PATH,
        glob="*.md",
    )
    documents = loader.load() 
    return documents

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    add_start_index=True,
)
