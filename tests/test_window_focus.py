"""Unit tests for window focus and desktop forwarding utilities."""

import sys
from unittest.mock import MagicMock, patch
import pytest

from blindspot.runtime.desktop_utils import ensure_default_desktop
from blindspot.runtime.window_utils import bring_browser_window_to_foreground, unpin_browser_window


def test_desktop_utils_skips_under_pytest(monkeypatch):
    """ensure_default_desktop must do nothing while running tests."""
    # Under pytest, it returns immediately without re-spawning
    assert ensure_default_desktop() is None


def test_window_utils_non_win32(monkeypatch):
    """bring_browser_window_to_foreground returns None on non-Windows platforms."""
    monkeypatch.setattr(sys, "platform", "linux")
    res = bring_browser_window_to_foreground()
    assert res is None


@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific test")
def test_window_utils_safe_execution():
    """Verify bring_browser_window_to_foreground executes safely without crashing."""
    # When no matching browser window is open, returns None cleanly
    res = bring_browser_window_to_foreground(hint="non_existent_domain_xyz_123")
    assert res is None or isinstance(res, int)
    unpin_browser_window()

