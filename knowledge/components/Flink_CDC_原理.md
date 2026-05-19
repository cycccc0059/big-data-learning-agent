# Flink CDC 原理

> 由知识收集器自动生成。

# Flink CDC 原理笔记

## 1. 核心概念

### 1.1 什么是 Flink CDC
Flink CDC（Change Data Capture）是 Apache Flink 提供的实时数据变更捕获框架，能够从数据库（如 MySQL、PostgreSQL、Oracle 等）中实时捕获数据变更事件（INSERT、UPDATE、DELETE），并将其转换为 Flink 可处理的流式数据。

### 1.2 核心特性
- **实时增量同步**：无需全量扫描，基于数据库日志（如 Binlog）捕获变更
- **Exactly-Once 语义**：保证数据不丢不重
- **Schema 自动演进**：支持源表结构变更的自动适配
- **无锁读取**：不阻塞源数据库的正常读写操作

### 1.3 架构组件
| 组件 | 说明 |
|------|------|
| **Source Connector** | 连接数据库，读取变更日志 |
| **Debezium** | 底层 CDC 引擎，解析数据库日志格式 |
| **Flink Runtime** | 分布式流处理引擎，负责状态管理和容错 |
| **Sink Connector** | 将变更数据写入目标系统（Kafka、Doris、ES 等） |

---

## 2. 关键机制

### 2.1 数据捕获流程
```mermaid
graph LR
    A[数据库] --> B[Binlog/Redo Log]
    B --> C[Debezium 解析]
    C --> D[Flink Source]
    D --> E[Flink 算子处理]
    E --> F[目标系统]
```

1. **日志读取**：Source Connector 连接数据库，持续读取变更日志
2. **事件解析**：Debezium 将日志解析为结构化变更事件（包含 before/after 镜像）
3. **状态管理**：Flink 维护读取偏移量（Offset），支持故障恢复
4. **数据输出**：处理后的变更事件写入下游系统

### 2.2 状态管理与容错
- **Checkpoint 机制**：周期性保存 Source 偏移量和算子状态，实现 Exactly-Once
- **Savepoint**：手动触发的状态快照，用于版本升级或作业暂停
- **增量 Checkpoint**：仅保存变更的状态部分，减少存储开销

### 2.3 事件时间处理
- **Event Time**：基于数据本身的时间戳（如 Binlog 中的事务时间）
- **Watermark**：处理乱序数据，控制延迟数据容忍度
- **Out-of-Order Handling**：支持配置迟到数据的处理策略（丢弃、侧输出等）

### 2.4 全量+增量一体化
- **全量阶段**：首次启动时，通过 JDBC 读取历史数据
- **增量阶段**：全量完成后，无缝切换至日志捕获模式
- **断点续传**：全量阶段也支持 Checkpoint，避免重复读取

---

## 3. 常见问题与优化

### 3.1 性能瓶颈
| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 全量读取慢 | 大表无索引或网络带宽不足 | 增加并行度、使用分片策略、调整 fetch-size |
| 增量延迟高 | 数据库日志保留时间短或写入压力大 | 增大 server-id 范围、优化数据库参数 |
| 状态过大 | 长时间运行导致状态膨胀 | 启用增量 Checkpoint、调整状态 TTL |
| 数据倾斜 | 分片不均匀或热点 Key | 自定义分区策略、使用 Rescale 算子 |

### 3.2 常见配置优化
```yaml
# 并行度设置
source.parallelism: 4

# 全量阶段优化
scan.incremental.snapshot.chunk.size: 8096
scan.snapshot.fetch.size: 1024

# 增量阶段优化
debezium.snapshot.locking.mode: none
debezium.heartbeat.interval.ms: 5000

# 状态管理
state.backend: rocksdb
state.checkpoints.dir: hdfs:///flink/checkpoints
execution.checkpointing.interval: 60000
```

### 3.3 数据一致性问题
- **重复数据**：启用幂等写入或使用 Upsert 语义
- **数据丢失**：确保 Checkpoint 间隔合理，Source 支持 Exactly-Once
- **Schema 变更**：使用 `include.schema.changes: true` 自动处理

---

## 4. 学习建议

### 4.1 前置知识
- 熟悉 Flink DataStream API 和 SQL
- 了解数据库日志机制（MySQL Binlog、PostgreSQL WAL）
- 掌握 Kafka 基础概念（作为中间件场景）

### 4.2 学习路径
1. **入门阶段**
   - 阅读 [Flink CDC 官方文档](https://flink.apache.org/cdc/)
   - 运行 MySQL CDC 示例：`flink-cdc-connectors` 中的 Quickstart
   - 理解 Debezium 的事件格式（JSON/AVRO）

2. **进阶阶段**
   - 学习多表同步和整库同步方案
   - 掌握动态表（Dynamic Table）和变更日志流（Changelog Stream）
   - 实践 Flink SQL CDC 语法：`CREATE TABLE ... WITH ('connector'='mysql-cdc')`

3. **实战阶段**
   - 搭建实时数仓：MySQL → Flink CDC → Kafka → Doris/ClickHouse
   - 处理复杂场景：分库分表合并、数据清洗、类型转换
   - 监控与调优：Flink Web UI 分析、Metrics 监控、日志排查

### 4.3 推荐资源
- **官方文档**：[Flink CDC 文档](https://nightlies.apache.org/flink/flink-cdc-docs-stable/)
- **源码仓库**：[flink-cdc-connectors](https://github.com/apache/flink-cdc-connectors)
- **社区博客**：Flink 官方博客中的 CDC 系列文章
- **实践案例**：阿里巴巴、字节跳动等公司的 CDC 落地分享

### 4.4 常见陷阱
- 忽略数据库日志保留时间，导致增量阶段失败
- 全量阶段未设置合理的分片策略，导致 OOM
- 未处理 Schema 变更，导致作业崩溃
- 未启用 Checkpoint，故障后无法恢复

> 来源：
> - [Apache Flink - Wikipedia](https://en.wikipedia.org/wiki/Apache_Flink)
> - [Apache Flink ® — Stateful Computations over Data Streams](https://flink.apache.org/)
> - [What is Apache Flink ? - Apache Flink Explained - AWS](https://aws.amazon.com/what-is/apache-flink/)
