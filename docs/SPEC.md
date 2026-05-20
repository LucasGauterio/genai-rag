# System Specification (SPEC.md)

This document contains the complete technical specification of the GenAI Flashcard Generator, including environment configurations, REST API endpoints, Pydantic schemas, and frontend view details.

---

## 1. Environment Configurations

### Backend Environment Variables (`backend/app/.env`)

These variables configure the Flask server connection to LLM APIs and local embedding services.

| Variable | Description | Example / Default Value |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | Selection of LLM connection client backend. | `"openrouter"` or `"gemini"` |
| `OPENROUTER_API_KEY` | API Key for OpenRouter.ai to execute remote LLM queries. | `sk-or-v1-...` |
| `OPENROUTER_MODEL` | LLM Model selector. | `openai/gpt-4o-mini` |
| `GEMINI_API_KEY` | Direct Google Gemini Studio API Key. | `AIzaSy...` |
| `GEMINI_MODEL` | Google Gemini LLM Model selector. | `gemini-2.5-flash` |

| `OLLAMA_BASE_URL` | Endpoint of the local Ollama docker service. | `http://localhost:11434` |
| `OLLAMA_EMBEDDING_MODEL`| Model name used by Ollama to compute embeddings. | `nomic-embed-text` |


### Frontend Environment Variables (`frontend/.env`)

These variables configure the Nuxt 3 development and production environment client-side behaviors.

| Variable | Description | Example / Default Value |
| :--- | :--- | :--- |
| `NUXT_BACKEND_API_URL` | Base URL of the Flask API. | `http://localhost:5000` |

---

## 2. API Endpoints Specification

All endpoints are prefixed with `/api`. Content types are `application/json` unless otherwise specified.

### 2.1 Session Management

#### Create Session
*   **Method / Route**: `POST /sessions`
*   **Request Body**: None
*   **Response (201 Created)**:
    ```json
    {
      "session_id": "8a7c2e1f",
      "collection_name": "session_8a7c2e1f",
      "created_at": "2026-05-20T11:50:00.123456"
    }
    ```

#### List Sessions
*   **Method / Route**: `GET /sessions`
*   **Response (200 OK)**:
    ```json
    {
      "sessions": [
        {
          "session_id": "8a7c2e1f",
          "collection_name": "session_8a7c2e1f",
          "chunk_count": 42,
          "created_at": "2026-05-20T11:50:00.123456"
        }
      ]
    }
    ```

#### Get Session Details
*   **Method / Route**: `GET /sessions/{session_id}`
*   **Response (200 OK)**:
    ```json
    {
      "session_id": "8a7c2e1f",
      "created_at": "2026-05-20T11:50:00.123456",
      "chunk_count": 42,
      "documents": [
        {
          "document_id": "doc-uuid-111",
          "filename": "lecture1.pdf",
          "chunks": 42
        }
      ]
    }
    ```
*   **Response (404 Not Found)**:
    ```json
    { "error": "Session not found" }
    ```

#### Delete Session
*   **Method / Route**: `DELETE /sessions/{session_id}`
*   **Response (200 OK)**:
    ```json
    { "message": "Session 8a7c2e1f deleted" }
    ```

---

### 2.2 Document Ingestion

#### Ingest Document
*   **Method / Route**: `POST /sessions/{session_id}/ingest`
*   **Content-Type**: `multipart/form-data`
*   **Request Body**:
    *   `file` (file binary, supports `.pdf`, `.txt`, `.md`)
*   **Response (201 Created)**:
    ```json
    {
      "document_id": "9f3b5d2e-405e-4c7b-91db-8ea13a6df912",
      "filename": "quantum_physics.pdf",
      "chunks_ingested": 18
    }
    ```
*   **Response (400 Bad Request)**:
    ```json
    { "error": "Unsupported file type. Use PDF, TXT, or MD" }
    ```

---

### 2.3 RAG Chat & Flashcard Generation

#### Chat in Session
*   **Method / Route**: `POST /sessions/{session_id}/chat`
*   **Request Body**:
    ```json
    {
      "question": "What is superposition?",
      "mode": "chat",
      "document_id": "optional-document-uuid",
      "k": 5
    }
    ```
    *   `mode`: `"chat"` (general dialog) or `"summary"` (condensed explanation).
    *   `document_id` (optional): Filter retrieval to a specific document.
    *   `k` (optional): Number of retrieved chunks to feed as context (default: `5`).
*   **Response (200 OK)**:
    ```json
    {
      "answer": "Superposition is a principle in quantum mechanics... [1].",
      "chunks_used": 3,
      "citations": {
        "[1]": {
          "source": "quantum_physics.pdf",
          "page_number": 2,
          "citation_id": "9f3b5d2e:p2:c1"
        }
      }
    }
    ```

#### Generate Flashcards
*   **Method / Route**: `POST /sessions/{session_id}/flashcards`
*   **Request Body**:
    ```json
    {
      "topic": "superposition",
      "document_id": "optional-document-uuid",
      "count": 5,
      "validate": true
    }
    ```
    *   `validate`: Activates the self-correction verification chain (default: `true`).
*   **Response (200 OK)**:
    ```json
    {
      "topic": "superposition",
      "flashcards": [
        {
          "question": "Explain the concept of quantum superposition.",
          "answer": "Superposition is the ability of a quantum system to be in multiple states at the same time until it is measured.",
          "tag": "concept",
          "citation": "[1]"
        }
      ],
      "citations": {
        "[1]": {
          "source": "quantum_physics.pdf",
          "page_number": 2,
          "citation_id": "9f3b5d2e:p2:c1"
        }
      },
      "stats": {
        "total": 5,
        "accepted": 4,
        "rejected": 1,
        "avg_accuracy": 4.6,
        "avg_overall": 4.4
      }
    }
    ```

---

## 3. Pydantic Schemas

### Concept & ConceptList (Extraction Stage)
```python
class Concept(BaseModel):
    name: str  # Name or title of the concept
    type: Literal["definition", "principle", "relationship", "procedure", "example"]
    description: str  # Clear explanation from context
    related_to: List[str]  # Cross-references to other concepts
    source_quote: str  # Exact quote preserving citation indices
    difficulty: Literal["basic", "intermediate", "advanced"]

class ConceptList(BaseModel):
    concepts: List[Concept]
```

### Flashcard & FlashcardSet (Transformation Stage)
```python
class Flashcard(BaseModel):
    question: str  # Min length: 10 chars
    answer: str  # Min length: 10 chars
    citation: Optional[str]  # e.g., "[1]" or "[1] [2]"
    tag: Literal["definition", "concept", "procedure", "comparison", "application"]

class FlashcardSet(BaseModel):
    cards: List[Flashcard]
```

### CritiqueResult (Validation Stage)
```python
class CritiqueResult(BaseModel):
    accuracy_score: float  # Range: 1.0 - 5.0
    completeness_score: float  # Range: 1.0 - 5.0
    clarity_score: float  # Range: 1.0 - 5.0
    relevance_score: float  # Range: 1.0 - 5.0
    issues: List[str]
```

---

## 4. Frontend Application Layout

The Nuxt 3 frontend operates as a single-page view partitioned into four interactive panels:

1.  **SessionPanel**: Left sidebar. Allows creating new study sessions, listing active sessions, and deleting sessions. Selecting a session loads its state.
2.  **DocumentsPanel**: Top-left body panel. Shows files uploaded to the current session, their status, chunk counts, and offers a drag-and-drop file uploader.
3.  **ChatPanel**: Main workspace panel. Displays a conversational dialogue list showing user questions and system answers with hoverable/clickable citations. Clicking a citation highlights the source chunk.
4.  **FlashcardPanel**: Right panel. Allows triggering flashcard generation. Shows a list of cards created for a topic, with tags and citation links, and supports interactive study flips (Question $\rightarrow$ Click $\rightarrow$ Answer).
