"""Factory for creating LLM adapters."""

from typing import Optional

from app.llm.base import LLMAdapter
from app.llm.gemini_adapter import GeminiAdapter


def create_llm_adapter(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> LLMAdapter:
    """Create and return appropriate LLM adapter based on provider.

    Args:
        provider: Provider name ("mock", "gemini")
        api_key: API key for the provider (not needed for mock)
        model: Optional model name override

    Returns:
        Initialized LLM adapter instance

    Raises:
        ValueError: If provider is unknown or if API key is missing for real providers
    """
    provider = provider.lower()

    if provider == "gemini":
        if not api_key:
            raise ValueError("Gemini API key is required")
        return GeminiAdapter(
            api_key=api_key,
            model=model or "gemini-2.5-flash"
        )

    else:
        raise ValueError(
            f"Unknown LLM provider: {provider}. "
            f"Supported providers: gemini"
        )
