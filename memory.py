from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Message:
    role: str
    content: str
    created_at: str


class MemoryStore:
    def __init__(self, path: str = "data/memory.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]\n", encoding="utf-8")

    def add(self, role: str, content: str) -> None:
        messages = self.all()
        messages.append(
            {
                "role": role,
                "content": content,
                "created_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
        self.path.write_text(
            json.dumps(messages[-40:], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def all(self) -> list[dict[str, str]]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def recent(self, limit: int = 8) -> list[dict[str, str]]:
        return self.all()[-limit:]
