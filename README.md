# GenAI Flashcard Generator

This project allows users to generate flashcards from uploaded documents using a Retrieval-Augmented Generation (RAG) pipeline. It features a Python Flask backend for processing and a Vue/Nuxt 4 frontend for the user interface.

## Prerequisites

Before starting, ensure you have the following installed:
-   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for local embeddings with ollama)
-   [Python 3.10+](https://www.python.org/downloads/)
-   [Node.js](https://nodejs.org/) (Latest LTS recommended)
-   [pnpm](https://pnpm.io/installation) (Recommended package manager)

## Configuration

The application uses environment variables for configuration. Example files are provided for both the backend and frontend.

### 1. Global / Backend Configuration
Copy `.env.example` in the root directory to `.env`:
```bash
cp .env.example .env
```
Open the `.env` file and configure your settings:
*   **LLM Provider**: Choose `gemini` (default) or `openrouter`.
*   **API Keys**: Enter your `GEMINI_API_KEY` or `OPENROUTER_API_KEY` depending on the provider chosen.
*   **Ollama Settings**: Defaults are set for local Ollama via Docker (`http://localhost:11434` and `nomic-embed-text`).

### 2. Frontend Configuration
Copy `frontend/.env.example` to `frontend/.env`:
```bash
cd frontend
cp .env.example .env
```
Ensure the API endpoint points to the backend server:
```env
NUXT_BACKEND_API_URL=http://localhost:5000
```

---

## Installation & Running

You can choose between the **Automated Setup & Execution** (recommended) or the **Manual Step-by-Step Setup**.

### Option A: Automated setup (Recommended)

Helper scripts in the `scripts/` directory automate the configuration, dependency installations, virtual environment setup, and start/stop tasks.

#### 1. Run Setup
Run the setup script from the root directory to create `.env` files, build the backend python virtual environment, and install all dependencies:
*   **Windows (PowerShell)**:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\scripts\setup_dev.ps1
    ```
*   **macOS / Linux / Windows (Manual Python)**:
    ```bash
    python scripts/setup_dev.py
    ```

#### 2. Start the Application Stack
Once setup is complete and your API key is configured in the root `.env`, launch all processes simultaneously (Docker, Flask backend, and Nuxt dev server):
*   **Windows (PowerShell)**:
    ```powershell
    powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1
    ```
*   **macOS / Linux / Windows (Manual Python)**:
    ```bash
    python scripts/run_all.py
    ```
*Press `Ctrl+C` in the terminal to cleanly shut down all services (including Docker).*

---

### Option B: Manual Setup

If you prefer to configure and run the services individually, follow these steps:

#### 1. Start Services (Ollama)
Start the local embedding service using Docker Compose:
```bash
docker compose up -d
```
*Note: The first run will automatically pull the `nomic-embed-text` model, which might take a few minutes.*

#### 2. Backend Setup (Flask)
From the root directory, navigate to the backend application:
```bash
cd backend/app
```
1.  **Create and activate a virtual environment**:
    *   **macOS / Linux**:
        ```bash
        python -m venv venv
        source venv/bin/activate
        ```
    *   **Windows (Command Prompt)**:
        ```cmd
        python -m venv venv
        venv\Scripts\activate.bat
        ```
    *   **Windows (PowerShell)**:
        ```powershell
        python -m venv venv
        .\venv\Scripts\Activate.ps1
        ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Start the server**:
    ```bash
    python app.py
    ```
    The Flask server runs at `http://localhost:5000`.

#### 3. Frontend Setup (Nuxt 4)
From the root directory, navigate to the frontend application:
```bash
cd frontend
```
1.  **Install node dependencies**:
    ```bash
    pnpm install
    ```
2.  **Start the Nuxt dev server**:
    ```bash
    pnpm run dev
    ```
    The frontend runs at `http://localhost:3000`.

---

## Usage

1.  Open your browser and navigate to `http://localhost:3000`.
2.  Click **"New Session"** in the left sidebar to start.
3.  Upload a PDF, TXT, or MD document in the main panel.
4.  The system will extract text, chunk it semantically, embed it locally with Ollama, and save it to ChromaDB.
5.  Use the **Chat Panel** to ask questions (showing citations with hoverable source details) or use the **Flashcard Panel** to generate and study flashcards based on the document's concepts.
