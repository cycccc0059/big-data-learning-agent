# Spark 内存管理调优

> 由知识收集器自动生成。

```markdown
# Spark 内存管理调优笔记

## 1. 核心概念

Spark 计算的内存密集型特性决定了其性能瓶颈通常出现在 CPU、网络带宽或内存。当数据能完全放入内存时，瓶颈多为网络带宽；否则，需通过调优（如序列化存储 RDD）来降低内存占用。

- **数据序列化**：影响网络性能与内存使用的关键因素。序列化格式的速度和大小直接决定计算效率。
- **内存管理**：涉及对象内存总量、访问开销及垃圾回收（GC）开销的平衡。

## 2. 关键机制

### 2.1 数据序列化

Spark 提供两种序列化库：

| 特性 | Java 序列化 | Kryo 序列化 |
|------|-------------|-------------|
| 默认 | 是 | 否 |
| 速度 | 慢 | 快（可达 10 倍） |
| 紧凑性 | 差 | 高 |
| 支持类型 | 所有实现 `Serializable` 的类 | 需提前注册类 |
| 配置 | 无需额外设置 | `spark.serializer` 设为 `org.apache.spark.serializer.KryoSerializer` |

- **Kryo 注册**：通过 `conf.registerKryoClasses()` 注册自定义类。未注册时仍可工作，但会存储完整类名，造成浪费。
- **缓冲区大小**：若对象较大，需增加 `spark.kryoserializer.buffer` 配置。
- **内部使用**：从 Spark 2.0.0 起，对简单类型、数组及字符串的 Shuffle 已默认使用 Kryo。

### 2.2 内存管理

- **对象开销**：Java 对象比原始数据多消耗 2-5 倍空间，原因包括对象头、对齐填充等。
- **GC 压力**：对象周转率高时，GC 成为性能瓶颈。
- **序列化 RDD 存储**：以序列化形式存储 RDD 可减少内存占用，但会增加 CPU 开销。

### 2.3 Spark SQL 缓存

- **列式缓存**：通过 `cacheTable()` 或 `DataFrame.cache()` 实现，自动选择压缩编码，减少内存与 GC 压力。
- **配置项**：
  - `spark.sql.inMemoryColumnarStorage.compressed`：是否自动选择压缩编码（默认 true）。
  - `spark.sql.inMemoryColumnarStorage.batchSize`：列式缓存批大小（默认 10000），增大可提升内存利用率，但可能引发 OOM。

### 2.4 分区调优

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `spark.sql.files.maxPartitionBytes` | 128 MB | 读取文件时单个分区的最大字节数 |
| `spark.sql.files.openCostInBytes` | 4 MB | 打开文件的估算开销，用于合并小文件 |

- **Coalesce Hints**：通过 `coalesce` 或 `repartition` 控制分区数，减少小文件问题。

### 2.5 自适应查询执行（AQE）

- **合并后 Shuffle 分区**：动态合并小分区。
- **拆分倾斜分区**：自动处理数据倾斜。
- **转换 Join 策略**：将 Sort-Merge Join 转换为 Broadcast Join 或 Shuffled Hash Join。

## 3. 常见问题与优化

### 3.1 序列化相关

- **问题**：Java 序列化导致网络传输慢、内存占用高。
- **优化**：切换至 Kryo 序列化，并注册所有自定义类。

### 3.2 内存占用过高

- **问题**：对象内存消耗超出预期，导致频繁 GC 或 OOM。
- **优化**：
  - 使用序列化 RDD 存储。
  - 调整数据结构，减少对象嵌套。
  - 增大 `spark.kryoserializer.buffer`。

### 3.3 GC 频繁

- **问题**：对象创建与销毁频繁，GC 停顿影响性能。
- **优化**：
  - 使用列式缓存减少对象数量。
  - 调整 JVM GC 参数（如 G1GC）。
  - 增大 `spark.memory.fraction` 和 `spark.memory.storageFraction`。

### 3.4 数据倾斜

- **问题**：部分分区数据量过大，导致任务执行缓慢。
- **优化**：
  - 使用 AQE 的倾斜分区拆分功能。
  - 手动重分区或使用 Salting 技术。

### 3.5 小文件问题

- **问题**：大量小文件导致任务调度开销大。
- **优化**：
  - 调整 `spark.sql.files.maxPartitionBytes` 和 `spark.sql.files.openCostInBytes`。
  - 使用 `coalesce` 或 `repartition` 合并分区。

## 4. 学习建议

1. **优先优化序列化**：对于网络密集型应用，立即切换至 Kryo 并注册类。
2. **监控内存使用**：通过 Spark UI 的 Storage 和 Executor 页面观察内存与 GC 情况。
3. **逐步调优**：先解决最明显的瓶颈（如序列化），再处理内存与 GC 问题。
4. **利用 AQE**：启用自适应查询执行（`spark.sql.adaptive.enabled=true`），自动优化 Join 与分区。
5. **测试与基准**：使用代表性数据与工作负载进行基准测试，验证调优效果。
6. **参考官方文档**：持续关注 Spark 版本更新，了解新特性（如动态分区裁剪、优化后的 Join 策略）。
```

> 来源：
> - [Tuning - Spark 4.1.1 Documentation - Apache Spark](https://spark.apache.org/docs/latest/tuning.html)
> - [Performance Tuning - Spark 4.1.1 Documentation](https://spark.apache.org/docs/latest/sql-performance-tuning.html)
> - [性能调优 - Spark 4.1.1 文档 - Spark 分析引擎 - Apache](https://spark.apache.ac.cn/docs/latest/tuning.html)
