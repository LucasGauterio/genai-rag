from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from llm.factory import get_llm

from .prompts import EXTRACTION_PROMPT
from .structured_output import ConceptList


from config import LLM_MODEL, LLM_TEMPERATURE


class ExtractorChain:
    def __init__(self, model_name: str = None, temperature: float = None):
        self.model = get_llm(
            model_name=LLM_MODEL,
            temperature=temperature,
        )
        
        self.prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT)
        self.structured_llm = self.model.with_structured_output(ConceptList)
        self.chain = self.prompt | self.structured_llm
    
    def extract(self, context: str) -> ConceptList:
        return self.chain.invoke({"context": context})
    
    def extract_from_documents(self, documents: List[Document]) -> ConceptList:
        
        context = self._format_documents(documents)
        return self.extract(context)
    
    def _format_documents(self, documents: List[Document]) -> str:
        formatted = []
        for i, doc in enumerate(documents, start=1):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page_number', 'N/A')
            section = doc.metadata.get('section_h1', 'N/A')
            
            formatted.append(
                f"[Source {i}: {source} | Page: {page} | Section: {section}]\n"
                f"{doc.page_content}"
            )
        
        return "\n\n---\n\n".join(formatted)


def extract_concepts(
    documents: List[Document],
    model_name: str = None,
) -> ConceptList:
    
    extractor = ExtractorChain(model_name=model_name)
    return extractor.extract_from_documents(documents)
