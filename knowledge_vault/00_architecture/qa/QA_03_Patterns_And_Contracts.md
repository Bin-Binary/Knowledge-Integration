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
