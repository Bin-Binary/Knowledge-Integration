# 推理服务层 · 目录说明

## 目录结构

```
inference/
├── overview-graph.md                           # 全局视图：Prefill→Decode 管线 + 部署三角
├── index.md                                    # 本文件
├── docs/
│   ├── Inference-Fundamentals.md               # 推理机制：Token/Prefill/Decode/SA/KV Cache
│   └── Why Efficient LLM Deployment Matters.md # 部署决策：SLO/硬件选型/权衡三角
└── faq/
    ├── GLM-5.2-W8A8-Output-Garbled.md          # W8A8 量化输出乱码
    └── FAQ-GLM5.2-Tool-Call-JSON-Parse-Failure.md # 工具调用 JSON 解析失败
```

> SVG 资源位于 [../svgs/inference/](../svgs/inference/)（4 张：推理概念、KV Cache 生命周期、PD 分离、知识-实践映射）。

## 内容清单

| 位置 | 说明 |
|------|------|
| `overview-graph.md` | 全局视图：Prefill→KV Cache→Decode 管线，部署三角，关键 SLO |
| `docs/Inference-Fundamentals.md` | 推理机制详解：Token、Self-Attention、KV Cache 公式与观测 |
| `docs/Why Efficient LLM Deployment Matters.md` | 部署决策：自建 vs API、硬件选型、Tradeoff Triangle |
| `faq/` | 2 个 GLM 推理问题 |
| `../svgs/inference/` | 4 张 SVG |

## 扩展指南

**新增推理层文档**：

1. 将 `.md` 放入 `docs/`
2. 在本文件「内容清单」表追加一行
3. 在 [overview-graph.md](./overview-graph.md) 底部追加引用链接

**新增推理层 FAQ**：

1. 将 `.md` 放入 `faq/`
2. 在本文件 FAQ 条目中追加

**新增推理层 SVG**：

1. 放入 `../svgs/inference/`
2. 在本文件 SVG 条目中追加
