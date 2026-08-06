# 硬件层 · 目录说明

## 目录结构

```
hardware/
├── overview-graph.md                  # 全局视图：四级存储层次 + Compute/Memory-Bound
├── index.md                           # 本文件
├── docs/
│   └── GPU-Memory-Hierarchy.md        # GPU 显存层次 + NPU 算力参数 + 生产观测
└── faq/                               # 硬件层问题记录
```

> SVG 资源位于 [../svgs/hardware/](../svgs/hardware/)（3 张：显存层次、NPU 管线、单节点拓扑）。

## 内容清单

| 位置 | 说明 |
|------|------|
| `overview-graph.md` | 全局视图：四级存储的物理约束、Prefill vs Decode 瓶颈差异 |
| `docs/GPU-Memory-Hierarchy.md` | 四级显存详解 + A2 算力参数 + 生产环境观测 |
| `faq/` | 硬件层问题（待补充） |
| `../svgs/hardware/` | 3 张 SVG：GPU 显存层次、NPU 推理管线、单节点拓扑 |

## 扩展指南

**新增硬件层文档**：

1. 将 `.md` 放入 `docs/`
2. 在本文件「内容清单」表追加一行
3. 若涉及新 SVG，放入 `../svgs/hardware/`，同步更新本表

**新增硬件层 FAQ**：

1. 将 `.md` 放入 `faq/`
2. 在本文件「FAQ」表追加一行

**新增硬件层 SVG**：

1. 放入 `../svgs/hardware/`
2. 在本文件「内容清单」表 SVG 条目中追加
