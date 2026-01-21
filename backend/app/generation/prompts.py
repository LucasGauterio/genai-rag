"""
Prompt Templates - Multi-step generation prompts.

These prompts implement the "Flow Engineering" pattern:
1. Extraction: Identify key concepts from source text
2. Transformation: Convert concepts to Q&A format
3. Structured Output: Enforce JSON schema compliance

Each prompt is carefully designed for:
- Grounding (only use source material)
- Abstention (don't hallucinate)
- Accuracy (preserve technical precision)
"""

# =============================================================================
# STEP 1: EXTRACTION PROMPT
# =============================================================================

EXTRACTION_PROMPT = """You are an Expert Knowledge Extractor analyzing technical documentation for flashcard creation.

Your task is to identify and extract learning-worthy information from the provided context.

## Extraction Categories

1. **KEY CONCEPTS**: Core ideas, principles, or patterns that a student must understand
2. **DEFINITIONS**: Technical terms with their precise meanings
3. **RELATIONSHIPS**: How concepts connect (e.g., "X is a type of Y", "A depends on B")
4. **PROCEDURES**: Step-by-step processes, algorithms, or workflows
5. **EXAMPLES**: Concrete illustrations that clarify abstract concepts

## Rules

1. **GROUNDING**: Extract ONLY information explicitly present in the provided context
2. **ACCURACY**: Preserve technical terminology exactly as written
3. **COMPLETENESS**: Capture all flashcard-worthy information
4. **DENSITY**: Aim to extract 5-10 concepts per context block when the material is rich
5. **CITATIONS**: The context contains citation markers like [1], [2]. **PRESERVE these markers** in the "source_quote" field of your extraction.

## Context to Analyze

{context}
"""


# =============================================================================
# STEP 2: TRANSFORMATION PROMPT
# =============================================================================

TRANSFORMATION_PROMPT = """You are an Expert Flashcard Designer creating exam-ready study materials.

You will receive a single extracted concept and must transform it into a high-quality Question & Answer pair.

## Extracted Concept

Name: {concept_name}
Type: {concept_type}
Description: {concept_description}
Source Quote: "{concept_quote}"

## Flashcard Design Principles

### Question Types (use variety):
- **Definition**: "What is [term]?" / "Define [concept]."
- **Explanation**: "How does [X] work?" / "Why is [X] important?"
- **Comparison**: "What is the difference between X and Y?"
- **Application**: "When would you use [X]?" / "In what scenario..."
- **Procedure**: "What are the steps to [process]?"
- **Relationship**: "How does X relate to Y?"

### Answer Quality Guidelines:
- **Concise but complete**: 2-4 sentences is ideal
- **Include key terminology**: Use the exact technical terms
- **Self-contained**: Answer should make sense without seeing the question
- **Accurate**: Must match the source material exactly

### Tagging Rules (assign exactly ONE):
- `definition` - Term explanations and meanings
- `concept` - Principles, theories, and abstract ideas
- `procedure` - How-to knowledge and step-by-step processes
- `comparison` - Differences, similarities, trade-offs
- `application` - Real-world usage and practical scenarios

## Output Format

Produce a valid JSON object for a single flashcard:

```json
{{
  "question": "Clear, specific question that tests understanding",
  "answer": "Accurate, complete answer based on source material",
  "citation": "[1]",
  "tag": "one_of_the_five_tags"
}}
```

## Rules

1. Create exactly ONE flashcard for this concept
2. Questions must be unambiguous - only one correct answer possible
3. Answers must be factually grounded in the extracted content
4. Avoid yes/no questions - require explanation
5. **CITATION**: You MUST include the citation marker (e.g., [1]) from the Source Quote in the `citation` field. If multiple citations apply, include them all (e.g. "[1] [2]").

## Generate Flashcards

Output only valid JSON:
"""






