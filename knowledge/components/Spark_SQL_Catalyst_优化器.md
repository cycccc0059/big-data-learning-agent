# Spark SQL Catalyst 优化器

> 由知识收集器自动生成。

# Spark SQL Catalyst 优化器笔记

## 1. 核心概念

### 1.1 Catalyst 优化器概述
Catalyst 是 Spark SQL 的可扩展查询优化框架，基于 **Scala 的模式匹配** 和 **树形结构** 构建。它将 SQL 或 DataFrame 操作转换为物理执行计划，并应用一系列规则进行优化。

### 1.2 核心组件
- **逻辑计划（Logical Plan）**：描述“做什么”的抽象表示，不涉及具体执行方式
- **物理计划（Physical Plan）**：描述“怎么做”的具体执行策略
- **优化规则（Optimization Rules）**：对逻辑/物理计划进行转换的规则集合
- **代价模型（Cost Model）**：用于评估不同执行计划的代价

### 1.3 优化阶段
1. **分析（Analysis）**：解析 SQL 语法树，绑定元数据（表、列、类型）
2. **逻辑优化（Logical Optimization）**：应用规则优化逻辑计划（谓词下推、列剪枝等）
3. **物理规划（Physical Planning）**：将逻辑计划转换为物理计划，选择执行策略
4. **代码生成（Code Generation）**：将物理计划编译为 Java 字节码（WholeStageCodegen）

---

## 2. 关键机制

### 2.1 分区优化（Partitioning Hints）
通过提示控制数据分区策略，优化数据分布和文件大小：

| Hint | 功能 | 参数 | 说明 |
|------|------|------|------|
| `COALESCE(N)` | 减少分区数到 N | 分区数 | 避免数据移动，适合合并小分区 |
| `REPARTITION(N, col)` | 按指定列重新分区 | 分区数、列名 | 全量 shuffle，适合数据倾斜 |
| `REPARTITION_BY_RANGE(col, N)` | 按范围分区 | 列名、可选分区数 | 避免全量 shuffle，适合有序数据 |
| `REBALANCE(col)` | 自动平衡分区大小 | 可选列名 | 依赖 AQE，自动拆分倾斜分区 |

**示例**：
```sql
SELECT /*+ REPARTITION(100, department) */ * FROM employees;
SELECT /*+ COALESCE(50) */ * FROM large_table;
```

### 2.2 连接优化（Join Hints）
控制 Join 策略选择，覆盖优化器默认决策：

| Hint | 策略 | 适用场景 |
|------|------|----------|
| `BROADCAST` | 广播小表 | 小表 < spark.sql.autoBroadcastJoinThreshold |
| `MERGE` | Sort Merge Join | 大表等值连接，数据已排序 |
| `SHUFFLE_HASH` | Shuffled Hash Join | 中等大小表，无排序需求 |
| `SHUFFLE_REPLICATE_NL` | 笛卡尔积/非等值连接 | 小表非等值连接 |

**示例**：
```sql
SELECT /*+ BROADCAST(dim) */ fact.*, dim.name 
FROM fact JOIN dim ON fact.key = dim.key;
```

### 2.3 自适应查询执行（AQE）
Spark 3.0+ 引入的运行时优化框架，动态调整执行计划：

| 特性 | 机制 | 配置参数 |
|------|------|----------|
| **动态合并分区** | 自动合并小 shuffle 分区 | `spark.sql.adaptive.coalescePartitions.enabled` |
| **动态拆分倾斜分区** | 自动拆分数据倾斜分区 | `spark.sql.adaptive.skewJoin.enabled` |
| **动态转换 Join 策略** | 将 SMJ 转为 BHJ 或 SHJ | `spark.sql.adaptive.convertToBroadcastJoin.enabled` |

**关键配置**：
```properties
spark.sql.adaptive.enabled=true
spark.sql.adaptive.coalescePartitions.parallelismFirst=false
spark.sql.adaptive.advisoryPartitionSizeInBytes=64MB
```

### 2.4 统计信息与代价优化
- **表统计**：通过 `ANALYZE TABLE` 收集行数、大小、列统计
- **列统计**：直方图、NDV（不同值数量）、空值比例
- **Hive 元存储集成**：自动读取 Hive 统计信息

**示例**：
```sql
ANALYZE TABLE sales COMPUTE STATISTICS;
ANALYZE TABLE sales COMPUTE STATISTICS FOR COLUMNS product_id, amount;
```

---

## 3. 常见问题与优化

### 3.1 数据倾斜
**现象**：某些任务运行时间远长于其他任务

**解决方案**：
1. **使用 AQE 倾斜 Join**：`spark.sql.adaptive.skewJoin.enabled=true`
2. **手动加盐**：对倾斜键添加随机前缀
3. **REBALANCE Hint**：`SELECT /*+ REBALANCE */ * FROM skewed_table`

### 3.2 小文件问题
**现象**：输出大量小文件，影响下游读取性能

**解决方案**：
1. **COALESCE Hint**：`SELECT /*+ COALESCE(10) */ * FROM source`
2. **调整分区大小**：`spark.sql.files.maxPartitionBytes=256MB`
3. **使用 AQE 动态合并**：启用 `coalescePartitions`

### 3.3 Join 策略选择不当
**现象**：大表广播导致 OOM，或小表未广播导致大量 shuffle

**解决方案**：
1. **显式指定 Join Hint**：`BROADCAST` 或 `MERGE`
2. **调整广播阈值**：`spark.sql.autoBroadcastJoinThreshold=50MB`
3. **启用 AQE 动态转换**：自动将 SMJ 转为 BHJ

### 3.4 谓词下推失效
**现象**：过滤条件未下推到数据源，导致全表扫描

**检查方法**：
```sql
EXPLAIN EXTENDED SELECT * FROM t WHERE col > 10;
-- 查看 Filter 节点是否出现在 Scan 之前
```

**优化**：
- 确保数据源支持谓词下推（Parquet、ORC、JDBC）
- 避免在过滤列上使用函数包装：`WHERE UPPER(name) = 'A'` → `WHERE name = 'a'`

---

## 4. 学习建议

### 4.1 实践路径
1. **基础阶段**：掌握 EXPLAIN 命令解读执行计划
   ```sql
   EXPLAIN FORMATTED SELECT ...;
   ```
2. **进阶阶段**：使用 Spark UI 的 SQL 标签页分析物理计划
3. **高级阶段**：自定义 Catalyst 优化规则（实现 `Rule[LogicalPlan]`）

### 4.2 调试技巧
- **查看优化规则**：`spark.sql.optimizer.maxIterations=100`
- **禁用特定规则**：`spark.sql.optimizer.excludedRules=org.apache.spark.sql.catalyst.optimizer.ConstantFolding`
- **打印优化日志**：`spark.sql.optimizer.logLevel=TRACE`

### 4.3 关键配置速查
| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `spark.sql.adaptive.enabled` | true | 启用 AQE |
| `spark.sql.autoBroadcastJoinThreshold` | 10MB | 广播 Join 阈值 |
| `spark.sql.files.maxPartitionBytes` | 128MB | 文件读取分区大小 |
| `spark.sql.shuffle.partitions` | 200 | Shuffle 分区数 |
| `spark.sql.adaptive.coalescePartitions.initialPartitionNum` | 200 | AQE 初始分区数 |

### 4.4 推荐资源
- **官方文档**：Spark SQL Guide 的 Performance Tuning 章节
- **源码阅读**：`org.apache.spark.sql.catalyst.optimizer` 包
- **实践项目**：对 TPCH/TPCDS 查询进行 EXPLAIN 分析并优化

> 来源：
> - [Hints - Spark 4.1.1 Documentation](https://spark.apache.org/docs/latest/sql-ref-syntax-qry-select-hints.html)
> - [Performance Tuning - Spark 4.1.1 Documentation](https://spark.apache.org/docs/latest/sql-performance-tuning.html)
> - [Apache Spark - Wikipedia](https://en.wikipedia.org/wiki/Apache_Spark)
