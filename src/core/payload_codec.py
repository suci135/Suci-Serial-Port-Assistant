"""Validation and encoding for outbound terminal payloads."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class PayloadAnalysis:
    valid: bool
    payload: bytes
    normalized: str
    error: str = ""

    @property
    def byte_count(self) -> int:
        return len(self.payload)


def _decode_hex(text: str) -> PayloadAnalysis:
    stripped = text.strip()
    if not stripped:
        return PayloadAnalysis(True, b"", "")

    tokens = [token for token in re.split(r"[\s,;]+", stripped) if token]
    compact_parts = []
    for token in tokens:
        part = token[2:] if token.lower().startswith("0x") else token
        if not part or any(char not in "0123456789abcdefABCDEF" for char in part):
            return PayloadAnalysis(False, b"", "", f"无效 HEX：{token}")
        compact_parts.append(part)

    compact = "".join(compact_parts)
    if len(compact) % 2:
        return PayloadAnalysis(False, b"", "", "HEX 必须由完整字节组成（每字节 2 位）")
    payload = bytes.fromhex(compact)
    normalized = " ".join(f"{byte:02X}" for byte in payload)
    return PayloadAnalysis(True, payload, normalized)


def analyze_payload(
    text: str,
    format_type: str,
    append_carriage: bool = False,
    append_newline: bool = False,
) -> PayloadAnalysis:
    """Validate input and return the exact bytes that should be transmitted."""
    try:
        if format_type == "HEX":
            analysis = _decode_hex(text)
            if not analysis.valid:
                return analysis
            payload = analysis.payload
            normalized = analysis.normalized
        elif format_type == "ASCII":
            payload = text.encode("ascii")
            normalized = text
        else:
            payload = text.encode("utf-8")
            normalized = text
    except UnicodeEncodeError:
        return PayloadAnalysis(False, b"", "", "ASCII 模式不能包含非 ASCII 字符")

    suffix = b""
    if append_carriage:
        suffix += b"\r"
    if append_newline:
        suffix += b"\n"
    return PayloadAnalysis(True, payload + suffix, normalized)
