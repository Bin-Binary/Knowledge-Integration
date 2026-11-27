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


### Q_9：配置驱动装配时，如何划分 `.json` 运维参数与 `.py` 架构拓扑的边界，避免装配容器膨胀？

* **归属档案**：[[QA_02_Registry_And_Routing]]（中观粒度）
* **核心疑惑**：当系统同时包含系统参数（超时、阈值）、业务目录（意图与正则规则）以及多插件责任链装配（异常映射规则、恢复插件执行顺序）时，应该全部塞进 JSON 配置文件，还是全部写在装配容器代码中？
* **核心答案**：必须执行**“动静分离与依赖单向化”**：将运维数值/文案开关放入 `config/*.json`（由 `AgentSystemConfig` 校验）；将业务规则数据（如斜杠指令、正则、意图示例）拆分为独立的 `config/intent_catalog.json`；将与代码类强绑定、存在严格先后依赖的控制流拓扑（如 `RECOVERY_PIPELINE_ORDER` 责任链顺序和 `ACTIVE_EXCEPTION_SPECS` 异常类映射）放入应用装配层的纯 `.py` 声明文件中（`/app/resilience_pipeline.py`）。若把责任链顺序放进 JSON，运维误调顺序会导致兜底插件提前截断修复插件，且失去 IDE 类型检查；若全硬编码进 `container.py`，则每次增删插件都要改动核心装配代码。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：在 `/app/container.py` 中硬编码 `CompositeRecoveryManager(handlers=[JsonHealRecoveryManager(...), ...])` 并手动传参，或者将 `["llm_json_repair", "model_degrade"]` 的执行拓扑暴露到运维 `agent_settings.json` 中。**死穴所在**：前者导致 `container.py` 随插件增多不断膨胀；后者让纯字符串配置承载强逻辑顺序依赖，极易因配置误改引发责任链短路失效。
  * ✅ **正例（Best Practice）**：在 `config/agent_settings.json` 中仅保留 `max_error_length`、`fallback_intent` 等运维参数；在 `/app/resilience_pipeline.py` 中用元组声明 `RECOVERY_PIPELINE_ORDER`；在 `container.py` 中调用 `RecoveryPluginRegistry.build_handlers(enabled_names=RECOVERY_PIPELINE_ORDER, shared_deps=...)` 利用 `inspect.signature` 自动匹配构造函数参数完成依赖注入。**核心收益**：`config/` 保持零代码依赖，`container.py` 代码行数永久冻结，新增插件只需加装饰器并在 `.py` 清单中注册名称。


### Q_10：在 LangGraph 状态机中，恢复节点（`recovery_node`）成功自愈后应如何设计出口路由与防死循环计数？

* **归属档案**：[[QA_02_Registry_And_Routing]]（中观粒度）
* **核心疑惑**：当 `recovery_node` 已经直接还原出当前阶段的合法业务对象（如 `IntentResult`）后，出口条件边如果统一重放原故障节点（如退回 `intent_recognition`），为什么会引发死循环与数据覆盖？
* **核心答案**：必须区分**“产物已直接还原（前向推进）”**与**“仅环境恢复（重放原阶段）”**两条路由语义，并在编排层设置状态防火墙统一维护全局熔断计数。当 `outcome.is_recovered == True` 且 `outcome.recovered_data is not None` 时，说明目标产物已回填至状态机，`_route_after_recovery` 必须直接将流程推进到原故障节点的**下一站**（如 `intent_recognition` 直接推进至 `routing`）；同时由外层防火墙 `_wrap_recovery_node` 统一递增 `_recovery_attempts` 并记录 `_last_failed_node`（支持 `agent_execution:*` 等动态子阶段前缀归一化），各业务节点捕获异常时统一读取全局 `_recovery_attempts` 传入 `FailureContext.retry_count`。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：`_route_after_recovery` 只要看到 `is_recovered=True` 就无条件 `return last_node`（退回 `INTENT_NODE`），且各节点在 `except` 块中通过 `prev_failure.retry_count` 读取重试次数。**死穴所在**：退回原节点会用故障主模型重新执行并覆盖掉已自愈的 `intent_result`，同时自愈成功清空 `failure_context` 后会导致 `prev_failure` 为 `None`，使累计重试计数归零并触发无限死循环。
  * ✅ **正例（Best Practice）**：`recovery_node` 查表将 `outcome.recovered_data` 写入 `state["intent_result"]` 并清空 `failure_context`；`_route_after_recovery` 检测到 `recovered_data is not None` 且 `last_node == INTENT_NODE` 时直接返回 `ROUTING_NODE` 前向推进；所有节点异常捕获时统一读取 `state.get("_recovery_attempts", 0)`。**核心收益**：自愈产物零覆盖、不走回头路，且跨阶段全局恢复次数受编排层防火墙严格熔断保护。


### Q_11：为什么传统静态工厂函数在参数或插件扩展时会导致“散弹式修改”，如何通过“装饰器自发现 + 自动签名依赖注入”彻底冻结工厂代码？

* **归属档案**：[[QA_02_Registry_And_Routing]]（中观粒度）
* **核心疑惑**：在使用传统工厂模式（如 `create_default_knowledge_engine`、`assemble_master_graph`）装配多插件系统时，为什么每次新增一个组件或调整某个子插件的构造函数参数，都要被迫在工厂文件、调用链和配置层之间来回修改，极其痛苦？
* **核心释义**：**自发现注册表 + 签名自动依赖注入（Auto-DI via Signature Introspection）**，是指通过装饰器在类定义处声明元信息，启动期自动扫描包路径完成注册，并利用 `inspect.signature` 反射读取目标类的 `__init__` 形参名，从共享依赖池（`shared_deps`）中按需自动匹配喂参，彻底消除工厂里的显式实例化与参数分发字典。
* **核心答案**：传统工厂模式把**“组件发现”、“参数透传”**与**“业务组装”**混在了一起，导致工厂成了所有子组件构造函数的参数中转站（Parameter Trampoline）——底层插件加一个 `workspace_root` 参数，外层三层工厂就得跟着改三遍签名与字典映射。正确的演进路径是**“保留极薄的外观工厂门面（Facade Factory） + 内部全权委托注册表 Auto-DI”**：工厂只负责构建基础共享依赖池（`shared_deps = {"llm_client": ..., "storage": ..., "workspace_root": ...}`），随后调用 `Registry.build_handlers(shared_deps=shared_deps)` 自动扫描并实例化所有注册插件。若不这样改造，工厂文件将随系统演进无限膨胀，且每次参数变动都会引发跨文件联动报错。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：在 `/components/internal_knowledge/factory.py` 中手动 `from ... import ShellRepoAcquirer` 触发装饰器注册，并在 `build_knowledge_organizer` 中硬编码字典分发参数：
    ```python
    organizer = build_knowledge_organizer(
        plugin_kwargs={
            "llm_hybrid": {"llm_client": llm_client},
            "llm_label": {"llm_client": llm_client},
            "llm_relation": {"llm_client": llm_client},
        }
    )
    ```
    **死穴所在**：每新增一个插件或给某个插件多传一个 `storage` 参数，就必须回头修改工厂代码与 `plugin_kwargs` 硬编码映射，严重违反开闭原则（OCP）。
  * ✅ **正例（Best Practice）**：使用 `@AcquisitionPluginRegistry.register(...)` 与 `@RecoveryPluginRegistry.register(...)` 声明插件；工厂层仅组装无状态的共享依赖池 `shared_deps`，由注册表内部反射参数签名自动注入：
    ```python
    sig = inspect.signature(target_cls.__init__)
    init_kwargs = {
        param: shared_deps[param]
        for param in sig.parameters
        if param != "self" and param in shared_deps
    }
    instance = target_cls(**init_kwargs)
    ```

### Q_12：当数据路由同时依赖“协议类型”与“资源细粒度特征”时，如何避免单一路由键导致的分发错乱？

* **归属档案**：[[QA_02_Registry_And_Routing]]（中观粒度）
* **核心疑惑**：在知识采集分发场景中，为什么仅按采集协议（`SourceScheme.FILE`）作为路由键注册采集器，会导致 `.md`、`.py` 等普通文件被错误分发给专门解析 `.sh` 脚本的 `ShellRepoAcquirer`？
* **核心释义**：**复合路由键（Composite Routing Key）与通配符降级（Wildcard Fallback）**，是指使用多维元组（如 `(scheme, suffix)`）精确标识路由匹配条件，并在查表时执行“精确键 `(scheme, suffix)` 优先 -> 协议通配符 `(scheme, "*")` 兜底”的两级匹配策略。
* **核心答案**：当业务分发逻辑存在正交的多维特征（例如外层是传输/存储协议 `SourceScheme`，内层是文件扩展名 `.sh`/`.py`/`.md`）时，强行压扁为单维枚举键必然引发路由冲突。调度器（`CompositeKnowledgeAcquirer`）必须支持以 `(SourceScheme, str)` 元组作为注册键，同时在调度查找时自动按 `(uri.scheme, ext) -> (uri.scheme, "*")` 顺序回退，并将通用切片工具（如 `generate_info_id`、`apply_window_bounds`）抽离为无状态工具函数供各处理器复用。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：在 `ShellRepoAcquirer` 上标注 `@BaseKnowledgeAcquirer.register(SourceScheme.FILE)`，独占整个本地文件协议，同时在类里定义未生效的 `supported_extensions = {".sh"}` 属性。**死穴所在**：`WorkspaceFileGapRouter` 扫出的所有本地 `.md`/`.py` 文件均带有 `SourceScheme.FILE`，全被误路由进 Shell 语法解析器导致切片错乱或丢失。
  * ✅ **正例（Best Practice）**：在 `CompositeKnowledgeAcquirer` 中按复合键注册：`register(SourceScheme.FILE, ".sh", ShellScriptHandler())` 与 `register(SourceScheme.FILE, "*", GenericTextFileHandler())`，查表时优先精确匹配后缀、未命中时自动降级到 `"*"` 通用处理器。**核心收益**：实现协议与文件类型的正交精准路由，新增专有解析器（如 `.py` AST 解析器）只需注册 `(SourceScheme.FILE, ".py")` 即可平滑接管，绝不影响其他文件类型。

### Q_13：为什么基于 `@Registry.register` 装饰器的插件体系必须配套 `__init__.py` 自动扫描，否则会导致静默路由丢失？
* **归属档案**：[[QA_02_Registry_And_Routing]]（中观粒度）
* **核心疑惑**：已经在 `ShellScriptHandler`、`GenericTextFileHandler` 和各组织插件类上添加了 `@register` 装饰器，为什么工厂装配时注册中心里的路由表依然是空的？
* **核心释义**：**导入期副作用注册（Import-Time Decorator Registration）**是指装饰器代码仅在 Python 解释器实际执行 `import` 该模块文件时才运行，未导入的 `.py` 文件对解释器而言形同虚设。
* **核心答案**：Python 不会因为 `import pkg` 就自动加载包目录内的子模块。如果 `acquisition/handlers/__init__.py` 和 `organization/plugins/__init__.py` 缺失或留空，运行时 `AcquisitionPluginRegistry.build_route_table()` 拿到的就是空字典，导致所有数据源因找不到处理器而失败。必须在插件包目录的 `__init__.py` 中使用 `pkgutil.iter_modules` + `importlib.import_module` 实现动态自动扫描，并在工厂入口处显式导入该包，才能实现“新增插件文件即自动注册、零手动配置”的真正开闭原则（OCP）。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：
    ```python
    # handlers/ 目录下没有 __init__.py，工厂里只导入了注册中心本身
    from components.internal_knowledge.acquisition.registry import AcquisitionPluginRegistry
    route_table = AcquisitionPluginRegistry.build_route_table(shared_deps=shared_deps)
    ```
    *死穴所在*：`shell_script_handler.py` 从未被导入，装饰器从未执行，`route_table` 为 `{}`，运行时全量报错“暂不支持 'file' 协议的数据源”。
  * ✅ **正例（Best Practice）**：
    ```python
    # components/internal_knowledge/acquisition/handlers/__init__.py
    import importlib, pkgutil
    from pathlib import Path

    for _mod in pkgutil.iter_modules([str(Path(__file__).resolve().parent)]):
        if not _mod.name.startswith("_"):
            importlib.import_module(f"{__name__}.{_mod.name}")
    ```
    *核心收益*：工厂只需 `import components.internal_knowledge.acquisition.handlers` 即可自动激活目录下全部处理器；未来新增 `python_ast_handler.py` 无需修改任何注册表或初始化文件。

### Q_14：在 `KnowledgeOrganizer` 进行背压规模采样与 `LLMRelationBuilder` 关系推理之间，如何避免跨文档上下文丢失？
* **归属档案**：[[QA_02_Registry_And_Routing]]（中观粒度）
* **核心疑惑**：在 `KnowledgeOrganizer` 中对去重后的 `unique_labels` 按频次采样 Top-K 传给 `relation_builder.build()`，为什么会导致 `LLMRelationBuilder` 的跨文档高频节点补全（Hub Window）和上下文聚合全部失效？
* **核心释义**：**引用降维丢失**是指多对一去重（`setdefault(lbl.label_id, lbl)`）时只保留了实体首次出现的单条外键（`info_id`），丢弃了该实体在其余文档切片中的共现引用关系。
* **核心答案**：一个高频核心概念往往跨越多个文档切片（`Information`）出现，这是推导出跨章节语义关系的关键桥梁。如果 `KnowledgeOrganizer` 直接把去重后的 `sampled_labels`（每个 `Labeling` 仅携带首个 `info_id`）传给 `LLMRelationBuilder`，下游就无法知道该概念还在哪些片段中出现，导致每个概念的文档频次永远退化为 1。正确的做法是：**用去重后的 `unique_labels` 统计跨切片频次选出 Top-K `label_id` 集合，然后从全量未去重的 `all_extracted_labels` 中筛选出命中这些 ID 的全部 `Labeling` 记录传给 `relation_builder.build()`**。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：
    ```python
    # KnowledgeOrganizer.organize() 直接传去重后的子集
    sampled_labels = sorted(unique_labels, key=lambda x: freq_counter[x.label_id], reverse=True)[:50]
    raw_relations = await self.relation_builder.build(sampled_labels, valid_infos)
    ```
    *死穴所在*：`sampled_labels` 中每个 `label_id` 只有 1 条记录，`LLMRelationBuilder` 统计的 `label_to_info_ids` 长度全为 1，Hub Window 永远不会触发，跨文件证据也被截断。
  * ✅ **正例（Best Practice）**：
    ```python
    # 采样确定 ID 集合后，回溯全量标注保留所有切片归属记录
    sampled_id_set: Set[str] = {lbl.label_id for lbl in sampled_labels}
    candidate_labels_with_all_refs: List[Labeling] = [
        lbl for lbl in all_extracted_labels if lbl.label_id in sampled_id_set
    ]
    raw_relations = await self.relation_builder.build(candidate_labels_with_all_refs, valid_infos)
    ```
    *核心收益*：`LLMRelationBuilder` 得以聚合同一概念在所有关联文档中的上下文，围绕概念词居中截取证据，并准确识别跨章节 Hub 核心节点建立全局语义边。

### Q_15：为什么领域快筛规则（如代码/对话/网页正则）不能直接写在评估器插件类里，而必须拆分为独立的 `heuristics/` 规则包？
* **归属档案**：[[QA_02_Registry_And_Routing]]（中观粒度）
* **核心疑惑**：在为 `InformationQualityEvaluator` 增加代码正向快筛规则时，如果直接把正则和判断函数写在 `plugins/info_evaluator.py` 里，会有什么隐患？
* **核心释义**：**策略外置与装配注入（Externalized Strategy Injection）**是指将“调度执行骨架（插件主类）”与“领域规则集合（纯函数字典）”物理分离，插件只负责执行调度，规则包随业务领域横向增删。
* **核心答案**：评估器插件（`InformationQualityEvaluator`）的职责是**连接通用两级评估引擎（`TwoStageQualityEvaluator`）与大模型语义打分（`_semantic_score`）**。如果把代码、Chat、Web 甚至未来图像作画的启发式规则全塞进同一个插件文件里，插件就会沦为不断膨胀的“上帝文件”，违反单一职责（SRP）与开闭原则（OCP）。正确的做法是将纯无状态规则按领域外置到独立的 `heuristics/` 目录（如 `code_rules.py`、`general_rules.py`），通过字典路由表导入注入插件，实现**新增领域规则零修改插件源码**。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：
    ```python
    # components/internal_knowledge/organization/plugins/info_evaluator.py
    def _heuristic_code_and_file(info: Information) -> Optional[float]: ...
    def _heuristic_chat(info: Information) -> Optional[float]: ...
    def _heuristic_web(info: Information) -> Optional[float]: ...
    # 以后每加一种新领域（如 Markdown、图像作画），都要打开修改 info_evaluator.py！
    ```
    *死穴所在*：插件主类随业务领域横向扩展而持续膨胀，规则与 LLM 调用逻辑混杂，单测和复用成本急剧上升。
  * ✅ **正例（Best Practice）**：
    ```python
    # 1. 领域规则独立归档：organization/heuristics/code_rules.py & general_rules.py
    # 2. 插件主类仅组合导入规则路由表，保持极简纯净：
    from components.internal_knowledge.organization.heuristics import DEFAULT_INFO_HEURISTIC_RULES

    class InformationQualityEvaluator(QualityEvaluatorProtocol[Information]):
        def __init__(self, llm_client: StructuredLLMProtocol, extra_rules: Optional[Dict[Hashable, HeuristicRuleFn[Information]]] = None) -> None:
            merged_rules = {**DEFAULT_INFO_HEURISTIC_RULES, **(extra_rules or {})}
            self._engine = TwoStageQualityEvaluator[Information](..., heuristic_rules=merged_rules)
    ```
    *核心收益*：插件主类永远冻结在极简状态，新增任何领域的快筛规则只需在 `heuristics/` 下新增纯函数模块并注册进默认字典即可，彻底杜绝类膨胀。

### Q_16：为什么内网慢推理模型下运行多切片知识组织时，经常只落盘了 L1（`information`）却丢失了 L2/L3/L4，且如何用双向快筛避免无谓超时？
* **归属档案**：[[QA_02_Registry_And_Routing]]（中观粒度）
* **核心疑惑**：10 条代码切片进入 `KnowledgeOrganizer` 后，所有请求都返回了 `200 OK`，但最终存储目录里只有 `debug/information/` 有文件，而 `labeling`、`relating`、`ontology` 全为空。
* **核心释义**：
  * **双向启发式快筛（Two-Way Heuristic Fast-Path）**：第一级规则引擎不仅要做“负向拦截噪声（0.0~0.1）”，还必须对结构化切片器产出的高确定性实体做“正向直通高分（0.85）”，跳过昂贵的第二级 LLM 语义打分。
  * **`P1-2` 阶段超时部分持久化**：当总组织超时（`asyncio.TimeoutError`）触发时，外层引擎捕获异常并保底将已采集的 `raw_infos` 落盘，避免前置采集白费（注意 `str(TimeoutError)` 为空，日志需打印 `type(exc).__name__`）。
* **核心答案**：内网部署的思考/大模型单次结构化输出常需 15~50 秒。当 3.1 评估阶段只有负向拦截规则时，10 条代码切片会全部排队调用 LLM 打分（耗尽 60+ 秒），导致后续 3.2 概念抽取跑到一半就触碰 `organize_timeout_seconds` 被整体取消，从而触发 `P1-2` 降级仅落盘 L1 切片。必须同时做两项治理：① 在 `heuristics/code_rules.py` 中增加正向结构化代码直通规则（把 3.1 评估耗时从 60 秒降至 0.001 秒）；② 在 `config/agent_settings.json` 中显式配置 `organize_timeout_seconds`（如 `480.0`）匹配慢模型吞吐窗口。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：
    ```python
    # _heuristic_code_and_file 仅做负向拦截，正常代码全部返回 None 走 LLM 打分
    if len(meaningful_tokens) < 4:
        return 0.1
    return None  # 10 条函数切片全部排长队调 LLM，耗尽阶段超时预算！
    ```
    *死穴所在*：已经被 `ShellScriptHandler` 精确切出的函数体还要花 60 秒让 LLM 评估“是否有价值”，挤占了后面概念抽取与建边的存活时间。
  * ✅ **正例（Best Practice）**：
    ```python
    # 规则外置至 organization/heuristics/code_rules.py，实现双向快筛（负向拦截 + 正向直通）
    has_code_logic = bool(_CODE_STRUCTURE_RE.search(joined))
    if (has_code_logic and len(meaningful_tokens) >= 12) or has_rich_docs:
        return 0.85  # 确定性高分直通，0 LLM 调用
    ```
    *核心收益*：3.1 评估阶段秒级完成且不膨胀插件主类，把 100% 的大模型算力预算留给高价值的 3.2 概念抽取与 3.3 关系建边。

### Q_17：当用户问题中已经包含明确本地文件路径，或单文件切片数超过 `top_k` 时，如何防止缺口路由器全盘扫描和引擎反复重采死循环？
* **归属档案**：[[QA_02_Registry_And_Routing]]（中观粒度）
* **核心疑惑**：用户输入 `"学习 D:/code-repo/ds-build/llm-wiki/cmc.sh"` 时，系统依然扫描了工作区 120 个文件并调用 LLM 路由（耗时 13 秒）；且当文件被切为 10 条而检索 `top_k=8` 时，第二轮迭代又会重复采集一模一样的 10 条切片。
* **核心答案**：
  1. **缺口路由显式路径快筛**：在 `WorkspaceFileGapRouter.route` 调用 `_infer_target_uris`（LLM 推理）前，先用正则提取文本中已存在的本地文件路径直接构造 `SourceURI`，0.001 秒直通（跳过全盘扫描与 LLM 路由）；同时 `workspace_root` 必须配置为目标知识仓库而非后端服务运行目录 `"."`。
  2. **引擎防空转短路（`seen_info_ids`）**：在 `InternalKnowledgeEngine.execute` 循环中记录已处理的 `info_id` 集合；若新一轮 `acquisition.acquire` 产出的切片无任何新增 `info_id`（`not fresh_ids`），说明数据源已穷尽，立即跳出组织与落盘进入 `_semantic_fallback` 收敛。
* **真实正反例对比**：
  * ❌ **反例（Anti-Pattern）**：
    ```python
    # 1. route() 每次无脑全盘 rglob("*") 扫描 120 个文件再发给 LLM 猜路径
    # 2. Engine.execute() 不检查新增切片差集，因为 top_k=8 漏掉 2 条而反复重采同一个文件
    current_env = await self.acquisition.acquire(current_env)
    current_env = await self.organization.organize(current_env)
    ```
    *死穴所在*：白白浪费 10+ 秒扫描无关代码库；遇到长文件（切片数 > `top_k`）时陷入“召回 8 条 ➔ 判定缺 2 条 ➔ 全量重采 10 条”的无限空转。
  * ✅ **正例（Best Practice）**：
    ```python
    # 1. WorkspaceFileGapRouter.route() 前置正则快筛真实存在的文件路径
    raw_uris = self._extract_explicit_local_uris(f"{clean_gap}\n{clean_context}")
    if not raw_uris:
        raw_uris = await self._infer_target_uris(gap_description=clean_gap, problem_context=clean_context)

    # 2. InternalKnowledgeEngine.execute() 检测无新增切片直接语义汇总收敛
    fresh_ids = {info.info_id for info in current_env.raw_infos} - seen_info_ids
    if not fresh_ids:
        return await self._semantic_fallback(current_env, reason="数据源已全量采集，无新增切片")
    ```
    *核心收益*：显式路径学习跳过全盘扫描直接秒级采集，多轮探索遇到已穷尽数据源时立即优雅收敛。

