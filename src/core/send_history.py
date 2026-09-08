"""Persistent, bounded history for manually transmitted payloads."""

import json
from pathlib import Path
from typing import Dict, List, Union


class SendHistoryStore:
    def __init__(self, path: Union[str, Path], maximum: int = 100):
        self.path = Path(path)
        self.maximum = max(1, int(maximum))
        self._entries = self._load()

    def _load(self) -> List[Dict[str, str]]:
        try:
            with self.path.open("r", encoding="utf-8") as file:
                value = json.load(file)
            if isinstance(value, list):
                return [
                    {"format": str(item["format"]), "text": str(item["text"])}
                    for item in value
                    if isinstance(item, dict) and item.get("text")
                ][: self.maximum]
        except (OSError, ValueError, TypeError, KeyError):
            pass
        return []

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            with temporary.open("w", encoding="utf-8") as file:
                json.dump(self._entries, file, ensure_ascii=False, indent=2)
            temporary.replace(self.path)
        except OSError:
            pass

    def add(self, text: str, format_type: str):
        if not text or not text.strip():
            return
        entry = {"format": format_type, "text": text}
        self._entries = [item for item in self._entries if item != entry]
        self._entries.insert(0, entry)
        del self._entries[self.maximum :]
        self._save()

    def recent(self) -> List[Dict[str, str]]:
        return [entry.copy() for entry in self._entries]

    def clear(self):
        self._entries.clear()
        self._save()
