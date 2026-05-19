# 大数据开发学习知识底稿

## 核心技术栈

- 离线计算：Hadoop、HDFS、YARN、Hive、Spark
- 实时计算：Kafka、Flink
- 数仓建模：ODS、DWD、DWS、ADS，维度建模，事实表与维度表
- 调度系统：Airflow、DolphinScheduler、Azkaban
- 数据治理：元数据、血缘、质量校验、权限、安全
- 湖仓方向：Iceberg、Hudi、Delta Lake

## 学习建议

1. 先建立整体链路：数据采集、存储、计算、建模、调度、服务。
2. 再深入组件机制：例如 Spark 的 shuffle、Flink 的 checkpoint、Hive 的执行计划。
3. 最后做项目闭环：从原始数据到指标产出，再到任务调度和监控。

## 工作排查常见问题

- SQL 慢：看执行计划、分区裁剪、join 策略、数据倾斜、小文件。
- Spark 任务失败：看 driver/executor 日志、资源配置、shuffle、OOM。
- Flink 延迟高：看反压、checkpoint、状态大小、Kafka lag、下游写入。
- 数据异常：看上游变更、字段口径、任务依赖、补数逻辑、质量规则。
