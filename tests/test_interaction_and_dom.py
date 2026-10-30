"""Tests for screenshot-first Markdown interaction logging without raw HTML code dumps."""

from pathlib import Path
import pytest

from blindspot.utils.html_formatter import format_html
from blindspot.execution.models import (
    ActionExecutionRecord,
    ActionType,
    AgentAction,
    ExecutionRunResult,
    PersonaExecutionResult,
    TaskExecutionResult,
    TaskStatus,
)
from blindspot.personas.models import Persona, PersonaPlan, PersonaTask
from blindspot.reporting.interaction_renderer import (
    render_full_run_interaction_markdown,
    render_task_interaction_markdown,
)


def test_html_formatter_indents_nested_dom():
    """Verify raw HTML is transformed into formatted, readable HTML code."""
    raw = '<html><head><title>Online Store</title></head><body><header><nav><a href="/home">Home</a><input type="text" name="q" placeholder="Search products..."/></nav></header><main><div><h1>Featured</h1><button type="button">Buy Now</button></div></main></body></html>'

    formatted = format_html(raw, indent_spaces=2)

    assert "<html>" in formatted
    assert "<title>" in formatted
    assert "  <head>" in formatted or "\n" in formatted
    assert 'placeholder="Search products..."' in formatted
    assert "<button type=\"button\">" in formatted
    assert "</button>" in formatted
    assert "</main>" in formatted
    lines = formatted.splitlines()
    assert len(lines) >= 8


def test_render_task_interaction_markdown(tmp_path: Path):
    """Verify task interaction is cleanly formatted into Markdown with screenshot embeds and no raw HTML code dumps."""
    task = PersonaTask(
        id="task_1",
        objective="Search for winter boots using the header input",
        success_criteria=["Search input focused", "Results listed"],
        evidence_to_collect=["Input focus screenshot"],
    )
    persona = Persona(
        id="alex_keyboard",
        name="Alex River",
        description="Keyboard-only shopper who uses screen magnifiers.",
        experience_level="Intermediate",
        accessibility_needs="Screen Magnifier, High Focus Contrast",
        goals=["Buy winter boots"],
        likely_difficulties=["Small clickable buttons", "Missing focus outline"],
        tasks=[task],
    )

    action = AgentAction(
        action=ActionType.CLICK,
        target="@e2",
        reasoning="Clicking the search input field to activate typing mode.",
    )
    rec = ActionExecutionRecord(
        step=1,
        action=action,
        success=True,
        page_url="https://example.com/store",
        page_title="Store Home",
        screenshot_path=str(tmp_path / "step1.png"),
        target_element={"tag": "input", "ref": "@e2", "placeholder": "Search..."},
    )

    task_res = TaskExecutionResult(
        task_id="task_1",
        persona_id="alex_keyboard",
        task_objective="Search for winter boots using the header input",
        status=TaskStatus.SUCCESS,
        start_time="2026-10-29T11:00:00Z",
        end_time="2026-10-29T11:00:15Z",
        initial_url="https://example.com/store",
        final_url="https://example.com/store?q=boots",
        actions_taken=[rec],
        evidence=["Observed search input accepted keystrokes"],
    )

    md = render_task_interaction_markdown(persona, task, task_res, output_dir=tmp_path)

    assert "Persona: Alex River" in md
    assert "Task: Search for winter boots using the header input" in md
    assert "Observable Success Criteria" in md
    assert "#### Step 1: `CLICK` → `@e2` (✓ SUCCESS)" in md
    assert "Clicking the search input field" in md
    assert "![Step 1 Screenshot](step1.png)" in md
    assert "Task Outcome & Verified Evidence" in md
    assert "SUCCESS" in md
    # Ensure no raw HTML dump block is embedded
    assert "```html" not in md


def test_render_full_run_interaction_markdown(tmp_path: Path):
    """Verify multi-persona run interaction markdown file aggregates visual journeys properly."""
    task = PersonaTask(
        id="t1",
        objective="Verify primary navigation links",
        success_criteria=["Navigation active"],
        evidence_to_collect=["Navigation links list"],
    )
    persona = Persona(
        id="p1",
        name="Chloe Davis",
        description="Tech enthusiast exploring navigation flows.",
        experience_level="Intermediate",
        goals=["Navigate home"],
        likely_difficulties=["Dropdown delays"],
        tasks=[task],
    )
    plan = PersonaPlan(
        personas=[persona],
        website_url="https://example.com",
        context="Test Marketplace",
        website_summary="Test Marketplace",
    )

    task_res = TaskExecutionResult(
        task_id="t1",
        persona_id="p1",
        task_objective="Verify primary navigation links",
        status=TaskStatus.SUCCESS,
        start_time="2026-10-29T11:00:00Z",
        end_time="2026-10-29T11:00:10Z",
        initial_url="https://example.com",
        final_url="https://example.com/home",
        actions_taken=[],
    )
    p_exec = PersonaExecutionResult(
        persona_id="p1",
        persona_name="Chloe Davis",
        task_results=[task_res],
    )
    run_exec = ExecutionRunResult(
        target_url="https://example.com",
        browser="chromium",
        headless=True,
        personas=[p_exec],
        results_file_path=str(tmp_path / "results.json"),
    )

    full_md = render_full_run_interaction_markdown(plan, run_exec, output_dir=tmp_path)

    assert "# Live Browser Interaction" in full_md
    assert "https://example.com" in full_md
    assert "Chloe Davis" in full_md
    assert "- **Status:** COMPLETED" in full_md
    # Ensure DOM code dumps are disabled
    assert "```html" not in full_md
