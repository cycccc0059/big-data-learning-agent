# Apache Kafka

> 此文件由知识收集器自动生成和更新。你也可以手动编辑。

## 核心概念

Kafka 是高吞吐量的分布式消息队列，用于实时数据管道和流处理。

## 关键机制

### 基本概念
- Topic、Partition、Broker、Consumer Group
- 分区内有序，分区间无序

### 消息可靠性
- ACK 机制：0、1、-1（all）
- ISR（In-Sync Replicas）
- 幂等生产者和事务

### Consumer
- 消费位移（Offset）管理
- Rebalance 机制
- 消费语义：at-most-once、at-least-once、exactly-once

## 常见问题

1. Consumer Lag 过高 — 消费速度跟不上生产速度
2. Rebalance 频繁 — 影响消费性能
3. 消息丢失 — ACK 配置、ISR 数量不足
4. 消息重复 — 未开启幂等

## 学习资源
<!-- 知识收集器会将网络资料自动追加到此处 -->
