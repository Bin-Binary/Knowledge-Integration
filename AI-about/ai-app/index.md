# AI 应用层 · 目录说明

## 目录结构

```
ai-app/
├── overview-graph.md               # 全局视图：Vibe Coding 五阶段方法论
├── index.md                        # 本文件
├── svgs/                           # 应用层 SVG（待补充）
├── faq/                            # 应用层问题记录
└── vibe-coding/
    └── docs/
        └── vibecoding.md           # Vibe Coding 完整工作流规范
```

## 内容清单

| 位置 | 说明 |
|------|------|
| `overview-graph.md` | 全局视图：五阶段流水线、角色产出表、议题分级 |
| `vibe-coding/docs/vibecoding.md` | Vibe Coding 工程规范：角色定义、议题收敛策略、自检清单、产物格式 |
| `faq/` | 应用层问题（待补充） |

## 扩展指南

**新增应用层领域**（如 `code-review/`）：

1. 在 `ai-app/` 下创建 `{domain}/`，包含：
   ```
   {domain}/
   ├── docs/     # 内容文档
   └── faq/      # 领域问题
   ```
2. 在本文件「内容清单」表追加一行
3. 在 [overview-graph.md](./overview-graph.md) 中评估是否需要追加该领域的概述

**新增应用层文档**：

1. 将 `.md` 放入对应领域的 `docs/`
2. 更新本文件「内容清单」表

**新增应用层 FAQ**：

1. 将 `.md` 放入 `faq/` 或对应领域的 `faq/`
