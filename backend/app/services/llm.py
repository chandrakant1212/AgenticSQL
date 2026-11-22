"""
Configurable LLM factory.

Provides a unified interface for initializing LLM providers.
The provider and model are configured via environment variables.

Supported providers:
- openai: GPT-4o, GPT-4o-mini, etc.
- google_genai: Gemini 2.0 Flash, Gemini 2.5 Pro, etc.
- anthropic: Claude Sonnet, etc.
- groq: Llama 3.x, etc.
"""

import logging
from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_llm(
    temperature: float | None = None,
    model: str | None = None,
    provider: str | None = None,
) -> BaseChatModel:
    """
    Create and return a configured LLM instance.

    Args:
        temperature: Override temperature (defaults to config value).
        model: Override model name (defaults to config value).
        provider: Override provider (defaults to config value).

    Returns:
        A LangChain BaseChatModel instance.
    """
    settings = get_settings()
    _provider = provider or settings.LLM_PROVIDER
    _model = model or settings.LLM_MODEL
    _temperature = temperature if temperature is not None else settings.LLM_TEMPERATURE
    _api_key = settings.LLM_API_KEY

    logger.info("Initializing LLM: provider=%s, model=%s", _provider, _model)

    if _provider == "openai":
        from langchain_openai import ChatOpenAI
        
        kwargs = {
            "model": _model,
            "temperature": _temperature,
            "api_key": _api_key,
        }
        if settings.LLM_BASE_URL:
            kwargs["base_url"] = settings.LLM_BASE_URL
            
        return ChatOpenAI(**kwargs)

    elif _provider == "google_genai":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=_model,
            temperature=_temperature,
            google_api_key=_api_key,
        )

    elif _provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=_model,
            temperature=_temperature,
            api_key=_api_key,
        )

    elif _provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=_model,
            temperature=_temperature,
            api_key=_api_key,
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider: '{_provider}'. "
            f"Supported: openai, google_genai, anthropic, groq"
        )


@lru_cache()
def get_default_llm() -> BaseChatModel:
    """Get a cached default LLM instance using application settings."""
    return get_llm()
