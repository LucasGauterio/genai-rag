# Study Assistant Backend

Flask backend for session-based RAG with citation support.

## Quick Start

### Option 1: VS Code Debugger (Recommended)

1. Open VS Code in the project root
2. Press `F5` or go to Run → Start Debugging
3. Select **"Python: Flask (Backend)"** configuration
4. Server starts at `http://localhost:5000`

### Option 2: Terminal

```bash
cd backend/app
pip install -r requirements.txt
python app.py
```

### Option 3: Flask CLI

```bash
cd backend/app
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5000
```

## Environment Variables

Create `.env` file in `backend/app/`:

```env
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
OLLAMA_BASE_URL=http://localhost:11434
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
