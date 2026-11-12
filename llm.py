import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_llm():
    """LLM configurable par variables d'environnement (voir .env.example)."""
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    model = os.getenv("LLM_MODEL")

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model or "llama-3.3-70b-versatile", temperature=0)
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model or "gpt-4o-mini", temperature=0)
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model=model or "claude-sonnet-4-6", temperature=0)