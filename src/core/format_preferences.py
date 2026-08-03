"""Normalization for persisted terminal data-format preferences."""

SUPPORTED_DATA_FORMATS = ("HEX", "ASCII", "UTF-8")


def normalize_data_format(value, default: str = "ASCII") -> str:
    normalized = str(value or "").strip().upper().replace("UTF8", "UTF-8")
    return normalized if normalized in SUPPORTED_DATA_FORMATS else default
