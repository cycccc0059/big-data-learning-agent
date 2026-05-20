from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


def _load_dotenv() -> None:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip()
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.3) -> str:
        if not self.enabled:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        return self._request(messages, temperature)

    def classify(self, question: str) -> str:
        """Classify a question into one of the 7 categories."""
        if not self.enabled:
            return "concept"
        prompt = (
            "将以下用户问题分类为以下类别之一，只回复类别名称，不要解释。\n"
            "类别：learning_plan, concept, troubleshoot, sql_optimize, "
            "project_design, interview, note_organize\n\n"
            f"问题：{question}\n\n类别："
        )
        try:
            result = self._request(
                [{"role": "user", "content": prompt}], temperature=0.1
            )
            return result.strip().lower()
        except Exception:
            return "concept"

    def extract_topic(self, question: str) -> str:
        """Extract core topic keywords from a user question."""
        if not self.enabled:
            return question.strip()[:40]
        prompt = (
            "从以下用户问题中提取核心主题关键词（3-5个词，空格分隔），只回复关键词，不要解释。\n\n"
            f"问题：{question}\n\n关键词："
        )
        try:
            result = self._request(
                [{"role": "user", "content": prompt}], temperature=0.1
            )
            return result.strip()[:80]
        except Exception:
            return question.strip()[:40]

    def summarize_knowledge(self, title: str, raw_text: str) -> str:
        """Summarize web content into structured Markdown knowledge."""
        if not self.enabled:
            raise RuntimeError("OPENAI_API_KEY is required for knowledge collection.")
        prompt = (
            f"你是一位大数据技术文档撰写者。请将以下关于「{title}」的网页内容整理成一份结构化的"
            f"Markdown 笔记，包含以下部分：\n"
            f"1. 核心概念\n2. 关键机制\n3. 常见问题与优化\n4. 学习建议\n\n"
            f"要求：只输出纯 Markdown 内容，不要用代码块包裹，语言简洁专业。\n\n"
            f"原始内容：\n{raw_text[:8000]}"
        )
        result = self._request([{"role": "user", "content": prompt}], temperature=0.3)
        # Strip code block wrappers if present
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            if len(lines) > 2:
                result = "\n".join(lines[1:-1])
        return result.strip()

    def _request(self, messages: list[dict[str, str]], temperature: float) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM request failed: {error.code} {detail}") from error
        return data["choices"][0]["message"]["content"].strip()
