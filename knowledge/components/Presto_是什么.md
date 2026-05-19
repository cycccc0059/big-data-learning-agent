# Presto 是什么

> 由知识收集器自动生成。

# Presto 笔记：分布式 SQL 查询引擎

## 1. 核心概念

### 1.1 定义
Presto（PrestoDB）是一种**开源的分布式 SQL 查询引擎**，专为对任意规模的数据进行快速分析查询而设计。它不存储数据，而是通过连接器与各种数据源通信，实现“数据在哪里，查询就在哪里”的能力。

### 1.2 核心特性
- **SQL-on-Anything**：支持查询关系型（MySQL、PostgreSQL、Redshift、SQL Server、Teradata）和非关系型（HDFS、S3、Cassandra、MongoDB、HBase、Kafka）数据源
- **ANSI SQL 兼容**：支持标准 SQL 语义，包括 JOIN、子查询、聚合、窗口函数、近似百分位数等
- **纯内存计算**：所有处理在内存中完成，以流水线方式跨网络阶段执行，避免不必要的 I/O 开销
- **MPP 架构**：采用经典的大规模并行处理设计，协调器节点调度查询到多个工作节点并行执行

### 1.3 适用场景
- 交互式分析查询（秒级响应）
- 跨数据源的联邦查询
- BI 工作负载优化
- 替代或补充 Hive 进行 PB 级数据查询

### 1.4 典型用户
Facebook（每天 30,000+ 查询，处理 1PB 数据）、Netflix（每天约 3,500 查询）、Airbnb、Atlassian、Nasdaq、Microsoft、Apple、AWS（Athena 和 EMR 底层引擎）

---

## 2. 关键机制

### 2.1 系统架构
Presto 集群由三种服务器类型组成：

| 组件 | 职责 |
|------|------|
| **协调器（Coordinator）** | 解析 SQL、规划查询、管理工作节点、从工作节点检索结果并返回客户端 |
| **工作节点（Worker）** | 执行查询任务、从数据源读取数据、节点间数据交换 |
| **资源管理器（Resource Manager）** | 收集所有节点数据，创建集群全局视图 |

### 2.2 查询执行流程
1. 用户提交 SQL 查询到协调器
2. 协调器解析语句，生成分布式查询计划
3. 将查询计划拆分为多个阶段，调度到工作节点
4. 工作节点在内存中并行执行，以流水线方式跨网络传递数据
5. 协调器汇总结果返回客户端

### 2.3 存储抽象与连接器
- **数据抽象**：将数据的表示与物理存储分离，使查询引擎专注于查询逻辑
- **连接器模式**：即插即用，每个数据源对应一个连接器，实现跨数据源统一查询
- 支持的数据源包括：HDFS、S3、Cassandra、MongoDB、HBase、MySQL、PostgreSQL、Redshift、SQL Server、Teradata、Kafka

### 2.4 与 Hadoop/Hive 的关系
- Presto **不替代 Hadoop**，而是与其互补
- 解决 Hive 交互式查询性能不足的问题（Hive 基于 MapReduce，写入磁盘；Presto 基于内存，流水线执行）
- 可部署在任何 Hadoop 发行版上

---

## 3. 常见问题与优化

### 3.1 性能优化要点
- **内存管理**：合理配置 `query.max-memory-per-node` 和 `query.max-total-memory-per-node`
- **并行度调优**：根据集群规模调整 `task.concurrency` 和 `task.max-worker-threads`
- **数据本地性**：确保工作节点与数据存储节点尽量靠近，减少网络传输
- **连接器优化**：为不同数据源选择合适的连接器配置（如 Hive 连接器的分区裁剪）

### 3.2 常见问题
| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 查询超时 | 数据量过大或内存不足 | 增加工作节点、优化 SQL、调整超时参数 |
| OOM（内存溢出） | 查询涉及大量聚合或 JOIN | 启用内存限制、拆分查询、使用近似聚合函数 |
| 跨数据源查询慢 | 网络延迟或数据源性能瓶颈 | 使用数据源侧过滤、考虑数据预聚合 |
| 连接器配置错误 | 数据源认证或参数不匹配 | 检查连接器配置文档，确保版本兼容 |

### 3.3 成本优化
- Presto 开源免费，可显著降低数据仓库成本（IBM 白皮书指出可降低成本高达 50%）
- 云部署（如 AWS Athena）按查询付费，无需管理基础设施
- 针对大量小型查询优化，适合 BI 场景

---

## 4. 学习建议

### 4.1 学习路径
1. **基础概念**：理解 MPP 架构、内存计算、连接器模式
2. **环境搭建**：本地部署单节点 Presto，连接 MySQL 或 PostgreSQL 进行实践
3. **SQL 实践**：掌握 Presto 支持的 ANSI SQL 语法，重点练习 JOIN、窗口函数、近似聚合
4. **性能调优**：学习查询计划分析（EXPLAIN）、内存配置、并行度调整
5. **生产部署**：了解集群规划、监控（JMX）、高可用配置

### 4.2 推荐资源
- **官方文档**：PrestoDB 官方 GitHub 和文档
- **云平台实践**：AWS Athena（无服务器 Presto）、Amazon EMR（托管集群）
- **社区资源**：Presto 论坛、Facebook Presto 页面
- **工具链**：Airbnb 开源的 Airpal（基于 Web 的查询工具）

### 4.3 进阶方向
- 对比学习：Presto vs Trino（Presto 的分支）、Presto vs Spark SQL、Presto vs ClickHouse
- 源码阅读：理解协调器调度、连接器 SPI、内存管理实现
- 扩展开发：编写自定义连接器、UDF 函数

### 4.4 注意事项
- Presto 不存储数据，需要搭配存储系统使用
- 不适合 ETL 场景（无数据写入能力）
- 对内存敏感，需要合理规划资源
- 版本演进较快，注意社区版本选择（PrestoDB vs PrestoSQL/Trino）

> 来源：
> - [面试官要求我了解过Presto——Presto到底是个什么东西 - 知乎](https://zhuanlan.zhihu.com/p/397641643)
> - [什么是 Presto？| IBM](https://www.ibm.com/cn-zh/think/topics/presto)
> - [什么是 Presto？- PrestoDB 简介 - AWS](https://aws.amazon.com/cn/what-is/presto/)
