"""
应用程序配置管理
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


class AppConfig:
    """应用程序配置管理类"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".bauddance_serial"
        self.config_file = self.config_dir / "config.json"
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not self.config_file.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                config = self._migrate_config(config)
                self._merge_defaults(config, self._get_default_config())
                return config
        except (json.JSONDecodeError, IOError):
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "config_version": 2,
            "serial": {
                "baud_rate": 9600,
                "data_bits": 8,
                "stop_bits": 1,
                "parity": "None",
                "flow_control": "None",
                "auto_reconnect": True,
                "read_timeout": 1.0
            },
            "bluetooth": {
                "scan_timeout": 10.0,
                "connection_timeout": 30.0,
                "auto_reconnect": True
            },
            "display": {
                "data_format": "ASCII",
                "show_timestamp": True,
                "timestamp_format": "%H:%M:%S.%f",
                "max_records": 1000,
                "auto_scroll": True,
                "word_wrap": True,
                "pause_buffer_bytes": 524288
            },
            "send": {
                "history_limit": 100,
                "data_format": "ASCII"
            },
            "window": {
                "splitter_sizes": [210, 720, 320]
            },
            "theme": {
                "style": "light",  # light, dark, auto
                "accent_color": "#007aff"
            }
        }

    @classmethod
    def _merge_defaults(cls, config: Dict[str, Any], defaults: Dict[str, Any]):
        """Recursively add new defaults without replacing user preferences."""
        for key, value in defaults.items():
            if key not in config:
                config[key] = value
            elif isinstance(value, dict) and isinstance(config[key], dict):
                cls._merge_defaults(config[key], value)

    @staticmethod
    def _migrate_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate settings that older releases displayed but never persisted."""
        try:
            version = int(config.get("config_version", 1))
        except (TypeError, ValueError):
            version = 1
        if version < 2:
            config.setdefault("display", {})["data_format"] = "ASCII"
            config.setdefault("send", {})["data_format"] = "ASCII"
            for obsolete in ("width", "height", "maximized"):
                config.setdefault("window", {}).pop(obsolete, None)
            config["config_version"] = 2
        return config
    
    def save_config(self):
        """保存配置到文件"""
        self.config_dir.mkdir(exist_ok=True)
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"保存配置文件失败: {e}")
    
    def get(self, key: str, default=None):
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        config = self._config
        
        # 导航到最后一级的父字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_serial_config(self) -> Dict[str, Any]:
        """获取串口配置"""
        return self._config.get("serial", {})
    
    def get_bluetooth_config(self) -> Dict[str, Any]:
        """获取蓝牙配置"""
        return self._config.get("bluetooth", {})
    
    def get_display_config(self) -> Dict[str, Any]:
        """获取显示配置"""
        return self._config.get("display", {})
    
    def get_window_config(self) -> Dict[str, Any]:
        """获取窗口配置"""
        return self._config.get("window", {})
