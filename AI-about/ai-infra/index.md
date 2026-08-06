# AI 基础设施 · 目录说明

## 目录结构

```
ai-infra/
├── overview-graph.md          # 架构(H1-H4) × 生命周期(L1-L4) 矩阵
├── index.md                   # 本文件
├── docs/
│   └── AI-Infrastructure-Graph.md  # H1-H4 分层 + L1-L4 生命周期框架定义
├── svgs/                      # 可视化资源（按层级分子目录）
├── hardware/                  # H1 硬件层
│   ├── overview-graph.md
│   ├── index.md
│   ├── docs/
│   └── faq/
├── inference/                 # H2 推理服务层
│   ├── overview-graph.md
│   ├── index.md
│   ├── docs/
│   └── faq/
└── platform/                  # H3 平台调度层
    ├── overview-graph.md
    ├── index.md
    ├── docs/
    └── faq/
```

## 内容清单

| 位置 | 说明 |
|------|------|
| `overview-graph.md` | 全局视图：每层在每个生命周期阶段的核心命题 |
| `docs/AI-Infrastructure-Graph.md` | 架构框架：H1-H4 分层定义 + L1-L4 生命周期定义 |
| `svgs/` | 全链路 SVG：架构总览 + 硬件/推理/平台各层图示 |
| `hardware/` | H1：GPU/NPU 算力、四级显存层次、互联拓扑 |
| `inference/` | H2：推理机制、KV Cache、部署决策、问题记录 |
| `platform/` | H3：路由管线、K8s/LiteLLM 编排、运维实操 |

## 扩展指南

**新增 H1/H2/H3 层文档**：

1. 将 `.md` 放入对应 `{layer}/docs/`
2. 更新该层的 `index.md`「内容清单」表
3. 若涉及跨层引用，同步更新被引用文档中的相对路径

**新增横切文档**（跨多层）：

1. 将 `.md` 放入 `ai-infra/docs/`
2. 在本文件「内容清单」表追加一行
3. 在 [overview-graph.md](./overview-graph.md) 中评估是否需要更新矩阵

**新增 SVG**：

1. 放入 `svgs/{layer}/`
2. 更新对应层的 `index.md`

**新增层**（如 H0 网络层、H5 数据层）：

1. 创建 `{layer}/`，包含 `overview-graph.md` + `index.md` + `docs/` + `faq/`
2. 在本文件「内容清单」表追加一行
3. 在 [overview-graph.md](./overview-graph.md) 矩阵中追加该层
