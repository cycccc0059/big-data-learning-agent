SYSTEM_PROMPT = """你是一个大数据开发学习助手 Agent，专注于帮助用户系统性地学习大数据技术。

你的能力范围：
1. 解释 Hadoop、Hive、Spark、Flink、Kafka 等组件的核心概念和机制。
2. 生成学习路线、计划和学习任务。
3. 针对工作问题（SQL 慢、任务失败、数据异常）给出排查路径。
4. 设计数仓方案、项目 Demo 和实操练习。
5. 准备面试回答框架。
6. 整理和沉淀学习笔记。

输出要求：
- 先给结论或方向，再展开步骤。
- 内容结构化、可执行。
- 如果引用了知识库内容，在末尾标注来源。
- 如果信息不足，说明假设后再给方案。
"""

CLASSIFY_RULES = {
    "learning_plan": ["学习路线", "学习计划", "怎么学", "入门", "路线", "规划", "路径", "学习"],
    "concept": ["是什么", "什么意思", "区别", "原理", "机制", "概念", "作用"],
    "troubleshoot": ["失败", "报错", "异常", "延迟", "lag", "排查", "OOM", "倾斜"],
    "sql_optimize": ["SQL", "sql", "优化", "慢查询", "执行计划", "join", "慢"],
    "project_design": ["设计", "架构", "方案", "数仓", "分层", "项目", "demo", "Demo"],
    "interview": ["面试", "面试题", "面经", "八股"],
    "note_organize": ["整理", "笔记", "总结", "记录", "保存"],
}


def classify_question(question: str) -> str:
    """Keyword-based classification with scoring. Returns category name."""
    scores: dict[str, int] = {}
    for category, keywords in CLASSIFY_RULES.items():
        scores[category] = sum(1 for kw in keywords if kw in question)
    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    return best if scores[best] > 0 else "concept"


TEMPLATES: dict[str, str] = {
    "learning_plan": (
        "这是一份针对「{topic}」的学习规划建议：\n\n"
        "## 1. 学习目标\n明确你希望达到的程度（了解 / 会用 / 深入原理 / 调优）。\n\n"
        "## 2. 前置知识\n列出学习该主题前需要掌握的基础。\n\n"
        "## 3. 分阶段路线\n"
        "- 第一阶段：基础概念和核心机制\n"
        "- 第二阶段：实操练习和 Demo 项目\n"
        "- 第三阶段：性能调优和原理深入\n\n"
        "## 4. 练习任务\n每个阶段的具体练习和检查标准。\n\n"
        "## 5. 学习资源\n推荐的文档、书籍、视频或博客。\n\n"
        "## 6. 检查标准\n如何判断自己是否真正掌握了每个阶段的内容。"
    ),
    "concept": (
        "## 核心概念\n对「{topic}」的核心定义和定位。\n\n"
        "## 关键机制\n深入解释其工作原理和重要机制。\n\n"
        "## 与其他组件的关系\n在技术栈中的位置和上下游依赖。\n\n"
        "## 常见误区\n学习时容易混淆或理解偏差的地方。\n\n"
        "## 延伸学习\n掌握基础后可以深入的方向。"
    ),
    "troubleshoot": (
        "## 现象确认\n先明确具体症状、频率和影响范围。\n\n"
        "## 常见原因\n列出最可能的原因（从最常见到最罕见）。\n\n"
        "## 排查步骤\n按优先级排列的排查顺序和每一步的检查方法。\n\n"
        "## 验证方式\n如何确认问题已经定位准确。\n\n"
        "## 解决方案\n具体的修复步骤和注意事项。\n\n"
        "## 预防措施\n如何避免同类问题再次发生。"
    ),
    "sql_optimize": (
        "## 当前问题分析\n分析 SQL 的性能瓶颈在哪里。\n\n"
        "## 优化方向\n- 分区裁剪：是否命中分区\n- 列裁剪：是否只读取需要的列\n- Join 优化：Map Join、Broadcast Join\n- 数据倾斜处理\n- 小文件合并\n\n"
        "## 优化后预期\n给出优化后的预期效果和验证 SQL。"
    ),
    "project_design": (
        "## 需求分析\n明确业务场景和数据需求。\n\n"
        "## 架构设计\n整体数据链路：采集 → 存储 → 计算 → 建模 → 服务。\n\n"
        "## 数仓分层\nODS / DWD / DWS / ADS 各层的设计思路。\n\n"
        "## 技术选型\n各环节的组件选择和原因。\n\n"
        "## 关键指标\n需要产出的核心指标和计算口径。\n\n"
        "## 调度与监控\n任务调度策略和数据质量监控方案。"
    ),
    "interview": (
        "## 问题分析\n这道面试题考察什么能力、什么层级。\n\n"
        "## 回答框架（STAR）\n- Situation：背景\n- Task：目标\n- Action：行动\n- Result：结果\n\n"
        "## 关键要点\n回答中必须覆盖的核心技术点。\n\n"
        "## 追问预测\n面试官可能的追问方向和应对思路。\n\n"
        "## 延伸展示\n如何借此展示你的知识广度和深度。"
    ),
}


LOCAL_FALLBACK_TEMPLATE = """你正在使用本地规则模式（未配置 LLM API Key）。

问题：{user_input}

建议从以下角度思考：
1. 这个问题属于哪个类别（学习规划 / 概念理解 / 故障排查 / 项目设计 / 面试准备）？
2. 涉及哪些大数据组件（Hadoop / Hive / Spark / Flink / Kafka / 数仓）？
3. 把大问题拆成 3-5 个小步骤，逐个解决。

提示：设置 OPENAI_API_KEY 环境变量（支持 DeepSeek、GLM 等兼容接口）后，Agent 可以给出更详细和个性化的回答。参考 .env.example 文件配置。
"""
