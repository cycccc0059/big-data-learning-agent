# DolphinScheduler 架构

> 由知识收集器自动生成。

# Apache DolphinScheduler 架构笔记

## 1. 核心概念

### 1.1 系统角色
- **MasterServer**：负责任务调度、工作流 DAG 切分、任务分发、状态监控
- **WorkerServer**：负责任务执行、日志服务、任务结果反馈
- **ApiServer**：提供 RESTful API，处理前端请求
- **AlertServer**：告警服务，支持邮件、钉钉、企业微信等
- **ZooKeeper**：分布式协调，用于 Master/Worker 选举、任务队列管理
- **Database**：存储元数据（工作流定义、任务实例、用户等）

### 1.2 核心对象
- **Workflow**：工作流定义，由多个 Task 组成的有向无环图（DAG）
- **Task**：任务节点，支持 Shell、SQL、Python、Spark、Flink 等类型
- **Task Instance**：任务实例，任务的一次运行记录
- **Process Instance**：流程实例，工作流的一次运行记录
- **Tenant**：租户，指定任务在 Worker 上执行的操作系统用户

### 1.3 编程接口
- **PyDolphinScheduler**：Python SDK，支持三种方式定义工作流
  - 传统方式：使用 `Workflow` 和 `Task` 类构建 DAG
  - 装饰器方式：通过 `@task` 装饰器将 Python 函数包装为任务
  - YAML 文件：通过 CLI 工具 `pydolphinscheduler` 加载 YAML 定义

## 2. 关键机制

### 2.1 分布式调度架构
```
ApiServer → MasterServer (DAG 解析/任务分发) → ZooKeeper (任务队列)
                                                      ↓
WorkerServer ← ZooKeeper (任务领取) → 执行 Task → 状态回写 DB
```

- **Master 高可用**：多 Master 通过 ZooKeeper 进行 Leader 选举，Leader 负责调度决策
- **Worker 负载均衡**：Worker 向 ZooKeeper 注册，Master 根据 Worker 负载分配任务
- **任务队列**：使用 ZooKeeper 临时节点实现任务分发，保证 Exactly-Once 语义

### 2.2 工作流执行流程
1. **提交**：用户通过 API 或 SDK 提交工作流定义
2. **解析**：Master 解析 DAG，生成 Process Instance
3. **切分**：根据 DAG 依赖关系，生成 Task Instance 并放入队列
4. **分发**：Master 将 Task 写入 ZooKeeper 任务队列
5. **领取**：Worker 监听 ZooKeeper，领取并执行任务
6. **回调**：任务完成后，Worker 更新 DB 状态，Master 触发下游任务

### 2.3 任务依赖与触发
- **时间驱动**：基于 Cron 表达式定时调度
- **事件驱动**：支持依赖上游任务完成、外部系统回调等事件触发
- **DAG 依赖**：任务间通过 `set_downstream()` 或 `<<` 运算符定义依赖关系

### 2.4 容错机制
- **Master 故障**：ZooKeeper 重新选举 Leader，恢复未完成的任务
- **Worker 故障**：Master 检测到 Worker 心跳超时，将任务重新分发
- **任务重试**：支持配置失败重试次数和重试间隔

## 3. 常见问题与优化

### 3.1 性能瓶颈
| 问题 | 原因 | 优化方案 |
|------|------|----------|
| Master 调度延迟 | 任务数量过多，DAG 解析耗时 | 增加 Master 节点，调整 `master.exec.threads` |
| Worker 资源不足 | 任务并发过高，CPU/内存耗尽 | 增加 Worker 节点，调整 `worker.exec.threads` |
| ZooKeeper 压力 | 频繁的节点创建/删除 | 使用 ZooKeeper 集群，调整 session 超时时间 |
| 数据库慢查询 | 大量任务实例查询 | 定期清理历史数据，添加索引 |

### 3.2 常见错误处理
- **任务状态卡在 RUNNING**：检查 Worker 日志，确认是否因资源不足被 OOM Kill
- **依赖任务未触发**：检查上游任务状态是否为 SUCCESS，确认 DAG 定义是否正确
- **租户权限问题**：确保 Worker 节点上存在对应租户用户，且具有执行权限

### 3.3 配置优化建议
```yaml
# master.properties
master.exec.threads: 100          # 根据 CPU 核数调整
master.task.commit.retryTimes: 5  # 任务提交重试次数

# worker.properties
worker.exec.threads: 50           # 根据 Worker 资源调整
worker.max.cpuload.avg: -1        # -1 表示不限制 CPU 负载

# common.properties
support.hive.oneSession: true     # 开启 Hive 会话复用
```

## 4. 学习建议

### 4.1 学习路径
1. **基础入门**（1-2 天）
   - 阅读官方 Quick Start，部署单机版
   - 通过 Web UI 创建第一个工作流（Shell 任务）
   - 理解 DAG 依赖关系配置

2. **深入理解**（3-5 天）
   - 学习 PyDolphinScheduler 三种定义方式
   - 掌握任务类型（SQL、Spark、Flink 等）的配置参数
   - 阅读源码中 Master/Worker 的核心调度逻辑

3. **实践进阶**（1-2 周）
   - 搭建高可用集群（多 Master + 多 Worker）
   - 实现自定义任务插件
   - 对接企业告警系统（钉钉/企微）

### 4.2 推荐资源
- **官方文档**：https://dolphinscheduler.apache.org/
- **源码分析**：关注 `dolphinscheduler-master` 和 `dolphinscheduler-worker` 模块
- **社区实践**：GitHub Issues 中的 FAQ 和 PR 讨论

### 4.3 避坑指南
- 生产环境务必使用 ZooKeeper 集群，单节点存在单点故障风险
- 任务日志默认存储在本地，建议配置远程日志中心（如 S3、HDFS）
- 租户配置需与 Worker 节点操作系统用户一致，否则任务执行失败
- 避免在 DAG 中创建过多并行任务（建议单 DAG 不超过 1000 个节点）

> 来源：
> - [Apache DolphinScheduler](https://dolphinscheduler.apache.org/)
> - [Tutorial — apache-dolphinscheduler 4.1.0-dev documentation](https://dolphinscheduler.apache.org/python/tutorial.html)
> - [Apache DolphinScheduler：深入了解大数据调度工具 - 知乎 DolphinScheduler 工作原理与使用指南-CSDN博客 第 10 篇收官！| 调度系统的下一站：从时间驱动到事件驱动的演进之路-... 第 10 篇收官！| 调度系统的下一站：从时间驱动到事件驱动的演进之路_... DolphinScheduler - 核心原理、特点、以及架构详解](https://zhuanlan.zhihu.com/p/679197362)
