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

