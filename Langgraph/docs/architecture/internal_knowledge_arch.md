# 域内知识库（Internal Knowledge & LLM-WIKI）架构设计文档

## 1. 架构

本系统采用 **依赖倒置原则（DIP）** 与 **黑板模式（Blackboard Pattern）** 设计，确保核心知识引擎与外部编排框架（如 LangGraph）、大模型供应商及底层物理存储完全解耦。

* **依赖方向单向无环**：`外部框架 (graphs/)` ➔ `接口契约 (protocols/)` + `数据契约 (schemas/)` 🡐 `具体算子 (components/)`。
* **核心零侵入**：领域核心层（`schemas/` 与 `components/`）仅依赖 Python 标准库与 Pydantic，绝对不引入 LangChain/LangGraph 等外部框架类型。

---

## 2. 四层代码分层与职责边界

| 架构层级 | 代码目录 | 核心职责 | 设计 |
| :--- | :--- | :--- | :--- |
| **数据契约层** | `schemas/internal_knowledge/` | 定义全链路流转的数据结构、枚举与结构不变式校验。 | **严格贫血 + 不可变（`frozen=True`）**。仅包含字段定义、`@model_validator` 自校验及无副作用渲染（`to_markdown()`），严禁包含 I/O 或推理逻辑。 |
| **接口协议层** | `protocols/internal_knowledge.py` | 定义四大环节及路由器的抽象行为契约（`Protocol`）。 | **高度泛化**。所有核心环节统一以 `PipelineEnvelope` 作为唯一输入与输出载体。 |
| **算子实现层** | `components/internal_knowledge/` | 提供模板方法基类（`Base*`）及具体适配器（LLM 推理、AST 切片、Markdown 落盘）。 | **向内实现协议，向外对接工具**。通过不可变副本（`model_copy`）推进黑板状态。 |
| **框架适配层** | `graphs/` | 充当“转接头（Adapter）”，将 LangGraph 的 `MasterAgentState` 与 `PipelineEnvelope` 双向翻译。 | 外部框架适应内部领域，绝不让外部状态污染内部模型。 |

---

## 3. 核心业务闭环与数据流转

全链路以 **`PipelineEnvelope`（黑板容器）** 为唯一传输载体，驱动“问题驱动（Problem-Driven）”的四阶闭合回路：

```text
[初始化 PipelineEnvelope(problem)]
    │
    ▼
1. 【存储.retrieve】 ──▶ 按可信度权重 (gold > release > debug) 召回已有知识 ID 填充 resolutions
    │
    ▼
2. 【运用.resolve】  ──▶ 评估现有知识是否足以解答问题
    ├── (outcome == SUCCESS) ──▶ 产出 resultant_situation，闭环正常终止
    └── (outcome != SUCCESS) ──▶ 诊断知识缺口 remaining_gap，进入增量构建回路：
            │
            ▼
        3. 【采集.acquire】  ──▶ 缺口路由推导 SourceURI ➔ 按协议切片生成原子 Information
            │
            ▼
        4. 【组织.organize】 ──▶ 3.1 质量过滤 ➔ 3.2 提取 Labeling ➔ 3.3 建模 Relating ➔ 3.4 聚拢 Ontology
            │
            ▼
        5. 【存储.save】     ──▶ 遵循写入隔离，将产物渲染为 Markdown 落盘至 debug/ 区
            │
            ▼
        [轮次交接清理] ──────▶ 清空本轮暂存工作区，iteration + 1，返回步骤 1 重新检索验证
```

---

## 4. LLM-WIKI 落盘治理规范（3层生命周期 × 4层抽象粒度）

文件系统存储遵循 `<vault_root>/<stage>/<layer>/<artifact_id>.md` 的目录结构：
<vault_root>: 根目录 ；<stage>：三层归档路径，对应生命周期； <layer>：四层知识形态； <artifact_id>.md： 具体知识文件名

* **三层生命周期（成熟度治理）**：
  * `debug/`：AI 自动生成的未审核知识缓冲区（写入隔离，自动化流水线**仅允许写入此区**）。
  * `release/`：人工审核通过的 AI 产物，或人工直接编写的准生产知识。
  * `gold/`：经过真实业务闭环验证有效（`outcome == SUCCESS`）的黄金标准知识。
* **四层抽象粒度（信息密度由低到高）**：
  * `information/` ➔ `labeling/` ➔ `relating/` ➔ `ontology/`。
* **跨层防断链机制**：所有跨文件引用严格使用全局唯一逻辑 ID（如 `[[lbl_101]]`），文件在 `debug -> release -> gold` 间迁移时零断链。

---

## 5. 核心架构决策问答录（FAQ：从宏观哲学到微观落盘）

### 【宏观粒度：架构哲学与边界】

#### Q1：依赖倒置原则（DIP）与六边形架构（端口与适配器模式）
> **核心疑惑**：为什么强调“协议（Protocols）是起点”，且核心组件只依赖纯数据模型与原生库？

* **核心答案**：这是**依赖倒置原则（DIP）**与**六边形架构**的基石。核心领域层（`schemas/` + `protocols/` + `components/`）必须保持高度泛化与纯净，绝不引入任何外部框架（如 LangGraph、FastAPI）或具体工具（如特定向量库）的字段。
* **架构收益**：依赖箭头永远只从外向内指（`外部框架 -> 协议/数据契约 <- 具体算子`）。无论未来替换底层存储介质，还是将本系统从 LangGraph 迁移至独立微服务或定时脚本，核心代码均无需修改。

**六边形架构**：
一句话精髓：核心领域定义标准插孔（Protocol），所有外部框架和底层存储都必须自己配转接头（Adapter）来插它
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


#### Q2：防腐层（Anti-Corruption Layer）与黑板模式（Blackboard Pattern）的职责隔离
> **核心疑惑**：域内实现了“零胶水代码”，但接入外部系统（如 LangGraph）时还是得写转换逻辑，这矛盾吗？

* **核心答案**：不矛盾，这是**域内高内聚**与**跨边界防腐层（Anti-Corruption Layer, ACL）**的自然分工。
  * **域内零胶水**：内部五大环节（`Storage` / `Application` / `Acquisition` / `Organization` / `Engine`）统一以 `PipelineEnvelope` 作为唯一黑板载体流转，组件间严丝合缝，零格式转换。
  * **边界适配层**：不同异构系统拥有各自的状态模型（如 LangGraph 的 `MasterAgentState`）。边界处的 `Adapter` 负责承担所有的“出入站翻译”脏活，从而守住核心领域层的 100% 纯净。

---

### 【中观粒度：异构系统集成与兼容性】

#### Q3：信息隐藏（Information Hiding）与黑板模式作用域隔离
> **核心疑惑**：外部系统（如 LangGraph 主图）需要在自己的全局 State 中定义 `knowledge_envelope` 吗？
释义： “不该让外部知道的内部变量（如 PipelineEnvelope），就绝对不要暴露到外部系统的全局状态（MasterAgentState）里”。

* **核心答案**：**不需要，且强烈建议不要定义**（避免内部实现细节扩散污染外部系统）。
  * **黑盒单节点挂载（推荐）**：通过 `InternalKnowledgeEngineProtocol.query_and_learn(problem)` 门面方法对外暴露极简契约。`PipelineEnvelope` 仅作为节点函数内部的局部变量创建并销毁，外部主图只需传入纯文本 `problem` 并接收 `rag_context` 字符串即可，实现零模型泄漏。
  * **白盒多节点编排（按需）**：仅当需要利用 LangGraph 原生条件边控制循环或做 Human-in-the-loop（人工审核中断）时，才在**子图私有 State** 中使用 `PipelineEnvelope`，跑完后依然只向外部主图输出标准结果字段。

#### Q4：系统互操作性（Interoperability）与适配集成模式
> **核心疑惑**：如果外部系统没有产生我们需要的数据，或者遗留系统改动成本极高，如何实现兼容？
释义：当外部旧系统改不动、或者没有提供你想要的字段时，不要去改内部核心代码，而是通过“缺啥补啥适配器”、“旁路监听 MQ”或“套一层 MCP / OpenAI 兼容协议外壳”让两边能顺畅对话。

* **核心答案**：遵循**“核心领域铁打不动，外部兼容向外延伸”**的三大渐进集成策略：
  1. **智能补全适配层（Enriching Adapter）**：外部传参缺字段时，在 Adapter 层自动补齐默认值（如生成 `trace_id`）或挂载轻量级 LLM 预处理器将杂乱输入浓缩为标准 `problem`。
  2. **旁路事件监听（Sidecar / MQ Consumer）**：当外部系统无主动查询意识时，通过订阅其现有的 Git Webhook 或消息队列，在后台静默触发 `acquire -> organize -> save` 沉淀知识，外部系统一行代码无需改动。
  3. **行业标准兼容协议外壳**：为引擎包裹一层 **MCP Server（Model Context Protocol）**、**OpenAPI REST 接口** 或 **OpenAI `/v1/chat/completions` 兼容接口**，让任何外部 Agent 或客户端零改造直接接入。

---

### 【微观粒度：数据模型、算子基类与文件落盘】

#### Q5：不可变贫血模型与模板方法（Template Method）职责切分
> **核心疑惑**：数据模型应该设计为“贫血模型”还是“充血模型”？具体实例交给谁生成？
释义： 
1.贫血模型（Anemic Domain Model） + 不可变对象（Immutable Object）：数据类（ImmutableSchema）只存数据和自校验规则，一旦创建就不能原地修改，更新只能靠生成新副本。
2.模板方法模式（Template Method）：基类（Base*）把固定流程（拆信封 ➔ 调子类 ➔ 装回新信封）写死成模板，只留出核心推理步骤让子类去填空

* **核心答案**：在黑板模式与不可变数据流下，采用**严格不可变的贫血模型（`ImmutableSchema`）**。
  * **模型边界**：仅保留字段定义、结构不变式自校验（`@model_validator`）、纯只读计算属性（`@property`）、纯函数式状态跃迁（如 `advance_to_next_iteration()`）以及无副作用渲染（`to_markdown()`）。
  * **实例生成权**：采用**模板方法模式**，基类（`Base*`）负责信封的拆箱校验与不可变回写（`model_copy`），具体子类（如 `LLMKnowledgeApplicator`）负责执行推理并生成新的领域数据实例；核心抽象方法保持 `@abstractmethod` 不写默认逻辑，防止静默失败。

#### Q6：开闭原则（OCP）与泛型多态（Parametric Polymorphism）
> **核心疑惑**：`Labeling.label` 应该用枚举还是字符串？`RelatingConcepts` 如何兼顾通用与领域扩展？
释义：开闭原则要求“对扩展开放，对修改关闭”。具体到这里就是：Labeling.label 用 str 而不是写死枚举，这样遇到新业务实体不用改代码；RelatingConcepts 用 Python 泛型 Generic[RelTypeT] 接收外部传入的领域枚举（如 CodeRelationType），核心文件不用反向导入任何具体业务文件

* **核心答案**：
  * **`Labeling.label` 必须保持 `str`**：开放域动态抽取的概念实体无法穷举，强行枚举会扼杀扩展性并破坏 DIP；若需结构化过滤，应正交增加抽象元分类字段（如 `category: NodeCategory`）。
  * **`RelatingConcepts` 禁止反向导入具体业务领域**：核心层仅定义 `GeneralRelationType`，通过泛型 `Generic[RelTypeT]` 或存储层命名空间支持具体领域（如 `CodeRelationType`）扩展，同时在模型内拦截 `label_1_id == label_2_id` 的无效自环边。

#### Q7： 值对象（Value Object）嵌入与位置透明性（图谱跨生命周期防断链机制）
> **核心疑惑**：语义边（`RelatingConcepts`）和采集源（`SourceURI`）在 Markdown 体系下如何落盘？
释义：
1.值对象（Value Object）：像 SourceURI 这种没有独立生命周期、只描述属性的数据结构，直接嵌套在 Information 里面存盘即可，不用单独建文件
2.位置透明性（Location Transparency）：在图谱引用时只认全局唯一的逻辑 ID（如 [[lbl_101]]），不写死物理文件夹路径。这样无论文件在 debug/、release/ 还是 gold/ 文件夹之间怎么搬家，链接永远不会失效

* **核心答案**：
  * **`SourceURI` 不单独落盘**：它属于溯源值对象，直接作为字段嵌入 `Information` 的 YAML Frontmatter 中（通过 `@field_serializer` 自动扁平化为紧凑 URI 字符串），保障增量更新的原子性。
  * **语义边采用独立卡片 + 本体双链聚合**：每条边按 `<vault_root>/<stage>/relating/<relation_id>.md` 独立落盘，正文中渲染标准 Obsidian 双向链接（`[[lbl_101]] ➔ causal ➔ [[lbl_205]]`）；上层 `Ontology` 卡片通过引用节点与边 ID 成为知识图谱的星型枢纽节点。
  * **跨生命周期防断链**：所有跨文件引用严格使用全局唯一逻辑 ID（如 `[[lbl_101]]`），严禁硬编码物理路径，确保文件在 `debug -> release -> gold` 之间人工审核迁移或自动晋升时零断链。

---

### 【中观粒度：插件注册与路由分发】

#### Q8：注册表模式（Registry Pattern）与数据驱动分发（Data-Driven Dispatch）
> **核心疑惑**：`BaseKnowledgeAcquirer` 用“类装饰器 + 类属性字典”做协议路由，而 `BaseGapRouter` 却是纯模板方法，为什么两者不一致？

释义：
1. 注册表模式（Registry Pattern）：维护一张“键 ➔ 实现类”的全局表，运行时按键查表得到具体实现，新增实现只需加一行装饰器，无需改动分发方代码。
2. 数据驱动分发（Data-Driven Dispatch）：分发依据来自**数据本身携带的字段**（如 `uri.scheme`），而不是代码里写死的 `if/elif` 分支。

* **核心答案**：这不是风格不统一，而是**分发键（dispatch key）是否存在**所决定的必然差异。注册表模式成立需要同时满足三个前提：

| 前提 | `BaseKnowledgeAcquirer` | `BaseGapRouter` |
| :--- | :--- | :--- |
| ① 存在来自数据的离散键 | ✅ `uri.scheme`（封闭枚举，固定取值） | ❌ 入参是自然语言 `gap_description`，无枚举键 |
| ② 单次调用内按键多次异构分发 | ✅ 一次 `acquire` 遍历多个不同协议 URI | ❌ 每轮只调一次 `_infer_target_uris` |
| ③ 多种实现按键共存 | ✅ 需同时支持 repo / file / http / s3 / db / chat | ❌ 通常只有一个活跃策略 |

  结论：**采集环节用注册表（按数据分发），路由环节用模板方法 + 构造注入（按装配选择）**。二者解决的是不同问题——**注册表负责选“实现”，依赖注入负责选“策略”**，不可互换。

* **若强行给 Router 套注册表会怎样**：`register(scheme)` 的 key 无从填写（系统里没有“缺口类型”枚举，而“把自然语言缺口分类成 key”这一动作本身就是 Router 的职责，形成自指循环）；且没有任何调用方会拿 key 去查这张表，最终得到一张“没人查的表”——属于伪抽象，违反 YAGNI。

* **Router 真正的多策略扩展姿势是组合（Composite / Chain），而非注册表**：

```text
route(gap, ctx)
   ├─ ① IndexRouter（本地目录索引，快 / 准 / 零成本） ── 命中即返回，短路后续
   └─ ② LlmRouter（语义推断，慢 / 贵 / 覆盖长尾）      ── 兜底
        └─ 合并结果 → 仍复用 BaseGapRouter.route() 的统一去重保序
```

  组合方式持有 `List[BaseGapRouter]`，可天然表达**优先级顺序**（dict 的 key 无序，还需自行发明 key 名）；新增策略 = 往列表追加一个元素，同样满足开闭原则。

#### Q9：注册表模式的三条落地约束（导入时机 / 静默覆盖 / 启动校验）
> **核心疑惑**：装饰器注册看起来一行就搞定，工程落地时最容易踩什么坑？

释义：注册表把“登记”这个副作用藏进了装饰器，隐藏了调用顺序依赖——**表什么时候被填充，取决于模块什么时候被导入**。

* **核心答案**：必须显式管理以下四类风险：
  1. **导入期副作用（最容易翻车）**：`register()` 在模块被 `import` 的那一刻才写入 `_registry`。若具体采集器模块从未被导入，`_registry` 为空，`acquire` 必然抛出“尚未注册”错误。→ 由引导层（聚合 `__init__.py` 或插件自动发现机制）**显式导入全部实现模块**，并在应用启动时做一次注册表完整性断言。
  2. **静默覆盖**：`cls._registry[scheme] = sub_cls` 无判重，两个模块注册同一 `scheme` 时**后注册者无声覆盖前者**，行为随 import 顺序漂移、极难复现。→ 注册时判重并抛错。
  3. **继承分叉**：`_registry` 是可变类属性，若某子类无意写了 `_registry = {}`，会“另开一张表”——装饰器写进 A 表、`acquire` 查 B 表，路由全部失效。→ 读取侧统一写 `type(self)._registry`，且禁止子类重新赋值。
  4. **错误语义**：注册缺失属于“装配/配置错误”，应抛领域异常（如 `UnregisteredSchemeError`）；`NotImplementedError` 按 Python 约定专指“抽象方法未被子类实现”，误用会把排查方向从“漏导入模块”误导到“漏写子类方法”。

* **补充：表里存“类”而非“实例”是刻意设计**。延迟实例化使 `gap_router` 等依赖可按调用方注入；`handlers_cache` 仅在单次 `acquire` 内复用同协议实例。若某实现持有昂贵跨轮资源（连接池、已 clone 的仓库），需提升到实例级或依赖注入，而非依赖这个单轮缓存。

#### Q10：注册模式向 Agent 问题定位的泛化（Router + Registry + LLM Fallback）
> **核心疑惑**：这套“注册 + 路由 + 分发”的思路能否迁移到 Agent 的问题定位？把兜底换成 LLM 是否成立？

释义：
1. 概率标签（Probabilistic Label）：由语义识别推断出的分类标签，附带置信度，可能未命中、可能多标签，与枚举式的“确定键”本质不同。
2. 弃权通道（Abstention Channel）：识别不出高置信标签时，不报错，而是显式路由到一个 `UNKNOWN` 处理器。

* **核心答案**：思路成立，属于主流的 **Router + Registry + Fallback** 三层架构；且本系统 `remaining_gap ➔ gap_router.route ➔ acquire ➔ 新 envelope` 已经就是 Agent 循环的骨架。但照搬前必须修正三点：
  1. **路由键从“确定枚举”降级为“概率标签”**：必须引入置信度与弃权通道，用分层漏斗替代单次精确匹配：

```text
问题描述 ──▶ 语义识别
   ├─ ① label ∈ registry 且 score ≥ 0.9 ──▶ 确定性 Handler（幂等 / 可复现 / 低成本）
   ├─ ② label ∈ registry 且 0.5 ≤ score < 0.9 ──▶ 确定性 Handler + 结果打 low_conf 标记
   └─ ③ label ∉ registry 或 score < 0.5 ──▶ @register(UNKNOWN) 的 LLM Handler
                                                 └─▶ 产出 suggested_label，写入未命中日志
                                                       └─▶ 同模式复现 N 次后晋升为确定性 Handler
```

  2. **兜底不要写进 `except` 分支**：应把 LLM 兜底**注册成一个 `UNKNOWN` 处理器**。否则统一循环、实例缓存、信封不可变回写这些不变式全部被绕过，代码分叉成两套路径，且无法统计兜底率。注册成处理器后，安全边界仍是**白名单**——LLM 只能选择注册表中允许的执行器，不会退化为开放式任意执行。
  3. **兜底产出必须携带审计字段**：`produced_by` / `deterministic: bool` / `confidence`。确定性结论与 LLM 推断结论可信度不同，下游（证据链、置信度打分）必须可区分、可追溯。

* **进阶技巧：用注册表驱动约束解码**。把注册表的 key 集合注入 LLM 输出 schema（如 `Literal[(*registry.keys(), "UNKNOWN")]`），使模型在结构层面不可能输出未注册标签，从源头消灭“路由键幻觉”，比“事后校验 + 重试”更可靠。

* **Agent 场景必须补的三道保险**：① 循环保护（`max_depth` / `visited` 集合，现有 `remaining_gap` 回路尚无收敛保护）；② 成本分层（确定性热路径优先，记录 `fallback_rate` 作为“下一个该补哪个处理器”的数据依据）；③ 白名单即安全边界（定位动作常涉及查库 / 跑脚本 / 调接口，绝不允许 LLM 自行拼接命令）。

* **一句话总结**：`register` = 给「路由键」和「实现类」牵线的注册表；`_registry` = 导入期自动填充的登记簿；分发入口 = 拿数据里的键去查表。**有数据键则用注册表，无数据键则用模板方法 + 依赖注入，二者正交、不可互换。**