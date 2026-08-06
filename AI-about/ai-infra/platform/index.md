# 平台调度层 · 目录说明

## 目录结构

```
platform/
├── overview-graph.md               # 全局视图：5 跳路由管线 + 容错矩阵
├── index.md                        # 本文件
├── docs/
│   └── LLM-Platform-Practice.md    # 运维实操：K8s/LiteLLM/Prometheus/vLLM 命令与验证
└── faq/                            # 平台层问题记录
```

> SVG 资源位于 [../svgs/platform/](../svgs/platform/)（9 张：RR-S00~S08 请求-响应快照）。

## 内容清单

| 位置 | 说明 |
|------|------|
| `overview-graph.md` | 全局视图：HAProxy→K8s→LiteLLM→header_proxy→vLLM 五跳管线，每跳职责与容错 |
| `docs/LLM-Platform-Practice.md` | 运维实操手册：环境配置、服务检查、路由查询、端到端测试、问题排查、诊断命令 |
| `faq/` | 平台层问题（待补充） |
| `../svgs/platform/` | 9 张 SVG：请求-响应全链路快照 |

## 扩展指南

**新增平台层文档**：

1. 将 `.md` 放入 `docs/`
2. 在本文件「内容清单」表追加一行
3. 在 [overview-graph.md](./overview-graph.md) 底部追加引用链接

**新增平台层 FAQ**：

1. 将 `.md` 放入 `faq/`
2. 在本文件 FAQ 条目中追加

**新增平台层 SVG**：

1. 放入 `../svgs/platform/`
2. 在本文件 SVG 条目中追加
