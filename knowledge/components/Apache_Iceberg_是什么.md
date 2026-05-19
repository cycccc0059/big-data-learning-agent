# Apache Iceberg 是什么

> 由知识收集器自动生成。

# Apache Iceberg 笔记

## 1. 核心概念

Apache Iceberg 是一种**高性能开放表格式**，专为大规模分析型数据集设计。它将 SQL 表的可靠性和简洁性引入大数据领域，支持多个计算引擎（Spark、Trino、Flink、Presto、Hive、Impala）同时安全操作同一张表。

### 关键特性
- **开放格式**：非绑定特定引擎，支持多引擎并发读写
- **高性能**：针对 PB 级表优化，支持文件级跳过和分区裁剪
- **ACID 语义**：提供快照隔离和事务一致性

## 2. 关键机制

### 2.1 表达性 SQL
支持灵活的数据操作命令：
- `MERGE INTO`：合并新数据、更新现有行、执行定向删除
- 支持两种更新策略：
  - **Eager 重写**：立即重写数据文件以优化读取性能
  - **Delete Delta**：使用删除增量文件实现快速更新

```sql
MERGE INTO prod.nyc.taxis pt
USING (SELECT * FROM staging.nyc.taxis) st
ON pt.id = st.id
WHEN NOT MATCHED THEN INSERT *;
```

### 2.2 全模式演进
- 添加列不会产生“僵尸数据”
- 支持列重命名和重新排序
- **无需重写表**即可完成所有模式变更

```sql
ALTER TABLE taxis ALTER COLUMN trip_distance TYPE double;
ALTER TABLE taxis ALTER COLUMN trip_distance AFTER fare;
ALTER TABLE taxis RENAME COLUMN trip_distance TO distance;
```

### 2.3 隐藏分区
- 自动处理分区值的生成，无需用户手动指定
- 自动跳过不必要的分区和文件
- 无需额外过滤器即可实现快速查询
- 表布局可随数据或查询模式动态调整

### 2.4 时间旅行与回滚
- **时间旅行**：使用相同表快照实现可重复查询，或检查历史变更
- **版本回滚**：快速将表重置到良好状态以纠正问题

```sql
-- 按版本查询
SELECT count(*) FROM nyc.taxis FOR VERSION AS OF 2188465307835585443;

-- 按时间戳查询
SELECT count(*) FROM nyc.taxis FOR TIMESTAMP AS OF TIMESTAMP '2022-01-01 00:00:00.000000 Z';
```

### 2.5 数据压缩
- 内置支持数据文件压缩
- 提供多种重写策略：**装箱（bin-packing）**、**排序（sorting）** 等
- 优化文件布局和大小

```sql
CALL system.rewrite_data_files("nyc.taxis");
```

## 3. 常见问题与优化

### 3.1 文件大小管理
- **问题**：小文件过多导致元数据膨胀和查询性能下降
- **优化**：定期执行数据压缩（`rewrite_data_files`），合并小文件为合理大小（建议 128MB-1GB）

### 3.2 分区策略选择
- **问题**：分区粒度过细或过粗影响查询性能
- **优化**：利用隐藏分区特性，根据查询模式动态调整分区布局；避免手动维护分区逻辑

### 3.3 并发写入冲突
- **问题**：多引擎同时写入可能导致冲突
- **优化**：利用 Iceberg 的乐观并发控制，合理设置重试策略；使用分支和标签（Branching & Tagging）管理不同写入路径

### 3.4 快照管理
- **问题**：过多历史快照占用存储空间
- **优化**：配置快照保留策略，定期清理过期快照；使用 `expire_snapshots` 过程

## 4. 学习建议

### 4.1 基础入门
1. **官方 Quickstart**：从 Spark、Flink、Hive 的快速入门开始，理解基本读写操作
2. **核心概念文档**：深入理解 Tables、Schemas、Partitioning、Snapshots 等概念
3. **动手实践**：在本地或云环境搭建 Iceberg + Spark/Flink 环境，运行示例代码

### 4.2 进阶学习
1. **性能调优**：学习文件布局优化、压缩策略、查询下推等高级特性
2. **多引擎集成**：掌握 Iceberg 与 Spark、Flink、Trino、Presto 的集成细节
3. **运维管理**：学习快照管理、元数据维护、监控指标（Metrics Reporting）

### 4.3 实战建议
- 从**小规模数据**开始，逐步扩展到 PB 级场景
- 关注**社区动态**（GitHub、Slack、YouTube），了解最新特性和最佳实践
- 阅读**Specification**文档，深入理解 Iceberg 的底层设计原理
- 对比学习：与 Delta Lake、Hudi 等其他表格式进行对比，理解各自优劣

### 4.4 推荐资源
- 官方文档：https://iceberg.apache.org/docs/latest/
- 社区：GitHub Issues、Slack 频道
- 第三方集成：Apache Amoro 等生态工具

> 来源：
> - [Apache Iceberg - Apache Iceberg](https://iceberg.apache.org/)
> - [Apache Iceberg - Apache Iceberg](https://iceberg.apache.org/?gclsrc=aw.ds)
> - [Apache Iceberg 解析，一文了解Iceberg定义、应用及未来发展](https://zhuanlan.zhihu.com/p/32985088890)
