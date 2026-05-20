from config import (
    LLM_PROVIDER,
    OPENROUTER_API_KEY,
    GEMINI_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
)

def get_llm(model_name: str = None, temperature: float = None):
    temp = temperature if temperature is not None else LLM_TEMPERATURE
    model = model_name or LLM_MODEL
    
    if LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model,
            temperature=temp,
            google_api_key=GEMINI_API_KEY,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temp,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
        )

