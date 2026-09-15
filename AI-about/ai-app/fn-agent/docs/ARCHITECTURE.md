# 架构总览

## 一、目标

基于框架语义学，构建一个可扩展的垂直领域智能体。

核心原则：

- 语义驱动提问
- 让 LLM 做选择题，不做填空题
- 用户最多两轮交互
- 不允许静默执行
- 零硬编码：FE 候选来源由 schema 声明，不在代码中写死

## 二、分层结构

### 2.1 知识表示层

```text
entity（语义层）
  Product / Version / CodeRepo / ConfigUnit / Artifact / Branch / Pipeline / Tool
     ↑ ref
unit（语料层）
  配置单元：关联配置代码仓、脚本代码仓、脚本文件
     ↑ ref
artifact（物理层）
  构建产物：关联语义实体与产生它的 unit
```

三层通过 ref 字段互联，各自独立注册。

### 2.2 框架语义层

```text
frames（10 个框架）
  F-INTENTIONALLY-ACT-00     意图性行动
  F-PROCESSING-MATERIALS-00  材料加工
  F-CHANGE-00                变化
  F-STATE-00                 状态
  F-USING-00                 使用工具
  F-CHOOSING-00              选择
  F-COMMUNICATION-00         交流
  F-ACT-00                   活动（基础）
  F-EVENT-00                 事件
  F-PROCESS-00               过程
```

每个框架定义 FE。FE 通过 fillers 引用知识表示层。

### 2.3 运行时流程

```text
请求输入
   ↓
LLM 选择题（parse_request）
   ↓
框架激活（activate_frames）
   ↓
候选生成
   ├── resolve_qualia     qualia 推导
   ├── resolve_relations  frame_refs
   └── resolve_candidates 声明式规则
   ↓
FE 填充（self_fill / converge）
   ↓
缺口检测（check_gaps）
   ↓
提问聚合（aggregate_questions）
   ↓
用户回答（user_answers）
   ↓
再检查（recheck）→ 条件分流
   ├── proceed_to_convergence → converge → execute
   ├── downgrade              → downgrade_with_notice
   └── escalate               → escalate_to_human
```

## 三、目录结构

```text
project-root/
├── schema/                 设计资产（JSON）
│   ├── specs/              规范层（5 个）
│   ├── registries/         跨层注册表（2 个）
│   ├── frames/             框架定义（10 个）
│   ├── indexes/            索引（1 个）
│   ├── entity/             实体层（4 个）
│   ├── unit/               单元层（2 个）
│   └── artifact/           产物层（2 个）
├── src/                    运行时源码
│   ├── llm/                LLM 客户端与选择器
│   ├── loader/             schema 加载与索引
│   ├── registry/           实体 / 单元 / 产物 / 框架实例
│   ├── providers/          候选生成
│   ├── convergence/        收敛与决策
│   └── graphs/             LangGraph 图与节点
├── tests/                  测试
└── docs/                   文档
```

## 四、技术栈

| 组件 | 选型 |
|---|---|
| 编排 | LangGraph |
| LLM 抽象 | LangChain |
| LLM 提供商 | DeepSeek / 千问（阿里云百炼） |
| Schema 格式 | JSON |
| Python | 3.10+ |

## 五、核心概念

### 5.1 框架（Frame）

从 Framenet 借用，定义一种语义场景的 FE 结构。

### 5.2 FE（Frame Element）

框架元素，分 core / peripheral。

### 5.3 qualia

实体的四角色语义增强：

- formal：它是什么
- constitutive：由什么构成
- telic：用来做什么
- agentive：怎么产生

### 5.4 开放选择题

LLM 的每次输出必须从有限候选集中选，但可以在选择前主动获取信息。

信息获取渠道 = fillers.sources：

```text
explicit / context / qualia / system / inferred / frame / history
```

### 5.5 候选来源四种机制

FE 的候选由四种机制生成：

| 机制 | 说明 | 存放位置 |
|---|---|---|
| qualia_paths | 从实体 qualia 推导 | frame-name-index.by_qualia_paths |
| frame_refs | 从其他框架的 FE 取 | frame-name-index.by_frame_refs |
| candidate_paths | 声明式规则，从注册表或 context 取 | frame-name-index.by_candidate_paths |
| system_queries | 调用系统接口 | 框架文件的 fillers.system_queries |

候选生成零硬编码。所有规则在 schema 中声明。

### 5.6 candidate_paths 四种 kind

| kind | 说明 |
|---|---|
| entity_relation | 遍历实体的 relations，按目标类型过滤 |
| unit_field | 读取 unit 的某字段 |
| artifact_field | 读取 artifact 的某字段 |
| context_key | 从 context 直接取 |

### 5.7 缺口（Gap）

未填的 FE，分三类：

- required hard：必填，无候选
- required pending：必填，有候选
- peripheral：非必填，无候选

只有 required hard 会触发用户提问。

## 六、当前能力

已完成：

- 框架层 schema（10 个框架）
- 知识表示层（entity / unit / artifact）
- LLM 开放选择题
- 端到端图执行
- 缺口检测与提问聚合
- 收敛与执行计划生成
- 降级与人工兜底分支
- 声明式候选路径（candidate_paths），零硬编码

未完成：

- RAG 接入
- 真实用户交互（当前为模拟）
- system_queries 的真实实现
- 与外部 CI 系统对接