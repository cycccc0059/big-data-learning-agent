# Apache Spark

> 此文件由知识收集器自动生成和更新。你也可以手动编辑。

## 核心概念

Spark 是一个基于内存计算的分布式计算引擎，支持批处理、流处理、机器学习和图计算。

## 关键机制

### RDD（弹性分布式数据集）
- Spark 最基础的抽象
- 不可变、可分区、可容错

### Shuffle
- 触发条件：groupByKey、reduceByKey、join 等宽依赖操作
- 优化方向：减少 shuffle 数据量、使用 map-side 预聚合

### Spark SQL
- Catalyst 优化器
- Tungsten 执行引擎
- DataFrame / Dataset API

## 常见问题

1. 数据倾斜 — 某些分区数据量远大于其他分区
2. OOM — 内存不足，需调整 executor 内存或分区数
3. 小文件问题 — 大量小文件导致 NameNode 压力大

## 学习资源
<!-- 知识收集器会将网络资料自动追���到此处 -->
