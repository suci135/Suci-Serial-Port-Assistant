"""Standard 7-bit ASCII catalog shared by UI tools."""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AsciiEntry:
    decimal: int
    hexadecimal: str
    character: str
    name: str
    description: str


_CONTROL_NAMES = (
    ("NUL", "空字符"), ("SOH", "标题开始"), ("STX", "正文开始"),
    ("ETX", "正文结束"), ("EOT", "传输结束"), ("ENQ", "请求"),
    ("ACK", "确认"), ("BEL", "响铃"), ("BS", "退格"),
    ("HT", "水平制表"), ("LF", "换行"), ("VT", "垂直制表"),
    ("FF", "换页"), ("CR", "回车"), ("SO", "移出"),
    ("SI", "移入"), ("DLE", "数据链路转义"), ("DC1", "设备控制 1 / XON"),
    ("DC2", "设备控制 2"), ("DC3", "设备控制 3 / XOFF"),
    ("DC4", "设备控制 4"), ("NAK", "否定确认"), ("SYN", "同步空闲"),
    ("ETB", "传输块结束"), ("CAN", "取消"), ("EM", "介质结束"),
    ("SUB", "替换"), ("ESC", "转义"), ("FS", "文件分隔"),
    ("GS", "组分隔"), ("RS", "记录分隔"), ("US", "单元分隔"),
)


def ascii_entries() -> List[AsciiEntry]:
    entries = []
    for value in range(128):
        if value < 32:
            name, description = _CONTROL_NAMES[value]
            character = f"<{name}>"
        elif value == 32:
            name, description, character = "SPACE", "空格", "␠"
        elif value == 127:
            name, description, character = "DEL", "删除", "<DEL>"
        else:
            character = chr(value)
            name = character
            description = "可打印字符"
        entries.append(
            AsciiEntry(value, f"{value:02X}", character, name, description)
        )
    return entries
