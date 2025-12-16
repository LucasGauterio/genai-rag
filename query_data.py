# query_data.py
import argparse
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from openai import OpenAI

load_dotenv()

CHROMA_PATH = "chroma_db"

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

def main():
    # 1. Get the user's question from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The question text.")
    args = parser.parse_args()
    query_text = args.query_text

    # 2. Prepare the DB
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
    # 3. Search the DB
    # k=3 means "find the top 3 most relevant chunks"
    results = db.similarity_search_with_relevance_scores(query_text, k=3)

    if len(results) == 0 or results[0][1] < 0.5:
        print(f"Unable to find matching results for: {query_text}")
        return

    # 4. Combine Context and Question
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # 5. Send to Gemini
    # Note: We use gemini-2.5-flash as it's efficient for this
    # model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    # response_text = model.invoke(prompt)

    client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    # read from .env file
    api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    # First API call with reasoning
    response = client.chat.completions.create(
    model="nvidia/nemotron-3-nano-30b-a3b:free",
    messages=[
            {
                "role": "user",
                "content": prompt
            }
            ],
    extra_body={"reasoning": {"enabled": True}}
    )
    response = response.choices[0].message
    print("Answer:")
    print(response.content)
    # 6. Print the result
    # print("\nAnswer:")
    # print(response_text.content)
    
    # Optional: Print the sources
    sources = [doc.metadata.get("source", None) for doc, _score in results]
    print(f"\nSources: {sources}")

if __name__ == "__main__":
    main()