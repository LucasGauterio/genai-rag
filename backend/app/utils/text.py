from langchain_experimental.text_splitter import SemanticChunker
from langchain_core.documents import Document
from config import OLLAMA_EMBEDDINGS

def chunk_text(
    text: str,
    *,
    source: str,
    document_id: str,
    page_number: int | None = None,
    embeddings= OLLAMA_EMBEDDINGS,
) -> list[Document]:

    splitter = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=95,
    )

    base_metadata = {
        "document_id": document_id,
        "source": source,
        "page_number": page_number,
    }

    docs = splitter.create_documents([text], metadatas=[base_metadata])

    cursor = 0
    for idx, doc in enumerate(docs):
        chunk_text = doc.page_content

        start = text.find(chunk_text, cursor)
        end = start + len(chunk_text)

        doc.metadata.update({
            "chunk_index": idx,
            "start_offset": start,
            "end_offset": end,
            "citation_id": f"{document_id}:p{page_number}:c{idx}",
        })

        cursor = end

    return docs
