# Study Assistant Backend

Flask backend for session-based RAG with citation support.

## Quick Start

The backend requires python dependencies and the environment variables configured.

### Option 1: Terminal (Manual Setup)

1. Navigate to the backend directory:
   ```bash
   cd backend/app
   ```
2. Create and activate a Python virtual environment:
   * **macOS / Linux**:
     ```bash
     python -m venv venv
     source venv/bin/activate
     ```
   * **Windows (Command Prompt)**:
     ```cmd
     python -m venv venv
     venv\Scripts\activate.bat
     ```
   * **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the server:
   ```bash
   python app.py
   ```
   The server starts at `http://localhost:5000`.

### Option 2: Flask CLI

```bash
cd backend/app
# Set environment variables if not using a .env file:
# On Linux/macOS:
export FLASK_APP=app.py
export FLASK_ENV=development
# On Windows (PowerShell):
# $env:FLASK_APP="app.py"; $env:FLASK_ENV="development"
flask run --host=0.0.0.0 --port=5000
```

## Environment Variables

The backend utilizes `python-dotenv` to dynamically find and load environment variables. It searches for a `.env` file starting from the current directory and walks up the folder tree.

You can configure the variables in either the **root directory** `.env` or in the **backend application directory** `backend/app/.env`:

```env
# LLM Provider: 'openrouter' or 'gemini'
LLM_PROVIDER=openrouter

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini

# Google Gemini Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Local Embeddings (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

## API Endpoints

### Session Management

```bash
# Create session
POST /api/sessions
→ { "session_id": "abc123", "created_at": "..." }

# List sessions
GET /api/sessions

# Get session info
GET /api/sessions/{id}

# Delete session
DELETE /api/sessions/{id}
```

### Document Ingestion

```bash
# Upload document to session
POST /api/sessions/{id}/ingest
Content-Type: multipart/form-data
Body: file=<PDF or TXT>

→ { "document_id": "...", "filename": "...", "chunks_ingested": 45 }
```

### Chat & Generation

```bash
# Chat with citations
POST /api/sessions/{id}/chat
{
  "question": "What is attention?",
  "mode": "chat" | "summary",
  "document_id": "optional",
  "k": 5
}

→ { "answer": "Attention is... [1]", "citations": {...} }

# Generate flashcards
POST /api/sessions/{id}/flashcards
{
  "topic": "attention mechanism",
  "document_id": "optional",
  "count": 10
}

→ { "flashcards": [...], "citations": {...} }
```

## Example Workflow

```bash
# 1. Create session
SESSION_ID=$(curl -X POST http://localhost:5000/api/sessions | jq -r '.session_id')

# 2. Upload document
curl -X POST http://localhost:5000/api/sessions/$SESSION_ID/ingest \
  -F "file=@lecture.pdf"

# 3. Chat
curl -X POST http://localhost:5000/api/sessions/$SESSION_ID/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is attention?"}'

# 4. Generate flashcards
curl -X POST http://localhost:5000/api/sessions/$SESSION_ID/flashcards \
  -H "Content-Type: application/json" \
  -d '{"topic": "attention", "count": 5}'

# 5. Close session
curl -X DELETE http://localhost:5000/api/sessions/$SESSION_ID
```

## Architecture

- **Session-based collections**: Each chat = one ChromaDB collection
- **Hybrid retrieval**: BM25 + Dense embeddings with RRF fusion
- **Citation metadata**: Page numbers, offsets, citation IDs
- **Cleanup**: Collections deleted when session closes

See `docs/BACKEND_ARCHITECTURE.md` for details.
