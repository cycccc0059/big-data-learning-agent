from __future__ import annotations

import re
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


def _clean_response(text: str) -> str:
    """Remove LLM-hallucinated reference lines. We add real references separately."""
    text = re.sub(r"\n?> (?:参考|资料|来源|References?).*\n?", "", text)
    return text.strip()

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
        knowledge_context, matched_files = self._retrieve_knowledge(user_input)
        template = TEMPLATES.get(category, TEMPLATES["concept"])
        notes = self._load_notes()

        # Auto-collect when no local knowledge matches, or only passing mentions
        should_collect = self.llm.enabled and self._should_auto_collect(
            user_input, matched_files
        )
        if should_collect:
            keywords = user_input.strip()[:60]
            print(f"\n  知识库无匹配，正在自动收集「{keywords}」...")
            try:
                result = self.collect_knowledge(keywords)
                print(f"  {result}")
                knowledge_context, matched_files = self._retrieve_knowledge(user_input)
            except Exception as exc:
                print(f"  自动收集失败: {exc}")

        if self.llm.enabled:
            response = self._answer_with_llm(
                user_input, category, template, knowledge_context, notes
            )
        else:
            response = self._answer_locally(user_input, category, knowledge_context)

        if matched_files:
            refs = "、".join(matched_files)
            response += f"\n\n> 参考本地资料：{refs}"
        elif not self.llm.enabled:
            response += (
                "\n\n> 知识库中暂无相关内容。"
                "配置 LLM 后可自动收集。参考 .env.example 文件。"
            )

        return response

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

    def _retrieve_knowledge(self, question: str) -> tuple[str, list[str]]:
        # Primary: semantic search via Chroma
        semantic_results = self.knowledge.search_semantic(question, limit=5)
        if semantic_results:
            parts: list[str] = []
            matched_files: list[str] = []
            seen_files: set[str] = set()
            for r in semantic_results:
                fname = r["source"]
                parts.append(
                    f"### {fname} (相关度: {r['score']})\n"
                    f"片段主题: {r['heading']}\n{r['content']}"
                )
                if fname not in seen_files:
                    matched_files.append(fname)
                    seen_files.add(fname)
            return "\n\n".join(parts), matched_files[:3]

        # Fallback: keyword search
        fallback = self.knowledge.search_local(question, limit=3)
        if not fallback:
            return "", []

        parts = []
        matched = []
        for r in fallback:
            parts.append(f"### {r['file']}\n{r['content']}")
            matched.append(r["file"])
        return "\n\n".join(parts), matched

    # ------------------------------------------------------------------
    # Knowledge collection (called from CLI)
    # ------------------------------------------------------------------

    def _should_auto_collect(
        self, question: str, matched_files: list[str]
    ) -> bool:
        """Auto-collect if no matches, or matches are only passing mentions."""
        if not matched_files:
            return True

        stop_words = {
            "是什么", "怎么", "如何", "什么", "为什么", "哪个", "哪些",
            "apache", "的", "了", "吗", "呢", "吧", "我", "想", "帮我",
            "一个", "一下", "这个", "那个", "和", "与", "或", "在", "有",
            "介绍", "解释", "说明",
        }
        keywords = [
            kw for kw in question.lower().split()
            if kw not in stop_words and len(kw) > 1
        ]
        if not keywords:
            return False

        for fname in matched_files:
            for kw in keywords:
                if kw in fname.lower():
                    return False
        return True

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
            f"请参考以下结构组织你的回答，填充具体内容：\n{template}"
        )
        messages.append({"role": "system", "content": instruction})

        if knowledge:
            messages.append(
                {
                    "role": "system",
                    "content": f"以下是从本地知识库检索到的相关资料，请优先参考其中的内容：\n\n{knowledge}",
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
        return _clean_response(self.llm.chat(messages))

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
