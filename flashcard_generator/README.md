# Flashcard Generator Pipeline

A Python-based pipeline for generating high-quality, exam-ready flashcards from technical 
documents using advanced RAG patterns and Flow Engineering principles.

## Features

- **Semantic Chunking**: Structure-aware parsing that respects document boundaries
- **Hybrid Search**: Dense vectors + BM25 for comprehensive retrieval
- **Multi-Step Generation**: Extract → Transform → Structured Output flow
- **Self-Correction**: LLM-based validation against source text

## Installation

```bash
cd flashcard_generator
pip install -r requirements.txt
```

## Usage

### CLI

```bash
# Ingest documents
python main.py ingest --input /path/to/documents

# Generate flashcards
python main.py generate --topic "Machine Learning" --max-cards 20

# Full pipeline
python main.py generate --input docs/ml_notes.pdf --output flashcards.json
```

### Streamlit UI

```bash
streamlit run app.py
```

## Architecture

```
Document → Semantic Chunking → Vector Store
                                    ↓
                            Hybrid Retrieval (Dense + BM25)
                                    ↓
                            Step 1: Extract Concepts
                                    ↓
                            Step 2: Transform to Q&A
                                    ↓
                            Step 3: Structured JSON Output
                                    ↓
                            Self-Correction & Validation
                                    ↓
                            Final Flashcards
```

## Configuration

Set your API key in `.env`:

```
GOOGLE_API_KEY=your_api_key_here
```

## Output Format

```json
{
  "cards": [
    {
      "question": "What is gradient descent?",
      "answer": "An optimization algorithm that iteratively adjusts parameters...",
      "tag": "definition"
    }
  ]
}
```
