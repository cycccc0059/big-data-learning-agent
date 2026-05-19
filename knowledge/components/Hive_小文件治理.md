# Hive 小文件治理

> 由知识收集器自动生成。

```markdown
# Hive 小文件治理笔记

## 1. 核心概念

- **小文件**：指文件大小远小于 HDFS 块大小（默认 128MB）的文件。大量小文件会导致 NameNode 内存压力增大，并降低 MapReduce/Spark 作业性能。
- **小文件治理**：通过合并、压缩、控制写入等手段，减少小文件数量，优化存储和计算效率。
- **Hive 元数据**：Hive 表的分区、文件信息存储在 Metastore 中，小文件治理通常涉及元数据与底层文件系统的协调操作。

## 2. 关键机制

- **Hive 写入机制**：INSERT、CTAS（CREATE TABLE AS SELECT）等操作默认每个 reducer 或 mapper 生成一个文件。若并行度设置过高或数据量小，易产生大量小文件。
- **合并机制**：
  - **手动合并**：使用 `INSERT OVERWRITE` 重新写入表或分区，利用较少 reducer 合并小文件。
  - **自动合并**：通过配置 `hive.merge.mapfiles`、`hive.merge.mapredfiles`、`hive.merge.size.per.task` 等参数，在作业完成后触发合并。
- **分区与分桶**：合理设计分区粒度（如按天分区）和分桶数，可控制每个目录下的文件数量。
- **压缩**：使用压缩格式（如 ORC、Parquet）可减少文件大小，但需注意压缩块大小与 HDFS 块大小的匹配。

## 3. 常见问题与优化

### 常见问题
- **NameNode 压力**：大量小文件占用 NameNode 大量内存，影响集群稳定性。
- **作业启动慢**：MapReduce/Spark 作业需扫描大量小文件，导致任务调度和元数据读取开销增加。
- **数据倾斜**：小文件分布不均，导致部分节点负载过高。

### 优化策略
- **调整写入并行度**：
  - 控制 `mapred.reduce.tasks` 或 `spark.sql.shuffle.partitions` 数量，避免过多输出文件。
  - 使用 `DISTRIBUTE BY` 或 `CLUSTER BY` 对数据进行重分区，减少文件数。
- **启用自动合并**：
  ```sql
  SET hive.merge.mapfiles = true;       -- 仅 Map 任务
  SET hive.merge.mapredfiles = true;    -- MapReduce 任务
  SET hive.merge.size.per.task = 256000000; -- 合并后目标文件大小（字节）
  SET hive.merge.smallfiles.avgsize = 16000000; -- 小文件平均大小阈值
  ```
- **定期治理**：
  - 使用 `INSERT OVERWRITE` 重新写入表或分区，指定较少 reducer。
  - 利用 `ALTER TABLE ... CONCATENATE` 合并 ORC/Parquet 文件（仅支持部分格式）。
- **分区设计优化**：
  - 避免过细粒度分区（如按小时分区），建议按天或周分区。
  - 使用动态分区时，限制 `hive.exec.max.dynamic.partitions` 防止生成过多空分区。
- **使用压缩格式**：
  - ORC 和 Parquet 支持文件内 stripe/row group 合并，减少小文件影响。
  - 配置 `hive.exec.orc.compression.snapshot` 等参数优化压缩。

## 4. 学习建议

- **理解 HDFS 特性**：掌握 HDFS 块大小、NameNode 内存模型，有助于理解小文件问题的根源。
- **实践合并操作**：在测试环境模拟小文件场景，尝试手动合并和自动合并参数调优。
- **关注版本差异**：Hive 不同版本对合并、压缩的支持有差异（如 Hive 2.x 与 3.x），查阅官方文档 `LanguageManual DDL` 和 `AdminManual Configuration`。
- **结合监控工具**：使用 HDFS 的 `fsck` 命令或 Ambari/Grafana 监控小文件数量，制定治理计划。
- **阅读源码与社区**：关注 Hive JIRA 中小文件相关 issue（如 HIVE-11703），了解最新优化进展。
```

> 来源：
> - [Apache Hive : LanguageManual DDL](https://hive.apache.org/docs/latest/language/languagemanual-ddl/)
> - [Apache Hive : AdminManual Configuration](https://hive.apache.org/docs/latest/admin/adminmanual-configuration/)
> - [LanguageManual SubQueries - Apache Hive - Apache Software...](https://cwiki.apache.org/confluence/display/Hive/LanguageManual+SubQueries)
