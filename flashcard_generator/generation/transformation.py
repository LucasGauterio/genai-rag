"""
Transformation Chain - Step 2 of the generation flow.

Converts extracted concepts into flashcard Q&A pairs.
Applies pedagogical best practices for question design.
"""

from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from .prompts import TRANSFORMATION_PROMPT

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import LLM_MODEL, LLM_TEMPERATURE


class TransformationChain:
    """
    Concept-to-flashcard transformation chain.
    
    Takes extracted concepts and generates Q&A pairs
    following flashcard design best practices.
    """
    
    def __init__(self, model_name: str = None, temperature: float = None):
        """
        Initialize the transformer.
        
        Args:
            model_name: LLM model to use
            temperature: Generation temperature
        """
        self.model = ChatGoogleGenerativeAI(
            model=model_name or LLM_MODEL,
            temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        )
        
        self.prompt = ChatPromptTemplate.from_template(TRANSFORMATION_PROMPT)
        self.chain = self.prompt | self.model | StrOutputParser()
    
    def transform(self, extracted_concepts: str) -> str:
        """
        Transform extracted concepts into flashcard JSON.
        
        Args:
            extracted_concepts: Output from extraction step
            
        Returns:
            JSON string with flashcard data
        """
        return self.chain.invoke({"extracted_concepts": extracted_concepts})


def transform_to_flashcards(
    extracted_concepts: str,
    model_name: str = None,
) -> str:
    """
    Convenience function to transform concepts to flashcards.
    
    Args:
        extracted_concepts: Extracted concept text
        model_name: Optional model override
        
    Returns:
        JSON string with flashcard data
    """
    transformer = TransformationChain(model_name=model_name)
    return transformer.transform(extracted_concepts)
