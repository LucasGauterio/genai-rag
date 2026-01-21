from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from config import VALID_TAGS
import re
import json


# =============================================================================
# PYDANTIC MODELS FOR STRICT VALIDATION
# =============================================================================

class Concept(BaseModel):
    name: str = Field(..., description="Name or title of the concept")
    type: Literal["definition", "principle", "relationship", "procedure", "example"] = Field(
        ..., description="Type of the concept"
    )
    description: str = Field(..., description="Clear, accurate explanation from the source")
    related_to: List[str] = Field(default_factory=list, description="List of related concepts")
    source_quote: str = Field(..., description="Exact quote from context supporting this extraction")
    difficulty: Literal["basic", "intermediate", "advanced"] = Field(..., description="Difficulty level")


class ConceptList(BaseModel):
    concepts: List[Concept] = Field(..., description="List of extracted concepts")


class Flashcard(BaseModel):
    question: str = Field(..., min_length=10, description="The question text")
    answer: str = Field(..., min_length=10, description="The answer text")
    citation: Optional[str] = Field(None, description="Source citation marker e.g. [1]")
    tag: Literal["definition", "concept", "procedure", "comparison", "application"] = Field(
        ..., description="Category tag for the flashcard"
    )
    
    @field_validator('question', 'answer')
    @classmethod
    def clean_text(cls, v: str) -> str:
        v = ' '.join(v.split())
        v = re.sub(r'\*\*([^*]+)\*\*', r'\1', v)
        v = re.sub(r'\*([^*]+)\*', r'\1', v) 
        return v.strip()


class FlashcardSet(BaseModel):
    cards: List[Flashcard] = Field(..., min_length=1, description="List of flashcards")
    
    def to_dict(self) -> dict:
        return {"cards": [card.model_dump() for card in self.cards]}
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

