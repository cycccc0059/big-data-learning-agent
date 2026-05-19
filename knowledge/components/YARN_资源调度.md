# YARN 资源调度

> 由知识收集器自动生成。

# YARN 资源调度笔记

## 1. 核心概念

### 1.1 YARN 设计思想
YARN（Yet Another Resource Negotiator）的核心思想是将**资源管理**与**作业调度/监控**功能分离为独立守护进程。

### 1.2 关键组件

| 组件 | 角色 | 说明 |
|------|------|------|
| **ResourceManager (RM)** | 全局资源管理器 | 负责整个集群的资源管理和调度决策 |
| **NodeManager (NM)** | 节点代理 | 管理单个节点的资源，执行来自RM的指令 |
| **ApplicationMaster (AM)** | 应用管理器 | 每个应用一个，负责任务调度、监控和容错 |
| **Container** | 资源抽象单元 | 封装CPU、内存等资源，是任务执行的基本单位 |

### 1.3 应用模型
- **Application**：可以是单个作业或DAG（有向无环图）作业
- 每个应用拥有独立的ApplicationMaster

## 2. 关键机制

### 2.1 资源调度流程

```
Client → ResourceManager (提交应用)
         ↓
ResourceManager → NodeManager (启动ApplicationMaster容器)
         ↓
ApplicationMaster → ResourceManager (请求资源)
         ↓
ResourceManager → NodeManager (分配容器给AM)
         ↓
ApplicationMaster → NodeManager (启动任务容器)
```

### 2.2 三种调度器

| 调度器 | 特点 | 适用场景 |
|--------|------|----------|
| **FIFO Scheduler** | 单队列，先入先出 | 简单测试环境 |
| **Capacity Scheduler** | 多队列，保证容量，弹性共享 | 生产环境，多租户 |
| **Fair Scheduler** | 多队列，公平分配，支持抢占 | 需要公平性的场景 |

### 2.3 资源模型
- **CPU**：虚拟核心（vcore）
- **内存**：MB/GB
- **扩展资源**：GPU、FPGA等（通过Node Labels/Attributes支持）

### 2.4 高可用机制
- **ResourceManager HA**：Active/Standby模式
- **ResourceManager Restart**：状态恢复
- **NodeManager Graceful Decommission**：优雅下线

## 3. 常见问题与优化

### 3.1 资源利用率问题

| 问题 | 原因 | 优化方案 |
|------|------|----------|
| 集群资源碎片化 | 容器大小不匹配 | 调整`yarn.scheduler.minimum-allocation-mb` |
| 资源利用率低 | 队列配置不合理 | 使用Fair Scheduler的抢占机制 |
| 任务等待时间长 | 调度器配置不当 | 调整队列容量和最大容量 |

### 3.2 性能优化建议

1. **内存配置**
   - `yarn.nodemanager.resource.memory-mb`：节点可用内存
   - `yarn.scheduler.maximum-allocation-mb`：单个容器最大内存

2. **CPU配置**
   - `yarn.nodemanager.resource.cpu-vcores`：节点可用vcore数
   - `yarn.scheduler.maximum-allocation-vcores`：单个容器最大vcore

3. **调度器调优**
   - Capacity Scheduler：设置`capacity`和`maximum-capacity`
   - Fair Scheduler：配置`minResources`和`maxResources`

### 3.3 常见故障处理

| 故障现象 | 可能原因 | 解决方案 |
|----------|----------|----------|
| RM启动失败 | ZooKeeper连接问题 | 检查ZK集群状态 |
| NM心跳超时 | 网络问题或NM负载过高 | 调整`yarn.nm.liveness-monitor.expiry-interval-ms` |
| 容器OOM | 内存配置不足 | 增加容器内存或调整`mapreduce.map.memory.mb` |

## 4. 学习建议

### 4.1 学习路径

1. **基础阶段**
   - 理解YARN架构设计思想
   - 掌握核心组件职责
   - 熟悉资源调度流程

2. **进阶阶段**
   - 深入理解三种调度器原理
   - 学习资源模型和容器管理
   - 掌握HA和容错机制

3. **实战阶段**
   - 配置和调优生产环境
   - 处理常见故障
   - 性能监控和优化

### 4.2 推荐资源

| 资源类型 | 推荐内容 |
|----------|----------|
| 官方文档 | Apache Hadoop YARN官方文档 |
| 源码分析 | Hadoop源码，重点关注RM和NM模块 |
| 实践项目 | 搭建3节点集群，配置不同调度器 |
| 监控工具 | YARN UI2、Ganglia、Prometheus |

### 4.3 关键配置参数

```xml
<!-- yarn-site.xml 核心配置 -->
<property>
  <name>yarn.resourcemanager.scheduler.class</name>
  <value>org.apache.hadoop.yarn.server.resourcemanager.scheduler.capacity.CapacityScheduler</value>
</property>

<property>
  <name>yarn.nodemanager.resource.memory-mb</name>
  <value>8192</value>
</property>

<property>
  <name>yarn.nodemanager.resource.cpu-vcores</name>
  <value>4</value>
</property>
```

### 4.4 学习要点总结

- **理解分离思想**：资源管理与作业调度分离是YARN的核心创新
- **掌握调度器差异**：根据业务场景选择合适的调度器
- **关注资源模型**：理解CPU、内存、扩展资源的配置和限制
- **重视高可用**：生产环境必须配置RM HA
- **持续监控优化**：使用YARN UI2监控集群状态，定期调整配置

> 来源：
> - [Apache Hadoop 3.5.0 – Apache Hadoop YARN](https://hadoop.apache.org/docs/current/hadoop-yarn/hadoop-yarn-site/YARN.html)
> - [Apache Hadoop](https://hadoop.apache.org/)
> - [Hadoop Yarn 的三种 资 源 调 度 器详解-CSDN博客](https://blog.csdn.net/b6ecl1k7BS8O/article/details/81518167)
