# 运行手册

## 一、环境准备

### 1.1 Python

- Python 3.10+

### 1.2 依赖

```cmd
pip install -r requirements.txt
```

### 1.3 环境变量

在项目根目录建 `.env`：

```dotenv
LLM_PROVIDER=qwen

# DeepSeek
OPENAI_API_KEY=sk-***
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_MODEL=deepseek-chat

# 千问
DASHSCOPE_API_KEY=sk-***
DASHSCOPE_BASE_URL=https://ws-xxxx.cn-beijing.maas.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen3.8-max
```

切换提供商只需改 `LLM_PROVIDER`。

## 二、目录结构

```text
project-root/
├── schema/        设计资产（26 个 JSON）
├── src/           运行时源码
├── tests/         测试
├── docs/          文档
├── .env
├── requirements.txt
└── README.md
```

## 三、快速验证

### 3.1 加载 schema

```cmd
python -m src.loader.loader
python -m src.loader.index
```

预期：

```text
[specs] 5 file(s)
[registries] 2 file(s)
[frames] 10 file(s)
[indexes] 1 file(s)
[entity] 4 file(s)
[unit] 2 file(s)
[artifact] 2 file(s)
```

### 3.2 实体注册表

```cmd
python -m src.registry.entity_registry
```

### 3.3 框架实例

```cmd
python -m src.registry.frame_instance
```

### 3.4 候选生成

```cmd
python -m src.providers.candidate_provider
```

### 3.5 LLM 连接

```cmd
python -m src.llm.client
python -m src.llm.selectors
```

### 3.6 端到端

```cmd
python -m src.graphs.build
```

预期输出包含：

- parsed_intent
- decision
- execution_plan
- trace

## 四、常见问题

### 4.1 LLM 调用 404

检查 `.env` 中：

- `LLM_PROVIDER` 是否正确
- 对应的 `API_KEY` / `BASE_URL` / `MODEL` 是否存在

### 4.2 框架激活 0 个

检查 `frame-name-index.json` 的 `name_to_id` 是否与 R-ROLES-00 的 `frame` 字段一致。

### 4.3 候选为空

检查：

- `entity-registry-example.json` 是否有对应实体
- `by_qualia_paths.entries` 中是否有对应 FE
- material 是硬编码规则，需确认 patient 有 depends_on

### 4.4 运行时警告 `<frozen runpy>`

无害。Python `-m` 执行时，模块既被 `__init__.py` 导入又被 `-m` 执行，触发警告。
不影响功能。

## 五、扩展指引

### 5.1 新增框架

1. 在 `schema/frames/` 加 `F-XXX-00.json`
2. 在 `frame-name-index.json` 的 `frames`、`name_to_id`、`id_to_name` 追加
3. 在 R-ROLES-00 的 ActionType.values 或相关 role 中映射到该框架

### 5.2 新增实体类型

1. 在 R-ROLES-00.EntityType.values 追加
2. 在 `entity/entity-attribute-index.json` 追加属性定义

### 5.3 新增关系类型

在 `entity/relation-type-index.json.relation_types` 追加。

### 5.4 新增 FE

在对应框架文件中追加 FE，含 constraint。

### 5.5 新增节点

1. 在 `src/graphs/nodes/` 加新文件
2. 在 `nodes/__init__.py` 导出
3. 在 `graphs/build.py` 中 `add_node` 和 `add_edge`

### 5.6 新增模型提供商

1. 在 `.env` 加 `{PROVIDER}_API_KEY` / `{PROVIDER}_BASE_URL` / `{PROVIDER}_MODEL`
2. 在 `src/llm/client.py` 的 `_resolve_provider` 加分支
3. 在 `.env` 中把 `LLM_PROVIDER` 切到新提供商

### 5.7 新增知识表示层

1. 在 `schema/specs/` 加 `{layer}-spec.json`
2. 在 `schema/{layer}/` 加 `{layer}-registry.schema.json` 和 `{layer}-registry-example.json`
3. 在 `src/loader/loader.py` 的 `SchemaBundle` 加字段，`load_all` 加目录加载
4. 在 `src/registry/` 加对应的运行时类
```

---

## 六、落盘清单

| 文件 | 状态 |
|---|---|
| README.md | 替换 |
| docs/ARCHITECTURE.md | 替换 |
| docs/SCHEMA.md | 替换 |
| docs/RUNTIME.md | 替换 |
| docs/RUNBOOK.md | 替换 |

---

## 七、需要你确认

1. 五份文档是否可以直接落盘？
2. 落盘后是否无需验证（文档不影响运行）？
3. 反馈后进入方向 B：把 unit / artifact 接入运行时。

请确认。