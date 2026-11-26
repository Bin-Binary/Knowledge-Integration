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

### Q6：混合向量检索（Hybrid GraphRAG）在六边形架构中的职责切分
* **核心疑惑**：向量检索与存储横跨底层驱动（Qdrant/Embedding）与领域知识图谱（`20_wiki` 分层索引与 `[[双链]]` 扩展），在 `infra/` 与 `components/internal_knowledge/` 之间如何划清边界？
* **核心释义**：
  1. **基础设施层（`infra/vector/`）**：只负责“数字与通用载体”的存取算（文本转向量、向量相似度计算、通用键值对过滤），**严禁感知任何业务语义**。
  2. **能力层（`components/internal_knowledge/storage/`）**：负责“领域知识规则”的翻译与图谱游走（L1~L4 差异化摘要提取、生命周期权重过滤、解析 `[[双链]]` 执行 1-Hop/多跳上下文水合）。
* **核心答案**（遵循 DIP 双向隔离，通过 `protocols/vector_store.py` 桥接）：
  ```text
  [ components/internal_knowledge/storage/HybridVectorMarkdownStorage ]
      │  ① 解析 20_wiki 抽取单行判据 + 组装过滤条件 (stage/layer/degree)
      │  ② 拿到锚点 ID 后解析底部 [[双链]] 执行确定性图谱扩展
      ▼ (依赖通用契约：EmbeddingProviderProtocol / VectorStoreProtocol)
  [ protocols/vector_store.py ]
      ▲ (底层驱动实现，零业务语义)
  [ infra/vector/LocalSentenceEmbedder + QdrantVectorStore ]
  ```
  * **演进收益**：Qdrant 在架构中仅作为轻量级“语义锚点指针库”（只存摘要向量、YAML 元数据与逻辑 ID），完整正文与拓扑关系依然保留在 Markdown Vault 中。未来将本地 Qdrant 切换为远程集群、pgvector 或更换云端 Embedding API 时，只需在 `infra/vector/` 替换适配器并在 `app/container.py` 改一行接线，知识库检索与双链扩展逻辑**零修改**。
* **代码正反例对比**：
  * **❌ 反例（业务语义污染基础设施层）**：
    ```python
    # 错误示范：infra/vector/qdrant_store.py 中出现领域概念与双链解析
    class QdrantVectorStore:
        def search_wiki(self, query_vec: list[float], stage: str):
            # 违反边界：底层存储驱动不应知道 "20_wiki"、"gold" 或 "[[双链]]" 是什么
            hits = self._client.query_points(..., query_filter={"stage": stage})
            for hit in hits:
                md_text = Path(f"20_wiki/{stage}/labeling/{hit.id}.md").read_text()
                links = re.findall(r"\[\[(.*?)\]\]", md_text)  # 图谱扩展逻辑泄漏到 infra
    ```
  * **✅ 正例（通用契约隔离，领域规则收口于能力层）**：
    ```python
    # 1. infra/vector/qdrant_store.py（纯技术驱动，只认通用字典过滤）
    class QdrantVectorStore(VectorStoreProtocol):
        def search(self, collection: str, query_vector: list[float], filters: dict, top_k: int):
            return self._client.query_points(
                collection_name=collection,
                query=query_vector,
                query_filter=self._build_filter(filters),
                limit=top_k,
            )

    # 2. components/internal_knowledge/storage/hybrid_storage.py（领域规则 + 双链游走）
    class HybridVectorMarkdownStorage(LocalMarkdownStorage):
        def __init__(self, embedder: EmbeddingProviderProtocol, vector_store: VectorStoreProtocol, **kwargs):
            super().__init__(**kwargs)
            self._embedder = embedder
            self._vector_store = vector_store

        def _sync_search_vault(self, problem: str) -> list[str]:
            vec = self._embedder.embed_text(problem)
            hits = self._vector_store.search("ci_20_wiki", vec, filters={"stage": ["gold", "release"]}, top_k=3)
            return [h.payload["artifact_id"] for h in hits]  # 拿到锚点后再由能力层执行双链水合
    ```

### Q_7：为什么大模型高可用（异构灾备切换）必须下沉到网关切面，而不能放在状态机恢复层？

• 归属档案：[[QA_01_Architecture_And_DIP]]（粗粒度）
• 核心疑惑：在多模型灾备场景下（如主模型 GLM-V5.1 限流时自动切换备用模型 DeepSeek-v4-Flash-SZ），为什么将其实现为 LangGraph 状态机恢复节点（recovery_node）的插件会导致代码严重膨胀，而下沉为 LLM Adapter 切面（Middleware）却能实现新节点零改动？
• 核心释义：网关级透明切面（Middleware / Decorator）是指在调用底层外部服务的客户端外层包裹装饰器，在不改变接口签名和上层业务感知的前提下，透明完成重试、熔断、格式清洗或主备切换。
• 核心答案：必须遵循关注点分离（SoC）与正交解耦原则——基础设施高可用（重试、异构模型切换、本地正则清洗）属于网关/客户端层职责，必须在调用点内部毫秒级闭环；状态机恢复层（Recovery Graph）只负责业务级语义自愈（如低置信度反问澄清）与最终静态降级。若将模型切换放在状态机层，状态机必须感知每个业务节点的输入构造、中间产物结构及回填路由，每新增一个业务子图就要同步修改恢复插件、装配容器与图路由边，严重违反开闭原则（OCP）且会中断已完成的前置多步迭代。
• 真实正反例对比：
	• ❌ 反例（Anti-Pattern）：在状态机恢复层实现 ModelFailoverRecovery 插件，并在 /app/container.py 注入 stage_executors 重建知识引擎，同时在 recovery_graph.py 和 master_graph.py 中硬编码回填 knowledge:deep_learn 的状态增量。死穴所在：业务节点拓扑与基础设施高可用强耦合，新增任意子图都必须修改 4 个核心架构文件，且子图内部第 N 步限流会导致前 N-1 步成果全部作废重跑。
	• ✅ 正例（Best Practice）：编写实现 StructuredLLMProtocol 与 StreamingLLMProtocol 的 ModelFailoverMiddleware，在 /app/llm_factory.py 中以洋葱模型包裹在 LocalJsonHealerMiddleware(HybridLangChainAdapter) 外层。核心收益：业务组件（HybridIntentRecognizer、WorkspaceGapRouter）与图路由层零修改、零感知，单次 LLM 调用失败时在毫秒级内部切换 DeepSeek 继续执行，只有双模型全挂时才冒泡至 recovery_node 走静态降级。


### Q_8：为什么需要消除中间层与标准化映射器之间的异常转换重叠，建立单一事实来源？

• 归属档案：[[QA_01_Architecture_And_DIP]]（粗粒度）
• 核心疑惑：当调用链路中已经存在统一的 RegistryExceptionMapper 负责将第三方异常映射为标准错误码时，为什么在 LLM 调用切面中再写一层 LLMErrorNormalizerMiddleware 会导致双轨制维护与架构冗余？
• 核心释义：单一事实来源（Single Source of Truth, SSOT）是指某一类映射规则或领域知识在系统中仅在一个权威位置维护，避免多处重复转换导致语义割裂或同步遗漏。
• 核心答案：必须区分“调用链路中的热修复（Middleware）”与“节点边界的事后快照（Mapper）”的职责边界。LocalJsonHealerMiddleware 能够原地清洗并返回合法业务对象，是不可替代的运行时热修复；而单纯把 RateLimitError、APITimeoutError 等 SDK 异常转译为业务异常的 LLMErrorNormalizerMiddleware，其转换规则与 RegistryExceptionMapper 完全重合。保留双层转译会导致同一异常写两遍映射逻辑，一旦新增第三方 SDK 就需两处同步修改。因此应删除单纯转译型中间件，将所有底层异常的归一化收敛到 RegistryExceptionMapper 配置表中。
• 真实正反例对比：
	• ❌ 反例（Anti-Pattern）：同时保留 LLMErrorNormalizerMiddleware（将 OpenAI SDK 异常转译为 ModelServiceUnavailableError）和 RegistryExceptionMapper（再次配置 RateLimitError 映射规则），增加一层无实质收益的异步装饰器调用栈。死穴所在：违反单一事实来源原则，同一类三方异常的映射逻辑分散在切面与配置表两处，新增 SDK 时极易遗漏或产生状态码定义冲突。
	• ✅ 正例（Best Practice）：仅保留 LocalJsonHealerMiddleware 与 ModelFailoverMiddleware 处理调用期热修复与主备切换；删除 LLMErrorNormalizerMiddleware，将所有未捕获的底层三方 SDK 异常直接穿透至节点 except 块，由 RegistryExceptionMapper 依据 DEFAULT_EXCEPTION_SPECS 统一映射为 FailureContext。核心收益：消除冗余装饰器栈，所有三方异常映射规则收口于单一声明式配置表，维护成本减半。


