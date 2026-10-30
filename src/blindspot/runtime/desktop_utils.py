"""Desktop and WindowStation utilities for Windows live browser execution."""

import os
import sys


def ensure_default_desktop() -> None:
    """Ensure the process runs on WinSta0\\Default desktop on Windows.

    When invoked inside isolated service/sandbox sessions (such as Antigravity's exebox-*),
    re-spawns the CLI process on WinSta0\\Default so headed Playwright browsers are physically
    visible on the user's desktop screen.
    """
    if sys.platform != "win32":
        return

    # Skip under test suites
    if "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST") or "unittest" in sys.modules:
        return

    if os.environ.get("BLINDSPOT_DESKTOP_FORWARDED") == "1":
        return

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        hd = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
        if not hd:
            return

        buf = ctypes.create_unicode_buffer(256)
        if not user32.GetUserObjectInformationW(hd, 2, buf, 256, None):
            return

        current_desktop = buf.value.lower()
        if current_desktop == "default":
            return

        # Current desktop is isolated (e.g. exebox-*). Forward to WinSta0\Default.
        class STARTUPINFOW(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("lpReserved", wintypes.LPWSTR),
                ("lpDesktop", wintypes.LPWSTR),
                ("lpTitle", wintypes.LPWSTR),
                ("dwX", wintypes.DWORD),
                ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD),
                ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD),
                ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD),
                ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_char_p),
                ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE),
                ("hStdError", wintypes.HANDLE),
            ]

        class PROCESS_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("hProcess", wintypes.HANDLE),
                ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD),
                ("dwThreadId", wintypes.DWORD),
            ]

        STD_INPUT_HANDLE = -10
        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12

        si = STARTUPINFOW()
        si.cb = ctypes.sizeof(STARTUPINFOW)
        si.lpDesktop = r"WinSta0\Default"
        si.dwFlags = 0x00000100  # STARTF_USESTDHANDLES
        si.hStdInput = kernel32.GetStdHandle(STD_INPUT_HANDLE)
        si.hStdOutput = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        si.hStdError = kernel32.GetStdHandle(STD_ERROR_HANDLE)

        pi = PROCESS_INFORMATION()

        kernel32.GetCommandLineW.restype = ctypes.c_wchar_p
        cmd_line = kernel32.GetCommandLineW()
        if not cmd_line:
            return

        os.environ["BLINDSPOT_DESKTOP_FORWARDED"] = "1"

        success = kernel32.CreateProcessW(
            None,
            cmd_line,
            None,
            None,
            True,  # bInheritHandles
            0,
            None,
            None,
            ctypes.byref(si),
            ctypes.byref(pi),
        )

        if success:
            try:
                # Wait for child process to finish
                kernel32.WaitForSingleObject(pi.hProcess, 0xFFFFFFFF)  # INFINITE
                exit_code = wintypes.DWORD()
                kernel32.GetExitCodeProcess(pi.hProcess, ctypes.byref(exit_code))
                kernel32.CloseHandle(pi.hProcess)
                kernel32.CloseHandle(pi.hThread)
                sys.exit(exit_code.value)
            except KeyboardInterrupt:
                kernel32.TerminateProcess(pi.hProcess, 1)
                kernel32.CloseHandle(pi.hProcess)
                kernel32.CloseHandle(pi.hThread)
                sys.exit(1)
    except Exception:
        pass

