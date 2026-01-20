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
from .structured_output import ConceptList, Flashcard, FlashcardSet


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
        # Structured output for single flashcard
        self.structured_llm = self.model.with_structured_output(Flashcard)
        self.chain = self.prompt | self.structured_llm
    
    def transform(self, concepts: ConceptList) -> FlashcardSet:
        """
        Transform extracted concepts into a FlashcardSet.
        
        loops through each concept in Python to guarantee 1-to-1 generation.
        
        Args:
            concepts: List of extracted concepts
            
        Returns:
            FlashcardSet with generated cards
        """
        generated_cards = []
        
        for concept in concepts.concepts:
            try:
                card = self.chain.invoke({
                    "concept_name": concept.name,
                    "concept_type": concept.type,
                    "concept_description": concept.description,
                    "concept_quote": concept.source_quote
                })
                generated_cards.append(card)
            except Exception as e:
                # Log error but continue with other concepts
                print(f"Error transforming concept '{concept.name}': {e}")
                continue
                
        return FlashcardSet(cards=generated_cards)


def transform_to_flashcards(
    concepts: ConceptList,
    model_name: str = None,
) -> FlashcardSet:
    """
    Convenience function to transform concepts to flashcards.
    
    Args:
        concepts: Extracted concept list
        model_name: Optional model override
        
    Returns:
        FlashcardSet object
    """
    transformer = TransformationChain(model_name=model_name)
    return transformer.transform(concepts)
