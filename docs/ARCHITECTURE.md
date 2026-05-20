# System Architecture: GenAI Flashcard Generator

This document details the architectural design, system components, data flows, and Retrieval-Augmented Generation (RAG) pipeline for the GenAI Flashcard Generator application.

---

## 1. High-Level System Architecture

The application is structured as a decoupled multi-tier web application consisting of a modern frontend interface, a lightweight REST API backend, and local/remote AI integration layers.

```mermaid
graph TD
    %% Clients
    User([User Browser]) <--> |HTTP/WS| FE[Nuxt 3 Frontend]

    %% Main Application Servers
    FE <--> |JSON API| BE[Flask Backend]

    %% Vector Database & Text Processing
    subgraph Local Storage & Compute
        BE <--> |In-Memory API| CDB[(ChromaDB Vector Store)]
        BE <--> |Python Object| BM25[BM25 Retriever]
    end

    %% AI Services
    subgraph AI Infrastructure
        BE --> |OpenRouter API / Gemini API| LLM[Google Gemini / GPT-4o-Mini]
        BE --> |HTTP POST| OLL[Ollama Service - Docker Compose]
        OLL --> |nomic-embed-text| EMB[Local Embeddings Engine]
    end

    %% Ingestion Data Flow
    UserDoc[User Documents .pdf, .txt, .md] -->|Upload| FE
```

### Components

1.  **Frontend (Nuxt 3 / Vue 3)**: A responsive single-page application (SPA) built with Nuxt 3, utilizing `@nuxt/ui` (Tailwind-based) and components for managing sessions, documents, chat interfaces, and flashcard practice.
2.  **Backend (Flask)**: A Python Flask web server exposing API endpoints for session control, file ingestion, hybrid search-based chat, and structured flashcard generation.
3.  **Local Services (Ollama in Docker)**: Runs the embedding service using the `nomic-embed-text` model in a Docker container.
4.  **LLM Layer (OpenRouter / Google Gemini)**: Provides LLM execution. Supports OpenRouter (defaulting to `openai/gpt-4o-mini`) and direct Google Gemini models (defaulting to `gemini-2.5-flash`) via LangChain adapters to handle chat completions, concept extractions, card transformations, and self-critiques.


---

## 2. Ingestion & RAG Pipeline

The application features a session-isolated RAG pipeline to prevent document leakage across user sessions.

### Ingestion Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as Nuxt 3 Frontend
    participant BE as Flask Backend
    participant OL as Ollama (nomic-embed-text)
    participant DB as ChromaDB & BM25

    User->>FE: Upload Document (PDF/TXT)
    FE->>BE: POST /api/sessions/{id}/ingest
    alt Is PDF
        BE->>BE: Extract text per page (pypdf)
    else Is TXT/MD
        BE->>BE: Extract raw text
    end
    BE->>BE: Run SemanticChunker (breakpoint_threshold_amount=95)
    BE->>OL: Request embeddings for chunks
    OL-->>BE: Return vector embeddings
    BE->>DB: Add chunks to session collection & BM25 index
    BE-->>FE: Return JSON (chunks_ingested, document_id)
    FE-->>User: Show upload success
```

1.  **Text Extraction**: PDF files are parsed using `pypdf` page by page, preserving page numbers. TXT and MD files are read as raw UTF-8 text.
2.  **Semantic Chunking**: Instead of fixed-character chunking, the project employs LangChain Experimental's `SemanticChunker`. 
    *   **Breakpoint Method**: `percentile` (threshold = 95).
    *   **Model**: Ollama's local `nomic-embed-text`.
    *   **Metadata**: Each chunk captures `document_id`, `source` (filename), `page_number`, `chunk_index`, character start/end offsets, and a unique `citation_id` formatted as `{document_id}:p{page_number}:c{chunk_index}`.
3.  **Vector & Keyword Storage**: Chunks are embedded and stored in an in-memory ChromaDB collection, and simultaneously added to an in-memory BM25 index for sparse keyword matching.

---

## 3. Hybrid Search & Retrieval Fusion

The system uses a hybrid retrieval mechanism combining dense and sparse search to maximize recall and precision.

```mermaid
graph LR
    Query[User Query / Topic] --> Dense[ChromaDB Dense Search]
    Query --> Sparse[BM25 Keyword Search]
    
    Dense -->|Top 3*K Chunks| RRF[Reciprocal Rank Fusion - RRF]
    Sparse -->|Top 3*K Chunks| RRF
    
    RRF -->|Calculate RRF Score| Rank[Rank and Filter]
    Rank -->|Top K Chunks| Out[Final Context + Citations]
```

### Reciprocal Rank Fusion (RRF)
Dense results from ChromaDB (using cosine distance on local embeddings) and sparse results from BM25 are fused together. The scoring formula for each chunk $d$ is:

$$RRF\_Score(d) = \sum_{m \in \{dense, sparse\}} \frac{1}{rrf\_k + rank_m(d)}$$

Where:
*   $rrf\_k$ is set to `60` (the smoothing constant).
*   $rank_m(d)$ is the 1-based rank position of chunk $d$ in retriever $m$. If a chunk is not retrieved by a retriever, its rank term is omitted.
*   The top $k$ chunks with the highest fused score are selected.

---

## 4. Citation Generation & Grounded Context

When preparing context for the Chat and Flashcard engines, the retrieved chunks are formatted into a single string. To provide precise academic citations, the backend maps citation indices to chunks dynamically.

```python
# Format returned to LLMs:
[Source 1: lecture.pdf | Page: 3 | Section: N/A]
"Semantic search allows matching text by conceptual similarity..."

[Source 2: notes.txt | Page: N/A | Section: N/A]
"Dense vector embeddings represent text as high-dimensional coordinates..."
```

As the answer is generated by the LLM, the source citation numbers (e.g., `[1]`, `[2]`) are extracted and returned as structured metadata in the JSON response, allowing the frontend to highlight the corresponding chunks.

---

## 5. Flashcard Generation & Flow Engineering

Generating high-quality, educationally-sound flashcards from raw context relies on a **Flow Engineering** pattern rather than a single prompt.

```mermaid
stateDiagram-v2
    [*] --> RetrieveContext: Search topic/document
    RetrieveContext --> ExtractorChain: Run Concept List Extraction
    note right of ExtractorChain: Enforces structured ConceptList schema
    
    ExtractorChain --> TransformationChain: Transform each concept to Card
    note right of TransformationChain: Maps name, description, and quotes to Q&A
    
    TransformationChain --> CritiqueChain: Critique & Self-Correction (Optional)
    note right of CritiqueChain: Scores 1-5 on Accuracy, Completeness, Clarity, Relevance
    
    CritiqueChain --> FilterVerdicts: Evaluate scores
    FilterVerdicts --> Accepted: Score >= 4.0 & Accuracy >= 4
    FilterVerdicts --> Rejected: Score < 4.0 or Accuracy < 4
    
    Accepted --> Output
    Rejected --> FallbackOrDiscard
    FallbackOrDiscard --> Output
    Output --> [*]
```

1.  **Extraction**: The `ExtractorChain` uses structured output to identify distinct `Concept` models from the context.
2.  **Transformation**: The `TransformationChain` takes each extracted concept and designs a custom Question/Answer pair, assigning an educational tag (`definition`, `concept`, `procedure`, `comparison`, or `application`).
3.  **Self-Correction**: The `CritiqueChain` acts as a validation agent. It compares each card against the source text and scores it. Cards that score poorly are filtered out or corrected.

---

## 6. Session and Memory Lifecycle

*   **Isolation**: Every active session has an isolated session memory structure mapping to its own ChromaDB collection: `session_{session_id}`.
*   **Volatile Storage**: The system operates with an in-memory client `chromadb.Client()`. Sessions and databases persist only as long as the backend server is running.
*   **Teardown**: A `DELETE /api/sessions/{session_id}` request drops the associated ChromaDB collection and clears the session's memory footprint on the Flask server.
