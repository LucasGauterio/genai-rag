# Project Setup and Installation

This project uses Python to manage documents, create embeddings, and query them using a vector database.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

To install the necessary packages, run the following command:

```bash
pip install python-dotenv langchain-community pypdf langchain-text-splitters langchain-chroma langchain-huggingface langchain-google-genai openai langchain
```

## Environment Variables

Create a `.env` file in the root directory and add your API keys:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

## Usage

1.  **Create the Database**:
    Run the `create_db.py` script to load documents and create the vector database.
    ```bash
    python create_db.py
    ```

2.  **Query the Data**:
    Run the `query_data.py` script with your question.
    ```bash
    python query_data.py "Your question here"
    ```
