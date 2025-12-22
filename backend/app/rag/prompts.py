def build_prompt(context: str, question: str) -> str:
    return f"""
You are an assistant answering questions using the provided context only.

Context:
{context}

Question:
{question}

If the answer is not in the context, say you do not know.
""".strip()
