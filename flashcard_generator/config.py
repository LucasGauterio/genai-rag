"""
Flashcard Generator Configuration

Centralized configuration for the entire pipeline.
Uses best-practice models for production-quality output.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMA_PATH = BASE_DIR / "chroma_db"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================================================
# LLM CONFIGURATION
# =============================================================================
# Using Gemini Flash - fast and effective for structured output
LLM_MODEL = "gemini-flash-latest"
LLM_TEMPERATURE = 0.1  # Low temperature for factual accuracy

# =============================================================================
# EMBEDDING CONFIGURATION  
# =============================================================================
# Using all-MiniLM-L6-v2 - fast and effective for testing
# Switch to "BAAI/bge-large-en-v1.5" for production (state-of-the-art but larger)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# =============================================================================
# CHUNKING CONFIGURATION
# =============================================================================
CHUNK_SIZE = 800  # Larger chunks to preserve context
CHUNK_OVERLAP = 150  # Overlap to maintain continuity

# Semantic separators - respect document structure
SEMANTIC_SEPARATORS = [
    "\n# ",      # H1 headers (markdown)
    "\n## ",     # H2 headers
    "\n### ",    # H3 headers
    "\n#### ",   # H4 headers
    "\n\n\n",    # Multiple newlines (section breaks)
    "\n\n",      # Paragraphs
    "\n",        # Lines
    ". ",        # Sentences
    " ",         # Words (fallback)
]

# =============================================================================
# RETRIEVAL CONFIGURATION
# =============================================================================
RETRIEVAL_K = 10  # Number of chunks to retrieve
BM25_WEIGHT = 0.4  # Weight for keyword matching
DENSE_WEIGHT = 0.6  # Weight for semantic matching
RERANK_MODEL = "ms-marco-MiniLM-L-12-v2"

# =============================================================================
# GENERATION CONFIGURATION
# =============================================================================
MAX_CARDS_PER_BATCH = 10  # Cards per generation batch
MIN_CONFIDENCE_SCORE = 3.5  # Minimum average score for acceptance (1-5 scale)

# Valid tags for flashcards
VALID_TAGS = ["definition", "concept", "procedure", "comparison", "application"]

# =============================================================================
# API KEYS
# =============================================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY not found in environment variables. "
        "Please set it in your .env file."
    )
