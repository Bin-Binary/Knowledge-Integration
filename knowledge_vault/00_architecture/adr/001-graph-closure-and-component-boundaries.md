---
title: ADR-001：主控状态图闭环防护与组件分层治理边界
tags: [adr, langgraph, architecture, dip, governance, persistence]
stage: gold
---

# ADR-001：主控状态图闭环防护与组件分层治理边界

* **状态**：已采纳（Accepted）
* **日期**：2026-11-23
* **关联总纲**：[[Internal_Knowledge_Architecture]] | [[QA_01_Architecture_And_DIP]]

## 1. 背景与问题（Context）
随着系统从单链路问答演进至包含异常自愈（`recovery_node`）、域内知识库（`knowledge`）、未来持久化（`context_guard` / `memory_commit`）与人工审批（`approval_gate`）的多节点状态机，架构上面临三个核心工程风险：
1. **状态机运行时死循环与脏写风险**：自愈节点若未彻底清理 `failure_context` 或重试次数失控，会导致 LangGraph 陷入无限回跳；异常提前终止若直接流向 `memory_commit`，会写入半成品脏记忆。
2. **异步节点适配冲突**：图节点工厂普遍为 `async def`，编排层包装器若使用同步调用会触发协程未等待异常。
3. **组件边界模糊**：随着后续新增持久化、人工审批及通用评估器，需明确哪些模块归属业务执行域（`components/agents/`），哪些应作为独立横切治理组件（`components/<domain>/`）或共享抽象基类（`components/_shared/`）。

## 2. 架构决策（Decision）

### 决策一：主图编排层状态防火墙（State Firewall）
在 `graphs/master_graph.py` 中对关键治理节点注入自适应同步/异步（`inspect.iscoroutinefunction`）包装器，保障任意可选扩展槽开关组合下的拓扑与运行时闭环：
1. **自愈防循环与断点续跑**：`_wrap_recovery_node` 在自愈成功（`is_recovered=True`）时强制擦除 `failure_context`，保留 `_last_failed_node` 快照并维护 `_recovery_attempts` 熔断计数器；`_route_after_recovery` 识别已还原的阶段产物（如 `intent_result`、`route_decision`），直接推进至下一业务阶段而非重复调用报错节点。
2. **记忆提交幂等门禁**：`_wrap_memory_commit_node` 在检测到未解决异常或无有效 `final_response` 的异常终止态时，自动跳过持久化落库。
3. **多轮会话入口归零**：`AgentApplication._build_initial_turn_state` 在每轮请求入口显式重置 `_recovery_attempts` 与 `_last_failed_node`，防止 `Checkpointer` 跨轮次累积计数。

### 决策二：三类组件物理分层红线
1. **业务执行域（`components/agents/`）**：仅存放由 `CatalogRouter` 互斥挑选、直接产出业务答案（`AgentResponse`）且可被 `PlanAndSolveAgent` 编排的 Worker（如 `GeneralChatAgent`）。**严禁将持久化、人工审核等横切机制写成 Agent**。
2. **横切治理与一级组件（`components/<domain>/`）**：持久化（`components/persistence/`）与人工审批（`components/governance/`）作为独立一级组件实现 `protocols/` 接口，以正交热插拔节点接入主图。
3. **极简共享基类池（`components/_shared/`）**：**仅收拢跨 2 个及以上一级业务域复用的抽象基类与无状态算子**（如 `BaseQualityEvaluator` 同时服务于知识库切片过滤与长期记忆价值评估）；域内私有基类（如 `BaseRecoveryManager`）保留在各自领域目录内以维持高内聚。

### 决策三：异构扩展遵循“子工厂 + 多图实例池”
* `graphs/` 与 `api/` 严禁直接导入 `components/` 具体实现（公共映射器下沉至 `infra/`，注册表抽象为 `AgentRegistryProtocol`）。
* 未来面对多租户拓扑异构或异构存储/审批渠道时，由各域 `factory.py` 根据配置路由多态实现，`bootstrap.py` 作为唯一组合根（Composition Root）编译并缓存多形态图实例。

## 3. 架构后果（Consequences）
* **正面收益**：主控状态图实现全路径物理与状态双闭环；`graphs/` 与 `components/` 保持 100% 依赖倒置；新增持久化与人工审核组件时主图拓扑零修改。
* **约束代价**：新增全局状态追踪字段（如 `_recovery_attempts`）时，必须同步在 `MasterAgentState` TypedDict 中声明，否则会被 LangGraph 状态合并器静默过滤。
