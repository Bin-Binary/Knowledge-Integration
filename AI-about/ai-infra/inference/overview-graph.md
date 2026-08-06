# 推理服务层 · 总览

> 一次请求 = 1 次 Prefill + N 次 Decode。KV Cache 是两阶段之间的桥梁。

```
  输入 ──→ [ Prefill ] ──→ KV Cache ──→ [ Decode × N ] ──→ 输出
           并行计算                缓存 K,V          串行生成
           Compute-Bound                          Memory-Bound
```

| 指标 | 含义 | 目标 |
|------|------|------|
| TTFT | 首 Token 延迟 | < 1s |
| ITL | Token 间延迟 | < 100ms |
| 吞吐 | 每秒生成 Token 数 | > 100 t/s |

| 部署取舍 | 选两项 | 牺牲 |
|---------|--------|------|
| 低成本 + 高性能 | W8A8 量化 | 精度可能下降 |
| 低成本 + 高精度 | 小模型低并发 | 性能受限 |
| 高性能 + 高精度 | 大模型多卡 | 成本高昂 |

> [Inference-Fundamentals.md](./docs/Inference-Fundamentals.md) — 推理机制详解。
> [Why Efficient LLM Deployment Matters.md](./docs/Why%20Efficient%20LLM%20Deployment%20Matters.md) — 部署决策与 SLO。
