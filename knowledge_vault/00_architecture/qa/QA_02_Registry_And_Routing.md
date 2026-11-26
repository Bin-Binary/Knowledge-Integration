---
title: QA-02 中观粒度：插件注册与路由分发
tags: [qa, registry-pattern, routing, dispatch, agent]
stage: gold
---

# 中观粒度：插件注册与路由分发

返回总纲：[[Internal_Knowledge_Architecture]]

### Q5：注册表模式（Registry Pattern）与数据驱动分发（Data-Driven Dispatch）
* **核心疑惑**：`BaseKnowledgeAcquirer` 用“类装饰器 + 类属性字典”做协议路由，而 `BaseGapRouter` 却是纯模板方法，为什么两者不一致？
* **核心释义**：
  1. **注册表模式（Registry Pattern）**：维护一张“键 ➔ 实现类”的全局表，运行时按键查表得到具体实现，新增实现只需加一行装饰器，无需改动分发方代码。
  2. **数据驱动分发（Data-Driven Dispatch）**：分发依据来自**数据本身携带的字段**（如 `uri.scheme`），而不是代码里写死的 `if/elif` 分支。
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

### Q6：注册表模式的三条落地约束（导入时机 / 静默覆盖 / 启动校验）
* **核心疑惑**：装饰器注册看起来一行就搞定，工程落地时最容易踩什么坑？
* **核心释义**：注册表把“登记”这个副作用藏进了装饰器，隐藏了调用顺序依赖——**表什么时候被填充，取决于模块什么时候被导入**。
* **核心答案**：必须显式管理以下四类风险：
  1. **导入期副作用（最容易翻车）**：`register()` 在模块被 `import` 的那一刻才写入 `_registry`。若具体采集器模块从未被导入，`_registry` 为空，`acquire` 必然抛出“尚未注册”错误。→ 由引导层（聚合 `__init__.py` 或插件自动发现机制）**显式导入全部实现模块**，并在应用启动时做一次注册表完整性断言。
  2. **静默覆盖**：`cls._registry[scheme] = sub_cls` 无判重，两个模块注册同一 `scheme` 时**后注册者无声覆盖前者**，行为随 import 顺序漂移、极难复现。→ 注册时判重并抛错。
  3. **继承分叉**：`_registry` 是可变类属性，若某子类无意写了 `_registry = {}`，会“另开一张表”——装饰器写进 A 表、`acquire` 查 B 表，路由全部失效。→ 读取侧统一写 `type(self)._registry`，且禁止子类重新赋值。
  4. **错误语义**：注册缺失属于“装配/配置错误”，应抛领域异常（如 `UnregisteredSchemeError`）；`NotImplementedError` 按 Python 约定专指“抽象方法未被子类实现”，误用会把排查方向从“漏导入模块”误导到“漏写子类方法”。
* **补充说明**：表里存“类”而非“实例”是刻意设计。延迟实例化使 `gap_router` 等依赖可按调用方注入；`handlers_cache` 仅在单次 `acquire` 内复用同协议实例。若某实现持有昂贵跨轮资源（连接池、已 clone 的仓库），需提升到实例级或依赖注入，而非依赖这个单轮缓存。

### Q7：注册模式向 Agent 问题定位的泛化（Router + Registry + LLM Fallback）
* **核心疑惑**：这套“注册 + 路由 + 分发”的思路能否迁移到 Agent 的问题定位？把兜底换成 LLM 是否成立？
* **核心释义**：
  1. **概率标签（Probabilistic Label）**：由语义识别推断出的分类标签，附带置信度，可能未命中、可能多标签，与枚举式的“确定键”本质不同。
  2. **弃权通道（Abstention Channel）**：识别不出高置信标签时，不报错，而是显式路由到一个 `UNKNOWN` 处理器。
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
* **进阶技巧**：用注册表驱动约束解码。把注册表的 key 集合注入 LLM 输出 schema（如 `Literal[(*registry.keys(), "UNKNOWN")]`），使模型在结构层面不可能输出未注册标签，从源头消灭“路由键幻觉”，比“事后校验 + 重试”更可靠。
* **Agent 场景必须补的三道保险**：① 循环保护（`max_depth` / `visited` 集合，防止路径震荡）；② 成本分层（确定性热路径优先，记录 `fallback_rate` 作为“下一个该补哪个处理器”的数据依据）；③ 白名单即安全边界（定位动作常涉及查库 / 跑脚本 / 调接口，绝不允许 LLM 自行拼接命令）。
* **一句话总结**：`register` = 给「路由键」和「实现类」牵线的注册表；`_registry` = 导入期自动填充的登记簿；分发入口 = 拿数据里的键去查表。**有数据键则用注册表，无数据键则用模板方法 + 依赖注入，二者正交、不可互换。**

### Q8：如何判定新功能应该放入 `components/agents/`，还是新建独立 `components/<domain>/`？面对异构扩展如何避免 `bootstrap.py` 膨胀？
* **核心疑惑**：后续新增持久化、人工审核或新业务能力时，放在哪里？多租户或多后端异构时怎么装配？
* **核心答案**：
  1. **Worker vs Middleware 判别铁律**：
     * **放入 `components/agents/`**：由 `CatalogRouter` 根据意图**互斥挑选**、直接产出业务答案（`AgentResponse`）且可被 `PlanAndSolveAgent` 规划调用的业务执行单元。
     * **新建独立 `components/<domain>/`**：每次请求必经的**横切治理流水线**（如 `context_guard`、`approval_gate`、`memory_commit`、`recovery`），必须在 `protocols/` 建协议、在 `graphs/` 建独立节点，严禁混入 `agents/`。
  2. **异构系统组合根（`bootstrap.py`）三策**：
     * **按域拆分“子装配工厂（Sub-Factories）”**：各复杂子系统在内部提供 `factory.py`（如 `components/internal_knowledge/factory.py`），由配置文件的 `provider` 字段驱动多态实例化，`bootstrap.py` 仅做顶层总装。
     * **多图实例池解决拓扑异构**：面对不同租户或安全等级需要不同节点组合时，启动期调用同一个 `build_master_agent_graph(...)` 编译并缓存多张图实例，请求入口按上下文路由至对应图实例，不在主图内部写业务 `if/else`。


Q_9：配置驱动装配时，如何划分 .json 运维参数与 .py 架构拓扑的边界，避免装配容器膨胀？

• 归属档案：[[QA_02_Registry_And_Routing]]（中观粒度）
• 核心疑惑：当系统同时包含系统参数（超时、阈值）、业务目录（意图与正则规则）以及多插件责任链装配（异常映射规则、恢复插件执行顺序）时，应该全部塞进 JSON 配置文件，还是全部写在装配容器代码中？
• 核心答案：必须执行“动静分离与依赖单向化”：将运维数值/文案开关放入 config/*.json（由 AgentSystemConfig 校验）；将业务规则数据（如斜杠指令、正则、意图示例）拆分为独立的 config/intent_catalog.json；将与代码类强绑定、存在严格先后依赖的控制流拓扑（如 RECOVERY_PIPELINE_ORDER 责任链顺序和 ACTIVE_EXCEPTION_SPECS 异常类映射）放入应用装配层的纯 .py 声明文件中（/app/resilience_pipeline.py）。若把责任链顺序放进 JSON，运维误调顺序会导致兜底插件提前截断修复插件，且失去 IDE 类型检查；若全硬编码进 container.py，则每次增删插件都要改动核心装配代码。
• 真实正反例对比：
	• ❌ 反例（Anti-Pattern）：在 /app/container.py 中硬编码 CompositeRecoveryManager(handlers=[JsonHealRecoveryManager(...), ...]) 并手动传参，或者将 ["llm_json_repair", "model_degrade"] 的执行拓扑暴露到运维 agent_settings.json 中。死穴所在：前者导致 container.py 随插件增多不断膨胀；后者让纯字符串配置承载强逻辑顺序依赖，极易因配置误改引发责任链短路失效。
	• ✅ 正例（Best Practice）：在 config/agent_settings.json 中仅保留 max_error_length、fallback_intent 等运维参数；在 /app/resilience_pipeline.py 中用元组声明 RECOVERY_PIPELINE_ORDER；在 container.py 中调用 RecoveryPluginRegistry.build_handlers(enabled_names=RECOVERY_PIPELINE_ORDER, shared_deps=...) 利用 inspect.signature 自动匹配构造函数参数完成依赖注入。核心收益：config/ 保持零代码依赖，container.py 代码行数永久冻结，新增插件只需加装饰器并在 .py 清单中注册名称。


Q_10：在 LangGraph 状态机中，恢复节点（recovery_node）成功自愈后应如何设计出口路由与防死循环计数？

• 归属档案：[[QA_02_Registry_And_Routing]]（中观粒度）
• 核心疑惑：当 recovery_node 已经直接还原出当前阶段的合法业务对象（如 IntentResult）后，出口条件边如果统一重放原故障节点（如退回 intent_recognition），为什么会引发死循环与数据覆盖？
• 核心答案：必须区分“产物已直接还原（前向推进）”与“仅环境恢复（重放原阶段）”两条路由语义，并在编排层设置状态防火墙统一维护全局熔断计数。当 outcome.is_recovered == True 且 outcome.recovered_data is not None 时，说明目标产物已回填至状态机，_route_after_recovery 必须直接将流程推进到原故障节点的下一站（如 intent_recognition 直接推进至 routing）；同时由外层防火墙 _wrap_recovery_node 统一递增 _recovery_attempts 并记录 _last_failed_node（支持 agent_execution:* 等动态子阶段前缀归一化），各业务节点捕获异常时统一读取全局 _recovery_attempts 传入 FailureContext.retry_count。
• 真实正反例对比：
	• ❌ 反例（Anti-Pattern）：_route_after_recovery 只要看到 is_recovered=True 就无条件 return last_node（退回 INTENT_NODE），且各节点在 except 块中通过 prev_failure.retry_count 读取重试次数。死穴所在：退回原节点会用故障主模型重新执行并覆盖掉已自愈的 intent_result，同时自愈成功清空 failure_context 后会导致 prev_failure 为 None，使累计重试计数归零并触发无限死循环。
	• ✅ 正例（Best Practice）：recovery_node 查表将 outcome.recovered_data 写入 state["intent_result"] 并清空 failure_context；_route_after_recovery 检测到 recovered_data is not None 且 last_node == INTENT_NODE 时直接返回 ROUTING_NODE 前向推进；所有节点异常捕获时统一读取 state.get("_recovery_attempts", 0)。核心收益：自愈产物零覆盖、不走回头路，且跨阶段全局恢复次数受编排层防火墙严格熔断保护。       
