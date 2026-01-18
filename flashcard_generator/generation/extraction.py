"""
Extraction Chain - Step 1 of the generation flow.

Analyzes retrieved context and extracts structured knowledge:
- Key concepts and definitions
- Relationships between ideas
- Procedures and examples
"""

from typing import List
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from .prompts import EXTRACTION_PROMPT

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import LLM_MODEL, LLM_TEMPERATURE


class ExtractorChain:
    """
    Concept extraction chain.
    
    Takes retrieved documents and extracts structured knowledge
    that can be transformed into flashcards.
    """
    
    def __init__(self, model_name: str = None, temperature: float = None):
        """
        Initialize the extractor.
        
        Args:
            model_name: LLM model to use
            temperature: Generation temperature
        """
        self.model = ChatGoogleGenerativeAI(
            model=model_name or LLM_MODEL,
            temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        )
        
        self.prompt = ChatPromptTemplate.from_template(EXTRACTION_PROMPT)
        self.chain = self.prompt | self.model | StrOutputParser()
    
    def extract(self, context: str) -> str:
        """
        Extract concepts from context.
        
        Args:
            context: Formatted context string from retrieval
            
        Returns:
            Structured extraction output
        """
        return self.chain.invoke({"context": context})
    
    def extract_from_documents(self, documents: List[Document]) -> str:
        """
        Extract concepts from a list of documents.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Structured extraction output
        """
        # Format documents into context
        context = self._format_documents(documents)
        return self.extract(context)
    
    def _format_documents(self, documents: List[Document]) -> str:
        """Format documents for the extraction prompt."""
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
) -> str:
    """
    Convenience function to extract concepts from documents.
    
    Args:
        documents: List of retrieved documents
        model_name: Optional model override
        
    Returns:
        Extracted concepts as structured text
    """
    extractor = ExtractorChain(model_name=model_name)
    return extractor.extract_from_documents(documents)
