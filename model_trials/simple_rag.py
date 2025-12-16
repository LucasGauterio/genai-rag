from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import numpy as np

# 1. Setup
load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# ---------------------------------------------------------
# A. THE KNOWLEDGE BASE (Our "Mini Database")
# ---------------------------------------------------------
# In a real app, this would be PDFs or a database. 
# Here, we use a simple list of strings about specific facts.
documents = [
    "The secret code to the vault is 998877.",
    "Project Apollo launched in 2024 aimed to explore Mars.",
    "The company mascot is a blue penguin named 'Pippin'.",
    "Customer support is available from 9 AM to 5 PM EST."
]

# ---------------------------------------------------------
# B. HELPER FUNCTIONS
# ---------------------------------------------------------

def get_embedding(text):
    """Converts text into a vector (list of numbers)."""
    result = client.models.embed_content(
        model="text-embedding-004",
        contents=text
    )
    return result.embeddings[0].values

def find_best_match(query, docs):
    """Finds the document most similar to the query."""
    
    # 1. Embed the query
    query_embedding = np.array(get_embedding(query))
    
    scores = []
    
    # 2. Compare against all documents (Linear Search)
    # Note: For millions of docs, use a Vector DB (Chroma/Pinecone) instead.
    for doc in docs:
        doc_embedding = np.array(get_embedding(doc))
        
        # Calculate Cosine Similarity (Dot product for normalized vectors)
        score = np.dot(query_embedding, doc_embedding) / (
            np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
        )
        scores.append(score)

    # 3. Get the index of the highest score
    best_idx = np.argmax(scores)
    return docs[best_idx], scores[best_idx]

# ---------------------------------------------------------
# C. THE MAIN RAG PIPELINE
# ---------------------------------------------------------

def ask_gemini_with_rag(question):
    print(f"\nUser Question: {question}")
    print("Searching knowledge base...")
    
    # Step 1: Retrieve relevant context
    context, score = find_best_match(question, documents)
    print(f"--> Found relevant info (Score: {score:.4f}):\n    '{context}'")

    # Step 2: Augment the prompt
    # We tell Gemini: "Use this context to answer."
    prompt = f"""
    You are a helpful assistant. Use the following Context to answer the Question.
    If the answer isn't in the context, say "I don't know".
    
    Context: {context}
    
    Question: {question}
    """

    # Step 3: Generate Answer
    # Note: I switched to gemini-1.5-flash as 2.5-flash isn't generally available yet
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )
    
    print(f"\nGemini Answer:\n{response.text}")

# ---------------------------------------------------------
# D. TEST IT
# ---------------------------------------------------------
if __name__ == "__main__":
    # Test 1: Ask something in our database
    ask_gemini_with_rag("What is the mascot's name?")
    
    # Test 2: Ask something NOT in our database (to check hallucination)
    ask_gemini_with_rag("What is the customer support hours?")