# AI 知识体系 · 目录说明

## 目录结构

```
AI-about/
├── overview-graph.md                 # 全局全局视图
├── terminology-quick-reference.md    # 术语速查（共享语汇）
├── ai-infra/                         # AI 基础设施
│   ├── overview-graph.md             # 架构×生命周期矩阵
│   ├── docs/                         # 横切文档
│   ├── svgs/                         # 可视化资源
│   ├── hardware/                     # H1 硬件层
│   ├── inference/                    # H2 推理服务层
│   └── platform/                     # H3 平台调度层
├── ai-app/                           # AI 应用层
└── templates/                        # SVG 制图模板
```

## 内容清单

| 位置 | 内容 | 入口 |
|------|------|------|
| `ai-infra/` | 硬件→推理→调度的全链路基础设施知识 | [overview-graph.md](./ai-infra/overview-graph.md) |
| `ai-app/` | AI 辅助编码方法论 (Vibe Coding) | [overview-graph.md](./ai-app/overview-graph.md) |
| `terminology-quick-reference.md` | 模型部署术语速查 | 直接阅读 |
| `templates/` | SVG 风格模板 | [templates/](./templates/) |

## 扩展指南

**新增领域目录**（如 `ai-ops/`）：

1. 在根目录创建 `{domain}/`，包含：
   ```
   {domain}/
   ├── overview-graph.md   # 该领域全局视图
   ├── index.md            # 目录说明与扩展指南
   ├── docs/               # 内容文档
   ├── svgs/               # 可视化资源（可选）
   └── faq/                # 问题记录
   ```
2. 在本文件「内容清单」表追加一行
3. 在 [overview-graph.md](./overview-graph.md) 中追加该层的入口引用

**新增术语**：直接追加到 `terminology-quick-reference.md` 对应分类表。
