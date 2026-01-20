"""
Structured Output - Step 3 of the generation flow.

Enforces strict JSON schema compliance using Pydantic models.
Handles validation, cleaning, and error correction.
"""

import json
import re
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from .prompts import STRUCTURED_OUTPUT_PROMPT

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import LLM_MODEL, LLM_TEMPERATURE, VALID_TAGS


# =============================================================================
# PYDANTIC MODELS FOR STRICT VALIDATION
# =============================================================================

class Concept(BaseModel):
    """Extracted knowledge concept."""
    name: str = Field(..., description="Name or title of the concept")
    type: Literal["definition", "principle", "relationship", "procedure", "example"] = Field(
        ..., description="Type of the concept"
    )
    description: str = Field(..., description="Clear, accurate explanation from the source")
    related_to: List[str] = Field(default_factory=list, description="List of related concepts")
    source_quote: str = Field(..., description="Exact quote from context supporting this extraction")
    difficulty: Literal["basic", "intermediate", "advanced"] = Field(..., description="Difficulty level")


class ConceptList(BaseModel):
    """List of extracted concepts."""
    concepts: List[Concept] = Field(..., description="List of extracted concepts")


class Flashcard(BaseModel):
    """Single flashcard with validation."""
    
    question: str = Field(..., min_length=10, description="The question text")
    answer: str = Field(..., min_length=10, description="The answer text")
    tag: Literal["definition", "concept", "procedure", "comparison", "application"] = Field(
        ..., description="Category tag for the flashcard"
    )
    
    @field_validator('question', 'answer')
    @classmethod
    def clean_text(cls, v: str) -> str:
        """Clean and normalize text fields."""
        # Remove excessive whitespace
        v = ' '.join(v.split())
        # Remove markdown formatting that might have leaked through
        v = re.sub(r'\*\*([^*]+)\*\*', r'\1', v)  # Bold
        v = re.sub(r'\*([^*]+)\*', r'\1', v)      # Italic
        return v.strip()


class FlashcardSet(BaseModel):
    """Collection of flashcards with validation."""
    
    cards: List[Flashcard] = Field(..., min_length=1, description="List of flashcards")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"cards": [card.model_dump() for card in self.cards]}
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


# =============================================================================
# VALIDATION AND CLEANING
# =============================================================================

def extract_json_from_text(text: str) -> str:
    """
    Extract JSON from text that may contain markdown or other content.
    
    Args:
        text: Raw text that may contain JSON
        
    Returns:
        Extracted JSON string
    """
    # Try to find JSON in code blocks
    code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1)
    
    # Try to find raw JSON object
    json_match = re.search(r'\{[^{}]*"cards"[^{}]*\[.*?\]\s*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    # Last resort: find anything that looks like JSON
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        return brace_match.group(0)
    
    return text


def validate_flashcards(raw_output: str, use_llm_fix: bool = True) -> FlashcardSet:
    """
    Validate and parse flashcard output, attempting repairs if needed.
    
    Args:
        raw_output: Raw JSON string from transformation step
        use_llm_fix: Whether to use LLM to fix invalid JSON
        
    Returns:
        Validated FlashcardSet
        
    Raises:
        ValueError: If validation fails after all attempts
    """
    # Step 1: Extract JSON from potential wrapper text
    json_str = extract_json_from_text(raw_output)
    
    # Step 2: Try direct parsing
    try:
        data = json.loads(json_str)
        return FlashcardSet(**data)
    except (json.JSONDecodeError, Exception) as e:
        if not use_llm_fix:
            raise ValueError(f"JSON parsing failed: {e}")
    
    # Step 3: Use LLM to fix the JSON
    fixed_json = fix_json_with_llm(raw_output)
    
    try:
        data = json.loads(extract_json_from_text(fixed_json))
        return FlashcardSet(**data)
    except Exception as e:
        raise ValueError(f"Validation failed after LLM fix attempt: {e}")


def fix_json_with_llm(broken_json: str) -> str:
    """
    Use LLM to fix malformed JSON.
    
    Args:
        broken_json: Malformed JSON string
        
    Returns:
        Fixed JSON string
    """
    model = ChatGoogleGenerativeAI(
        model=LLM_MODEL,
        temperature=0,  # Zero temperature for deterministic fixing
    )
    
    prompt = ChatPromptTemplate.from_template(STRUCTURED_OUTPUT_PROMPT)
    chain = prompt | model | StrOutputParser()
    
    return chain.invoke({"raw_cards": broken_json})


def filter_valid_cards(card_set: FlashcardSet) -> FlashcardSet:
    """
    Filter out cards that don't meet quality thresholds.
    
    Args:
        card_set: Validated FlashcardSet
        
    Returns:
        Filtered FlashcardSet with only high-quality cards
    """
    valid_cards = []
    
    for card in card_set.cards:
        # Check minimum length requirements
        if len(card.question) >= 15 and len(card.answer) >= 20:
            # Check tag is valid
            if card.tag in VALID_TAGS:
                valid_cards.append(card)
    
    if not valid_cards:
        raise ValueError("No valid cards remain after filtering")
    
    return FlashcardSet(cards=valid_cards)


# =============================================================================
# FULL PIPELINE
# =============================================================================

def process_to_structured_output(raw_cards: str) -> FlashcardSet:
    """
    Full structured output pipeline.
    
    Args:
        raw_cards: Raw output from transformation step
        
    Returns:
        Validated and filtered FlashcardSet
    """
    # Validate and parse
    card_set = validate_flashcards(raw_cards)
    
    # Apply quality filtering
    filtered_set = filter_valid_cards(card_set)
    
    return filtered_set
