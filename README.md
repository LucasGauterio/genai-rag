# GenAI Flashcard Generator

This project allows users to generate flashcards from uploaded documents using a Retrieval-Augmented Generation (RAG) pipeline. It features a Python Flask backend for processing and a Vue/Nuxt 3 frontend for the user interface.

## Prerequisites

Before starting, ensure you have the following installed:
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for local embeddings with ollama)
-   [Python 3.10+](https://www.python.org/downloads/)
-   [Node.js](https://nodejs.org/) (Latest LTS recommended)
-   [pnpm](https://pnpm.io/installation) (Recommended package manager)

## Configuration

### Backend Configuration

1.  Create a `.env` file in the root directory.
2.  Add the following environment variables:

    ```env
    # LLM Provider (OpenRouter)
    OPENROUTER_API_KEY=your_openrouter_api_key_here
    OPENROUTER_MODEL=openai/gpt-4o-mini

    # Local Embeddings (Ollama)
    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_EMBEDDING_MODEL=nomic-embed-text
    ```

### Frontend Configuration

1.  Create a `.env` file in the `frontend` directory.
2.  Add the following environment variable:

    ```env
    # Backend API URL
    NUXT_BACKEND_API_URL=http://localhost:5000
    ```

    You can copy `.env.example` as a starting point:
    
    ```bash
    cd frontend
    cp .env.example .env
    ```

## Installation & Running

The application consists of three parts that need to be running simultaneously: internal services (Docker), the backend, and the frontend.

### 1. Start Services (Ollama)

Start the local embedding service using Docker Compose.

```bash
docker-compose up -d
```
*Note: The first run will automatically pull the `nomic-embed-text` model, which may take a few minutes.*

### 2. Backend Setup (Flask)

Open a new terminal window and navigate to the backend application directory:

```bash
cd backend/app
```

1.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Start the server**:
    ```bash
    python app.py
    ```
    The backend will run at `http://localhost:5000`.

### 3. Frontend Setup (Nuxt 3)

Open a new terminal window and navigate to the frontend directory:

```bash
cd frontend
```

1.  **Install dependencies**:
    ```bash
    pnpm install
    ```

2.  **Start the development server**:
    ```bash
    pnpm run dev
    ```
    The frontend will run at `http://localhost:3000`.

## Usage

1.  Open your browser and navigate to `http://localhost:3000`.
2.  Upload a PDF document via the interface.
3.  The system will process the file using the local embedding model.
4.  Generate specific flashcards or interact with your document.
