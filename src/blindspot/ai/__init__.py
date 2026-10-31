"""Universal AI provider integration layer for BlindSpot."""

from blindspot.ai.base import BaseAIProvider, extract_json_string, mask_api_key
from blindspot.ai.exceptions import (
    AIAuthenticationError,
    AIConnectionError,
    AIModelNotFoundError,
    AIProviderError,
    AIStructuredOutputError,
    AITimeoutError,
)
from blindspot.ai.factory import create_provider
from blindspot.ai.models import AIResponse, ProviderStatus
from blindspot.ai.providers.antigravity import AntigravityProvider
from blindspot.ai.providers.ollama import OllamaProvider
from blindspot.ai.providers.openai_compatible import OpenAICompatibleProvider

CURATED_MODELS = {
    "ollama": ["gemma4", "gemma4:12b", "gemma4:e4b", "llama3.2", "mistral", "phi3", "qwen2.5"],
    "gemini": ["gemini-2.5-flash"],
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "anthropic": ["claude-3-5-sonnet-20241022"],
    "openrouter": ["meta-llama/llama-3.1-8b-instruct"],
    "custom": [],
}
DEFAULT_BASE_URLS = {
    "ollama": "http://localhost:11434",
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}
DEFAULT_KEY_ENVS = {
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "custom": "CUSTOM_API_KEY",
    "openai_compatible": "OPENAI_API_KEY",
}
DEFAULT_PROVIDER_MODELS = {
    "ollama": "gemma4:e4b",
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-20241022",
    "openrouter": "meta-llama/llama-3.1-8b-instruct",
    "custom": "default",
    "openai_compatible": "gpt-4o-mini",
}

def get_models_for_provider(provider: str, base_url: str = None):
    """Return curated model choices, discovering local Ollama models when possible."""
    if provider.lower().strip() == "ollama":
        try:
            import httpx
            response = httpx.get(f"{(base_url or DEFAULT_BASE_URLS['ollama']).rstrip('/')}/api/tags", timeout=4.0)
            if response.status_code == 200:
                models = [model.get("name", "") for model in response.json().get("models", [])]
                if models:
                    return models
        except Exception:
            pass
    return CURATED_MODELS.get(provider.lower().strip(), [])

try:
    from blindspot.ai.adapter import (
        CURATED_MODELS,
        DEFAULT_BASE_URLS,
        DEFAULT_KEY_ENVS,
        DEFAULT_PROVIDER_MODELS,
        UnifiedAIAdapter,
        get_models_for_provider,
    )
except ImportError:
    UnifiedAIAdapter = None
else:
    pass

__all__ = [
    "AIAuthenticationError",
    "AIConnectionError",
    "AIModelNotFoundError",
    "AIProviderError",
    "AIResponse",
    "AIStructuredOutputError",
    "AITimeoutError",
    "AntigravityProvider",
    "BaseAIProvider",
    "CURATED_MODELS",
    "DEFAULT_BASE_URLS",
    "DEFAULT_KEY_ENVS",
    "DEFAULT_PROVIDER_MODELS",
    "OllamaProvider",
    "OpenAICompatibleProvider",
    "ProviderStatus",
    "UnifiedAIAdapter",
    "create_provider",
    "extract_json_string",
    "get_models_for_provider",
    "mask_api_key",
]
