from llm.factory import get_llm

def call_llm(prompt: str) -> str:
    llm = get_llm()
    # Execute and return string content
    return llm.invoke(prompt).content

# Keep compatibility with existing codebase references
call_openrouter = call_llm

__all__ = ["call_openrouter", "call_llm"]

