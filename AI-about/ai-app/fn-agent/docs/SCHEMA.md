# Schema 层说明

## 一、目录

```text
schema/
├── specs/                 规范层（5 个）
│   ├── constraint-field-spec.json
│   ├── frame-inheritance-spec.json
│   ├── entity-spec.json
│   ├── unit-spec.json
│   └── artifact-spec.json
├── registries/            跨层注册表（2 个）
│   ├── R-ROLES-00.json
│   └── system-queries.json
├── frames/                框架定义（10 个）
├── indexes/               索引（1 个）
│   └── frame-name-index.json
├── entity/                实体层（4 个）
│   ├── entity-attribute-index.json
│   ├── relation-type-index.json
│   ├── entity-registry.schema.json
│   └── entity-registry-example.json
├── unit/                  单元层（2 个）
│   ├── unit-registry.schema.json
│   └── unit-registry-example.json
└── artifact/              产物层（2 个）
    ├── artifact-registry.schema.json
    └── artifact-registry-example.json
```

共 26 个文件。

## 二、分层规则

| 目录 | 装什么 |
|---|---|
| specs/ | 所有规范 |
| registries/ | 跨层共享的注册表 |
| frames/ | 框架定义 |
| indexes/ | 名称索引、引用登记 |
| entity/ unit/ artifact/ | 各层的 schema + example |

## 三、框架 schema 结构

每个 F-XXX-00.json 含：

| 字段 | 说明 |
|---|---|
| metadata | 框架 id、名称、父框架、版本 |
| core_fe | 核心 FE，含 constraint |
| peripheral_fe | 外围 FE |
| inheritance_notes | 子框架的继承摘要 |
| lus / lus_zh | 英文 / 中文词元 |

每个 FE 的 constraint 含四个子字段：

| 字段 | 说明 |
|---|---|
| type | 类型（kind + ref + cardinality） |
| fillers | 填充来源 |
| default | 缺省策略 |
| multi_candidate | 多候选收敛 |

## 四、type.kind 四种

| kind | 含义 | 递归行为 |
|---|---|---|
| entity | 指向实体类型 | 查实体层 |
| frame | 指向框架 | 立即激活 |
| role | 指向角色值域 | 惰性映射 |
| primitive | 基础类型 | 不激活 |

## 五、fillers 字段

### 5.1 sources 九种

| 值 | 含义 |
|---|---|
| explicit | 用户显式说出 |
| implicit | 句法省略但可推断 |
| qualia | 从实体 qualia 推导 |
| system | 从 entity / unit / artifact 查询 |
| default | 默认策略 |
| inferred | 上下文推理 |
| frame | 来自其他框架的 FE |
| context | 从当前会话上下文注入 |
| history | 从历史记录获取 |

### 5.2 qualia_paths

三种写法：

| 写法 | 含义 |
|---|---|
| placeholder | `{entity}` / `{material}` / `{instrument}` |
| entity | 具体 EntityType |
| fe_source | 本框架内其他 FE |

### 5.3 candidate_paths

声明式候选规则。四种 kind：

#### entity_relation

```json
{
  "kind": "entity_relation",
  "from": "context.version",
  "relation": "depends_on",
  "target_types": ["CodeRepo", "ConfigUnit"],
  "value_field": "id"
}
```

从 context 的实体出发，遍历其 relations，取目标实体的 id。

#### unit_field

```json
{
  "kind": "unit_field",
  "field": "code_repo_refs",
  "value_field": "self"
}
```

遍历所有 unit，取指定字段的值。

#### artifact_field

```json
{
  "kind": "artifact_field",
  "field": "id",
  "filter": { "belongs_to": "context.version" },
  "value_field": "id"
}
```

遍历所有 artifact，按过滤条件筛选，取指定字段的值。

#### context_key

```json
{
  "kind": "context_key",
  "key": "config_unit",
  "value_field": "self"
}
```

从 context 直接取。

### 5.4 candidate_paths 的存放

在 `frame-name-index.json` 的 `reference_map.by_candidate_paths.entries` 中登记。

key 格式：`{frame_id}.{fe_name}.candidate_paths[N]`。

### 5.5 已登记的 candidate_paths

| FE | 规则 | 说明 |
|---|---|---|
| F-PROCESSING-MATERIALS-00.material[0] | entity_relation | patient.depends_on → CodeRepo / ConfigUnit |
| F-PROCESSING-MATERIALS-00.material[1] | unit_field | unit.code_repo_refs |
| F-PROCESSING-MATERIALS-00.product[0] | artifact_field | artifact.belongs_to = context.version |

### 5.6 system_queries

调用系统接口。接口清单见 `registries/system-queries.json`。

### 5.7 frame_refs

引用其他框架的 FE。target 用 `frame_schema_name`。

## 六、知识表示层

### 6.1 entity（语义层）

主字段：

```text
id / type / name / qualia / attributes / state / relations / domain / tags
```

类型：Product / Version / CodeRepo / ConfigUnit / Artifact / Branch / Pipeline / Tool

### 6.2 unit（语料层）

主字段：

```text
id / type / name / qualia / parameters / environment
/ code_repo_refs / script_repo_ref / script_refs
/ dependencies / state / domain / tags / relations
```

id 格式：`unit:{env}:{name}`

### 6.3 artifact（物理层）

主字段：

```text
id / type / name / qualia / files / checksum / storage / status
/ belongs_to / produced_by / produced_at / format
/ domain / tags / relations
```

id 格式：`artifact:{version}:{name}`

files 每项：`{path, size?, hash?}`

## 七、命名约定

| 对象 | 格式 |
|---|---|
| 框架 id | `F-XXX-NN` |
| 角色 id | `XxxType` 或 `AgentRole` |
| 实体 id | `entity:{type}:{name}` |
| 单元 id | `unit:{env}:{name}` |
| 产物 id | `artifact:{version}:{name}` |
| 关系 id | `rel:{seq}` |
| 属性名 | `snake_case` |
| domain | `general` / `ci` |

## 八、索引

`frame-name-index.json` 的 `reference_map` 含六类索引：

| 索引 | 内容 |
|---|---|
| by_role | role.values[].frame |
| by_frame_refs | frame_refs |
| by_type_refs | type.kind=frame |
| by_qualia_paths | qualia_paths |
| by_candidate_paths | candidate_paths |
| by_external_refs | external_refs |