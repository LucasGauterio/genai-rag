"""Generation Module - Multi-step flashcard generation with structured output"""

from .prompts import (
    EXTRACTION_PROMPT,
    TRANSFORMATION_PROMPT,
    STRUCTURED_OUTPUT_PROMPT,
)
from .extraction import ExtractorChain, extract_concepts
from .transformation import TransformationChain, transform_to_flashcards
from .structured_output import FlashcardSet, Flashcard, validate_flashcards

__all__ = [
    "EXTRACTION_PROMPT",
    "TRANSFORMATION_PROMPT",
    "STRUCTURED_OUTPUT_PROMPT",
    "ExtractorChain",
    "extract_concepts",
    "TransformationChain",
    "transform_to_flashcards",
    "FlashcardSet",
    "Flashcard",
    "validate_flashcards",
]
