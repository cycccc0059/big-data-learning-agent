# HDFS 架构原理

> 由知识收集器自动生成。

# HDFS 架构原理笔记

## 1. 核心概念

### 1.1 什么是 HDFS

HDFS（Hadoop Distributed File System）是 Apache Hadoop 的核心存储系统，设计运行在通用硬件上，具有高容错性、高吞吐量的特点，适用于存储和处理超大规模数据集。

### 1.2 设计目标与假设

| 目标 | 说明 |
|------|------|
| **硬件故障常态化** | 集群包含成百上千台机器，组件故障是常态而非例外，系统必须能快速自动检测和恢复 |
| **流式数据访问** | 面向批处理而非交互式使用，强调数据的高吞吐量而非低延迟 |
| **大数据集支持** | 单个文件可达 TB/PB 级别，单集群可存储 PB 级数据 |
| **简化一致性模型** | 采用"一次写入、多次读取"模型，简化数据一致性保证 |
| **移动计算优于移动数据** | 将计算逻辑移动到数据所在节点执行，减少网络传输开销 |
| **跨平台可移植性** | 支持异构硬件和软件平台 |

### 1.3 核心组件

#### NameNode（名称节点）
- **主节点**，管理文件系统命名空间和元数据
- 维护文件到数据块的映射关系
- 控制客户端对文件的访问
- 管理 DataNode 的心跳和块报告

#### DataNode（数据节点）
- **从节点**，实际存储数据块
- 负责处理客户端的读写请求
- 定期向 NameNode 发送心跳和块报告
- 执行数据块的创建、复制和删除操作

### 1.4 数据块（Block）

- 默认块大小：**128 MB**（早期版本为 64 MB）
- 大块设计减少寻址开销，提升吞吐量
- 每个块独立存储，便于分布式处理和容错

### 1.5 数据复制（Replication）

- 默认复制因子：**3**
- 每个数据块在集群中保存多个副本
- 副本分布在不同节点上，确保容错性

## 2. 关键机制

### 2.1 副本放置策略

**第一副本**：放置在客户端所在节点（若客户端在集群外，则随机选择）
**第二副本**：放置在与第一副本不同机架的节点上
**第三副本**：放置在与第二副本相同机架的不同节点上

> 这种策略在保证容错性的同时，平衡了写入性能和读取性能。

### 2.2 数据写入流程（流水线复制）

```
客户端 → DataNode A → DataNode B → DataNode C
```

1. 客户端向 NameNode 请求写入权限
2. NameNode 返回可写入的 DataNode 列表
3. 客户端将数据写入第一个 DataNode
4. 第一个 DataNode 将数据转发给第二个，依此类推
5. 所有副本写入完成后，客户端收到确认

### 2.3 数据读取机制

- 客户端向 NameNode 获取数据块的位置信息
- 优先选择与客户端最近的副本（同机架优先）
- 直接从 DataNode 读取数据

### 2.4 心跳与块报告

- DataNode 每 **3 秒** 向 NameNode 发送心跳
- 若 NameNode 超过 **10 分钟** 未收到心跳，判定该 DataNode 失效
- DataNode 定期发送块报告，包含其存储的所有块信息

### 2.5 安全模式（Safemode）

- NameNode 启动时进入安全模式
- 等待 DataNode 报告块信息
- 当满足最小副本条件的块比例达到阈值（默认 99.9%）时退出安全模式
- 安全模式下不允许修改文件系统

### 2.6 元数据持久化

- **FsImage**：文件系统元数据的快照
- **EditLog**：记录所有元数据变更操作日志
- NameNode 启动时合并 FsImage 和 EditLog
- Secondary NameNode 定期合并并生成新的 FsImage

## 3. 常见问题与优化

### 3.1 数据容错与恢复

| 故障类型 | 处理机制 |
|----------|----------|
| DataNode 故障 | NameNode 检测到心跳超时后，将失效节点上的块标记为"待复制"，在其他节点上创建新副本 |
| 数据块损坏 | 客户端读取时校验 CRC，发现损坏后从其他副本读取并通知 NameNode |
| NameNode 故障 | 单点故障（SPOF），可通过 HDFS HA（高可用）配置解决 |

### 3.2 集群再平衡

- 当新增或移除节点时，数据分布可能不均匀
- 使用 `balancer` 工具手动触发再平衡
- 调整带宽限制避免影响正常业务

### 3.3 数据完整性

- 每个数据块写入时计算 **CRC32** 校验和
- 读取时验证校验和，确保数据完整性
- DataNode 后台定期校验数据块

### 3.4 空间回收

**文件删除机制**：
1. 文件被移动到 `/trash` 目录（可配置保留时间）
2. 在保留期内可恢复
3. 过期后真正删除，释放空间

**副本因子降低**：
- 减少副本数时，NameNode 选择多余的副本删除
- 优先删除同一机架内的多余副本

### 3.5 性能优化建议

| 优化方向 | 具体措施 |
|----------|----------|
| 块大小调整 | 根据文件平均大小调整块大小（128 MB ~ 256 MB） |
| 副本因子 | 对非关键数据可降低副本数（如 2） |
| 机架感知 | 配置网络拓扑，优化数据本地性 |
| 缓冲区调优 | 调整 `dfs.buffer.size` 和 `io.file.buffer.size` |
| 压缩 | 对中间数据和结果数据启用压缩 |

## 4. 学习建议

### 4.1 前置知识要求

- 理解分布式系统基本概念（CAP 理论、一致性模型）
- 熟悉 Linux 基本操作和网络基础知识
- 了解 Java 编程基础（HDFS 使用 Java 实现）

### 4.2 学习路径

1. **基础阶段**
   - 搭建单节点 Hadoop 环境
   - 掌握 HDFS Shell 命令（`hdfs dfs -ls`, `-put`, `-get` 等）
   - 理解数据读写流程

2. **进阶阶段**
   - 搭建多节点集群
   - 配置机架感知和高可用
   - 理解 NameNode 元数据管理机制
   - 学习 HDFS API 编程

3. **深入阶段**
   - 研究 HDFS 源码（RPC 通信、块管理、副本策略）
   - 学习 HDFS Federation（联邦架构）
   - 了解 HDFS 与对象存储（如 S3）的对比

### 4.3 实践建议

- **动手搭建**：在虚拟机或云环境搭建 3 节点集群
- **故障演练**：模拟 DataNode 宕机，观察副本恢复过程
- **性能测试**：使用 `TestDFSIO` 工具测试读写性能
- **监控配置**：配置 NameNode Web UI 和日志监控

### 4.4 常见误区

| 误区 | 正确理解 |
|------|----------|
| HDFS 适合小文件 | HDFS 针对大文件优化，小文件会占用大量 NameNode 内存 |
| HDFS 是通用文件系统 | HDFS 是"一次写入、多次读取"模型，不支持随机修改 |
| 副本越多越好 | 副本增加写入开销和存储成本，需权衡 |
| NameNode 无单点问题 | 默认配置下 NameNode 是 SPOF，需配置 HA |

### 4.5 推荐资源

- **官方文档**：Apache Hadoop HDFS Architecture Guide
- **书籍**：《Hadoop: The Definitive Guide》
- **实践平台**：Cloudera QuickStart VM、Hortonworks Sandbox
- **社区**：Apache Hadoop 邮件列表、Stack Overflow

> 来源：
> - [HDFS Architecture Guide - Apache Hadoop](https://hadoop.apache.org/docs/r1.2.1/hdfs_design.html)
> - [HDFS (Hadoop Distributed File System ) - GeeksforGeeks](https://www.geeksforgeeks.org/big-data/hadoop-hdfs-hadoop-distributed-file-system/)
> - [What is a Hadoop Distributed File System (HDFS )? | Databricks](https://www.databricks.com/blog/what-is-hdfs)
