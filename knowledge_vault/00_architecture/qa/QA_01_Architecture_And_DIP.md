---
title: QA-01 粗粒度：方法论、原则、设计与架构相关
tags: [qa, architecture, dip, hexagonal, acl, lifecycle]
stage: gold
---

# 粗粒度：方法论、原则、设计与架构相关

返回总纲：[[Internal_Knowledge_Architecture]]

### Q1：依赖倒置原则（DIP）与六边形架构（Ports & Adapters）
* **核心疑惑**：为什么强调协议（`protocols/`）是系统起点，且核心业务组件绝对不能导入 LangGraph、OpenAI SDK 或具体存储驱动？
* **核心答案**：核心领域层（`schemas/` + `protocols/` + `components/`）必须保持绝对纯粹，只依赖 Python 原生库与基础类型校验器。依赖箭头永远只从外向内单向流动（`外部框架 -> 协议/数据契约 <- 具体算子`）。外部框架（如 LangGraph）仅仅是六边形最外层的驱动适配器，核心系统随时可零成本脱离它独立运行、迁移至微服务或暴露为 MCP Server。
* **架构拓扑（一句话精髓：核心领域定义标准插孔，所有外部框架和底层存储都必须自己配转接头来插它）**：
  ```text
           [ LangGraph 主图 ]          [ FastAPI 接口 ]
                   │                           │
                   ▼ (左侧：驱动适配器)         ▼
          ┌─────────────────────────────────────────┐
          │          Ports (端口 = protocols/)       │
          │   ┌─────────────────────────────────┐   │
          │   │   Core Domain (核心领域层)       │   │
          │   │   schemas/ + Engine + Base*     │   │
          │   └─────────────────────────────────┘   │
          │          Ports (端口 = protocols/)       │
          └─────────────────────────────────────────┘
                   ▲ (右侧：被驱动适配器)       ▲
                   │                           │
          [ LocalMarkdownStorage ]     [ LLM 推理算子 ]
  ```

### Q2：防腐层（ACL）与域内黑板模式（Blackboard Pattern）的边界划分
* **核心疑惑**：系统内部号称“零胶水代码”，但接入 LangGraph 时还是要在节点里写字段翻译代码，这两者是否矛盾？
* **核心答案**：不矛盾，这是域内高内聚与跨边界防腐层（Anti-Corruption Layer）的职责正交：
  * **域内零胶水**：内部五大环节（`Storage` / `Application` / `Acquisition` / `Organization` / `Engine`）统一以 `PipelineEnvelope` 作为唯一通用黑板载体接力演化，组件间严丝合缝，零格式转换。
  * **边界防腐层**：异构系统（如 LangGraph 的 `MasterAgentState`）拥有各自的状态结构。边界处的 Adapter 节点专门承担“出入站翻译”脏活，守住核心领域层的 100% 纯净。

### Q3：信息隐藏（Information Hiding）与外部状态机零泄漏
* **核心疑惑**：外部系统（如 LangGraph 主图）需要在全局 State 中定义 `knowledge_envelope` 吗？如果遗留外部系统难以改动，如何实现低成本兼容？
* **核心释义**：不该让外部知道的内部变量（如 `PipelineEnvelope`），绝不暴露到外部系统的全局状态（`MasterAgentState`）里；当外部旧系统改不动时，通过外围适配层而非修改核心代码实现互操作。
* **核心答案**：
  * **状态隐藏（黑盒单节点挂载 vs 白盒多节点编排）**：
    * **黑盒单节点挂载（推荐）**：通过 `InternalKnowledgeEngineProtocol.query_and_learn(problem)` 门面方法对外暴露极简契约。`PipelineEnvelope` 仅作为节点局部临时变量创建并销毁，对外仅输出 `rag_context` 字符串，实现零模型泄漏。
    * **白盒多节点编排（按需）**：仅当需要利用 LangGraph 原生条件边控制循环或做 Human-in-the-loop（人工审核中断）时，才将其隔离在子图私有 State（`KnowledgeSubGraphState`）中，跑完后依然只向主图输出标准结果字段。
  * **异构系统兼容三策**：
    1. **智能补全适配层（Enriching Adapter）**：对外系统缺字段时自动补齐默认值（如生成 `trace_id`）或挂载轻量预处理将杂乱输入浓缩为标准 `problem`。
    2. **旁路事件监听（Sidecar / MQ Consumer）**：对无主动调用意识的系统订阅现有 Git Webhook 或消息队列，在后台静默触发 `acquire -> organize -> save` 沉淀知识。
    3. **行业标准兼容协议外壳**：为引擎包裹一层 **MCP Server**、**OpenAPI REST** 或 **OpenAI `/v1/chat/completions` 兼容接口**，实现多 Agent 生态零改造接入。

### Q4：数据治理生命周期与开闭原则（OCP）演进
* **核心疑惑**：如何防止 AI 自动生成的未审核知识污染生产环境？同时如何保证未来新增采集源、领域关系或组织算子时不修改核心调度器？
* **核心答案**：
  1. **三层生命周期物理隔离（`debug -> release -> gold`）**：
     * **写入隔离**：自动化自学习流水线（`Acquisition -> Organization -> Storage`）**仅拥有 `debug/` 目录的写权限**，严禁直接写入 `release/` 或 `gold/`。
     * **权重遮蔽检索**：`Storage.retrieve` 召回时按可信度加权（`gold: 1.0 > release: 0.8 > debug: 0.4`），当同一逻辑 ID 存在高成熟度版本时自动遮蔽低层级副本。
     * **跨层晋升零断链**：所有文件命名与跨文件引用（如 `[[lbl_101]]`）均基于内容指纹生成的全局唯一逻辑 ID，文件在目录间审核晋升时无需重写任何内部链接。
  2. **双注册表插件化演进（OCP）**：
     * **采集侧**：通过 `@BaseKnowledgeAcquirer.register(SourceScheme.XXX)` 装饰器注册协议解析器，新增数据源（如 Notion、Confluence、AST）只需新增实现类并注册。
     * **组织侧**：通过 `@OrganizationPluginRegistry.register(stage=...)` + `pkgutil` 启动扫描自动装配微算子，新增质量过滤器或建边策略对 `KnowledgeOrganizer` 零侵入。       
  3. **开闭原则扩展点**：
    * **开放域概念**：`Labeling.label` 保持 `str`（无法穷举，辅以泛化元分类枚举 `category: NodeCategory` 支持结构化过滤）。
    * **领域关系边**：核心层仅定义通用关系 `GeneralRelationType`，通过泛型 `Generic[RelTypeT]` 注入具体领域枚举（如 `CodeRelationType`），禁止核心文件反向导入业务代码，同时在模型内拦截 `label_1_id == label_2_id` 的无效自环边。
    * **零配置算子发现**：新算子通过装饰器注册表 + `pkgutil` 动态包扫描实现自动发现，主干代码零修改。

### Q5：组件层（`components/`）与编排适配层（`graphs/`、`api/`）的依赖红线是什么？
* **核心疑惑**：组件之间能否互相导入？图编排层能否直接引用注册表或异常映射器等组件工具？
* **核心答案**：严格遵守**单向依赖铁律（零例外）**，防止网状耦合与循环导入：
  1. **适配层（`graphs/`、`api/`）禁入具体组件**：编排层与网关层只能导入 `protocols/`、`schemas/` 与 `infra/`，全局搜索 `from components` 必须为 0 条。若某个映射器（如 `ExceptionMapper`）同时被图编排层和组件层需要，必须下沉至 `infra/`；注册表则抽象为 `AgentRegistryProtocol` 放入 `protocols/`。
  2. **一级业务组件之间禁止横向互导**：例如 `IntentRecognizer` 严禁直接 `import CatalogRouter`。组件间的协作必须通过 `protocols/` 声明依赖，由组合根（`bootstrap.py`）在启动时统一注入。
  3. **二级共享基类收拢原则（`components/_shared/`）**：仅当某个抽象模板或无状态算子**跨 2 个及以上一级业务域复用**时（如 `BaseQualityEvaluator` 同时服务于知识库切片打分与持久化记忆价值评估），才收入 `components/_shared/`；域内私有基类（如 `BaseRecoveryManager`）保留在各自领域目录内以维持高内聚。


