from __future__ import annotations

from agent_core import BigDataLearningAgent


def main() -> None:
    agent = BigDataLearningAgent()
    print("Big Data Learning Agent v0.1")
    print("输入你的问题，输入 exit 或 quit 退出。\n")

    while True:
        user_input = input("你 > ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("Agent > 下次继续，我们可以把这个 Demo 逐步升级。")
            break
        if not user_input:
            continue

        try:
            response = agent.answer(user_input)
        except Exception as exc:
            response = f"调用失败：{exc}"

        print(f"\nAgent > {response}\n")


if __name__ == "__main__":
    main()
