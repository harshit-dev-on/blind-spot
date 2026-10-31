"""Unit tests for BlindSpot MCP live browser sessions and tools."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from mcp_types import CallToolResult, ImageContent, TextContent

from blindspot.mcp.live_browser import (
    LiveBrowserSessions,
    _BrowserWorker,
    _page_observation,
    _write_context,
    result_with_screenshot,
)
from blindspot.mcp.server import create_mcp_server


def test_mcp_server_registers_live_browser_tools():
    """Verify that create_mcp_server exposes the live browser tool suite."""
    server = create_mcp_server()
    import asyncio
    tools = asyncio.run(server.list_tools())
    tool_names = [t.name for t in tools]

    expected = [
        "live_browser_open",
        "live_browser_observe",
        "live_browser_action",
        "live_browser_finish",
        "live_browser_close",
    ]
    for exp in expected:
        assert exp in tool_names, f"Tool {exp} should be registered in MCP server"


def test_locator_resolves_stamped_refs():
    """Verify that _locator correctly transforms stamped refs into [data-blindspot-ref] selectors."""
    page_mock = MagicMock()

    # 1. Target with leading @
    _BrowserWorker._locator(page_mock, "@e5", "text")
    page_mock.locator.assert_called_with("[data-blindspot-ref='e5']")

    # 2. Target with bare ref e12
    _BrowserWorker._locator(page_mock, "e12", "text")
    page_mock.locator.assert_called_with("[data-blindspot-ref='e12']")

    # 3. Strategy explicit ref
    _BrowserWorker._locator(page_mock, "@e3", "ref")
    page_mock.locator.assert_called_with("[data-blindspot-ref='e3']")

    # 4. Strategy placeholder
    _BrowserWorker._locator(page_mock, "Search products", "placeholder")
    page_mock.get_by_placeholder.assert_called_with("Search products", exact=False)

    # 5. Strategy role
    _BrowserWorker._locator(page_mock, "button:Search", "role")
    page_mock.get_by_role.assert_called_with("button", name="Search", exact=False)


def test_perform_action_blocks_sensitive_phone_and_otp():
    """Verify that filling phone, OTP, or credentials raises a PermissionError."""
    worker = _BrowserWorker("test_session", Path("/tmp"), allow_local=False)
    page_mock = MagicMock()
    page_mock.url = "https://example.com"

    # Blocked by target name
    with pytest.raises(PermissionError, match="credentials, phone numbers, OTPs"):
        worker._perform_action(page_mock, {
            "action": "fill",
            "target": "Enter your phone number",
            "value": "1234567890",
        })

    # Blocked by 10-digit phone value
    with pytest.raises(PermissionError, match="credentials, phone numbers, OTPs"):
        worker._perform_action(page_mock, {
            "action": "fill",
            "target": "@e1",
            "value": "9876543210",
        })

    # Blocked by OTP target
    with pytest.raises(PermissionError, match="credentials, phone numbers, OTPs"):
        worker._perform_action(page_mock, {
            "action": "fill",
            "target": "otp_code",
            "value": "123456",
        })


def test_perform_action_blocks_destructive_actions():
    """Verify that destructive operations like placing orders or wiping data are blocked."""
    worker = _BrowserWorker("test_session", Path("/tmp"), allow_local=False)
    page_mock = MagicMock()

    with pytest.raises(PermissionError, match="destructive action"):
        worker._perform_action(page_mock, {
            "action": "click",
            "target": "Place Order",
        })


def test_perform_action_blocks_ssrf_navigation():
    """Verify that navigation to private subnets or cloud metadata is blocked."""
    worker = _BrowserWorker("test_session", Path("/tmp"), allow_local=False)
    page_mock = MagicMock()

    with pytest.raises(PermissionError, match="strictly blocked"):
        worker._perform_action(page_mock, {
            "action": "navigate",
            "value": "http://169.254.169.254/latest/meta-data/",
        })


def test_write_context_generates_markdown(tmp_path):
    """Verify _write_context creates website_context.md with controls table."""
    observation = {
        "session_id": "test_1",
        "context": "Audit e-commerce discovery",
        "url": "https://example.com",
        "title": "Example Shop",
        "captured_at": "2026-10-30T00:00:00Z",
        "auth_barrier_detected": False,
        "page_text": "Welcome to our shop. Browse our products.",
        "controls": [
            {
                "ref": "@e1",
                "tag": "input",
                "role": "",
                "text": "",
                "aria": "Search",
                "name": "q",
                "id": "search-input",
                "placeholder": "Search catalog",
                "type": "text",
                "href": "",
            },
            {
                "ref": "@e2",
                "tag": "button",
                "role": "button",
                "text": "Search",
                "aria": "",
                "name": "",
                "id": "search-btn",
                "placeholder": "",
                "type": "submit",
                "href": "",
            },
        ],
        "screenshot_path": str(tmp_path / "screenshots" / "step-000.png"),
        "output_dir": str(tmp_path),
    }

    _write_context(tmp_path, observation)
    context_file = tmp_path / "website_context.md"
    assert context_file.is_file()

    content = context_file.read_text(encoding="utf-8")
    assert "# Website Context: Example Shop" in content
    assert "Audit e-commerce discovery" in content
    assert "`@e1`" in content
    assert "`@e2`" in content
    assert "Search catalog" in content
    assert "screenshots/step-000.png" in content


def test_result_with_screenshot_returns_image_content(tmp_path):
    """Verify result_with_screenshot packages text payload and image content block."""
    shot_file = tmp_path / "test.png"
    # Write a minimal 1x1 transparent PNG
    shot_file.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    payload = {
        "session_id": "test_123",
        "url": "https://example.com",
        "screenshot_path": str(shot_file),
    }

    res = result_with_screenshot(payload)
    assert isinstance(res, CallToolResult)
    assert len(res.content) == 2
    assert isinstance(res.content[0], TextContent)
    assert "test_123" in res.content[0].text
    assert isinstance(res.content[1], ImageContent)
    assert res.content[1].type == "image"
    assert res.content[1].mime_type == "image/png"
    assert len(res.content[1].data) > 0


def test_run_live_bridge_executes_actions_and_finishes(tmp_path):
    """Verify run_live_bridge executes next_action.json commands and finishes cleanly."""
    from blindspot.mcp.live_browser import run_live_bridge

    output_dir = tmp_path / "live_test_run"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Thread to simulate Antigravity writing next_action.json
    import threading
    import time

    def agent_simulator():
        # Wait for action_needed.json to appear
        needed_file = output_dir / "action_needed.json"
        for _ in range(50):
            if needed_file.is_file():
                break
            time.sleep(0.05)
        
        # Send a click action
        action_1 = {
            "action": "click",
            "target": "@e1",
            "rationale": "Click the first link"
        }
        (output_dir / "next_action.json").write_text(json.dumps(action_1), encoding="utf-8")

        # Wait for next step
        for _ in range(50):
            if needed_file.is_file():
                try:
                    data = json.loads(needed_file.read_text(encoding="utf-8"))
                    if data.get("step") == 1:
                        break
                except Exception:
                    pass
            time.sleep(0.05)

        # Send finish
        action_2 = {
            "action": "finish",
            "summary": "Completed testing",
            "findings_markdown": "- Verified button click"
        }
        (output_dir / "next_action.json").write_text(json.dumps(action_2), encoding="utf-8")

    t = threading.Thread(target=agent_simulator, daemon=True)

    with patch("playwright.sync_api.sync_playwright") as mock_pw:
        mock_browser = MagicMock()
        mock_ctx = MagicMock()
        mock_page = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Example Test"
        mock_page.locator.return_value.inner_text.return_value = "Example page text"
        mock_page.locator.return_value.evaluate_all.return_value = [
            {"ref": "@e1", "tag": "a", "role": "link", "text": "Link", "aria": "", "name": "", "id": "", "placeholder": "", "type": "", "href": ""}
        ]

        mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_ctx
        mock_ctx.new_page.return_value = mock_page
        mock_ctx.pages = [mock_page]

        t.start()
        res_dir = run_live_bridge(
            url="https://example.com",
            goal="Test live bridge",
            output_dir=output_dir,
            timeout_seconds=5,
        )

        t.join(timeout=2)

    assert res_dir == output_dir
    assert (output_dir / "browser_interaction.md").is_file()
    assert (output_dir / "improvements_suggestions.md").is_file()
    assert not (output_dir / "problems_found.md").exists()
    assert (output_dir / "action_needed.json").is_file()
    assert not (output_dir / "website_context.md").exists()

    interaction_text = (output_dir / "browser_interaction.md").read_text(encoding="utf-8")
    assert "Step 1: `click`" in interaction_text
    assert "Click the first link" in interaction_text
    assert "Run completed" in interaction_text

    findings_text = (output_dir / "improvements_suggestions.md").read_text(encoding="utf-8")
    assert "Completed testing" in findings_text
    assert "Verified button click" in findings_text


def test_run_live_bridge_autonomous_execution(tmp_path):
    """Verify run_live_bridge drives autonomous execution with local Ollama provider."""
    from blindspot.mcp.live_browser import run_live_bridge
    from blindspot.ai.models import AIResponse, ProviderStatus

    output_dir = tmp_path / "live_autonomous_run"
    output_dir.mkdir(parents=True, exist_ok=True)

    mock_status = ProviderStatus(
        provider="ollama",
        model="gemma4:e4b",
        base_url="http://localhost:11434",
        is_reachable=True,
        model_available=True,
    )

    action_response = AIResponse(
        content='{"action": "click", "target": "@e1", "value": "", "rationale": "Elena clicks link to test affordance", "is_done": false}',
        model="gemma4:e4b",
        provider="ollama",
    )

    finish_report_response = AIResponse(
        content=(
            "# UX Improvement Suggestions: https://example.com\n\n"
            "- **Target URL:** https://example.com\n"
            "- **Audit Goal:** Usability\n"
            "- **Date:** 2026-10-31\n\n"
            "## 1. Executive Summary\nElena found issues.\n\n"
            "## 2. Interactive Journey Summary\n- **Total Steps Taken:** 1\n- **Key Milestones Explored:** None\n\n"
            "## 3. Improvement Suggestions\n"
            "### Suggestion 1: Contrast <Low contrast>\n"
            "- **Observed Behavior:** Low contrast\n"
            "- **UX Friction / Impact:** Hard to read\n"
            "- **Suggested Improvement:** Increase contrast\n"
            "- **Evidence:** screenshots/step-000.png\n"
        ),
        model="gemma4:e4b",
        provider="ollama",
    )

    with patch("playwright.sync_api.sync_playwright") as mock_pw, \
         patch("blindspot.ai.providers.ollama.OllamaProvider") as mock_prov_cls:

        mock_provider = mock_prov_cls.return_value
        mock_provider.model = "gemma4:e4b"
        mock_provider.check_health.return_value = mock_status
        mock_provider.start_session.return_value = True
        mock_provider.stop_session.return_value = True
        mock_provider.generate.side_effect = [action_response, finish_report_response]

        mock_browser = MagicMock()
        mock_ctx = MagicMock()
        mock_page = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.title.return_value = "Example Test"
        mock_page.locator.return_value.inner_text.return_value = "Example page text"
        mock_page.locator.return_value.evaluate_all.return_value = [
            {"ref": "@e1", "tag": "a", "role": "link", "text": "Link", "aria": "", "name": "", "id": "", "placeholder": "", "type": "", "href": ""}
        ]

        mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_ctx
        mock_ctx.new_page.return_value = mock_page
        mock_ctx.pages = [mock_page]

        res_dir = run_live_bridge(
            url="https://example.com",
            goal="Autonomous test",
            output_dir=output_dir,
            autonomous=True,
            max_steps=1,
            timeout_seconds=5,
        )

    assert res_dir == output_dir
    assert (output_dir / "browser_interaction.md").is_file()
    assert (output_dir / "improvements_suggestions.md").is_file()
    assert (output_dir / "action_needed.json").is_file()

    mock_provider.start_session.assert_called_once()
    mock_provider.stop_session.assert_called_once()

    status_data = json.loads((output_dir / "action_needed.json").read_text(encoding="utf-8"))
    assert status_data["status"] == "completed"

    report_text = (output_dir / "improvements_suggestions.md").read_text(encoding="utf-8")
    assert "# UX Improvement Suggestions" in report_text
    assert "Suggestion 1: Contrast" in report_text


def test_decide_autonomous_action_flexible_visual_analysis(tmp_path):
    """Verify _decide_autonomous_action performs dynamic visual and UX analysis for any website."""
    from blindspot.ai.models import AIResponse
    from blindspot.mcp.live_browser import _decide_autonomous_action

    mock_provider = MagicMock()
    mock_provider.generate.return_value = AIResponse(
        content=json.dumps({
            "visual_observation": "The header contains a dark blue banner with a high-contrast logo.",
            "ux_friction": "The search input placeholder has low contrast gray text on white.",
            "action": "click",
            "target": "@e2",
            "value": "",
            "rationale": "Elena clicks the Documentation link to view user guides.",
            "is_done": False,
        }),
        model="gemma4:e4b",
        provider="ollama",
    )

    controls = [
        {"ref": "@e1", "tag": "input", "role": "searchbox", "text": "", "placeholder": "Search docs...", "aria": "Search"},
        {"ref": "@e2", "tag": "a", "role": "link", "text": "Documentation", "href": "/docs"},
        {"ref": "@e3", "tag": "button", "role": "button", "text": "Get Started"},
    ]

    shot_path = tmp_path / "shot.png"
    shot_path.write_bytes(b"\x89PNG\r\n\x1a\n")

    result = _decide_autonomous_action(
        provider=mock_provider,
        url="http://localhost:8088",
        title="Developer Dashboard",
        goal="Audit website usability",
        step=1,
        controls=controls,
        screenshot_path=shot_path,
        history_summary="## Step 0: Initial page observation\nLoaded page successfully.",
        page_text="Welcome to the developer dashboard. Access documentation and metrics below.",
    )

    assert result["action"] == "click"
    assert result["target"] == "@e2"
    # Rationale must incorporate visual observation and friction
    assert "dark blue banner" in result["rationale"]
    assert "low contrast" in result["rationale"]

    # Verify prompt received real page text and history
    sent_prompt = mock_provider.generate.call_args.kwargs["prompt"]
    assert "Developer Dashboard" in sent_prompt
    assert "developer dashboard" in sent_prompt
    assert "Step 0: Initial page observation" in sent_prompt
    assert "### Inputs & Form Fields:" in sent_prompt
    assert "### Navigation & Content Links:" in sent_prompt


def test_decide_autonomous_action_anti_looping_dynamic_control():
    """Verify anti-looping guard dynamically picks the active button on screen without hardcoding."""
    from blindspot.ai.models import AIResponse
    from blindspot.mcp.live_browser import _decide_autonomous_action

    mock_provider = MagicMock()
    # Model mistakenly returns scroll after already scrolling
    mock_provider.generate.return_value = AIResponse(
        content=json.dumps({
            "action": "scroll",
            "target": "",
            "value": "down",
            "rationale": "Scrolling again",
        }),
        model="gemma4:e4b",
        provider="ollama",
    )

    controls = [
        {"ref": "@e5", "tag": "button", "role": "button", "text": "Confirm Selection"},
    ]

    result = _decide_autonomous_action(
        provider=mock_provider,
        url="https://example.com/form",
        title="Form Test",
        goal="Submit form",
        step=2,
        controls=controls,
        screenshot_path=Path("/nonexistent.png"),
        history_summary="",
        recent_actions=["scroll"],
    )

    # Must override scroll and click the active button dynamically
    assert result["action"] == "click"
    assert result["target"] == "@e5"
    assert "Confirm Selection" in result["rationale"]


