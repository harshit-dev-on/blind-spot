"""Factory function and registry for universal AI providers."""

from blindspot.ai.base import BaseAIProvider
from blindspot.config.models import AIConfig


def create_provider(config: AIConfig) -> BaseAIProvider:
    """Instantiate a universal AI provider from an AIConfig object."""
    provider_name = config.provider.lower().strip()
    if provider_name in ("antigravity", "agy"):
        from blindspot.ai.providers.antigravity import AntigravityProvider
        return AntigravityProvider(
            model=config.model or "antigravity-brain",
            base_url=config.base_url,
            timeout=config.timeout,
        )

    if provider_name == "ollama":
        target_model = config.model or "gemma4:e4b"
        if target_model.strip().lower() in ("gemma4", "gemma", "default"):
            target_model = "gemma4:e4b"
        try:
            from blindspot.ai.adapter import UnifiedAIAdapter
        except ImportError:
            UnifiedAIAdapter = None
        if UnifiedAIAdapter is not None:
            return UnifiedAIAdapter(
                provider="ollama",
                model=target_model,
                base_url=config.base_url,
                api_key=config.api_key,
                api_key_env=config.api_key_env,
                timeout=config.timeout,
            )
        from blindspot.ai.providers.ollama import OllamaProvider
        return OllamaProvider(
            model=target_model,
            base_url=config.base_url,
            timeout=config.timeout,
        )

    if provider_name in ("custom", "openai_compatible"):
        try:
            from blindspot.ai.adapter import UnifiedAIAdapter
        except ImportError:
            UnifiedAIAdapter = None
        if UnifiedAIAdapter is not None:
            return UnifiedAIAdapter(
                provider="custom",
                model=config.model or "gpt-4o-mini",
                base_url=config.base_url,
                api_key=config.api_key,
                api_key_env=config.api_key_env,
                timeout=config.timeout,
            )
        from blindspot.ai.providers.openai_compatible import OpenAICompatibleProvider
        return OpenAICompatibleProvider(
            model=config.model or "gpt-4o-mini",
            base_url=config.base_url,
            api_key=config.api_key,
            api_key_env=config.api_key_env or "OPENAI_API_KEY",
            timeout=config.timeout,
        )

    if provider_name in ("gemini", "openai", "anthropic", "openrouter"):
        try:
            from blindspot.ai.adapter import UnifiedAIAdapter
        except ImportError as exc:
            raise RuntimeError(
                "The hosted-model adapter is missing from this installation. "
                "Repair it with: python -m pip install --upgrade blindspot1"
            ) from exc
        return UnifiedAIAdapter(
            provider=provider_name,
            model=config.model,
            base_url=config.base_url,
            api_key=config.api_key,
            api_key_env=config.api_key_env,
            timeout=config.timeout,
        )

    try:
        from blindspot.ai.adapter import UnifiedAIAdapter
    except ImportError as exc:
        raise RuntimeError(
            "This provider's adapter is missing from the installation. "
            "Repair it with: python -m pip install --upgrade blindspot1"
        ) from exc

    return UnifiedAIAdapter(
        provider=provider_name,
        model=config.model,
        base_url=config.base_url,
        api_key=config.api_key,
        api_key_env=config.api_key_env,
        timeout=config.timeout,
    )
