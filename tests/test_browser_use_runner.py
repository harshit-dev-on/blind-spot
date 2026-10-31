"""Tests for browser-use agent and runner integration."""

import pytest
from unittest.mock import MagicMock, patch

from blindspot.execution.browser_use_runner import (
    BrowserUsePersonaRunner,
    BrowserUseTaskAgent,
    build_persona_system_extension,
    is_browser_use_available,
    resolve_browser_use_llm,
)
from blindspot.execution.runner import PersonaTestRunner
from blindspot.personas.models import Persona, PersonaPlan, PersonaTask


def test_is_browser_use_available():
    """Verify that browser-use package is detected."""
    with patch.dict("sys.modules", {"browser_use": MagicMock()}):
        assert is_browser_use_available() is True


def test_build_persona_system_extension():
    """Verify system extension formatting with persona traits and goals."""
    persona = Persona(
        id="p1",
        name="Alex River",
        description="An elderly user trying to purchase gifts online.",
        experience_level="Beginner",
        accessibility_needs="Screen Magnifier, High Contrast",
        goals=["Purchase a blue shirt"],
        likely_difficulties=["Small clickable buttons", "Low contrast text"],
        tasks=[
            PersonaTask(
                id="t1",
                objective="Find a blue shirt",
                success_criteria=["Blue shirt detail page loaded"],
                evidence_to_collect=["Screenshot of product page"],
            )
        ],
    )

    prompt = build_persona_system_extension(persona)
    assert "Alex River" in prompt
    assert "elderly user" in prompt.lower()
    assert "Screen Magnifier" in prompt
    assert "Small clickable buttons" in prompt
    assert "NEVER enter real personal passwords" in prompt


def test_persona_test_runner_engine_selection():
    """Verify PersonaTestRunner initializes with browser-use engine."""
    mock_provider = MagicMock()
    mock_provider.model = "gpt-4o-mini"

    runner = PersonaTestRunner(
        provider=mock_provider,
        engine="browser-use",
    )
    assert runner.engine == "antigravity"

    auto_runner = PersonaTestRunner(
        provider=mock_provider,
        engine="auto",
    )
    assert auto_runner.engine == "antigravity"


def test_resolve_browser_use_llm():
    """Verify LLM resolver creates a ChatLiteLLM instance."""
    mock_provider = MagicMock()
    mock_provider.model = "openai/gpt-4o-mini"
    mock_provider._api_key = "test-key"
    mock_provider._base_url = "https://api.openai.com/v1"

    mock_chat_class = MagicMock()
    mock_chat_class.return_value = MagicMock(model="openai/gpt-4o-mini")
    mock_mod = MagicMock(ChatLiteLLM=mock_chat_class)

    with patch.dict("sys.modules", {"browser_use": MagicMock(), "browser_use.llm.litellm.chat": mock_mod}):
        llm = resolve_browser_use_llm(mock_provider)
        assert llm is not None
        assert "gpt-4o-mini" in llm.model
