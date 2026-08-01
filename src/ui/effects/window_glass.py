"""Best-effort native backdrop material with a safe cross-platform fallback."""

import ctypes
import platform
import sys


class _Margins(ctypes.Structure):
    _fields_ = (
        ("left", ctypes.c_int),
        ("right", ctypes.c_int),
        ("top", ctypes.c_int),
        ("bottom", ctypes.c_int),
    )


class WindowGlassEffect:
    """Apply Windows 11 Desktop Acrylic; QSS glass remains the fallback."""

    DARK_MODE_ATTRIBUTE = 20
    CORNER_ATTRIBUTE = 33
    BACKDROP_ATTRIBUTE = 38
    ROUND_CORNER = 2
    DESKTOP_ACRYLIC = 3

    def __init__(self, window):
        self.window = window
        self.native_enabled = False
        self.backend = "layered-qss"

    def apply(self, dark: bool = False) -> bool:
        self.native_enabled = False
        self.backend = "layered-qss"
        if sys.platform != "win32":
            return False
        try:
            if platform.version() and sys.getwindowsversion().build < 22621:
                return False
            hwnd = int(self.window.winId())
            dwm = ctypes.windll.dwmapi
            self._set_attribute(dwm, hwnd, self.DARK_MODE_ATTRIBUTE, int(dark))
            self._set_attribute(dwm, hwnd, self.CORNER_ATTRIBUTE, self.ROUND_CORNER)
            result = self._set_attribute(
                dwm, hwnd, self.BACKDROP_ATTRIBUTE, self.DESKTOP_ACRYLIC
            )
            margins = _Margins(-1, -1, -1, -1)
            dwm.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
            self.native_enabled = result == 0
            self.backend = "windows-desktop-acrylic" if self.native_enabled else "layered-qss"
        except (AttributeError, OSError, TypeError, ValueError):
            self.native_enabled = False
        return self.native_enabled

    @staticmethod
    def _set_attribute(dwm, hwnd: int, attribute: int, value: int) -> int:
        data = ctypes.c_int(value)
        return int(
            dwm.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(data), ctypes.sizeof(data)
            )
        )
