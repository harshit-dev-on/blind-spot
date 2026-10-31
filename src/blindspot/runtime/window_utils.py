"""Window and OS desktop focus utilities for visible headed browser testing."""

import sys
import time
from typing import Optional, Set

_PINNED_BROWSER_HWNDS: Set[int] = set()


def bring_browser_window_to_foreground(hint: Optional[str] = None, stay_topmost: bool = True) -> Optional[int]:
    """Safely bring ONLY the Playwright browser window to the active foreground on Windows.
    Strictly ignores external Electron and desktop applications (Notion, ChatGPT, Copilot, etc.).

    Args:
        hint: Optional window title hint or target domain.
        stay_topmost: If True, keeps the browser pinned to HWND_TOPMOST so it stays visible
                      in front of desktop apps while the persona operates.
    """
    if sys.platform == "darwin":
        try:
            import subprocess
            subprocess.run(
                ["osascript", "-e", 'tell application "Chromium" to activate'],
                capture_output=True,
                check=False,
                timeout=1,
            )
        except Exception:
            pass
        return None
    elif sys.platform != "win32":
        return None

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Explicit blacklist of desktop applications that share Chromium's window class
        ignored_app_titles = (
            "notion",
            "chatgpt",
            "copilot",
            "slack",
            "discord",
            "visual studio",
            "vscode",
            "teams",
            "spotify",
            "obsidian",
            "antigravity",
        )

        clean_hint = (hint or "").strip().lower()

        SW_RESTORE = 9
        SW_SHOW = 5
        HWND_TOP = 0
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_SHOWWINDOW = 0x0040

        found_hwnd = None

        def _enum_cb(hwnd: int, extra: int) -> bool:
            nonlocal found_hwnd
            if not user32.IsWindowVisible(hwnd):
                return True

            length = user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return True

            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value.lower()

            # Ignore any known desktop application
            if any(app in title for app in ignored_app_titles):
                return True

            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 256)
            class_name = class_buf.value

            if "Chrome_WidgetWin_1" in class_name:
                # Query owning process image name to guarantee it is a real browser executable
                pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                h_proc = kernel32.OpenProcess(0x1000, False, pid.value)
                exe_name = ""
                if h_proc:
                    pbuf = ctypes.create_unicode_buffer(1024)
                    size = ctypes.c_ulong(1024)
                    if kernel32.QueryFullProcessImageNameW(h_proc, 0, pbuf, ctypes.byref(size)):
                        exe_name = pbuf.value.lower()
                    kernel32.CloseHandle(h_proc)

                # Skip non-browser electron apps
                if any(app in exe_name for app in ("code.exe", "slack.exe", "discord.exe", "notion.exe", "antigravity.exe")):
                    return True

                is_browser = any(exe_name.endswith(b) for b in ("chrome.exe", "chromium.exe", "msedge.exe", "firefox.exe"))

                target_matches = False
                if any(m in title for m in ("chrome for testing", "chromium", "playwright")):
                    target_matches = True
                elif clean_hint and clean_hint in title:
                    target_matches = True
                elif is_browser:
                    target_matches = True

                if target_matches:
                    found_hwnd = hwnd

                    # 1. Reset Windows focus stealing lock via synthetic Alt key event & AllowSetForegroundWindow
                    try:
                        user32.AllowSetForegroundWindow(-1)
                        user32.keybd_event(0x12, 0, 0, 0)  # VK_MENU down
                        user32.keybd_event(0x12, 0, 2, 0)  # VK_MENU up
                    except Exception:
                        pass

                    # 2. Restore window if minimized
                    user32.ShowWindow(hwnd, SW_RESTORE)

                    # 3. Bypass Windows focus stealing prevention by attaching to foreground thread if available
                    fg_hwnd = user32.GetForegroundWindow()
                    attached = False
                    if fg_hwnd and fg_hwnd != hwnd:
                        try:
                            fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None)
                            cur_tid = kernel32.GetCurrentThreadId()
                            if fg_tid != cur_tid:
                                attached = bool(user32.AttachThreadInput(cur_tid, fg_tid, True))
                        except Exception:
                            attached = False

                    user32.BringWindowToTop(hwnd)

                    if stay_topmost:
                        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
                        _PINNED_BROWSER_HWNDS.add(hwnd)
                    else:
                        user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)

                    user32.SetForegroundWindow(hwnd)

                    if attached:
                        try:
                            user32.AttachThreadInput(cur_tid, fg_tid, False)
                        except Exception:
                            pass

                    return False  # Target window focused, stop enumeration

            return True

        cb_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

        # Check Default desktop first if running across stations/desktops
        h_default = user32.OpenDesktopW("Default", 0, False, 0x10000000)
        if h_default:
            try:
                user32.EnumDesktopWindows(h_default, cb_type(_enum_cb), 0)
            finally:
                user32.CloseDesktop(h_default)
        else:
            user32.EnumWindows(cb_type(_enum_cb), 0)

        return found_hwnd
    except Exception:
        return None


def unpin_browser_window(hwnd: Optional[int] = None) -> None:
    """Release HWND_TOPMOST pin when browser session is done."""
    if sys.platform != "win32":
        return

    try:
        import ctypes

        user32 = ctypes.windll.user32
        HWND_NOTOPMOST = -2
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_SHOWWINDOW = 0x0040

        hwnds_to_unpin = [hwnd] if hwnd else list(_PINNED_BROWSER_HWNDS)
        for h in hwnds_to_unpin:
            if h and user32.IsWindow(h):
                user32.SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
        if not hwnd:
            _PINNED_BROWSER_HWNDS.clear()
    except Exception:
        pass
