"""Integer radix conversion with optional fixed-width two's complement."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RadixConversion:
    value: int
    binary: str
    octal: str
    decimal: str
    hexadecimal: str
    byte_hex: str


def _clean_number(text: str) -> str:
    return "".join(text.strip().split()).replace("_", "").replace(",", "")


def parse_integer(text: str, base: Optional[int] = None) -> int:
    cleaned = _clean_number(text)
    if not cleaned:
        raise ValueError("请输入需要转换的数值")

    sign = ""
    if cleaned[0] in "+-":
        sign, cleaned = cleaned[0], cleaned[1:]
    lowered = cleaned.lower()
    prefixes = {"0b": 2, "0o": 8, "0x": 16}
    detected = next((value for prefix, value in prefixes.items() if lowered.startswith(prefix)), None)
    if detected is not None:
        if base not in (None, detected):
            raise ValueError("数值前缀与所选进制不一致")
        base = detected
        cleaned = cleaned[2:]
    if not cleaned:
        raise ValueError("数值不完整")
    return int(sign + cleaned, base or 10)


def convert_integer(
    text: str,
    source_base: Optional[int] = None,
    bit_width: Optional[int] = None,
) -> RadixConversion:
    value = parse_integer(text, source_base)
    if bit_width is not None:
        if bit_width not in (8, 16, 32, 64):
            raise ValueError("位宽只能是 8、16、32 或 64")
        minimum = -(1 << (bit_width - 1))
        maximum = (1 << bit_width) - 1
        if not minimum <= value <= maximum:
            raise ValueError(f"数值超出 {bit_width} 位可表示范围")
        raw = value & ((1 << bit_width) - 1)
        binary = f"{raw:0{bit_width}b}"
        hexadecimal = f"{raw:0{bit_width // 4}X}"
        octal = format(raw, "o")
    else:
        sign = "-" if value < 0 else ""
        magnitude = abs(value)
        binary = sign + format(magnitude, "b")
        octal = sign + format(magnitude, "o")
        hexadecimal = sign + format(magnitude, "X")
        raw = value

    if raw < 0:
        byte_hex = ""
    else:
        compact = hexadecimal if bit_width is not None else format(raw, "X")
        if len(compact) % 2:
            compact = "0" + compact
        byte_hex = " ".join(compact[index:index + 2] for index in range(0, len(compact), 2))

    return RadixConversion(
        value=value,
        binary=binary,
        octal=octal,
        decimal=str(value),
        hexadecimal=hexadecimal,
        byte_hex=byte_hex,
    )
