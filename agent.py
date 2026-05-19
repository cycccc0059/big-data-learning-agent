from __future__ import annotations

from agent_core import BigDataLearningAgent

HELP_TEXT = """命令：
  :collect <主题>   收集知识（搜索网络 + 整理到知识库）
  :list             列出知识库中的所有文件
  :help             显示此帮助
  exit / quit       退出"""


def main() -> None:
    agent = BigDataLearningAgent()

    llm_status = "已配置 LLM" if agent.llm.enabled else "本地规则模式（未配置 LLM）"
    print(f"Big Data Learning Agent v0.2 — 知识库构建版")
    print(f"状态：{llm_status}")
    print(f"知识库文件数：{len(agent.knowledge.list_files())}")
    print("输入 :help 查看更多命令，输入 exit 或 quit 退出。\n")

    while True:
        user_input = input("你 > ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Agent > 下次见，继续升级这个 Agent 吧。")
            break
        if not user_input:
            continue

        try:
            if user_input.startswith(":collect"):
                topic = user_input[len(":collect"):].strip()
                if not topic:
                    print("\nAgent > 用法：:collect <主题>，例如 :collect Spark shuffle\n")
                    continue
                print()
                result = agent.collect_knowledge(topic)
                print(f"\nAgent > {result}\n")
            elif user_input == ":list":
                result = agent.list_knowledge()
                print(f"\nAgent > {result}\n")
            elif user_input == ":help":
                print(f"\n{HELP_TEXT}\n")
            else:
                response = agent.answer(user_input)
                print(f"\nAgent > {response}\n")
        except Exception as exc:
            print(f"\nAgent > 出错了：{exc}\n")


if __name__ == "__main__":
    main()
