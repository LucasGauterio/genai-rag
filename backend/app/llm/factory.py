from langchain_openai import ChatOpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, LLM_MODEL, LLM_TEMPERATURE

def get_llm(model_name: str = None, temperature: float = None) -> ChatOpenAI:
    return ChatOpenAI(
        model=model_name or LLM_MODEL,
        temperature=temperature if temperature is not None else LLM_TEMPERATURE,
        openai_api_key=OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
    )
