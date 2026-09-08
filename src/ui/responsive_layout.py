"""Pure responsive-layout policy for the desktop workbench.

Keeping width decisions out of widget construction makes the policy easy to
test and lets future layouts reuse it without importing communication code.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkbenchLayoutState:
    show_navigation: bool
    show_inspector: bool
    compact_toolbar: bool


def layout_state_for_width(width: int) -> WorkbenchLayoutState:
    """Return pane visibility for the available workbench width."""
    if width < 900:
        return WorkbenchLayoutState(False, False, True)
    if width < 1080:
        return WorkbenchLayoutState(True, False, True)
    if width < 1320:
        return WorkbenchLayoutState(True, True, True)
    return WorkbenchLayoutState(True, True, False)
