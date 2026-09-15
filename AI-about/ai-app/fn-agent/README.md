# fn-agent

基于框架语义学的可扩展垂直领域智能体。

## 核心理念

- **语义驱动提问**：不是用户问系统，而是系统主动发问。
- **LLM 做选择题**：每次输出必须从有限候选集中选，不做自由生成。
- **用户最多两轮**：一次请求 + 一次聚合追问，超过走人工兜底。
- **不允许静默执行**：任何降级必须显式告知。

## 快速开始

```cmd
pip install -r requirements.txt
copy .env.example .env
:: 编辑 .env 填入 API Key
python -m src.graphs.build
```

## 目录结构

```text
fn-agent/
├── schema/        设计资产（JSON）
│   ├── specs/     规范层（5 个）
│   ├── registries/ 角色与系统接口（2 个）
│   ├── frames/    框架定义（10 个）
│   ├── indexes/   名称索引（1 个）
│   ├── entity/    实体注册表（4 个）
│   ├── unit/      配置单元注册表（2 个）
│   └── artifact/  构建产物注册表（2 个）
├── src/           运行时源码
│   ├── llm/       LLM 客户端与选择器
│   ├── loader/    schema 加载与内存索引
│   ├── registry/  实体与框架实例
│   ├── providers/ 候选生成
│   ├── convergence/ 收敛与决策
│   └── graphs/    LangGraph 图与节点
├── tests/         测试
└── docs/          文档
    ├── ARCHITECTURE.md
    ├── SCHEMA.md
    ├── RUNTIME.md
    └── RUNBOOK.md
```

## 知识表示层

三层结构，通过 ref 互联：

| 层 | 内容 | 文件 |
|---|---|---|
| entity | 语义层（Product / Version / CodeRepo / …） | schema/entity/ |
| unit | 语料层（配置单元） | schema/unit/ |
| artifact | 物理层（构建产物） | schema/artifact/ |

关系：

```text
entity（语义）
   ↑ ref
unit（语料）──→ entity:CodeRepo
   ↑ ref
artifact（物理）──→ entity:Version / unit:xxx
```

## 文档索引

| 文档 | 内容 |
|---|---|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 架构总览、核心概念 |
| [SCHEMA.md](docs/SCHEMA.md) | schema 层结构、命名约定 |
| [RUNTIME.md](docs/RUNTIME.md) | 节点职责、状态流转 |
| [RUNBOOK.md](docs/RUNBOOK.md) | 运行手册、常见问题 |

## 技术栈

- LangGraph 1.x
- LangChain 1.x
- OpenAI 兼容协议（DeepSeek / 千问）
- Python 3.10+

## 许可

内部项目。