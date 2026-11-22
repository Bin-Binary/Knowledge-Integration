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
