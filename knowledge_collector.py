from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


class _TextExtractor(HTMLParser):
    """Extract visible text from HTML, stripping tags and scripts."""

    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "code", "pre"}:
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "code", "pre"}:
            self._skip = False

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.text.append(data)


def _extract_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    raw = " ".join(parser.text)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


TOPIC_TO_DIR: dict[str, str] = {
    "hadoop": "components",
    "hdfs": "components",
    "yarn": "components",
    "mapreduce": "components",
    "spark": "components",
    "spark sql": "components",
    "spark streaming": "components",
    "flink": "components",
    "flink sql": "components",
    "checkpoint": "components",
    "hive": "components",
    "hive sql": "components",
    "kafka": "components",
    "zookeeper": "components",
    "hbase": "components",
    "presto": "components",
    "clickhouse": "components",
    "doris": "components",
    "数仓": "projects",
    "数据仓库": "projects",
    "离线数仓": "projects",
    "实时数仓": "projects",
    "数据治理": "projects",
    "数据质量": "projects",
    "血缘": "projects",
    "调度": "projects",
    "airflow": "projects",
    "dolphinscheduler": "projects",
    "面试": "interview",
    "面试题": "interview",
    "学习路线": "roadmap",
    "学习路径": "roadmap",
    "入门": "roadmap",
    "排查": "cases",
    "优化": "cases",
    "倾斜": "cases",
    "OOM": "cases",
}


def _topic_to_dir(topic: str) -> tuple[str, str]:
    """Determine directory and filename for a topic. Returns (dir_name, file_name)."""
    topic_lower = topic.lower()
    for key, dir_name in TOPIC_TO_DIR.items():
        if key in topic_lower:
            safe_name = re.sub(r"[^\w一-鿿\-]", "_", topic.strip()).strip("_")
            return dir_name, f"{safe_name}.md"
    return "components", "general.md"


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Search DuckDuckGo and return list of {title, href, body}."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS  # 旧版兼容
        except ImportError:
            raise ImportError(
                "需要安装 ddgs 库: pip install ddgs"
            )

    results: list[dict[str, str]] = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append(
                {
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", ""),
                }
            )
    return results


def fetch_page(url: str) -> str:
    """Fetch and extract text content from a URL."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; BigDataLearningAgent/0.2)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()

            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].strip()
            else:
                charset = "utf-8"

            try:
                html = raw.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                html = raw.decode("utf-8", errors="replace")

            return _extract_text(html)
    except Exception as exc:
        return f"[无法抓取此页面: {exc}]"


class KnowledgeCollector:
    def __init__(self, knowledge_dir: str = "knowledge") -> None:
        self.root = Path(knowledge_dir)

    def collect(self, topic: str, llm_summarize, max_pages: int = 3) -> str:
        """Collect knowledge on a topic: search -> fetch -> summarize -> save."""
        print(f"  搜索「{topic}」...")
        search_results = search_web(topic, max_results=max_pages)
        if not search_results:
            return f"未找到关于「{topic}」的搜索结果。"

        print(f"  找到 {len(search_results)} 个结果，正在抓取页面内容...")
        raw_texts: list[str] = []
        for r in search_results:
            url = r["href"]
            print(f"    -> {url[:80]}...")
            text = fetch_page(url)
            raw_texts.append(f"来源: {r['title']} ({url})\n{text[:3000]}")
            time.sleep(1)

        combined = "\n\n---\n\n".join(raw_texts)
        print(f"  正在用 LLM 整理知识点...")
        summary = llm_summarize(topic, combined)

        sub_dir, filename = _topic_to_dir(topic)
        target_dir = self.root / sub_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        filepath = target_dir / filename

        header = f"# {topic}\n\n> 由知识收集器自动生成。\n\n"
        content = header + summary + "\n"
        filepath.write_text(content, encoding="utf-8")

        return f"已保存到 {filepath}"

    def list_files(self) -> list[str]:
        """List all knowledge files."""
        if not self.root.exists():
            return []
        files: list[str] = []
        for path in sorted(self.root.rglob("*.md")):
            rel = path.relative_to(self.root)
            files.append(str(rel))
        return files

    def search_local(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        """Simple keyword search across knowledge files."""
        if not self.root.exists():
            return []

        results: list[dict[str, str]] = []
        keywords = query.lower().split()

        for path in sorted(self.root.rglob("*.md")):
            try:
                content = path.read_text(encoding="utf-8").lower()
            except Exception:
                continue

            score = sum(1 for kw in keywords if kw in content)
            if score > 0:
                rel = str(path.relative_to(self.root))
                full = path.read_text(encoding="utf-8")
                results.append(
                    {
                        "file": rel,
                        "score": str(score),
                        "content": full[:2000],
                    }
                )

        results.sort(key=lambda x: int(x["score"]), reverse=True)
        return results[:limit]
