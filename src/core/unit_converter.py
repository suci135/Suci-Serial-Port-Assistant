"""Common embedded-engineering unit conversion without third-party dependencies."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Unit:
    symbol: str
    factor: float = 1.0
    offset: float = 0.0


UNIT_GROUPS = {
    # 按嵌入式常用规则统一使用 1024 进制：1 B = 8 b。
    "数据": (Unit("b"), Unit("B", 8), Unit("KB", 8 * 1024), Unit("MB", 8 * 1024**2), Unit("GB", 8 * 1024**3), Unit("TB", 8 * 1024**4)),
    "频率": (Unit("Hz"), Unit("kHz", 1e3), Unit("MHz", 1e6), Unit("GHz", 1e9)),
    "时间": (Unit("ns", 1e-9), Unit("μs", 1e-6), Unit("ms", 1e-3), Unit("s"), Unit("min", 60)),
    "电容": (Unit("pF", 1e-12), Unit("nF", 1e-9), Unit("μF", 1e-6), Unit("mF", 1e-3), Unit("F")),
    "电阻": (Unit("mΩ", 1e-3), Unit("Ω"), Unit("kΩ", 1e3), Unit("MΩ", 1e6)),
    "电压": (Unit("μV", 1e-6), Unit("mV", 1e-3), Unit("V"), Unit("kV", 1e3)),
    "电流": (Unit("μA", 1e-6), Unit("mA", 1e-3), Unit("A"), Unit("kA", 1e3)),
    "功率": (Unit("μW", 1e-6), Unit("mW", 1e-3), Unit("W"), Unit("kW", 1e3)),
    "能量": (Unit("mJ", 1e-3), Unit("J"), Unit("kJ", 1e3), Unit("Wh", 3600), Unit("kWh", 3.6e6)),
    "长度": (Unit("mm", 1e-3), Unit("cm", 1e-2), Unit("m"), Unit("km", 1e3)),
    "温度": (Unit("°C"), Unit("°F", 5 / 9, -32), Unit("K", 1, -273.15)),
}


def convert(value: float, source: Unit, target: Unit) -> float:
    base = (float(value) + source.offset) * source.factor
    return base / target.factor - target.offset


def format_value(value: float) -> str:
    if not math.isfinite(value):
        return "—"
    if abs(value) < 1e-12:
        value = 0.0
    return f"{value:.12g}"
