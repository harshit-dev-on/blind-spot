"""Unit tests for customized persona selection, default 1 persona, and strict report formatting."""

from pathlib import Path
import pytest
from typer.testing import CliRunner

from blindspot.cli import app
from blindspot.personas.generator import (
    find_specific_persona_file,
    get_bundled_personas_dir,
    load_personas_from_markdown,
    rank_persona_files,
)
from blindspot.reporting.interaction_renderer import render_full_run_interaction_markdown
from blindspot.reporting.markdown_renderer import render_markdown_report


runner = CliRunner()


def test_find_specific_persona_file_aliases():
    """Verify Elena persona blueprint is found directly or as fallback."""
    bundled_dir = get_bundled_personas_dir()
    assert bundled_dir.is_dir()

    # Elena direct name
    elena_file = find_specific_persona_file("elena")
    assert elena_file is not None
    assert "elena" in elena_file.stem

    # Senior alias
    senior_file = find_specific_persona_file("senior")
    assert senior_file is not None
    assert "elena" in senior_file.stem


def test_load_personas_defaults_to_single_persona():
    """Verify load_personas_from_markdown selects exactly 1 persona by default."""
    bundled_dir = get_bundled_personas_dir()
    plan = load_personas_from_markdown(
        source=bundled_dir,
        website_url="https://example.com",
        context="General user flow testing",
    )
    assert plan is not None
    assert len(plan.personas) == 1


def test_load_personas_honors_specific_persona():
    """Verify load_personas_from_markdown loads Elena persona blueprint."""
    bundled_dir = get_bundled_personas_dir()
    plan = load_personas_from_markdown(
        source=bundled_dir,
        website_url="https://example.com",
        context="Cart inspection",
        specific_persona="elena",
    )
    assert plan is not None
    assert len(plan.personas) == 1
    assert "Elena" in plan.personas[0].name


def test_cli_persona_options_help():
    """Verify --persona and -P are exposed in CLI options."""
    res = runner.invoke(app, ["--help"])
    assert res.exit_code == 0
    assert "--persona" in res.stdout
    assert "-P" in res.stdout

    live_res = runner.invoke(app, ["live", "--help"])
    assert live_res.exit_code == 0
    assert "--persona" in live_res.stdout
    assert "-P" in live_res.stdout


def test_strict_interaction_markdown_template(tmp_path: Path):
    """Verify render_full_run_interaction_markdown matches the strict template."""
    md = render_full_run_interaction_markdown(
        plan=None,
        execution_result=None,
        output_dir=tmp_path,
    )
    assert md.startswith("# Live Browser Interaction")
    assert "- **Target URL:**" in md
    assert "- **Current URL:**" in md
    assert "- **Page Title:**" in md
    assert "- **Audit Goal:**" in md
    assert "- **Status:** COMPLETED"
    assert "## Step 0: Initial page observation" in md
    assert "## Step 1:" in md
    assert "## Run completed" in md
    assert "- **Output Report:** `improvements_suggestions.md`" in md


def test_strict_improvements_suggestions_template():
    """Verify render_markdown_report matches the strict template."""
    from blindspot.reporting.models import BlindSpotReport, FindingCategory, SeverityLevel, UXFinding

    report = BlindSpotReport(
        report_id="rep_test_001",
        target_url="https://example.com",
        context="Example Domain Audit",
        executive_summary="Clear and concise overview of usability issues.",
        findings=[
            UXFinding(
                id="f1",
                title="Low contrast search placeholder",
                category=FindingCategory.VERIFIED_ISSUE,
                severity=SeverityLevel.HIGH,
                description="Input placeholder has 2.1:1 contrast ratio against white background.",
                suggested_improvement="Increase color contrast to at least 4.5:1 using #595959.",
                expected_benefit="Low vision users can clearly locate the search field.",
                screenshot_paths=["screenshots/step-002.png"],
            )
        ],
    )
    md = render_markdown_report(report)
    assert md.startswith("# UX Improvement Suggestions:")
    assert "## 1. Executive Summary" in md
    assert "## 2. Interactive Journey Summary" in md
    assert "## 3. Improvement Suggestions" in md
    assert "### Suggestion 1: [Category: Contrast] Low contrast search placeholder" in md
    assert "- **Observed Behavior:**" in md
    assert "- **UX Friction / Impact:**" in md
    assert "- **Suggested Improvement:**" in md
    assert "- **Evidence:** `screenshots/step-002.png`" in md
    assert "- **Date:** " in md
    # Ensure no rogue backticks around date
    assert "- **Date:** `" not in md


def test_antigravity_single_persona_generation():
    """Verify AntigravityProvider generates exactly the Elena elderly persona."""
    from blindspot.ai.providers.antigravity import AntigravityProvider
    from blindspot.personas.models import PersonaPlanPayload

    prov = AntigravityProvider()

    prompt = 'WEBSITE INTENDED CONTEXT & AUDIENCE:\n"Shop online store"\n\nINSTRUCTIONS:\n2. Generate exactly 1 diverse, realistic user personas.'
    res = prov.generate_structured(prompt=prompt, schema=PersonaPlanPayload)
    assert len(res.personas) == 1
    assert "Elena" in res.personas[0].name


def test_load_personas_honors_elena():
    """Verify load_personas_from_markdown loads Elena senior user blueprint."""
    bundled_dir = get_bundled_personas_dir()
    plan = load_personas_from_markdown(
        source=bundled_dir,
        website_url="https://www.flipkart.com",
        context="Shopping",
        max_personas=1,
    )
    assert plan is not None
    assert len(plan.personas) == 1
    assert "Elena" in plan.personas[0].name


def test_runner_pipeline_browser_interaction_matches_template(tmp_path: Path):
    """Verify run_pipeline initializes browser_interaction.md with strict # Live Browser Interaction header."""
    from blindspot.core.runner import PipelineConfig, run_pipeline

    out_dir = tmp_path / "test_run"
    cfg = PipelineConfig(
        url="https://example.com",
        context="USability test",
        output_dir=out_dir,
        personas=1,
        headless=True,
        skip_ai=True,
        skip_execution=True,
        skip_report=True,
        allow_local=True,
    )

    try:
        run_pipeline(cfg)
    except Exception:
        pass

    interaction_file = out_dir / "browser_interaction.md"
    assert interaction_file.is_file()
    content = interaction_file.read_text(encoding="utf-8")
    assert content.startswith("# Live Browser Interaction")
    assert "## Step 0: Initial page observation" in content
    assert "screenshots/step-000.png" in content
    assert "BlindSpot Browser Interaction Log" not in content
    assert "stage0_baseline.png" not in content

