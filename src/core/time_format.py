"""Consistent display timestamps for terminal events."""

from datetime import datetime
from typing import Optional


def millisecond_timestamp(value: Optional[datetime] = None) -> str:
    """Return local time with exactly three fractional-second digits."""
    current = value or datetime.now()
    return current.strftime("%H:%M:%S.%f")[:-3]
