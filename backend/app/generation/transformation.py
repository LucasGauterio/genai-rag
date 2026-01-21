from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from llm.factory import get_llm

from .prompts import TRANSFORMATION_PROMPT


from config import LLM_MODEL, LLM_TEMPERATURE
from .structured_output import ConceptList, Flashcard, FlashcardSet


class TransformationChain:
    def __init__(self, model_name: str = None, temperature: float = None):
        self.model = get_llm(
            model_name=LLM_MODEL,
            temperature=temperature,
        )
        
        self.prompt = ChatPromptTemplate.from_template(TRANSFORMATION_PROMPT)
        self.structured_llm = self.model.with_structured_output(Flashcard)
        self.chain = self.prompt | self.structured_llm
    
    def transform(self, concepts: ConceptList) -> FlashcardSet:
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
                print(f"Error transforming concept '{concept.name}': {e}")
                continue
                
        return FlashcardSet(cards=generated_cards)


def transform_to_flashcards(
    concepts: ConceptList,
    model_name: str = None,
) -> FlashcardSet:
    transformer = TransformationChain(model_name=model_name)
    return transformer.transform(concepts)
