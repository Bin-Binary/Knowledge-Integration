# Internal Knowledge QA

## 粗粒度：方法论、原则、设计与架构相关

Q1：依赖倒置原则（DIP）与六边形架构（Ports & Adapters）

核心疑惑：为什么强调协议（protocols/）是系统起点，且核心业务组件绝对不能导入 LangGraph、OpenAI SDK 或具体存储驱动？
• 核心答案：核心领域层（schemas/ + protocols/ + components/）必须保持绝对纯粹，只依赖 Python 原生库与基础类型校验器。依赖箭头永远只从外向内单向流动（外部框架 -> 协议/数据契约 <- 具体算子）。外部框架（如 LangGraph）仅仅是六边形最外层的驱动适配器，核心系统随时可零成本脱离它独立运行或暴露为 MCP Server。

Q2：防腐层（ACL）与域内黑板模式（Blackboard Pattern）的边界划分

核心疑惑：系统内部号称“零胶水代码”，但接入 LangGraph 时还是要在节点里写字段翻译代码，这两者是否矛盾？
• 核心答案：不矛盾，这是域内高内聚与跨边界防腐层（Anti-Corruption Layer）的职责正交：
	• 域内零胶水：内部五大环节统一以 PipelineEnvelope 作为唯一通用传输载体接力演化，组件间严丝合缝，零格式转换。
	• 边界防腐层：异构系统（如 LangGraph 的 MasterAgentState）拥有各自的状态结构。边界处的 Adapter 节点专门承担“出入站翻译”脏活，守住核心领域层的 100% 纯净。

Q3：信息隐藏（Information Hiding）与外部状态机零泄漏

核心疑惑：外部系统（如 LangGraph 主图）需要在全局 State 中定义 knowledge_envelope 吗？如果遗留外部系统难以改动，如何实现低成本兼容？
• 核心答案：
	• 状态隐藏：主图采用黑盒单节点挂载时，全局 State 严禁定义 knowledge_envelope，该载体仅作为节点局部临时变量流转，对外仅输出 rag_context 字符串；仅在白盒多节点编排时，才将其隔离在子图私有 State（KnowledgeSubGraphState）中。
	• 异构系统兼容三策：对外系统缺字段时采用智能补全适配器（自动生成默认值或轻量预处理）；对无主动调用意识的系统采用旁路事件监听（订阅 Git Webhook / MQ）；对多 Agent 生态直接套一层 MCP / OpenAI 兼容协议外壳实现零改造接入。

Q4：数据治理生命周期与开闭原则（OCP）演进

核心疑惑：如何防止 AI 自动生成的未审核知识污染生产环境？同时如何保证未来新增采集源、领域关系或组织算子时不修改核心调度器？
• 核心答案：
	• 三层生命周期治理：引入 debug（AI 自动生成隔离区）➔ release（人工审核/编写区）➔ gold（闭环验证有效区）矩阵，配合跨层引用使用全局唯一逻辑 ID（位置透明性），确保文件跨目录晋升时全图谱零断链。
	• 开闭原则扩展点：开放域概念 label 保持 str（辅以泛化元分类枚举）；领域关系边采用 Generic[RelTypeT] 泛型注入；新算子通过装饰器注册表 + pkgutil 动态包扫描实现零配置自动发现。

## 细粒度：标准抽象、职责边界与设计模式

Q5：不可变贫血模型与模板方法模式（Template Method）的职责切分

核心疑惑：数据模型应该采用贫血还是充血模型？数据实例究竟由谁生成，基类是否该提供核心业务方法的默认实现？
• 核心答案：
	• 严格不可变贫血模型（ImmutableSchema）：数据契约层只保留字段定义、结构不变式校验（@model_validator）、只读计算属性（@property）、纯函数状态跃迁（advance_to_next_iteration()）及无副作用渲染（to_markdown()），绝不包含 I/O 与策略推理。
	• 模板方法收口样板代码：基类（Base*）负责信封拆箱校验、并发限流、不可变副本回写与回执封装；具体子类负责核心推理并生成新实例。核心抽象方法保持 @abstractmethod 不写默认逻辑，遵循 Fail-Fast（快速失败） 原则防止静默错误。

Q6：组合优于继承（Composition over Inheritance）与通用能力下沉

核心疑惑：信息质量评估过滤（3.1 环节）是通用能力，抽离为全局工具放入根目录是否违背 DIP？组织阶段内部四步子步骤应该用基类钩子还是拆分为独立组件？
• 核心答案：
	• 跨切面能力下沉：在根目录 protocols/evaluation.py 定义逆变泛型协议 QualityEvaluatorProtocol[ItemT_contra]，知识库组件通过构造函数注入使用，完全不违背 DIP；具体业务子类（InformationQualityEvaluator）必须归属在高度相关的知识库业务组件目录下（包内聚原则）。
	• 微算子组合替代多层继承：当组织阶段四步剥离外层模板控制后，拆分为独立的原子微算子组件（直接实现轻量级内部协议），由编排器（KnowledgeOrganizer）注入组合，彻底消除上帝类，支持“LLM 抽点建边 + 零延迟并查集图聚类”的混合算力装配。

Q7：插件自动发现与多实现冲突仲裁策略

核心疑惑：当统一注册中心扫描出同阶段的多个算子实现时，系统如何确定调用哪一个，还是全部调用？
• 核心答案：在注册中心（OrganizationPluginRegistry）中按阶段特性实施双模式仲裁：
	• 单选激活模式（Exclusive Selection，适用于 3.1 评估 / 3.4 聚类）：通过 is_default=True 指定默认胜出者，同时支持运行期传入配置名称动态切换（如测试环境切换为纯规则评估器）。
	• 并发累加模式（Fan-Out & Merge，适用于 3.2 提特征 / 3.3 建边）：并发调度所有已启用算子，并基于确定性主键自动去重合并输出（保留高置信度结果）。

Q8：完整契约注入与实体标识符水合（Entity Hydration）

核心疑惑：检索环节仅返回知识 ID 列表，运用环节需要读取 Markdown 原文才能推理，应该传回调函数还是直接注入存储协议？
• 核心答案：直接注入完整的 KnowledgeStorageProtocol（在协议中补充异步契约 async def load_contents(artifact_ids: List[str]) -> str）。向内依赖协议完全符合 DIP，且原生支持 async/await 异步非阻塞加载，语义远比零散的同步 Callable 回调函数清晰健壮。

## 精细粒度：微观代码技巧、算法与防御性细节

Q9：逻辑定位键 + 局部结构指纹（解决 ID 稳定性与同源多切片唯一性）

核心技巧：构建 info_id 哈希种子时，严格剥离易变的 Git revision 与物理行号（L42-L68），仅保留逻辑根路径，同时叠加切片级局部身份标识 slice_identity（如 AST 符号名 func:login、文档标题路径 heading:1.2 或分块序号 chunk:0），并采用 16 位 hex 摘要（info_<16位hex>）。既保证同源多切片 100% 不撞车，又实现代码增删改后的确定性原地覆盖。

Q10：利用 Python 字典有序性与后键覆盖实现幂等 Upsert 合并

核心技巧：在采集合并 raw_infos、特征提取去重 labels 时，利用 Python 3.7+ 字典天然保持插入顺序且后键自动覆盖前键的特性，用单行字典推导式 {item.id: item for item in (*old_items, *new_items)} 即可同时完成“O(1) 复杂度去重 + 最新切片覆盖旧切片 + 保留原始顺序”，杜绝重复切片浪费下游 LLM 算力。

Q11：Pydantic v2 不可变拷贝校验绕过防御（Explicit Re-Validation）

核心技巧：Pydantic v2 的 model.model_copy(update={...}) 默认跳过 @model_validator 校验。在基类模板方法（如 BaseKnowledgeApplicator.resolve）接收子类返回的更新副本后，显式执行 ResolveProblem.model_validate(updated.model_dump()) 强制重校验，死守闭环不变式（如未解决时必填 remaining_gap）。

Q12：子类隔离策略注册表（__init_subclass__）

核心技巧：在通用模板基类 BaseQualityEvaluator 中重写 __init_subclass__，为每个继承它的业务子类自动初始化独立的 _heuristic_registry = {} 类字典。彻底防止不同业务域（知识库切片 vs 聊天历史窗口）通过装饰器注册快筛规则时发生字典键污染。

Q13：高成熟度优先遮蔽（Priority Shadowing）与零依赖双字滑窗检索

核心技巧：
• 目录遮蔽：LocalMarkdownStorage 检索时严格按 gold (1.0) -> release (0.8) -> debug (0.4) 顺序遍历，配合 seen_ids: Set[str] 集合，一旦高成熟度目录命中某 ID，自动屏蔽低层级目录的同名旧残留副本。
• 轻量分词与动态代码围栏：内置“英文/下划线标识符正则 + 中文 2-gram 滑窗”混合分词器实现零依赖本地检索；渲染 Information 正文时动态递增反引号长度（while fence in text: fence += ""`），彻底防止切片内嵌 Markdown 代码块破坏外层文档结构。

Q14：无大模型图连通分量聚拢（Union-Find）与悬空边清洗

核心技巧：在 3.3 关系建模后，先用合法节点 ID 集合过滤掉大模型幻觉产生的悬空边（label_1_id not in valid_ids）与自环边；在 3.4 本体聚拢中，直接采用纯内存并查集（Union-Find）将连通的节点与边聚拢为 Ontology，0 毫秒延迟且 100% 满足“多节点子图必填语义边”的模型约束。

## 全链路核心架构亮点 QA 总结

Q1：请求从 FastAPI 网关进入，经过 LangGraph 再到知识库引擎，各层是如何实现“职责隔离与零耦合”的？

• 核心答案：通过 四层同心圆隔离（六边形架构） 确保每一层只认识自己相邻的抽象契约：
	1. 网关层（FastAPI）：只负责 HTTP 协议解析、超时熔断与 trace_id 注入，只认识 AgentApplication。
	2. 容器装配层（bootstrap.py）：作为全系统唯一的“组装厂”，负责实例化具体的大模型客户端和存储后端，并把它们塞进抽象协议中。
	3. 编排层（graphs/）：LangGraph 主图只负责节点拓扑流转与异常分支跳转；knowledge_graph.py 充当防腐层（ACL），将外部 MasterAgentState 翻译为内部 PipelineEnvelope 局部变量，外部状态机零污染。
	4. 核心领域层（InternalKnowledgeEngine）：只依赖 protocols/ 和 schemas/，彻底不知道外面有 FastAPI 或 LangGraph，随时可拆出独立运行或暴露为 MCP Server。

Q2：当知识库遇到“未知问题（冷启动）”时，全链路是如何自动完成“现学现卖 + 自我验证”闭环的？

• 核心答案：依赖 黑板模式（PipelineEnvelope） + 确定性状态机闭环：
	1. 缺口驱动（Gap-Driven）：第 0 轮检索为空时，LLMKnowledgeApplicator 不会瞎编，而是输出 outcome=FAILURE 并生成具体的 remaining_gap 写入黑板信封。
	2. 四阶信息提纯与隔离落盘：引擎检测到未解决且未超最大轮次（can_continue_loop），自动驱动【采集（按协议切片生成确定性 info_id） ➔ 组织（两级质量过滤 + LLM 抽点建边 + 并查集图聚类生成 Ontology） ➔ 存储（渲染为带 Obsidian 双链的 Markdown 写入 debug/ 隔离区）】。
	3. 工作区清零与二次召回验证：落盘后调用 advance_to_next_iteration() 清空本轮暂存列表防止重复入库，随后 iteration + 1 重新回到【检索 ➔ 运用】验证新沉淀的知识是否足以回答原问题，直至收敛输出 rag_context。

Q3：在这套全链路设计中，如何兼顾“生产环境高安全性（防异常崩溃、防脏数据）”与“未来高扩展性”？

• 核心答案：依靠三大工程级防御与扩展机制：
	1. 全链路异常自愈网：无论是上游意图识别出错，还是知识库内部大模型超时/解析失败，均由 ExceptionMapper 标准化为 FailureContext，无缝路由至主图的 recovery_node 执行修复或安全降级兜底，绝不直接向用户抛出 500 堆栈。
	2. 知识成熟度治理（debug -> release -> gold）：AI 自动生成的知识严格隔离在 debug/ 目录；检索时按 gold (1.0) > release (0.8) > debug (0.4) 权重遮蔽低层级副本；跨文件引用全采用全局唯一逻辑 ID（[[lbl_xxx]]），文件跨目录晋升零断链。
	3. 插件化自动发现（OCP）：采集协议（@BaseKnowledgeAcquirer.register）与组织微算子（@OrganizationPluginRegistry.register + pkgutil 动态扫描）均支持装饰器自动注册，未来新增数据源或建边算法只需新增文件，主干代码零修改。

## 开放问题：

### LLM输出字段不合规致组织失败

闭环测试中，LLM 频繁擅自修改或遗漏 JSON 字段名触发 ValidationError，加上部分算子误对同步接口使用 await 触发 TypeError，导致知识库最终只落盘了 information 切片，labeling、relating、ontology 三层全空。

单点报错后，由于 asyncio.gather 没有做单条异常隔离，导致整批并发组织任务一起崩溃；异常一路穿透引擎冒泡到主图的 recovery_node，又因为外部恢复器未注册知识库内部 Schema 而无法修复，最终全链路被迫降级致歉。

核心根因有四点：json_mode 仅保证 JSON 格式合法而不强制约束字段名，且提示词未注入明确字段说明；底层适配器缺少“校验失败后携带报错原地重试”的自愈机制；并发编排缺少单条切片的 try/except 舱壁隔离；以及直接 await 了同步的 generate_structured 方法。

```
1. engine.execute() 进入 iteration 0
2. storage.retrieve() → 空（冷启动）
3. application.resolve() → outcome=FAILURE, remaining_gap="了解 cmc.sh 脚本功能"
4. acquisition.acquire() → GapRouter 路由到 cmc.sh → ShellRepoAcquirer 采集 7 条 Information 切片
5. organization.organize() →
   5.1  quality_evaluator.evaluate(info) →
        LLM 被要求输出 {"reason": "...", "score": 0.0~1.0}
        但实际返回 {"value_density": 0.3, "reason": "..."} 或 {"score": 0.3}（缺 reason）
        → Pydantic ValidationError: Field required / Field missing
        → 异常上抛
6. knowledge_blackbox_node try/except 捕获 → ExceptionMapper.to_failure_context()
   → failure_context 写入 MasterAgentState
7. _route_after_knowledge → "recovery_node"
8. recovery_node → JsonHealRecoveryManager.can_handle() 检查 target_schema_name
   → SCHEMA_REGISTRY 只含 "IntentResult"，不含 "_InfoQualityOutput"
   → can_handle=False → 兜底降级 → 输出 "抱歉，系统处理您的请求时遇到了一点小问题"
9. 结果：rag_context=None, labels/relations/complexes 全空, 只有 information 层落盘
```

### 根因分析

**根因 1：json_mode 不强制字段名**

`LangChainStructuredAdapter.generate_structured()` 使用 `with_structured_output(schema, method="json_mode")`。`json_mode` 模式下，OpenAI 兼容网关只要求 LLM 输出合法 JSON，**不强制字段名必须与 JSON Schema 一致**。LLM（尤其国产推理模型如 GLM-V5.1）经常自行替换字段名为更"语义化"的名称：
- 期望 `"score"` → 实际输出 `"value_density"` / `"quality_score"` / `"rating"`
- 期望 `"reason"` → 完全省略（只输出了 `{"score": 0.3}`）
- 期望 `"concept_tag"` → 可能输出 `"tag"` / `"concept"` / `"label"` 等
- 期望 `"source_label_id"` → 可能输出 `"source"` / `"from_id"` 等

**根因 2：必填字段无容错**

`_InfoQualityOutput` 的 `reason: str = Field(...)` 为必填，LLM 遗漏时直接 `ValidationError`。
`_ExtractedConceptItem` 的 `concept_tag: str = Field(...)` 为必填，LLM 换名时同上。

**根因 3：组织环节无异常隔离**

`organizer.organize()` 使用 `asyncio.gather(*(_eval_one(info) for info in envelope.raw_infos))` 并发调度所有评估。任何一条 info 的评估异常都会导致整个 gather 崩溃，全部评估结果丢失。同理，3.2 提特征和 3.3 建边的 LLM 调用也无 try/except 兜底。

**根因 4：recovery 不覆盖知识库内部 Schema**

`JsonHealRecoveryManager.SCHEMA_REGISTRY` 只注册了 `"IntentResult"`，知识库内部的所有 LLMOutputSchema（`_InfoQualityOutput`、`_LabelBatchOutput`、`_RelationBatchOutput`）均未被注册，导致 recovery 无法修复任何知识库环节的输出异常。

**根因 5：generate_structured() 返回同步结果但调用方误用 await**

`label_extractor.py:51` 和 `relation_builder.py:67` 直接 `await self.llm.generate_structured(...)`，但 `generate_structured` 是同步方法（`def` 非 `async def`），返回非 awaitable 对象。Python 中 `await` 一个非 awaitable 会抛 `TypeError: object X can't be used in 'await' expression`。`info_evaluator.py` 则正确使用了 `inspect.isawaitable` 判断。


#### Q16：弱约束结构化输出（`json_mode`）的适配器层微闭环自愈与批量并发舱壁隔离
> **核心疑惑**：端到端测试中，大模型在 `json_mode` 下频繁偏离 Pydantic 字段名约定，且 `asyncio.gather` 并发调用时单条报错会引爆整条组织流水线；如何在不靠穷举同义词“猜词”的前提下，从根本上解决字段漂移与并发雪崩？

* **核心答案**：严禁在 Schema 中通过 `AliasChoices` 穷举同义词（无法随模型切换收敛），应采用 **“输入强引导 + 适配器内生自愈 + 算子舱壁隔离”** 三层架构治理：
  1. **输入层显式契约注入**：针对 `json_mode` 不自动下发 Schema 结构的特性，在调用大模型前统一将 `response_schema.to_prompt_guide()`（及标准 JSON 示例）注入 System Prompt，消除信息不对称。
  2. **适配器内生自愈微闭环（Self-Healing Adapter）**：在 `LangChainStructuredAdapter.generate_structured` 基础设施内部封装局部重试循环（1~2 次）。一旦触发 `ValidationError` 或 JSON 解析异常，立即将**原始错误输出 + Pydantic 精确缺失字段报错信息**追加进对话上下文要求模型原地纠偏，将格式波动消化在底层适配器内，无需惊动外层 LangGraph `recovery_node` 导致全图回退。
  3. **调用规范与舱壁隔离（Bulkhead Pattern）**：
     * 统一异步非阻塞调用包装器（兼容 `inspect.isawaitable` 并自动将同步方法卸载至 `asyncio.to_thread`），根除 `await` 同步方法引发的 `TypeError`。
     * 在 `KnowledgeOrganizer` 的并发批处理中为单条切片加上局部 `try...except` 舱壁隔离，单条重试耗尽后仅降级跳过该条目，保障其余切片的 `labeling -> relating -> ontology` 链路完整落盘。
