# Apache Flink

> 此文件由知识收集器自动生成和更新。你也可以手动编辑。

## 核心概念

Flink 是一个分布式流处理框架，以"有状态的流处理"为核心，同时支持批处理。

## 关键机制

### Checkpoint
- 分布式快照机制（基于 Chandy-Lamport 算法）
- 保证 exactly-once 语义
- 关键参数：间隔时间、超时时间、最小暂停时间

### Savepoint
- 手动触发的检查点
- 用于升级、迁移、A/B 测试

### 反压（Backpressure）
- 下游消费慢导致上游发送阻塞
- 排查：看 Web UI 的反压状态、Kafka lag、下游写入性能

### 状态后端
- MemoryStateBackend、FsStateBackend、RocksDBStateBackend

## 常见问题

1. Checkpoint 失败 — 超时、状态过大、存储不可用
2. 延迟升高 — 反压、外部 IO 慢、状态访问慢
3. 数据倾斜 — keyBy 后某些并行度压力大

## 学习资源
<!-- 知识收集器会将网络资料自动追加到此处 -->
