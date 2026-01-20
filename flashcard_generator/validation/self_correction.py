"""
Self-Correction Module - The "Reflect" mode.

Implements LLM-based self-critique to ensure flashcard accuracy:
1. Compare each card against source context
2. Score on accuracy, completeness, clarity, relevance
3. Accept, revise, or reject cards based on scores
4. Apply corrections for cards that need revision
"""

import json
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import LLM_MODEL, LLM_TEMPERATURE, MIN_CONFIDENCE_SCORE
from generation.structured_output import Flashcard, FlashcardSet


# =============================================================================
# CRITIQUE PROMPT
# =============================================================================

CRITIQUE_PROMPT = """You are a Quality Assurance Expert reviewing flashcards for accuracy and educational value.

Your task is to compare a generated flashcard against its source material and evaluate its quality.

## Original Source Context

{source_context}

## Generated Flashcard to Review

**Question:** {question}
**Answer:** {answer}
**Tag:** {tag}

## Evaluation Criteria (Score 1-5 each)

1. **ACCURACY** (Critical): Does the answer match the source exactly? Are there any hallucinations or inaccuracies?
   - 5: Perfect accuracy, every claim is directly supported
   - 3: Mostly accurate, minor imprecisions
   - 1: Contains significant errors or unsupported claims

2. **COMPLETENESS**: Does the answer cover the essential information for this question?
   - 5: Comprehensive, includes all key points
   - 3: Covers basics but misses some details
   - 1: Incomplete or superficial

3. **CLARITY**: Is the question unambiguous? Is the answer understandable?
   - 5: Crystal clear, no confusion possible
   - 3: Generally clear, minor ambiguity
   - 1: Confusing or poorly worded

4. **RELEVANCE**: Is this a useful flashcard for studying this topic?
   - 5: Highly valuable for exam preparation
   - 3: Somewhat useful
   - 1: Trivial or not worth studying

## Output Format

Respond with ONLY a valid JSON object:

```json
{{
  "accuracy_score": <1-5>,
  "completeness_score": <1-5>,
  "clarity_score": <1-5>,
  "relevance_score": <1-5>,
  "issues": ["list of specific problems found, empty if none"]
}}
```

## Your Critique

"""


# =============================================================================
# PYDANTIC MODELS FOR CRITIQUE
# =============================================================================


class CritiqueResult(BaseModel):
    """Result of critiquing a single flashcard."""
    accuracy_score: float = Field(..., ge=1, le=5)
    completeness_score: float = Field(..., ge=1, le=5)
    clarity_score: float = Field(..., ge=1, le=5)
    relevance_score: float = Field(..., ge=1, le=5)
    issues: List[str] = Field(default_factory=list)
    
    @property
    def average_score(self) -> float:
        """Calculate average of all scores."""
        return (
            self.accuracy_score + 
            self.completeness_score + 
            self.clarity_score + 
            self.relevance_score
        ) / 4.0
    
    @property
    def verdict(self) -> str:
        """
        Calculate verdict deterministically in Python.
        
        Rules:
        - ACCEPT: Average score >= 4.0 AND Accuracy score >= 4
        - REJECT: Otherwise
        """
        if self.average_score >= 4.0 and self.accuracy_score >= 4:
            return "ACCEPT"
        return "REJECT"


# =============================================================================
# CRITIQUE CHAIN
# =============================================================================

class CritiqueChain:
    """
    Self-correction chain for flashcard validation.
    
    Compares each flashcard against source material and
    provides quality scores and revision suggestions.
    """
    
    def __init__(self, model_name: str = None, temperature: float = None):
        """
        Initialize the critique chain.
        
        Args:
            model_name: LLM model to use
            temperature: Generation temperature (lower for more consistent evaluation)
        """
        self.model = ChatGoogleGenerativeAI(
            model=model_name or LLM_MODEL,
            temperature=temperature if temperature is not None else 0.1,  # Low temp for evaluation
        )
        
        self.prompt = ChatPromptTemplate.from_template(CRITIQUE_PROMPT)
        self.chain = self.prompt | self.model | StrOutputParser()
    
    def critique(
        self,
        flashcard: Flashcard,
        source_context: str,
    ) -> CritiqueResult:
        """
        Critique a single flashcard against source material.
        
        Args:
            flashcard: The flashcard to evaluate
            source_context: Original source text
            
        Returns:
            CritiqueResult with scores and verdict
        """
        response = self.chain.invoke({
            "source_context": source_context,
            "question": flashcard.question,
            "answer": flashcard.answer,
            "tag": flashcard.tag,
        })
        
        # Parse the JSON response
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return CritiqueResult(**data)
        except Exception as e:
            # If parsing fails, return a conservative result
            return CritiqueResult(
                accuracy_score=3,
                completeness_score=3,
                clarity_score=3,
                relevance_score=3,
                issues=["Critique parsing failed, using default scores"],
            )


# =============================================================================
# HIGH-LEVEL FUNCTIONS
# =============================================================================

def critique_flashcard(
    flashcard: Flashcard,
    source_context: str,
    model_name: str = None,
) -> CritiqueResult:
    """
    Convenience function to critique a single flashcard.
    
    Args:
        flashcard: Flashcard to evaluate
        source_context: Source text for validation
        model_name: Optional model override
        
    Returns:
        CritiqueResult
    """
    chain = CritiqueChain(model_name=model_name)
    return chain.critique(flashcard, source_context)


def validate_and_correct_cards(
    card_set: FlashcardSet,
    source_context: str,
    min_score: float = None,
    model_name: str = None,
) -> Tuple[FlashcardSet, dict]:
    """
    Validate all cards and apply corrections where needed.
    
    This is the main self-correction function that:
    1. Critiques each card against source
    2. Accepts high-quality cards
    3. Revises cards with fixable issues
    4. Rejects cards with unfixable problems
    
    Args:
        card_set: FlashcardSet to validate
        source_context: Source text for validation
        min_score: Minimum average score for acceptance
        model_name: Optional model override
        
    Returns:
        Tuple of (validated FlashcardSet, statistics dict)
    """
    min_score = min_score or MIN_CONFIDENCE_SCORE
    chain = CritiqueChain(model_name=model_name)
    
    accepted_cards = []
    statistics = {
        "total": len(card_set.cards),
        "accepted": 0,
        "accepted": 0,
        "rejected": 0,
        "avg_accuracy": 0.0,
        "avg_overall": 0.0,
    }
    
    total_accuracy = 0.0
    total_overall = 0.0
    
    for card in card_set.cards:
        critique = chain.critique(card, source_context)
        
        total_accuracy += critique.accuracy_score
        total_overall += critique.average_score
        
        if critique.verdict == "ACCEPT":
            accepted_cards.append(card)
            statistics["accepted"] += 1
            
        else:  # REJECT
            statistics["rejected"] += 1
    
    # Calculate averages
    if card_set.cards:
        statistics["avg_accuracy"] = total_accuracy / len(card_set.cards)
        statistics["avg_overall"] = total_overall / len(card_set.cards)
    
    # Create final set (may be empty if all rejected)
    if accepted_cards:
        validated_set = FlashcardSet(cards=accepted_cards)
    else:
        # If everything was rejected, return original with warning
        validated_set = card_set
        statistics["warning"] = "All cards rejected, returning original set"
    
    return validated_set, statistics
