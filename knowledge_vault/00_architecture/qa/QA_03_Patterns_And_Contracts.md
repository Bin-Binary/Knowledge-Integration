---
title: QA-03 细粒度：标准抽象、职责边界与设计模式
tags: [qa, design-patterns, template-method, composition, hydration]
stage: gold
---

# 细粒度：标准抽象、职责边界与设计模式

返回总纲：[[Internal_Knowledge_Architecture]]

### Q8：不可变贫血模型与模板方法模式（Template Method）的职责切分
* **核心疑惑**：数据模型应该采用贫血还是充血模型？数据实例究竟由谁生成，基类是否该提供核心业务方法的默认实现？
* **核心释义**：
  1. **贫血模型 + 不可变对象**：数据类（`ImmutableSchema`）只存数据和自校验规则，一旦创建就不能原地修改，更新只能靠生成新副本。
  2. **模板方法模式**：基类（`Base*`）把固定流程（拆信封 ➔ 调子类 ➔ 装回新信封）写死成模板，只留出核心推理步骤让子类去填空。
* **核心答案**：
  * **严格不可变贫血模型（`ImmutableSchema`）**：数据契约层只保留字段定义、结构不变式校验（`@model_validator`）、只读计算属性（`@property`）、纯函数状态跃迁（`advance_to_next_iteration()`）及无副作用渲染（`to_markdown()`），绝不包含 I/O 与策略推理。
  * **模板方法收口样板代码**：基类（`Base*`）负责信封拆箱校验、并发限流、不可变副本回写（`model_copy`）与回执封装；具体子类（如 `LLMKnowledgeApplicator`）负责核心推理并生成新实例。核心抽象方法保持 `@abstractmethod` 不写默认逻辑，遵循 **Fail-Fast（快速失败）** 原则防止静默错误。

### Q9：组合优于继承（Composition over Inheritance）与通用能力下沉
* **核心疑惑**：信息质量评估过滤（3.1 环节）是通用能力，抽离为全局工具放入根目录是否违背 DIP？组织阶段内部四步子步骤应该用基类钩子还是拆分为独立组件？
* **核心答案**：
  * **跨切面能力下沉**：在根目录 `protocols/evaluation.py` 定义逆变泛型协议 `QualityEvaluatorProtocol[ItemT_contra]`，知识库组件通过构造函数注入使用，完全不违背 DIP；具体业务子类（`InformationQualityEvaluator`）必须归属在高度相关的知识库业务组件目录下（包内聚原则）。
  * **微算子组合替代多层继承**：当组织阶段四步剥离外层模板控制后，拆分为独立的原子微算子组件（直接实现轻量级内部协议），由编排器（`KnowledgeOrganizer`）注入组合，彻底消除上帝类，支持“LLM 抽点建边 + 零延迟并查集图聚类”的混合算力装配。

### Q10：插件自动发现与多实现冲突仲裁策略
* **核心疑惑**：当统一注册中心扫描出同阶段的多个算子实现时，系统如何确定调用哪一个，还是全部调用？
* **核心答案**：在注册中心（`OrganizationPluginRegistry`）中按阶段特性实施双模式仲裁：
  * **单选激活模式（Exclusive Selection，适用于 3.1 评估 / 3.4 聚类）**：通过 `is_default=True` 指定默认胜出者，同时支持运行期传入配置名称动态切换（如测试环境切换为纯规则评估器）。
  * **并发累加模式（Fan-Out & Merge，适用于 3.2 提特征 / 3.3 建边）**：并发调度所有已启用算子，并基于确定性主键自动去重合并输出（保留高置信度结果）。

### Q11：完整契约注入与实体标识符水合（Entity Hydration）
* **核心疑惑**：检索环节仅返回知识 ID 列表，运用环节需要读取 Markdown 原文才能推理，应该传回调函数还是直接注入存储协议？
* **核心答案**：直接注入完整的 `KnowledgeStorageProtocol`（在协议中补充异步契约 `async def load_contents(artifact_ids: List[str]) -> str`）。向内依赖协议完全符合 DIP，且原生支持 `async/await` 异步非阻塞加载，语义远比零散的同步 `Callable` 回调函数清晰健壮。

### Q12：依赖倒置（DIP）落地后的“二次修改反模式”排查与开闭原则（OCP）加固
* **核心疑惑**：系统已经通过 `protocols/` 实现了依赖倒置，为什么在扩展新领域关系、新数据源或新存储能力时，依然被迫回头修改已有的核心 Schema 或基类代码？
* **核心答案**：DIP 只能保证“高层不依赖低层实现”，若要实现真正的**开闭原则（新增能力不改旧代码）**，必须消除以下四类隐性反向耦合：
  1. **核心契约反向导入具体领域枚举（`Union` 膨胀反模式）**：
     * *反模式*：在核心文件 `relating_concepts.py` 中直接导入 `CodeRelationType` 并写死 `AnyRelationType = Union[GeneralRelationType, CodeRelationType]`。每新增一个业务域（如 CI 流水线领域），都必须回来修改核心契约。
     * *加固策略*：斩断核心目录对 `domain/` 子目录的任何 `import`。核心模型保持泛型 `Generic[RelTypeT]` 或接受泛化基类，具体领域枚举仅在最外层业务算子与装配层可见。
  2. **模板基类包揽子类实例化（构造函数锁死反模式）**：
     * *反模式*：在分发基类（如 `BaseKnowledgeAcquirer.acquire`）内部硬编码 `handler_cls(gap_router=self.gap_router)`。一旦新子类需要注入 `repo_root` 或 `http_client` 等新依赖，就必须回头修改基类源码。
     * *加固策略*：将“协议路由分发器”与“具体采集器”解耦，由装配中心（`app/container.py`）完成依赖注入并将**实例字典**传入分发器，彻底消除基类对子类 `__init__` 签名的假设。
  3. **跨切面增强直接修改原实现类（而非装饰/组合）**：
     * *反模式*：为 `LocalMarkdownStorage` 增加向量检索时，直接在其内部 `if/else` 侵入修改原有分词检索代码。
     * *加固策略*：保持原实现类只读封闭，通过继承重写钩子或组合封装为新的 `HybridVectorMarkdownStorage`，仅在组合根切换接线。
  4. **过度使用聚合 `__init__.py` 全量重导出（放大重构爆炸半径）**：
     * *反模式*：每一层包目录的 `__init__.py` 均无差别 `from .xxx import Yyy` 导出所有子模块。重构期修改任意一个叶子文件的类名，都会导致全库级联 `ImportError`。
     * *加固策略*：聚合导出仅限已定型的稳定公共接口；处于快速演进期的子域内部模块直接按完整路径精确导入（`from schemas.internal_knowledge.labeling import ...`）。
* **代码正反例对比**：
  * **❌ 反例 A（核心契约反向依赖具体领域枚举）**：
    ```python
    # schemas/internal_knowledge/relating_concepts.py
    from schemas.internal_knowledge.domain.code_relation_type import CodeRelationType  # 核心层反向导入业务域！
    AnyRelationType = Union[GeneralRelationType, CodeRelationType]  # 每次加 CI 领域或新业务域，都必须回来改这行
    ```
  * **✅ 正例 A（核心契约泛型化，具体枚举留给外层注入）**：
    ```python
    # schemas/internal_knowledge/relating_concepts.py（零 domain 导入，永不因业务扩展而修改）
    RelTypeT = TypeVar("RelTypeT", bound=DocumentedEnum)
    class RelatingConcepts(ImmutableSchema, Generic[RelTypeT]):
        relationship_type: RelTypeT

    # 业务侧使用时再绑定具体枚举（核心文件零改动）：
    ci_edge = RelatingConcepts[CIRelationType](relationship_type=CIRelationType.BLOCKS, ...)
    ```
  * **❌ 反例 B（分发基类写死子类构造函数）**：
    ```python
    # components/internal_knowledge/acquisition/base_acquirer.py
    handlers_cache[uri.scheme] = handler_cls(gap_router=self.gap_router)  # 锁死子类只能接收 gap_router！
    # 一旦新写 GitRepoAcquirer(repo_root=...)，必须回头修改基类源码
    ```
  * **✅ 正例 B（装配层注入实例字典，分发器只管路由）**：
    ```python
    # 分发器只接收已装配好的实例映射（新增任何带复杂依赖的采集器，分发器零修改）
    class CompositeKnowledgeAcquirer(KnowledgeAcquisitionProtocol):
        def __init__(self, handlers: dict[SourceScheme, SingleSourceAcquirerProtocol]):
            self._handlers = handlers

        async def acquire(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
            for uri in envelope.source_locators:
                handler = self._handlers[uri.scheme]  # 直接使用外部注入的实例
                ...
    ```


### Q_13：如何消除异常标准化映射器中的 if isinstance 硬编码与业务枚举耦合，实现开闭原则？

• 归属档案：[[QA_03_Patterns_And_Contracts]]（细粒度）
• 核心疑惑：异常标准化映射器（Mapper）需要同时处理自研业务异常与各类第三方 SDK 异常（如 openai、httpx、pydantic），如何避免每次接入新 SDK 或新增错误类型时都去修改 Mapper 源码和中心化枚举？
• 核心释义：协议自省（Protocol Introspection）结合声明式规则注册表，是指利用 @runtime_checkable 协议让领域异常携带纯原语路由键自描述，同时让第三方异常通过外部只读数据规格（Spec）动态注册到零三方依赖的映射器中。
• 核心答案：核心策略是“协议自省直通 + 声明式 Spec 注册 + 删除封闭枚举”。保留纯原语契约 ClassifiableErrorProtocol（定义 error_code、user_friendly_hint 和 to_failure_metadata()），删除中心化的 FailureCategory 枚举并统一改用点分命名空间字符串（如 model.rate_limited、intent.low_confidence）。自研基类 AgentBusinessError 实现该协议后自动直通；第三方异常则通过纯标准库的 ExceptionMappingSpec 声明在 infra/default_exception_specs.py 中，由 RegistryExceptionMapper.register_specs() 无副作用注册。若不这样做，底层映射器将反向依赖所有三方库且每次扩展都必须修改核心代码。
• 真实正反例对比：
	• ❌ 反例（Anti-Pattern）：在 DefaultExceptionMapper._classify_and_format 中堆砌 if isinstance(curr, httpx.TimeoutException): return FailureCategory.MODEL_SERVICE_UNAVAILABLE, ...，并在装配层通过 setattr(exc, "_injected_hint", ...) 动态篡改第三方异常实例。死穴所在：违反开闭原则，映射器强耦合第三方库与中心枚举，且 setattr 遇到带 __slots__ 的异常类会直接抛出 AttributeError。
	• ✅ 正例（Best Practice）：AgentBusinessError 实现 ClassifiableErrorProtocol 返回点分错误码；RegistryExceptionMapper 仅依赖标准库与协议，通过 register_spec(ExceptionMappingSpec(...)) 将匹配结果封装为只读内部载体 _MatchResult 提取元数据与提示语。核心收益：映射器代码永久冻结且零三方库依赖，新增业务异常只需继承基类直接 raise，新增三方异常只需在 DEFAULT_EXCEPTION_SPECS 追加一条不可变配置。


### Q_14：为什么业务异常与配置规则在跨模块传递时，必须统一元数据契约键名并避免多套分类双轨制？

• 归属档案：[[QA_03_Patterns_And_Contracts]]（细粒度）
• 核心疑惑：在异常捕获（AgentBusinessError / ExceptionMappingSpec）、标准化映射（RegistryExceptionMapper）与下游降级恢复（CompositeRecoveryManager）的跨层流转中，为什么字段键名不统一（如 user_hint vs user_friendly_hint）以及保留旧枚举双轨制会导致反复修改多处代码与静默降级失效？
• 核心释义：契约单一规范化（Canonical Contract）是指跨组件传递的半结构化字典（如 FailureContext.metadata）与状态字段（如 category），必须在协议定义阶段就锁定唯一的命名与类型规范，上下游所有生产者与消费者严格对齐同一套命名。
• 核心答案：必须做到“协议字段名全链路唯一对齐”与“彻底废除旧分类体系”。在本次重构中，上游业务异常与配置表使用了 user_hint 作为字段名，映射器写入元数据字典时使用了 user_friendly_hint，而下游恢复管理器却去读取 metadata.get("user_hint")，导致业务异常自带的友好引导话术在运行时静默丢失、退化为冷冰冰的系统默认报错；同时，若不彻底清除旧的 FailureCategory 枚举（下划线命名），上游产出点分字符串 model.rate_limited 而旧节点仍访问 .category.value，就会引发运行时 AttributeError。因此，重构数据契约时必须执行全链路端到端键名核对与旧枚举全局清零。
• 真实正反例对比：
	• ❌ 反例（Anti-Pattern）：RegistryExceptionMapper._build_metadata 写入 meta["user_friendly_hint"] = matched.user_hint，而 CompositeRecoveryManager.handle_failure 读取 context.metadata.get("user_hint")；同时部分节点残留 failure_ctx.category.value 访问已降级为 str 的分类字段。死穴所在：字典键名错位不会在编译期报错，而是导致运行时降级话术静默失效；枚举残留属性访问则会在异常路径触发二次崩溃。
	• ✅ 正例（Best Practice）：以 ClassifiableErrorProtocol 的属性名 user_friendly_hint 为全链路唯一标准键名，统一写入与读取 context.metadata["user_friendly_hint"]；删除 FailureCategory 枚举并在全图节点统一使用纯字符串 failure_ctx.category 点分路由键。核心收益：消除跨层字典取值的静默空值隐患与双轨制来回返工，确保业务异常的定制化提示语 100% 透传至终端用户。

### Q_14：什么是装饰器洋葱模型（Onion Model），以及多切面嵌套顺序反了会引发什么架构灾难？

• 归属档案：[[QA_03_Patterns_And_Contracts]]（细粒度）
• 核心疑惑：在为大模型客户端同时挂载“本地正则清洗切面（LocalJsonHealerMiddleware）”与“异构灾备切换切面（ModelFailoverMiddleware）”时，为什么必须严格规定谁在里层、谁在外层，包反了会导致什么严重后果？
• 核心释义：洋葱模型（Onion Model / Decorator Chain）是指多个实现同一协议的中间件层层包裹核心对象；请求从最外层逐层穿透至最内层核心执行，而返回值或异常则从最内层逐层向外冒泡经过各层拦截处理，形如剥洋葱。
• 核心答案：必须遵循“低成本就地修复在最内层，高成本跨网关切换在最外层”的嵌套顺序。具体在当前架构中，必须采用 ModelFailoverMiddleware(外层) -> LocalJsonHealerMiddleware(内层) -> HybridLangChainAdapter(核心) 的嵌套结构。原因有二：其一，当主模型 GLM-V5.1 仅因输出了 <think> 标签或 Markdown 代码块报错时，内层的 LocalJsonHealerMiddleware 会在毫秒级就地清洗并返回合法对象，外层的 ModelFailoverMiddleware 根本不会感知到异常，从而避免白白浪费 Token 切换到备用模型 DeepSeek；其二，当主模型真正挂掉（如 429 限流）触发外层切换至 DeepSeek 时，如果 DeepSeek 本身也包裹了内层 LocalJsonHealerMiddleware，则备用模型的输出同样自动享有零成本本地清洗能力。若内外层包反，轻微格式污染就会直接触发昂贵的异构模型重跑。
• 真实正反例对比：
	• ❌ 反例（Anti-Pattern）：在 /app/llm_factory.py 中写成 LocalJsonHealerMiddleware(ModelFailoverMiddleware(primary=raw_intent, backup=raw_recovery))（清洗切面在外，灾备切面在内，且灾备模型未包清洗切面）。死穴所在：当主模型输出带 Markdown 代码块的合法 JSON 时，内层 HybridLangChainAdapter 抛出 StructuredOutputError 会直接被中层的 ModelFailoverMiddleware 拦截并立刻重跑备用模型，导致外层的零成本本地正则清洗形同虚设，白白浪费备用模型额度和响应时间。
	• ✅ 正例（Best Practice）：在 build_llm_adapter 中先为每个单角色基础适配器包裹内层清洗切面 LocalJsonHealerMiddleware(raw_adapter)，再在 build_adapter_pool 中用外层 ModelFailoverMiddleware(primary=intent_healed, backup=recovery_healed) 进行组合。核心收益：轻微格式污染在内层毫秒级零成本消化；真正网络/限流故障由外层透明切换备用模型，且备用模型输出同样受内层清洗保护。

### Q_15：为什么应摒弃 `ABC` 抽象基类与 `ClassVar` 全局注册表，改用“零继承组合引擎 + 实例级注册表”？

* **归属档案**：[[QA_03_Patterns_And_Contracts]]（细粒度）
* **核心疑惑**：在构建两级质量评估器（`BaseQualityEvaluator`）或协议采集器（`BaseKnowledgeAcquirer`）时，使用 `ABC` 抽象基类配合 `ClassVar` 类级别注册表和 `__init_subclass__` 隔离，为什么不如“组合式通用引擎 + 实例级注册”简洁健壮？
* **核心释义**：**组合式泛化引擎（Composable Generic Engine）**是指将通用执行骨架（如“前置长度过滤 -> L1 规则快筛 -> L2 语义打分 -> 边界钳制”）封装为不依赖继承的独立类，直接实现 `Protocol`，并通过构造函数接收纯函数回调（Callable）与实例级策略字典。
* **核心答案**：必须遵循**“组合优于继承（Composition over Inheritance）”**与**“消除隐式类状态”**原则。基于 `ABC` 的模板方法模式强迫业务类继承特定基类并重写多个受保护钩子（`_extract_text`、`_resolve_routing_key`），不仅增加了继承层级负担，且将策略注册表放在 `ClassVar` 上会引入模块导入顺序副作用，导致同一进程内无法实例化规则集不同的多个评估器或采集器（如“严格模式”与“宽松模式”）。改用 `TwoStageQualityEvaluator` 与 `CompositeKnowledgeAcquirer` 后，业务组件只需直接实现 `Protocol` 并组合通用引擎，规则注册完全收敛在实例的 `self._rules` 中。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：定义 `class BaseQualityEvaluator(ABC, QualityEvaluatorProtocol[ItemT])`，内部使用 `_heuristic_registry: ClassVar` 和 `__init_subclass__` 隔离字典，业务类 `InformationQualityEvaluator` 必须继承该基类并用 `@InformationQualityEvaluator.register_heuristic(...)` 挂载规则。**死穴所在**：引入不必要的继承耦合与元类/子类化魔法，无法在运行时隔离构建不同规则配置的同类型实例，且单元测试容易受全局类状态残留污染。
  * ✅ **正例（Best Practice）**：封装零继承的 `TwoStageQualityEvaluator[ItemT]`，在 `__init__` 中接收 `semantic_scorer`、`text_extractor`、`routing_key_resolver` 和实例级 `heuristic_rules` 字典；`InformationQualityEvaluator` 直接实现 `QualityEvaluatorProtocol[Information]` 并内部组合 `self._engine = TwoStageQualityEvaluator(...)`。**核心收益**：全项目彻底告别 `ABC` 继承，快筛规则退化为纯粹无状态函数，实例间 100% 隔离且极易单元测试。

### Q_16：在 Pydantic 数据契约中，何时应保留封闭枚举，何时应改用泛型枚举（`Generic[EnumT]`）或纯原语 `str`？

* **归属档案**：[[QA_03_Patterns_And_Contracts]]（细粒度）
* **核心疑惑**：面对系统中不同的分类字段（如状态机结果 `ResolutionOutcome`、图谱关系类型 `RelatingConcepts.relationship_type`、错误路由键 `FailureContext.category`），如何判断哪种字段该用封闭枚举，哪种该用泛型枚举或纯字符串？
* **核心释义**：**分类契约三层选型法**：根据分类集合的**变更频率**与**约束强度**，在“封闭枚举（Closed Enum）”、“泛型枚举（Generic Enum）”与“纯原语字符串（Primitive `str`）”之间做精准匹配。
* **核心答案**：遵循以下三条边界判定铁律：
  1. **系统架构拓扑或有限状态机边界（极低变更频率）→ 保留封闭枚举**：如 `TargetDomain`（`knowledge` / `execution`）和 `ResolutionOutcome`（`PENDING` / `SUCCESS` / `PARTIAL` / `FAILURE`），直接决定主控图拓扑边与闭环控制流，必须用封闭枚举实现启动期 Fail-Fast 防呆。
  2. **需要 LLM 结构化输出强约束，但不同业务域需扩展专属词表 → 使用泛型枚举 `Generic[EnumT]`**：如 `RelatingConcepts[RelTypeT]`，核心层提供通用关系枚举，特定领域通过 `RelatingConcepts[CodeRelationType]` 注入专属枚举，兼顾强类型校验、提示词自省与开闭原则。
  3. **跨层横向扩展的业务路由标签（高频新增）→ 使用纯原语 `str`**：如 `FailureContext.category`（点分命名空间 `model.rate_limited`）和 `FallbackPlan.trigger`，避免中心化枚举成为所有模块修改的瓶颈。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：将高频新增的异常分类定义为封闭枚举 `FailureCategory`，导致每次新增业务异常都要修改 `schemas/recovery.py`；或者在图谱边模型中硬编码单一枚举，导致代码库域无法扩展专属代码依赖关系类型。**死穴所在**：前者引发频繁修改中心契约文件的耦合痛苦；后者限制了领域模型的横向复用能力。
  * ✅ **正例（Best Practice）**：状态机状态（`ResolutionOutcome`）与顶层架构域（`TargetDomain`）保留 `DocumentedEnum` 封闭枚举；图谱关系（`RelatingConcepts[RelTypeT]`）使用受 `DocumentedEnum` 约束的 `TypeVar` 实现泛型扩展；错误分类（`category`）使用纯原语点分 `str`。**核心收益**：在需要严格防呆的边界享受强类型保护，在需要横向扩展的业务点享受零修改自由度。

### Q_17：为什么在存储检索（1-Hop GraphRAG 邻域扩展）和跨层物化落盘时，必须严格校验生命周期可见性与数据结构字段契约？
* **归属档案**：[[QA_03_Patterns_And_Contracts]]（细粒度）
* **核心疑惑**：为什么 `LocalMarkdownStorage` 在检索时把命中卡片底部的双链 ID 直接加入召回列表，却在加载正文时静默丢失？以及为什么 3.2 阶段提炼的 `rich_semantics` 在落盘时退化成了默认占位文本？
* **核心答案**：跨层协同必须严守**双向契约一致性**：
  1. **生命周期可见性一致**：生产环境检索通常配置 `allowed_retrieval_stages=(GOLD, RELEASE)`，当主节点已晋升至 `release/` 而其引用的原始切片仍在 `debug/` 时，1-Hop 邻域扩展必须先校验 `linked_id in accessible_ids`，否则不可见节点会挤占 `top_k` 名额且水合正文为空。
  2. **跨阶段模型字段契约一致**：生产方与消费方必须共享公开字段名（如 `Labeling.rich_semantics` 与 `Ontology.complex_id`），消费方在合并多切片同 ID 实体时（`_prepare_items`）应做集合并集聚合，而非简单丢弃后续实例的语义补充。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：
    ```python
    # 1. 邻域扩展不校验目标节点是否在允许的生命周期目录内
    for linked_id in bottom_links.get("溯源切片", [])[:2]:
        if linked_id not in final_ids and len(final_ids) < self.top_k:
            final_ids.append(linked_id)

    # 2. LabelingArtifactWriter 读取不存在的私有属性，且去重时丢弃后续切片语义
    sem = getattr(item, "_rich_semantics", {}) or {}
    ```
    *死穴所在*：未晋升的 `debug` 切片挤占 `top_k` 召回配额却读不出内容；`_rich_semantics` 拼写失配导致大模型提炼的 `core_definition` 和 `trigger_criteria` 全部丢失。
  * ✅ **正例（Best Practice）**：
    ```python
    # 1. 仅纳入当前 allowed_retrieval_stages 扫描范围内真实存在的关联节点
    if linked_id in accessible_ids and linked_id not in final_ids and len(final_ids) < self.top_k:
        final_ids.append(linked_id)

    # 2. 兼容读取 rich_semantics 并在 _prepare_items 中聚合多切片 trigger_criteria 与 boundaries
    sem = getattr(lbl, "rich_semantics", None) or getattr(lbl, "_rich_semantics", None) or {}
    ```
    *核心收益*：杜绝检索配额浪费与上下文空洞，保证多切片同名概念的业务判据完整沉淀到 L2 知识卡片中。

### Q_18：一个高内聚业务组件的顶层 `__init__.py` 是否应该只暴露 Protocol 协议，还是同时暴露入口工厂与传输载体？
* **归属档案**：[[QA_03_Patterns_And_Contracts]]（细粒度）
* **核心疑惑**：既然对外要遵循依赖倒置（DIP），那么 `components/internal_knowledge/__init__.py` 是不是应该只暴露 `InternalKnowledgeEngineProtocol` 纯协议，或者只暴露一个纯函数？
* **核心释义**：**组件对外门面（Component Facade）**是指组件向外部调用方公开的最小可用 API 集合，外部调用方严禁绕过 `__init__.py` 深层导入组件内部子模块。
* **核心答案**：不能只暴露协议（否则调用方拿不到构造实例的入口和入参模型），也不能只暴露无状态纯函数（纯函数无法持有存储连接池、信号量与 `mtime` 缓存索引）。最标准的对外门面应通过 `__init__.py` 的 `__all__` 精准暴露**“对外三件套”**：① **类型契约**（`InternalKnowledgeEngineProtocol`）；② **组装入口函数**（`create_default_knowledge_engine`）；③ **核心交互载体与业务异常**（`PipelineEnvelope`、`ResolveProblem`、`SourceURI`、`KnowledgePipelineError`），而将内部所有具体实现类（如 `KnowledgeOrganizer`、`LocalMarkdownStorage`）隐藏在子包中。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：
    ```python
    # 1. 上层调用方直接深层耦合内部文件物理路径
    from components.internal_knowledge.internal_knowledge_engine import InternalKnowledgeEngine
    from components.internal_knowledge.acquisition.composite_acquirer import CompositeKnowledgeAcquirer

    # 2. 或者 __init__.py 只导出 Protocol，导致调用方无法实例化引擎
    __all__ = ["InternalKnowledgeEngineProtocol"]
    ```
    *死穴所在*：一旦内部重命名 `internal_knowledge_engine.py` 为 `engine.py`，上层全线报 `ImportError`；仅导出 Protocol 则导致调用方无从下手。
  * ✅ **正例（Best Practice）**：
    ```python
    # components/internal_knowledge/__init__.py 统一门面收口
    from .factory import create_default_knowledge_engine
    from protocols.internal_knowledge import InternalKnowledgeEngineProtocol
    from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope
    from schemas.internal_knowledge.resolve_problem import ResolveProblem, ResolutionOutcome
    from schemas.internal_knowledge.source_uri import SourceURI, SourceScheme
    from infra.exceptions import KnowledgePipelineError

    __all__ = [
        "create_default_knowledge_engine",
        "InternalKnowledgeEngineProtocol",
        "PipelineEnvelope",
        "ResolveProblem",
        "ResolutionOutcome",
        "SourceURI",
        "SourceScheme",
        "KnowledgePipelineError",
    ]
    ```
    *核心收益*：外部调用方只需一行 `from components.internal_knowledge import ...` 即可完成全链路接入，内部文件结构重构对外部 100% 透明。

### Q_19：为什么组件内聚业务异常无需继承基础设施基类，以及 `RegistryExceptionMapper` 的异常链遍历机制对异常转译有何启示？
* **归属档案**：[[QA_03_Patterns_And_Contracts]]（细粒度）
* **核心疑惑**：既然底层定义了 `AgentBusinessError`，组件内部的 `KnowledgePipelineError` 是否必须继承它？在组件内部使用 `raise ... from exc` 转译异常时，又该如何避免遮蔽底层模型的恢复策略？
* **核心释义**：
  * **自描述异常直通**：`RegistryExceptionMapper` 在匹配异常链时，优先检查是否实现结构化鸭子类型协议（`error_code`、`user_friendly_hint`、`to_failure_metadata()`），不强制依赖特定继承树。
  * **异常链外向内匹配**：遍历 `__cause__` / `__context__` 时采取“自外向内”原则，**最先命中的规则直接胜出**。
* **核心答案**：
  1. **零继承解耦**：组件异常可直接继承原生 `Exception` 并实现上述鸭子类型成员，即可被 `RegistryExceptionMapper` 识别，无需反向依赖底层基类。
  2. **异常链遮蔽规避**：由于外层异常会优先短路匹配，若在组件内用 `raise ... from exc` 包装底层异常，会导致内层的限流或超时异常（如 429/504）无法触发模型恢复分支。因此，需模型自愈的底层异常严禁转译包装；仅在业务语义阻断时才允许抛出业务异常。
* **正反例总结**：
  * **反例**：强制继承跨层基类，并在单次 LLM 调用前置逻辑中使用 `raise ... from exc` 转译异常，导致外层协议直接遮蔽内层的 `RateLimitError`，使重试机制失效。
  * **正例**：组件内部异常零继承、仅靠鸭子类型实现协议；对于原生模型/网络异常直接透传占链头，仅在纯业务规则不满足时才抛出 `KnowledgePipelineError`，兼顾自包含与精准恢复。

### Q_20：为什么只读问答链路调用 `engine.fast_retrieve(envelope)` 后，下游拿到的 `rag_context` 只有干巴巴的卡片 ID 列表而没有正文？
* **归属档案**：[[QA_03_Patterns_And_Contracts]]（细粒度）
* **核心疑惑**：`storage.retrieve(envelope)` 执行成功并召回了 8 条知识 ID，但下游执行节点收到的背景资料却是 `"ont_xxx\n\n---\n\nlbl_yyy"`，完全没有知识内容。
* **核心答案**：`storage.retrieve(envelope)` 的职责边界是**“检索索引并返回排序后的知识 ID 列表填充 `resolution.resolutions`”**，它刻意不做磁盘正文水合（以支持上层做 ID 级去重或重排）。但在 `InternalKnowledgeEngine.fast_retrieve` 对外暴露的只读检索门面中，如果直接 `return await self.storage.retrieve(envelope)` 而不调用 `storage.load_contents(res.resolutions)` 水合正文写回 `resultant_situation`，出站封包器（`_pack_retrieval_to_state`）就会把字符串 ID 当成正文拼装进上下文。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：
    ```python
    class InternalKnowledgeEngine(InternalKnowledgeEngineProtocol):
        async def fast_retrieve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
            return await self.storage.retrieve(envelope)  # resolutions 里只有 ["ont_xxx", "lbl_yyy"]！
    ```
    *死穴所在*：下游 `executor` 看到一堆无意义的哈希 ID，根本不知道知识库里写了什么规则，导致基于知识库的问答退化为盲猜。
  * ✅ **正例（Best Practice）**：
    ```python
    class InternalKnowledgeEngine(InternalKnowledgeEngineProtocol):
        async def fast_retrieve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
            retrieved_env = await self.storage.retrieve(envelope)
            res = retrieved_env.problem_resolution
            if res and res.resolutions and not res.resultant_situation:
                hydrated = await self.storage.load_contents(res.resolutions)
                if hydrated.strip():
                    updated_res = res.model_copy(update={"resultant_situation": hydrated})
                    return retrieved_env.model_copy(update={"problem_resolution": updated_res})
            return retrieved_env
    ```
    *核心收益*：保持 `storage.retrieve` 与 `storage.load_contents` 底层职责分离的同时，确保上层只读检索门面直接交付完整的 Markdown 知识正文。
