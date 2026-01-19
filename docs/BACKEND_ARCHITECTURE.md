# Backend Architecture
## Study Assistant: Session-Based RAG with Citations

**Chosen Architecture: Option 2 - Session-Based Collections**

---

## Architecture Decision

We use **session-based ChromaDB collections** where:
- Each chat session = one ChromaDB collection
- Documents are isolated per session
- Collection is deleted when session closes
- Full citation metadata (page, offset) for referencing

---

## Current Backend Flow (DEPRECATED)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CURRENT FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│   Frontend   │────▶│  /api/ingest │────▶│  Chunking    │────▶│  ChromaDB  │
│   (Nuxt)     │     │  -file       │     │  (text.py)   │     │  (global)  │
└──────────────┘     └──────────────┘     └──────────────┘     └────────────┘
       │                                                              │
       │                                                              │
       ▼                                                              ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────┐
│   /api/chat  │────▶│  Retriever   │────▶│  Hybrid      │────▶│  Query     │
│              │     │              │     │  Search      │     │  ChromaDB  │
└──────────────┘     └──────────────┘     └──────────────┘     └────────────┘
       │                                                              │
       ▼                                                              │
┌──────────────┐     ┌──────────────┐                                │
│   LLM        │◀────│  Context +   │◀───────────────────────────────┘
│  (OpenRouter)│     │  Prompt      │
└──────────────┘     └──────────────┘
       │
       ▼
┌──────────────┐
│   Response   │
│   + Citations│
└──────────────┘
```

### Problem with Current Flow

1. **Global collection**: All documents go into one "documents" collection
2. **No session isolation**: Documents from different users/chats mix together
3. **No cleanup**: Documents persist forever
4. **Citation metadata exists but isn't stored**: `text.py` creates metadata, `ingest.py` doesn't save it

---

## Proposed Architecture: Session-Based Collections

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NEW SESSION-BASED FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘

1. CREATE SESSION
   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────┐
   │   Frontend   │────▶│ POST /api/   │────▶│ Create ChromaDB Collection   │
   │              │     │ sessions     │     │ Name: "session_{uuid}"       │
   └──────────────┘     └──────────────┘     └──────────────────────────────┘
                              │
                              ▼
                        Return: { session_id: "abc123" }

2. UPLOAD DOCUMENTS (to session)
   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────┐
   │   Frontend   │────▶│ POST /api/   │────▶│ Store in session's collection│
   │  + session_id│     │ sessions/    │     │ WITH citation metadata       │
   │  + file      │     │ {id}/ingest  │     │ (page, offset, citation_id)  │
   └──────────────┘     └──────────────┘     └──────────────────────────────┘

3. CHAT (within session)
   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────┐
   │   Frontend   │────▶│ POST /api/   │────▶│ Retrieve from session's      │
   │  + session_id│     │ sessions/    │     │ collection ONLY              │
   │  + question  │     │ {id}/chat    │     │                              │
   └──────────────┘     └──────────────┘     └──────────────────────────────┘

4. CLOSE SESSION
   ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────┐
   │   Frontend   │────▶│ DELETE /api/ │────▶│ Delete ChromaDB Collection   │
   │  + session_id│     │ sessions/{id}│     │ All documents removed        │
   └──────────────┘     └──────────────┘     └──────────────────────────────┘
```

---

## API Design

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions` | Create new session (collection) |
| GET | `/api/sessions/{id}` | Get session info (documents list) |
| POST | `/api/sessions/{id}/ingest` | Upload document to session |
| POST | `/api/sessions/{id}/chat` | Chat within session |
| POST | `/api/sessions/{id}/flashcards` | Generate flashcards |
| DELETE | `/api/sessions/{id}` | Close session (delete collection) |

### Request/Response Examples

**Create Session:**
```bash
POST /api/sessions
Response: { "session_id": "abc123", "created_at": "..." }
```

**Upload Document:**
```bash
POST /api/sessions/abc123/ingest
Body: multipart/form-data with file
Response: {
  "document_id": "doc-uuid",
  "filename": "lecture.pdf",
  "chunks_ingested": 45,
  "pages": 20
}
```

**Chat:**
```bash
POST /api/sessions/abc123/chat
Body: { "question": "What is attention?", "mode": "chat" }
Response: {
  "answer": "Attention is... [1]",
  "citations": {
    "[1]": { "page": 15, "source": "lecture.pdf", "text": "..." }
  }
}
```

---

## Trade-offs of Session-Based Collections

### ✅ Pros

1. **Clean isolation**: Each user/chat has its own collection
2. **No data leakage**: Documents don't mix between sessions
3. **Easy cleanup**: Delete collection = delete all documents
4. **Simple scoping**: No need for `doc_id` filters, whole collection is the scope

### ⚠️ Cons

1. **No persistence**: Documents lost when session closes
2. **Re-upload required**: Same document must be uploaded for each new session
3. **More collections**: Many collections if many concurrent users
4. **Memory usage**: Each collection has overhead

### Alternative: Hybrid Approach

If you want persistence, consider:
- **User-based collections**: One collection per user (persists across sessions)
- **Document-level filtering**: Store all docs globally, filter by `session_id` or `user_id`

---

## Citation Metadata (Already Implemented!)

Your `text.py` already creates excellent citation metadata:

```python
# From utils/text.py - YOU ALREADY HAVE THIS!
doc.metadata.update({
    "chunk_index": idx,
    "start_offset": start,
    "end_offset": end,
    "citation_id": f"{document_id}:p{page_number}:c{idx}",
})
```

**The gap**: `ingest.py` doesn't store this in ChromaDB yet!

---

## Implementation Files

```
backend/app/
├── api/
│   ├── __init__.py          # Register blueprints (updated)
│   ├── sessions.py          # NEW: Session management ✅
│   ├── chat.py              # Legacy endpoint
│   └── ingest.py            # Legacy endpoint
├── rag/
│   ├── __init__.py          # Updated exports
│   ├── session_store.py     # NEW: Session-aware store ✅
│   ├── vector_store.py      # Original vector store
│   ├── bm25.py              # BM25 retriever
│   └── ...
├── utils/
│   └── text.py              # Chunking with citation metadata ✅
├── config.py                # Configuration (updated)
└── app.py                   # Flask app (updated)
```

---

## What We Implemented

### 1. SessionStore (`rag/session_store.py`)

- Creates/deletes ChromaDB collections per session
- Hybrid search (Dense + BM25) with RRF fusion
- Stores citation metadata (page, offset, citation_id)

### 2. Sessions API (`api/sessions.py`)

| Endpoint | Description |
|----------|-------------|
| `POST /api/sessions` | Create new session |
| `GET /api/sessions` | List all sessions |
| `GET /api/sessions/{id}` | Get session info |
| `DELETE /api/sessions/{id}` | Delete session |
| `POST /api/sessions/{id}/ingest` | Upload document |
| `POST /api/sessions/{id}/chat` | Chat with citations |
| `POST /api/sessions/{id}/flashcards` | Generate flashcards |

### 3. Citation Metadata (`utils/text.py`)

Already stores:
```python
{
    "document_id": "uuid",
    "source": "filename.pdf",
    "page_number": 15,
    "chunk_index": 3,
    "start_offset": 1234,
    "end_offset": 1890,
    "citation_id": "uuid:p15:c3"
}
```

---

## Usage Example

```bash
# 1. Create session
curl -X POST http://localhost:5000/api/sessions
# Returns: { "session_id": "abc123" }

# 2. Upload document
curl -X POST http://localhost:5000/api/sessions/abc123/ingest \
  -F "file=@lecture.pdf"
# Returns: { "document_id": "...", "chunks_ingested": 45 }

# 3. Chat
curl -X POST http://localhost:5000/api/sessions/abc123/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is attention?"}'
# Returns: { "answer": "Attention is... [1]", "citations": {...} }

# 4. Generate flashcards
curl -X POST http://localhost:5000/api/sessions/abc123/flashcards \
  -H "Content-Type: application/json" \
  -d '{"topic": "attention mechanism", "count": 5}'
# Returns: { "flashcards": [...], "citations": {...} }

# 5. Close session
curl -X DELETE http://localhost:5000/api/sessions/abc123
# Returns: { "message": "Session abc123 deleted" }
```
