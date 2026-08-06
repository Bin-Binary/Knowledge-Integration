# 硬件层 · 总览

> 推理的物理基础：四级存储，容量递增、带宽递减。搬运速度远慢于计算速度——这是所有优化的根源。

```
  SRAM   (~20MB,  数十TB/s)  ← 计算核心直接读写
    ↕     ← 推理延迟的核心瓶颈
  HBM    (64GB,   2TB/s)     ← 模型权重 + KV Cache 常驻
    ↕
  DRAM   (512GB,  100GB/s)   ← UCM 温层 KV Cache
    ↕
  SSD    (2TB,    几GB/s)    ← UCM 冷层持久化
```

| 特征 | Prefill | Decode |
|------|---------|--------|
| 瓶颈类型 | **Compute-Bound** | **Memory-Bound** |
| 根因 | 大量计算掩盖搬运 | 每步搬全量权重，只算一点点 |
| 硬件需求 | 高 TP 压算力 | 高 DP 扩吞吐 |

> [GPU-Memory-Hierarchy.md](./docs/GPU-Memory-Hierarchy.md) — 完整公式 + 生产观测。
