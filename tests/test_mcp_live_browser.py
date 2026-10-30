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
    assert (output_dir / "problems_found.md").is_file()
    assert (output_dir / "action_needed.json").is_file()

    interaction_text = (output_dir / "browser_interaction.md").read_text(encoding="utf-8")
    assert "Step 1: `click`" in interaction_text
    assert "Click the first link" in interaction_text
    assert "Run completed" in interaction_text

    findings_text = (output_dir / "problems_found.md").read_text(encoding="utf-8")
    assert "Completed testing" in findings_text
    assert "Verified button click" in findings_text

