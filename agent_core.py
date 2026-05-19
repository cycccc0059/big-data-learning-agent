from __future__ import annotations

from pathlib import Path

from knowledge_collector import KnowledgeCollector
from llm_client import LLMClient
from memory import MemoryStore
from prompts import (
    CLASSIFY_RULES,
    LOCAL_FALLBACK_TEMPLATE,
    SYSTEM_PROMPT,
    TEMPLATES,
    classify_question,
)

NOTE_DIR = "notes"
KNOWLEDGE_DIR = "knowledge"


class BigDataLearningAgent:
    def __init__(self) -> None:
        self.memory = MemoryStore()
        self.llm = LLMClient()
        self.notes_dir = Path(NOTE_DIR)
        self.knowledge = KnowledgeCollector(KNOWLEDGE_DIR)

    # ------------------------------------------------------------------
    # Core answer flow
    # ------------------------------------------------------------------

    def answer(self, user_input: str) -> str:
        self.memory.add("user", user_input)

        response = self._build_response(user_input)

        self.memory.add("assistant", response)
        return response

    def _build_response(self, user_input: str) -> str:
        category = self._classify(user_input)
        knowledge_context = self._retrieve_knowledge(user_input, category)
        template = TEMPLATES.get(category, TEMPLATES["concept"])
        notes = self._load_notes()

        if self.llm.enabled:
            return self._answer_with_llm(
                user_input, category, template, knowledge_context, notes
            )
        return self._answer_locally(user_input, category, knowledge_context)

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def _classify(self, question: str) -> str:
        if self.llm.enabled:
            llm_result = self.llm.classify(question)
            if llm_result in CLASSIFY_RULES:
                return llm_result
        return classify_question(question)

    # ------------------------------------------------------------------
    # Knowledge retrieval
    # ------------------------------------------------------------------

    def _retrieve_knowledge(self, question: str, category: str) -> str:
        results = self.knowledge.search_local(question, limit=3)
        if not results:
            return ""

        parts: list[str] = []
        for r in results:
            parts.append(f"### 本地资料: {r['file']}\n{r['content']}")
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Knowledge collection (called from CLI)
    # ------------------------------------------------------------------

    def collect_knowledge(self, topic: str) -> str:
        if not self.llm.enabled:
            return "知识收集需要配置 LLM API Key。请参考 .env.example 配置。"
        return self.knowledge.collect(topic, self.llm.summarize_knowledge)

    def list_knowledge(self) -> str:
        files = self.knowledge.list_files()
        if not files:
            return "知识库为空。使用 :collect <主题> 命令收集知识。"
        lines = ["知识库文件："]
        for f in files:
            lines.append(f"  - {f}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # LLM path
    # ------------------------------------------------------------------

    def _answer_with_llm(
        self,
        user_input: str,
        category: str,
        template: str,
        knowledge: str,
        notes: str,
    ) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        instruction = (
            f"当前问题分类：{category}\n"
            f"请参考以下结构组织你的回答，但不要照搬模板，而是填充具体内容：\n{template}"
        )
        messages.append({"role": "system", "content": instruction})

        if knowledge:
            messages.append(
                {
                    "role": "system",
                    "content": f"以下是从本地知识库检索到的相关资料，请优先参考：\n\n{knowledge}",
                }
            )

        if notes:
            messages.append(
                {
                    "role": "system",
                    "content": f"以下是用户本地笔记：\n\n{notes}",
                }
            )

        for item in self.memory.recent(limit=8):
            messages.append({"role": item["role"], "content": item["content"]})

        messages.append({"role": "user", "content": user_input})
        return self.llm.chat(messages)

    # ------------------------------------------------------------------
    # Local (no LLM) path
    # ------------------------------------------------------------------

    def _answer_locally(
        self, user_input: str, category: str, knowledge: str
    ) -> str:
        response = LOCAL_FALLBACK_TEMPLATE.format(user_input=user_input)
        response += f"\n\n检测到问题分类：{category}"

        if knowledge:
            response += "\n\n已从本地知识库检索到相关资料：\n"
            response += knowledge[:1500]

        notes = self._load_notes()
        if notes:
            response += "\n\n已读取到本地知识笔记。"

        response += (
            "\n\n---\n提示：配置 DeepSeek 或 GLM 的 API Key 后，"
            "Agent 可以给出更详细和个性化的回答。参考 .env.example 文件。"
        )
        return response

    # ------------------------------------------------------------------
    # Notes (unchanged from v0.1)
    # ------------------------------------------------------------------

    def _load_notes(self) -> str:
        if not self.notes_dir.exists():
            return ""
        chunks: list[str] = []
        for path in sorted(self.notes_dir.glob("*.md"))[:8]:
            content = path.read_text(encoding="utf-8").strip()
            if content:
                chunks.append(f"# {path.name}\n{content[:2000]}")
        return "\n\n".join(chunks)
