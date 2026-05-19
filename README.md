# Big Data Learning Agent v0.1

一个面向大数据开发学习与工作问题处理的个人任务与知识助手 Agent Demo。

这个版本先做成命令行工具，目标不是一次性做成“万能 Agent”，而是先跑通最小闭环：

- 澄清你的问题或学习目标
- 拆解成可执行步骤
- 结合本地知识笔记生成建议
- 保存会话记忆，方便后续迭代
- 可选接入 OpenAI 兼容接口

## 适合处理的问题

- “我想系统学习 Spark，给我一个 4 周计划”
- “Flink checkpoint 和 savepoint 有什么区别？”
- “帮我分析 Hive SQL 慢查询排查思路”
- “我今天要准备数仓面试，帮我安排任务”
- “把 notes 里的内容作为我的知识库参考”

## 快速开始

```bash
python3 agent.py
```

直接输入问题即可。输入 `exit` / `quit` 退出。

## 可选：接入大模型

设置环境变量：

```bash
export OPENAI_API_KEY="你的 API Key"
export OPENAI_MODEL="gpt-4.1-mini"
```

如果使用 OpenAI 兼容服务，也可以设置：

```bash
export OPENAI_BASE_URL="https://api.openai.com/v1"
```

没有设置 `OPENAI_API_KEY` 时，Agent 会自动使用本地规则模式，方便先看整体流程。

## 项目结构

```text
.
├── agent.py              # CLI 入口
├── agent_core.py         # Agent 核心逻辑
├── llm_client.py         # OpenAI 兼容接口调用
├── memory.py             # 简单本地记忆
├── prompts.py            # Agent 角色与提示词
├── data/
│   └── memory.json       # 自动生成的会话记忆
└── notes/
    └── big_data_basics.md
```

## v0.1 边界

当前版本只做文本问答、任务拆解和本地 Markdown 知识读取。后续可以继续迭代：

- 接入向量数据库，支持更强的知识库检索
- 增加工具调用，例如 SQL 解释、日志分析、代码读取
- 做成 Web UI
- 增加学习计划追踪和每日复盘
- 接入真实项目资料和面试题库
