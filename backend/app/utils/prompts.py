"""
Prompt templates for LLM generation.
"""

import re
from typing import List, Dict


# --- System Prompts ---

SYSTEM_PROMPTS = {
    "chat": """You are a helpful study assistant. Answer questions based on the provided sources.
Always cite your sources using [1], [2], etc. when making factual claims.
If the sources don't contain relevant information, say so.""",

    "summary": """You are a study assistant creating concise summaries.
Summarize the key points from the sources, citing each point with [1], [2], etc.
Focus on main concepts, definitions, and important details.""",

    "flashcards": """You are a study assistant creating flashcards.
Generate Q&A flashcards from the sources. Each answer must cite its source.""",
}

TASK_INSTRUCTIONS = {
    "chat": "answer the question",
    "summary": "provide a comprehensive summary",
    "flashcards": "create study flashcards",
}


def get_system_prompt(mode: str) -> str:
    """Get system prompt based on mode."""
    return SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["chat"])


def get_task_instruction(mode: str) -> str:
    """Get task instruction based on mode."""
    return TASK_INSTRUCTIONS.get(mode, "respond")


# --- Context Building ---

def build_context_with_citations(chunks: List[Dict]) -> tuple[str, Dict]:
    """
    Build context string with citation markers.
    
    Args:
        chunks: List of chunks with text and metadata
    
    Returns:
        Tuple of (context_string, citations_dict)
    """
    context_parts = []
    citations = {}
    
    for i, chunk in enumerate(chunks, start=1):
        marker = f"[{i}]"
        context_parts.append(f"{marker} {chunk['text']}")
        
        citations[marker] = {
            "page": chunk["metadata"].get("page_number"),
            "source": chunk["metadata"].get("source"),
            "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
            "citation_id": chunk["metadata"].get("citation_id"),
            "start_offset": chunk["metadata"].get("start_offset"),
            "end_offset": chunk["metadata"].get("end_offset"),
        }
    
    context = "\n\n".join(context_parts)
    return context, citations


def build_chat_prompt(context: str, question: str, mode: str) -> str:
    """Build complete chat prompt."""
    system_prompt = get_system_prompt(mode)
    task = get_task_instruction(mode)
    
    return f"""{system_prompt}

Based on the following sources, {task}

Sources:
{context}

User request: {question}

Remember to cite sources using [1], [2], etc. for any factual claims."""


def build_flashcard_prompt(context: str, topic: str, count: int) -> str:
    """Build flashcard generation prompt."""
    return f"""You are a study assistant creating flashcards.

Based on the following sources, generate {count} flashcards about "{topic}".

Format each flashcard as:
Q: [question]
A: [answer] [citation]

Rules:
- Each answer MUST cite its source using [1], [2], etc.
- Focus on definitions, key concepts, formulas, and examples
- Make questions clear and specific
- Keep answers concise but complete

Sources:
{context}

Generate {count} flashcards:"""


# --- Response Parsing ---

def parse_flashcards(text: str) -> List[Dict]:
    """Parse flashcard format from LLM response."""
    flashcards = []
    
    # Pattern: Q: ... A: ...
    pattern = r'Q:\s*(.+?)\s*A:\s*(.+?)(?=Q:|$)'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    
    for question, answer in matches:
        citation_match = re.search(r'\[(\d+)\]', answer)
        citation = citation_match.group(0) if citation_match else None
        
        flashcards.append({
            "question": question.strip(),
            "answer": answer.strip(),
            "citation": citation,
        })
    
    return flashcards
