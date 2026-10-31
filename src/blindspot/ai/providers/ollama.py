"""Ollama AI provider integration for local model inference."""

import time
from typing import Any, Dict, List, Optional
import httpx

from blindspot.ai.base import BaseAIProvider, strip_thinking_tags
from blindspot.ai.exceptions import (
    AIConnectionError,
    AIModelNotFoundError,
    AITimeoutError,
    AIProviderError,
)
from blindspot.ai.models import AIResponse, ProviderStatus


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "gemma4:e4b"


class OllamaProvider(BaseAIProvider):
    """Local model provider using Ollama HTTP API."""

    def __init__(
        self,
        model: str = DEFAULT_OLLAMA_MODEL,
        base_url: Optional[str] = None,
        timeout: float = 90.0,
    ) -> None:
        effective_url = base_url or DEFAULT_OLLAMA_URL
        chosen_model = model.strip() if model else DEFAULT_OLLAMA_MODEL
        super().__init__(model=chosen_model, base_url=effective_url, timeout=timeout)

    @property
    def name(self) -> str:
        return "ollama"

    def start_session(self) -> bool:
        """Start running and warm/preload the Gemma 4 e4b model into memory for inspection."""
        target_model = self._resolve_installed_model() or self.model
        try:
            with httpx.Client(timeout=min(self.timeout, 120.0)) as client:
                res = client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": target_model, "keep_alive": "30m"},
                )
                return res.status_code == 200
        except Exception:
            return False

    def stop_session(self) -> bool:
        """Stop running and unload the model from memory when inspection finishes."""
        target_model = self._resolve_installed_model() or self.model
        success = False
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": target_model, "keep_alive": 0},
                )
                success = (res.status_code == 200)
        except Exception:
            pass

        try:
            import subprocess
            subprocess.run(["ollama", "stop", target_model], capture_output=True, timeout=5)
            success = True
        except Exception:
            pass

        return success

    def check_health(self) -> ProviderStatus:
        """Check if local Ollama server is running and the model is loaded."""
        tags_url = f"{self.base_url}/api/tags"
        start_time = time.perf_counter()

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(tags_url)
                latency = round((time.perf_counter() - start_time) * 1000, 2)

                if res.status_code != 200:
                    return ProviderStatus(
                        provider=self.name,
                        model=self.model,
                        base_url=self.base_url,
                        is_reachable=False,
                        model_available=False,
                        latency_ms=latency,
                        message=f"Ollama server returned HTTP {res.status_code}: {res.text[:100]}",
                    )

                data = res.json()
                models_list = data.get("models", [])
                available_names: List[str] = [m.get("name", "") for m in models_list]

                # Check if configured model matches (e.g. 'gemma4:e4b' or family 'gemma4')
                target = self.model.lower()
                base_family = target.split(":")[0] if ":" in target else target
                model_found = any(
                    target == name.lower()
                    or name.lower() == base_family
                    or name.lower().startswith(f"{base_family}:")
                    or name.lower().startswith(f"{target}:")
                    for name in available_names
                )

                if not model_found:
                    return ProviderStatus(
                        provider=self.name,
                        model=self.model,
                        base_url=self.base_url,
                        is_reachable=True,
                        model_available=False,
                        latency_ms=latency,
                        available_models=available_names,
                        message=(
                            f"Ollama is running, but model '{self.model}' is not installed.\n"
                            f"Installed models: {', '.join(available_names) if available_names else 'None'}.\n"
                            f"Run 'ollama pull {self.model}' to download it."
                        ),
                    )

                return ProviderStatus(
                    provider=self.name,
                    model=self.model,
                    base_url=self.base_url,
                    is_reachable=True,
                    model_available=True,
                    latency_ms=latency,
                    available_models=available_names,
                    message=f"Connected to Ollama. Model '{self.model}' is ready ({latency}ms).",
                )

        except httpx.ConnectError:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url,
                is_reachable=False,
                model_available=False,
                message=(
                    f"Could not connect to Ollama server at {self.base_url}.\n"
                    "Ensure Ollama is installed and running (e.g. run 'ollama serve' or open the Ollama app)."
                ),
            )
        except httpx.TimeoutException:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url,
                is_reachable=False,
                model_available=False,
                message=f"Connection to Ollama server at {self.base_url} timed out ({self.timeout}s).",
            )
        except Exception as exc:
            return ProviderStatus(
                provider=self.name,
                model=self.model,
                base_url=self.base_url,
                is_reachable=False,
                model_available=False,
                message=f"Error connecting to Ollama: {exc}",
            )

    def _resolve_installed_model(self) -> Optional[str]:
        """Attempt to find an exact or tagged match for the configured model name."""
        try:
            with httpx.Client(timeout=min(self.timeout, 5.0)) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models_list = res.json().get("models", [])
                    available_names = [m.get("name", "") for m in models_list]
                    target = self.model.lower()
                    base_family = target.split(":")[0] if ":" in target else target
                    for name in available_names:
                        if name.lower() == target:
                            return name
                    for name in available_names:
                        if name.lower().startswith(f"{target}:"):
                            return name
                    for name in available_names:
                        if name.lower() == base_family or name.lower().startswith(f"{base_family}:"):
                            return name
        except Exception:
            pass
        return None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        format_json: bool = False,
        image_b64: Optional[str] = None,
        images: Optional[List[str]] = None,
    ) -> AIResponse:
        """Send chat completion request to Ollama with text and multimodal vision support."""
        chat_url = f"{self.base_url}/api/chat"

        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})

        user_msg: Dict[str, Any] = {"role": "user", "content": prompt.strip()}

        # Collect images (stripping data URI header if present for Ollama's raw base64 requirement)
        img_list: List[str] = []
        if image_b64 and image_b64.strip():
            raw_b64 = image_b64.strip()
            if "," in raw_b64 and "base64" in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1].strip()
            img_list.append(raw_b64)

        if images:
            for img in images:
                if img and img.strip():
                    raw_b64 = img.strip()
                    if "," in raw_b64 and "base64" in raw_b64:
                        raw_b64 = raw_b64.split(",", 1)[1].strip()
                    img_list.append(raw_b64)

        if img_list:
            user_msg["images"] = img_list

        messages.append(user_msg)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": temperature,
            },
        }

        if format_json:
            payload["format"] = "json"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(chat_url, json=payload)

                if res.status_code == 404:
                    # Attempt smart resolution if model has a variant or tag installed
                    resolved = self._resolve_installed_model()
                    if resolved and resolved != payload["model"]:
                        payload["model"] = resolved
                        res = client.post(chat_url, json=payload)

                if res.status_code == 404:
                    raise AIModelNotFoundError(
                        f"Model '{self.model}' not found on Ollama server.",
                        provider=self.name,
                        suggestion=f"Run 'ollama pull {self.model}' in your terminal to install the model.",
                    )

                if res.status_code != 200:
                    raise AIProviderError(
                        f"Ollama returned HTTP error {res.status_code}: {res.text}",
                        provider=self.name,
                    )

                data = res.json()
                raw_content = data.get("message", {}).get("content", "")
                content = strip_thinking_tags(raw_content)
                usage = {
                    "prompt_eval_count": data.get("prompt_eval_count"),
                    "eval_count": data.get("eval_count"),
                    "total_duration": data.get("total_duration"),
                }

                return AIResponse(
                    content=content,
                    model=data.get("model", self.model),
                    provider=self.name,
                    usage=usage,
                    raw_response=data,
                )

        except httpx.ConnectError as exc:
            raise AIConnectionError(
                f"Cannot connect to Ollama at {self.base_url}.",
                provider=self.name,
                suggestion="Make sure the Ollama service is active. Run 'ollama serve' in your terminal.",
            ) from exc
        except httpx.TimeoutException as exc:
            raise AITimeoutError(
                f"Ollama request timed out after {self.timeout} seconds.",
                provider=self.name,
                suggestion="Increase timeout in configuration or verify model is loaded into memory.",
            ) from exc
        except (AIProviderError, AIModelNotFoundError, AIConnectionError, AITimeoutError):
            raise
        except Exception as exc:
            raise AIProviderError(
                f"Unexpected error communicating with Ollama: {exc}",
                provider=self.name,
            ) from exc
