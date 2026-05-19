from __future__ import annotations

from pathlib import Path

from llm_client import LLMClient
from memory import MemoryStore
from prompts import LOCAL_FALLBACK_TEMPLATE, SYSTEM_PROMPT


class BigDataLearningAgent:
    def __init__(self, notes_dir: str = "notes") -> None:
        self.memory = MemoryStore()
        self.llm = LLMClient()
        self.notes_dir = Path(notes_dir)

    def answer(self, user_input: str) -> str:
        self.memory.add("user", user_input)

        if self.llm.enabled:
            response = self._answer_with_llm(user_input)
        else:
            response = self._answer_locally(user_input)

        self.memory.add("assistant", response)
        return response

    def _answer_with_llm(self, user_input: str) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        knowledge = self._load_notes()
        if knowledge:
            messages.append(
                {
                    "role": "system",
                    "content": f"下面是用户本地知识库中的相关资料，可作为参考：\n\n{knowledge}",
                }
            )

        for item in self.memory.recent(limit=8):
            messages.append({"role": item["role"], "content": item["content"]})

        messages.append({"role": "user", "content": user_input})
        return self.llm.chat(messages)

    def _answer_locally(self, user_input: str) -> str:
        notes = self._load_notes()
        response = LOCAL_FALLBACK_TEMPLATE.format(user_input=user_input)
        if notes:
            response += "\n\n已读取到本地知识笔记，可在接入大模型后用于增强回答：\n"
            response += self._summarize_note_titles()
        return response

    def _load_notes(self) -> str:
        if not self.notes_dir.exists():
            return ""

        chunks: list[str] = []
        for path in sorted(self.notes_dir.glob("*.md"))[:8]:
            content = path.read_text(encoding="utf-8").strip()
            if content:
                chunks.append(f"# {path.name}\n{content[:2000]}")
        return "\n\n".join(chunks)

    def _summarize_note_titles(self) -> str:
        titles = []
        for path in sorted(self.notes_dir.glob("*.md"))[:8]:
            titles.append(f"- {path.name}")
        return "\n".join(titles)
