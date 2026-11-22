---
title: 域内知识库（Internal Knowledge & LLM-WIKI）架构设计文档
tags: [architecture, dip, blackboard-pattern, llm-wiki, blueprint]
stage: gold
---

# 域内知识库（Internal Knowledge & LLM-WIKI）架构设计文档

## 1. 全局架构拓扑

```text
[用户请求 POST /v1/agent/chat]
   │  (FastAPI 网关绑定 trace_id，零感知内部实现)
   ▼
[AgentApplication.ainvoke_turn] (单例容器，隔离历史快照与内网代理)
   │
   ▼
[LangGraph 主控图 MasterAgentGraph]
   ├── 1. intent_recognition (意图识别) ──(若异常)──▶ recovery_node (自愈闭环)
   │
   ▼ (携带改写后的标准 query)
   └── 2. knowledge_retrieval (防腐层 Adapter 节点：创建局部 PipelineEnvelope)
           │
           ▼
      [InternalKnowledgeEngine] (纯领域闭环引擎，脱离 LangGraph 亦可独立运行)
           ├── ① Storage.retrieve    : 按 gold > release > debug 权重召回知识 ID
           ├── ② Application.resolve : 调用 Storage.load_contents 读取卡片全文并推理
           │       ├── (若已解决 SUCCESS) ──▶ 退出循环，通过 Adapter 写回 state["rag_context"]
           │       └── (若存在缺口 gap)   ──▶ 触发增量自学习回路：
           │               ├── ③ Acquisition.acquire   : 缺口路由 -> 切片并生成确定性 info_id
           │               ├── ④ Organization.organize : 评估过滤 -> 抽标签 -> 建边 -> 并查集聚本体
           │               └── ⑤ Storage.save          : 渲染 YAML+Markdown 隔离写入 debug/ 区
           └── 轮次交接 (advance_to_next_iteration): 清空暂存缓冲区，iteration + 1，重返 ①
```

本系统采用 **依赖倒置原则（DIP）** 与 **黑板模式（Blackboard Pattern）** 设计，确保核心知识引擎与外部编排框架（如 LangGraph）、大模型供应商及底层物理存储完全解耦。

* **依赖方向单向无环**：`外部框架 (graphs/)` ➔ `接口契约 (protocols/)` + `数据契约 (schemas/)` 🡐 `具体算子 (components/)`。
* **核心零侵入**：领域核心层（`schemas/` 与 `components/`）仅依赖 Python 标准库与 Pydantic，绝对不引入 LangChain/LangGraph 等外部框架类型（详见 [[QA_01_Architecture_And_DIP]]）。

---

## 2. 四层代码分层与职责边界

| 架构层级 | 代码目录 | 核心职责 | 设计约束 |
| :--- | :--- | :--- | :--- |
| **数据契约层** | `schemas/internal_knowledge/` | 定义全链路流转的数据结构、枚举与结构不变式校验。 | **严格贫血 + 不可变（`frozen=True`）**。仅包含字段定义、`@model_validator` 自校验及无副作用渲染（`to_markdown()`），严禁包含 I/O 或推理逻辑（详见 [[QA_03_Patterns_And_Contracts]]）。 |
| **接口协议层** | `protocols/internal_knowledge.py` | 定义四大环节及路由器的抽象行为契约（`Protocol`）。 | **高度泛化**。所有核心环节统一以 `PipelineEnvelope` 作为唯一输入与输出载体。 |
| **算子实现层** | `components/internal_knowledge/` | 提供模板方法基类（`Base*`）及具体适配器（LLM 推理、AST 切片、Markdown 落盘）。 | **向内实现协议，向外对接工具**。通过不可变副本（`model_copy`）推进黑板状态（详见 [[QA_02_Registry_And_Routing]]）。 |
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
* `<vault_root>`：知识图谱根目录（对应 `20_wiki/`）；
* `<stage>`：三层归档路径，对应成熟度生命周期；
* `<layer>`：四层知识形态抽象；
* `<artifact_id>.md`：全局唯一逻辑 ID 命名的知识卡片文件（详见 [[QA_04_Micro_Tricks_And_Storage]]）。

* **三层生命周期（成熟度治理）**：
  * `debug/`：AI 自动生成的未审核知识缓冲区（写入隔离，自动化流水线**仅允许写入此区**）。
  * `release/`：人工审核通过的 AI 产物，或人工直接编写的准生产知识。
  * `gold/`：经过真实业务闭环验证有效（`outcome == SUCCESS`）的黄金标准知识。
* **四层抽象粒度（信息密度由低到高）**：
  * `information/` ➔ `labeling/` ➔ `relating/` ➔ `ontology/`。
* **跨层防断链机制**：所有跨文件引用严格使用全局唯一逻辑 ID（如 `[[lbl_101]]`），文件在 `debug -> release -> gold` 间迁移时零断链。

---

## 5. 架构专题问答索引（Design Rationale & QA）

系统各层级的详细设计权衡已按架构粒度拆分为以下长效专题档案：
* **粗粒度（架构哲学与边界）**：[[QA_01_Architecture_And_DIP]]（六边形架构、ACL 防腐层、信息隐藏与生命周期治理）
* **中观粒度（插件注册与路由分发）**：[[QA_02_Registry_And_Routing]]（注册表模式 vs 模板方法、落地约束与 Agent 泛化）
* **细粒度（标准抽象与设计模式）**：[[QA_03_Patterns_And_Contracts]]（不可变贫血模型、微算子组合、冲突仲裁与契约水合）
* **精细粒度（微观代码与落盘技巧）**：[[QA_04_Micro_Tricks_And_Storage]]（局部结构指纹、幂等 Upsert、Pydantic 重校验、并查集与双链落盘）

---

## 6. 全链路核心架构亮点 QA 总结

### [全链路-Q1]：请求从 FastAPI 网关进入，经过 LangGraph 再到知识库引擎，各层是如何实现“职责隔离与零耦合”的？
* **核心答案**：通过 **四层同心圆隔离（六边形架构）** 确保每一层只认识自己相邻的抽象契约：
  1. **网关层（FastAPI）**：只负责 HTTP 协议解析、超时熔断与 `trace_id` 注入，只认识 `AgentApplication`。
  2. **容器装配层（`bootstrap.py`）**：作为全系统唯一的“组装厂”，负责实例化具体的大模型客户端和存储后端，并把它们塞进抽象协议中。
  3. **编排层（`graphs/`）**：LangGraph 主图只负责节点拓扑流转与异常分支跳转；`knowledge_graph.py` 充当防腐层（ACL），将外部 `MasterAgentState` 翻译为内部 `PipelineEnvelope` 局部变量，外部状态机零污染。
  4. **核心领域层（`InternalKnowledgeEngine`）**：只依赖 `protocols/` 和 `schemas/`，彻底不知道外面有 FastAPI 或 LangGraph，随时可拆出独立运行或暴露为 MCP Server。

### [全链路-Q2]：当知识库遇到“未知问题（冷启动）”时，全链路是如何自动完成“现学现卖 + 自我验证”闭环的？
* **核心答案**：依赖 **黑板模式（`PipelineEnvelope`） + 确定性状态机闭环**：
  1. **缺口驱动（Gap-Driven）**：第 0 轮检索为空时，`LLMKnowledgeApplicator` 不会瞎编，而是输出 `outcome=FAILURE` 并生成具体的 `remaining_gap` 写入黑板信封。
  2. **四阶信息提纯与隔离落盘**：引擎检测到未解决且未超最大轮次（`can_continue_loop`），自动驱动【采集（按协议切片生成确定性 `info_id`） ➔ 组织（两级质量过滤 + LLM 抽点建边 + 并查集图聚类生成 `Ontology`） ➔ 存储（渲染为带 Obsidian 双链的 Markdown 写入 `debug/` 隔离区）】。
  3. **工作区清零与二次召回验证**：落盘后调用 `advance_to_next_iteration()` 清空本轮暂存列表防止重复入库，随后 `iteration + 1` 重新回到【检索 ➔ 运用】验证新沉淀的知识是否足以回答原问题，直至收敛输出 `rag_context`。

### [全链路-Q3]：在这套全链路设计中，如何兼顾“生产环境高安全性（防异常崩溃、防脏数据）”与“未来高扩展性”？
* **核心答案**：依靠三大工程级防御与扩展机制：
  1. **全链路异常自愈网**：无论是上游意图识别出错，还是知识库内部大模型超时/解析失败，均由 `ExceptionMapper` 标准化为 `FailureContext`，无缝路由至主图的 `recovery_node` 执行修复或安全降级兜底，绝不直接向用户抛出 500 堆栈。
  2. **知识成熟度治理（`debug -> release -> gold`）**：AI 自动生成的知识严格隔离在 `debug/` 目录；检索时按 `gold (1.0) > release (0.8) > debug (0.4)` 权重遮蔽低层级副本；跨文件引用全采用全局唯一逻辑 ID（`[[lbl_xxx]]`），文件跨目录晋升零断链。
  3. **插件化自动发现（OCP）**：采集协议（`@BaseKnowledgeAcquirer.register`）与组织微算子（`@OrganizationPluginRegistry.register` + `pkgutil` 动态扫描）均支持装饰器自动注册，未来新增数据源或建边算法只需新增文件，主干代码零修改。
