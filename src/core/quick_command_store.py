"""Persistence for user-defined quick serial commands."""

import json
from pathlib import Path
from typing import Any, Dict, List, Union


DEFAULT_QUICK_COMMANDS: List[Dict[str, Any]] = [
    {"name": "重启模块", "command": "AT+RST", "description": "重启模块", "enabled": True, "delay": 1000, "is_hex": False},
    {"name": "查询版本信息", "command": "AT+GMR", "description": "查询版本信息", "enabled": True, "delay": 1000, "is_hex": False},
    {"name": "扫描WiFi热点", "command": "AT+CWLAP", "description": "扫描WiFi热点", "enabled": True, "delay": 1000, "is_hex": False},
    {"name": "HEX测试数据", "command": "01 02 03 04", "description": "HEX测试数据", "enabled": False, "delay": 1000, "is_hex": True},
    {"name": "连接WiFi网络", "command": "AT+CWJAP=\"SSID\",\"PASS\"", "description": "连接WiFi网络", "enabled": False, "delay": 1000, "is_hex": False},
]


class QuickCommandStore:
    """Load and save quick commands without coupling persistence to the UI."""

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)

    def load(self) -> List[Dict[str, Any]]:
        try:
            if self.path.exists():
                with self.path.open("r", encoding="utf-8") as file:
                    commands = json.load(file)
                if isinstance(commands, list):
                    return commands
        except (OSError, json.JSONDecodeError, TypeError):
            pass
        return [command.copy() for command in DEFAULT_QUICK_COMMANDS]

    def save(self, commands: List[Dict[str, Any]]) -> bool:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
            with temporary_path.open("w", encoding="utf-8") as file:
                json.dump(commands, file, ensure_ascii=False, indent=4)
            temporary_path.replace(self.path)
            return True
        except OSError:
            return False
