"""Shared helpers for locating application resources in source and packaged runs."""

import os
import sys


def resource_path(relative_path: str) -> str:
    """Return an absolute path for a bundled or source-tree resource."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.normpath(os.path.join(base, relative_path))
