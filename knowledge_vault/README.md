# Internal Knowledge & 20-wiki 知识库仓库

本仓库采用**双轨隔离架构**，将人类编写的权威架构文档与 AI 知识引擎的自动化图谱演进安全融合在同一个 Obsidian Vault 中。

## 1. 目录结构与读写权限

| 目录路径 | 定位说明 | 人类权限 | 引擎权限 |
| :--- | :--- | :--- | :--- |
| `00_architecture/` | 系统架构总纲、专题 QA 档案库与架构决策记录（ADR） | 读写 | 仅只读（`gold` 种子） |
| `10_inbox/` | 待吸收的会议纪要、需求文档、外部技术资料缓冲区 | 读写 | 只读扫描切片 |
| `20_wiki/debug/` | AI 自动生成的未审核知识图谱缓冲区 | 审核后移出 | **唯一可写落盘区** |
| `20_wiki/release/` | 人工审核通过的准生产知识（支持人工直接编写） | 读写 | 只读检索 |
| `20_wiki/gold/` | 经过真实业务闭环验证有效的黄金标准知识 | 读写 | 只读检索 |

### 1.1 20-wiki 物理目录矩阵（3层生命周期 × 4层抽象粒度）

引擎落盘严格遵循 `<vault_root>/<stage>/<layer>/<artifact_id>.md` 规范：

* **三层生命周期 (`WikiMaturityStage`)**：
  1. `debug/`：AI 自动生成的未审核知识缓冲区（高风险，允许试错）。
  2. `release/`：经人工审核通过的 AI 产物，或人工直接编写的准生产知识。
  3. `gold/`：经真实生产问题求解闭环验证有效（`outcome=SUCCESS`）的黄金标准知识。
* **四层知识形态 (`WikiArtifactLayer`，信息密度由低到高)**：
  1. `information/`：L1 原始符号切片（采集即生成）。
  2. `labeling/`：L2 概念节点（采集后生成 $N \ge 0$ 条）。
  3. `relating/`：L3 有向语义边（`labeling >= 2` 且存在明确关联时生成）。
  4. `ontology/`：L4 知识闭环体（多轮积累后低频聚拢生成）。

### 1.2 20-wiki 引用规则

为了让图谱呈现出清晰的“信息提纯金字塔”流向，双链引用必须严格遵守“下层指向上层、上游指向下游”

各层级引用权限矩阵（杜绝双向互相 [[...]]）

| 知识层级 | 物理目录 | 允许写入正文的 `[[...]]` 双链（箭头射出方向） | 禁止写入正文的 `[[...]]`（仅保留在 YAML ID 中） |
| :--- | :--- | :--- | :--- |
| **L1 原始切片** | `information/` | • 指向衍生出的 L2 概念 (`[[lbl_...]]`)<br>• 指向顶层总纲 (`[[..._Architecture]]`) | 禁止直接指向 `[[ont_...]]` 或同级 `[[info_...]]`（防止底层噪音污染高层灯塔） |
| **L2 概念节点** | `labeling/` | • 指向它是起点的 L3 关系边 (`[[rel_...]]`)<br>• 指向归属的 L4 闭环体 (`[[ont_...]]`) | 禁止反向指向 `[[info_...]]`（L1 已经指向它了，反指会变双向箭头） |
| **L3 有向语义边** | `relating/` | • 仅指向终点 L2 概念 (`[[lbl_target]]`)<br>• 指向归属的 L4 闭环体 (`[[ont_...]]`) | 禁止反向指向起点 `[[lbl_source]]`（起点 L2 会主动指向它，从而形成 `A ➔ rel ➔ B` 单向链） |
| **L4 知识闭环体** | `ontology/` | • 仅指向顶层架构总纲 (`[[..._Architecture]]`) | 禁止反向指向 `[[lbl_...]]` 和 `[[info_...]]`（下层节点会自动汇聚指向它） |


### 1.3 20-wiki 四层知识形态Markdown落盘规范

• 落盘边界说明：引擎对 10_inbox/ 仅有只读权限，扫描切片与知识抽取均在引擎内存中完成；
所有结构化 Markdown 产物均直接按照本规范落盘至 20_wiki/debug/<layer>/ 目录，严禁在 10_inbox/ 中生成中间文件。

• 锚点条件渲染：为解决流水线分阶段异步执行时“下游节点尚未生成，导致上游双链无法填充”的问题，所有产物均采用 “YAML 强契约 + 尾部锚点条件渲染 + 渐进式增量回填” 机制。
正文分割线 --- 下方统一使用 <!-- GRAPH_LINKS_START --> 与 <!-- GRAPH_LINKS_END --> 包裹图谱双链区；若某组双链数组为空，直接隐藏该行标题（禁止输出空 [[]] 或 无）。


模板 A：L1 原始符号切片 （原子事实溯源与长尾细节库）
• 核心作用：保留未经过度压缩的高保真原始语料（代码片段、堆栈、配置表），作为所有上层结论的证据锚点（Ground Truth），专门承接具体行号、报错原文、参数明细等长尾细节查询。
• YAML 来源：自动继承 Information 原生字段（info_id、cognizer_id、topic、source）+ 包装追踪字段（trace_id、domain）。
• 双链规则：无提炼概念时隐藏**提炼概念**行；归属架构缺省时占位 [[Unclassified_Architecture]]。

```markdown
---
info_id: "info_llm_config_isolation"
cognizer_id: "arch_review_agent"
topic: "llm-config"
source: "repo:knowledge-engine#main:docs/flaws.md"
trace_id: "tr_session_20261124"
domain: "knowledge-engine"
---

# LLM 配置独立化与超时治理

## 核心摘要
> [!abstract] 一句话摘要
> knowledge 角色必须有独立 LLM profile；模型选择看输出特性而非推理能力；max_iterations 需全链路透传验证。

## 原始切片明细
（高保真原始符号内容，保留代码片段、表格与 `[!bug]` / `[!caution]` / `[!important]` / `[!tip]` 细节标注）

## 遗留问题
- `assemble_master_graph()` 透传遗漏需在 Batch 1 修补。

---
**提炼概念**：[[lbl_model_per_role]] | [[lbl_config_transparency_chain]] | [[lbl_backpressure]]
**归属架构**：[[Internal_Knowledge_Architecture]]

```


模板 B：L2 概念节点 （下游语义检索的主力索引层）
• 核心作用：全库检索的第一入口与路由枢纽。通过标准化受控词表（6 大元类型）与单行高密判据，实现高信噪比的语义匹配，并作为图谱跳数的起点连接上游切片与下游因果边。
• YAML 来源：继承 Labeling 原生字段（label_id、category、timestamp）+ 受控词表字段（label_type 6选1、confidence、domain）。
• 双链规则：初始落盘仅有**溯源切片**；后续跨批次异步追加**发出关系**（仅起点回填）与**汇聚闭环**；若无任何有效链接行则不渲染底部分割线。

```markdown
---
label_id: "lbl_backpressure"
category: "concept"
timestamp: 1732512000.0
label_type: "mechanism"
confidence: 0.95
domain: "engineering"
---

# 背压控制（Backpressure）

## 核心定义
> [!quote] 一句话判据
> 在流水线阶段之间设置规模门控，防止上游产物爆炸导致下游 LLM 调用超时。

## 触发判据
- 上游单批次输出节点数超过阈值 $N > 50$ 时，强制挂起分发并触发流控。
- 当 LLM 调用出现 `LengthFinishReasonError` 且失败阶段为 3.3+ 时，判定背压不足。

## 边界与反例
- 仅适用于异步多阶段流水线（3.1→3.2→3.3→3.4），同步单步脚本无需引入。

---
**溯源切片**：[[info_organization_design_flaws]] | [[info_organization_pipeline_diagnostic]]
**发出关系**：[[rel_backpressure_enables_partial_persistence]] | [[rel_schema_cardinality_refines_backpressure]]
**汇聚闭环**：[[ont_organization_scalability]]


```

模板 C：L3 有向语义边 (多跳因果推理与机制传导桥)
• 核心作用：消除向量检索“只见孤立概念、不见逻辑因果”的盲区。明确记录概念间的方向性作用机制（封闭 8 动词）与置信度权重（degree），专门回答*“为什么 A 会导致 B”、“什么手段能缓解 C”* 等归因与方案推导类问题。
• YAML 来源：继承 RelatingConcepts 原生字段（relation_id、label_1_id、label_2_id、relationship_type 封闭8动词、degree）+ 扩展字段（domain）。
• 双链规则：**指向目标** 落盘即必填（单向流动），**汇聚闭环** 由 Phase 4 聚类回填。

```markdown
---
relation_id: "rel_backpressure_enables_partial_persistence"
label_1_id: "lbl_backpressure"
label_2_id: "lbl_partial_persistence"
relationship_type: "enables"
degree: 0.9
domain: "engineering"
---

# 背压 → 使能 → 部分持久化

## 关系语义
> [!note] 关系断言（`enables` / 置信度 0.9）
> 背压控制（正常路径预防规模爆炸）与部分持久化（异常路径保证中间产物不丢失）构成互补闭环。

## 传导路径
- `lbl_backpressure` 在 3.2→3.3 之间拦截超限批次 ➔ 降低单次事务负载 ➔ 使能 `lbl_partial_persistence` 稳定落盘。

## 置信度依据
- 源自 `info_organization_design_flaws` 中的 P0/P1 级故障复盘记录。

---
**指向目标**：`lbl_backpressure` ➔ [[lbl_partial_persistence]]
**汇聚闭环**：[[ont_organization_scalability]]


```

模板 D：L4 知识闭环体 (宏观架构全景与复杂系统摘要层)
• 核心作用：面向系统级、全局性综述问题的顶层入口。将高内聚的子图节点与多条因果边聚拢为完整的“问题—方案集群—演进约束”闭环，避免模型在回答宏观设计问题时陷入碎片化细节。
• YAML 来源：继承 Ontology 原生字段（complex_id、label_ids、relation_ids、descriptor）+ 扩展字段（domain）。
• 双链规则：**证据切片** 聚合子图内所有概念的溯源切片；**支撑总纲** 必填（缺省占位 [[Unclassified_Architecture]]）。

```markdown
---
complex_id: "ont_organization_scalability"
label_ids: ["lbl_backpressure", "lbl_partial_persistence", "lbl_schema_cardinality_constraint"]
relation_ids: ["rel_backpressure_enables_partial_persistence"]
descriptor: "组织流水线在切片内容丰富时从 3.3 开始不可用；解决方案集群 = 背压 + 部分持久化 + 按角色选模型 + 配置透传。"
domain: "knowledge-engine"
---

# 组织流水线规模弹性

## 闭环总结
> [!abstract] 一句话总结
> 组织流水线在切片内容丰富时从 3.3 开始不可用；解决方案集群 = 背压 + 部分持久化 + 按角色选模型 + 配置透传。

## 逻辑拓扑
```text
细化层:
  Schema基数约束 (lbl_schema_cardinality_constraint) --refines--> 背压机制 (lbl_backpressure)
因果层:
  背压机制 --enables--> 部分持久化 (lbl_partial_persistence)
```

## 演进与约束
- 背压阈值（N>50）和窗口大小（window_size=20）为经验值，需在 P0 修复后实测校准。
- 部分持久化仅保留 labels，半成品关系边和本体不保留。

---
**证据切片**：[[info_organization_pipeline_diagnostic]] | [[info_organization_design_flaws]] | [[info_llm_config_isolation]]
**支撑总纲**：[[Internal_Knowledge_Architecture]]

```

### 1.3.1 20-wiki 四层知识形态图谱双链生命周期（从初始态到稳定态的演化规则）
由于知识提纯是跨批次异步进行的，双链字段遵循 “允许前向声明、允许初始缺省、禁止全量重写、仅做锚点回填” 四大核心原则：


| 演化阶段 | 触发动作 | 各层 YAML 与锚点区状态变化 | 工程约束与防污染规则 |
| :--- | :--- | :--- | :--- |
| **Phase 1：采集与切片** | 生成 L1 | • `derived_labels: []`（隐藏 **提炼概念** 行）<br>• `architecture_ref` 若无法识别，默认填入 `Unclassified_Architecture` | 禁止生成空双链 `[[]]`；允许写入尚不存在的 `[[Unclassified_Architecture]]` 作为虚链接占位。 |
| **Phase 2：单轮概念抽取** | 从 L1 提取 N 个 L2 概念 | • 落盘 L2 文件，此时 `outgoing_relations: []`、`parent_ontologies: []`，锚点区完全留空。<br>• 回填 L1：更新 L1 的 `derived_labels`，在锚点区渲染 **提炼概念** 行。 | 若同批次已分配好 `lbl_id`，允许先写 L1 再写 L2（利用图谱虚链接特性自动连线）。 |
| **Phase 3：窗口关系构建** | 任意两个 L2 满足关联阈值，生成 L3 | • 落盘 L3 文件，**指向目标** 必填（强约束）。<br>• 回填起点 L2：向起点 `label_1_id` 的 `outgoing_relations` 追加该 `rel_id`，并在锚点区渲染/追加 **发出关系** 行。 | 严格单向：只回填起点 L2，绝不回填终点 L2（保证 `A ➔ rel ➔ B` 单向流动）。 |
| **Phase 4：低频聚拢闭环** | 累积多轮后触发 L4 聚类任务 | • 落盘 L4 文件，绑定 `architecture_ref`。<br>• 批量回填 L2 & L3：向被聚拢的 L2、L3 节点的 `parent_ontologies` 追加该 `ont_id`，并渲染 **汇聚闭环** 行。 | 幂等去重：回填时先读取 YAML 列表并做集合去重（set union），再整体重绘锚点区。 |
| **Phase 5：晋升稳定态** | 人工审核（`debug/` ➔ `release/`）或业务验证（➔ `gold/`） | • 修改 YAML 中的 `stage` 字段与物理路径。<br>• 人工补全或修正 `architecture_ref`（替换 `Unclassified_Architecture`）。 | ID 不可变原则：跨目录移动时，文件主名（`info_id` / `label_id` 等）严禁修改，确保全库双链零断链。 |

### 1.3.2 20-wiki 四层知识形态回填操作安全规范
当上游或下游任务需要更新已存在文件的双链时，引擎必须遵守以下 I/O 契约：
1. 只读正文原则：回填程序严禁修改 # 标题 至 --- 分割线之间的任何正文内容。
2. 双写一致性：任何双链变更必须同时更新 YAML Frontmatter 对应数组（供程序结构化查询）与 <!-- GRAPH_LINKS_START/END --> 锚点区 Markdown 文本（供图谱引擎渲染）。
3. 跨目录检索优先顺序：当引擎需要回填某个 artifact_id 时，按 debug/ ➔ release/ ➔ gold/ 顺序定位文件；若目标文件已处于 release/ 或 gold/（引擎只读区），则将回填指令写入待审队列，由人工或晋升脚本合并，严禁引擎直接覆写已审核资产。

### 1.4 面向 Obsidian 原生检索算子的产物组织规范
为使人类排查与 Agent 检索均能直接利用 Obsidian 原生搜索引擎实现毫秒级精准过滤，所有落盘产物必须严格遵循以下六大算子映射规则

| Obsidian 筛选项 | 对应产物组织机制 | 规划与落盘规范 | 实战检索示例（人类 / Agent 均可直接用） |
| :--- | :--- | :--- | :--- |
| `path:` | 物理目录树 | 严格锁定 `<stage>/<layer>/` 路径隔离生命周期与抽象层级。 | `path:20_wiki/gold/ontology/`（只搜已验证的黄金闭环体） |
| `file:` | 强前缀文件命名 | 文件名强制携带层前缀 + 蛇形英文 ID（`info_` / `lbl_` / `rel_` / `ont_`），禁止使用中文或空格。 | `file:lbl_backpressure` 或 `file:rel_ -path:debug`（查所有非调试期的关系边） |
| `tag:` | 三段式层级标签 | 废弃扁平标签，改用嵌套命名空间：`#layer/<层级>`、`#domain/<业务域>`、`#rel/<关系类型>`、`#topic/<主题>`。 | `tag:#layer/labeling tag:#domain/engineering`（按域过滤概念节点） |
| `property:` | YAML 强类型属性 | 规范 YAML 键名与数据类型（数组、布尔、数值），供 Obsidian Dataview 和属性面板直接做范围过滤。 | `[degree:>=0.8]`（筛选高置信度语义边）<br>`[stage:release]`（筛选准生产资产） |
| `section:` | 标准 H2 标题骨架 | 固定每层产物的 `##` 章节名称，确保同一段落（Section）内的关键词共现才能命中。 | `section:("核心定义" "背压")`（只在“核心定义”段落里搜背压，排除正文噪音） |
| `line:` | Callout 单行高密摘要 | 每个首节 `##` 下方放置 Callout 块，把核心结论压缩在单行内（禁止内部换行），保证原子级共现命中。 | `line:("P0" "背压")`（要求“P0”和“背压”必须出现在同一行摘要中，极高精度） |


### 1.4.1 各层级固定 ## 章节骨架校验表

引擎在生成正文时禁止自由发挥二级标题，必须严格按以下清单输出（供 section: 算子与 Schema 校验器使用）：
• L1 (information/)：## 核心摘要 ➔ ## 原始切片明细 ➔ ## 遗留问题
• L2 (labeling/)：## 核心定义 ➔ ## 触发判据 ➔ ## 边界与反例
• L3 (relating/)：## 关系语义 ➔ ## 传导路径 ➔ ## 置信度依据
• L4 (ontology/)：## 闭环总结 ➔ ## 逻辑拓扑 ➔ ## 演进与约束

### 1.4.2 20-wiki Callout 语义使用速查表
引擎生成规则（防滥用约束）

1. 首节单行原则：凡是作为各层首节（## 核心摘要 / ## 核心定义 / ## 关系语义 / ## 闭环总结）的 Callout，正文严禁换行或包含列表，确保 line: 算子原子级共现命中。
2. 禁止自定义别名：统一使用表内标准的 7 个标识符，禁止输出 [!tldr]、[!warning]、[!danger] 等同义别名，保证全库 CSS 渲染与正则校验 100% 一致。

所有落盘产物禁止随意使用花哨的 Callout 类型，必须严格按以下“层级 + 场景”映射表渲染（首节摘要块强制单行，正文细节块允许列表）：

| 适用层级 / 场景 | 强制标识符 | Obsidian 视觉效果 | 语义定位与内容约束 | 标准写法示例 |
| :--- | :--- | :--- | :--- | :--- |
| L1 核心摘要<br>L4 闭环总结 | `[!abstract]` | 浅蓝色框 + 剪贴板图标 | **全局结论 / 摘要**：放在首节 `##` 下方，内容必须压缩在单行内（适配 `line:` 检索算子）。 | `> [!abstract] 一句话摘要`<br>`> 组织流水线存在 6 个设计缺陷，核心问题是无背压。` |
| L2 核心定义 | `[!quote]` | 灰色框 + 双引号图标 | **权威概念定义**：放在 L2 首节 `## 核心定义` 下方，给出该概念的一句话判据（单行）。 | `> [!quote] 一句话判据`<br>`> 背压控制是在阶段间设置规模门控，防止下游超时。` |
| L3 关系语义 | `[!note]` | 蓝色框 + 铅笔图标 | **语义断言与置信度**：放在 L3 首节 `## 关系语义` 下方，明确阐述 `A ➔ B` 的作用机制。 | `> [!note] 关系断言（enables / 0.9）`<br>`> 背压与部分持久化构成正常与异常路径的互补闭环。` |
| 正文：故障/缺陷 | `[!bug]` | 红色框 + 虫子图标 | **历史故障与根因**：仅用于 L1 原始切片或复盘记录中，标记已发现的系统缺陷。 | `> [!bug] 原问题`<br>`> knowledge 角色无独立 profile，fallback 导致超时。` |
| 正文：风险/遗漏 | `[!caution]` | 橙黄色框 + 三角警告图标 | **边界隐患与待办**：标记尚未修复的遗漏点、配置陷阱或系统约束红线。 | `> [!caution] 遗漏点`<br>`> assemble_master_graph() 尚未传递 max_iterations。` |
| 正文：阻塞/强约束 | `[!important]` | 紫红色框 + 感叹号图标 | **P0 级阻塞项 / 铁律**：标记最高优先级的阻塞问题，或不可违背的架构红线。 | `> [!important] 当前阻塞项`<br>`> L3 关系建模超时需设计层面修复后方可上线。` |
| 正文：经验/结论 | `[!tip]` | 青绿色框 + 火焰图标 | **最佳实践与提炼**：从实验或调优中总结出的通用工程准则。 | `> [!tip] 核心结论`<br>`> 意图识别看推理能力，组织阶段需输出紧凑、结构化可靠。` |

### 1.5 工程级运行与质量约束（防图谱腐化）

**L2 概念元类型受控词表（label_type 6 选 1 判据）**
| 元类型 (`label_type`) | 语义边界（什么算合法概念） | 正例（允许落盘为 L2） | 反例（严禁抽取，留在 L1 即可） |
| :--- | :--- | :--- | :--- |
| `mechanism` | 架构机制、控制策略、设计模式 | `lbl_backpressure`（背压控制） | `lbl_retry_3_times`（具体参数配置值） |
| `component` | 核心模块、角色、服务边界 | `lbl_knowledge_profile`（知识角色配置） | `lbl_llm_factory_line_86`（具体代码行号） |
| `principle` | 架构原则、设计红线、系统不变量 | `lbl_dip_purity`（依赖倒置纯净度） | `lbl_code_should_be_clean`（空泛口号） |
| `failure_mode` | 系统性缺陷、典型故障模式 | `lbl_output_truncation`（输出截断） | `lbl_deepseek_timeout_nov24`（单次偶发报错） |
| `metric` | 关键度量指标、阈值判据 | `lbl_schema_cardinality`（基数约束） | `lbl_77_llm_calls`（单次运行统计数字） |
| `workflow` | 标准化流程、状态机、交互协议 | `lbl_staged_commit`（分批提交策略） | `lbl_yesterday_meeting`（临时会议动作） |

## 2. 持续知识集成与扩展规则（知识生命周期管理）

1. **扁平化防嵌套**：除 `20_wiki/` 严格遵循 `<stage>/<layer>/` 两级矩阵外，其余目录内**严禁新建多级子文件夹**，新增文档一律在对应层级平铺，依靠命名规范与双链 `[[...]]` 关联。
2. **新增主题总纲**：直接在 `00_architecture/` 下新建 `<主题名>_Architecture.md`（附 `stage: gold` YAML 头），并在 `00_architecture/README.md` 登记双链。
3. **新增与管理 QA**：
   * 属于已有粒度则追加至对应 `QA_01~04` 文件末尾；属于新模块则新建 `QA_<模块>_<主题>.md` 并在 `qa/README.md` 登记。
   * **全局顺延编号，永不重排**：全库 QA 编号全局唯一且持续递增（当前已至 `Q18`，下一条统一为 `### Q19：<标题>`），确保切片器与跨文件双链（`[[文件名#Q19]]`）永久有效。
4. **原始资料消化与图谱晋升**：
   * 零散文档丢入 `10_inbox/` ➔ 引擎自动切片并生成图谱落盘至 `20_wiki/debug/<layer>/` ➔ 人类在 Obsidian 中审核后直接拖拽至 `release/<layer>/` 或 `gold/<layer>/`（全局逻辑 ID 确保迁移零断链）。
5. **机器写隔离与采集过滤**：后端 `vault_root` 指向 `20_wiki/`，引擎仅可写入 `debug/`；所有文件采集器默认忽略 `README.md`。

## 3. Obsidian 接入配置（首次打开必改）

1. 打开 Obsidian ➔ **打开本地仓库（Open folder as vault）** ➔ 选中 `knowledge_vault/`。
2. 进入 **设置 ➔ 文件与链接**：
   * **内部链接类型**：设为 **基于仓库根目录的简短路径（Shortest path when possible）**。
   * **自动更新内部链接**：保持 **开启**。

## 4. 关系图谱（Graph View）视觉配色与治理规范

采用**“核心灯塔高亮 + 生命周期流转色”**双维度视觉规范：颜色优先标出 L4 知识闭环体，其余节点严格按可信度阶段着色，并开启有向箭头（`showArrow: true`）凸显 L3 语义边方向。

### 4.1 目录配色与配置顺序

打开关系图谱右上角 **设置（齿轮图标） ➔ 分组（Groups）**，严格按以下优先级顺序配置（规则自上而下排他匹配）：

| 优先级 | 检索筛选规则 | 匹配目标 | 推荐颜色 | Hex 色值 | 视觉语义 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `path:"20_wiki" path:"ontology/"` | L4 知识闭环体（全阶段） | **洋红色** | `#EC4899` | **核心灯塔**，跨阶段高亮高密度聚合体 |
| **2** | `path:"20_wiki/gold"` | 业务闭环黄金标准（L1~L3） | **翡翠绿** | `#10B981` | 最高成熟度，高价值知识沉淀 |
| **3** | `path:"20_wiki/release"` | 人工审核准生产区（L1~L3） | **天蓝色** | `#3B82F6` | 安全、已清洗、可信赖常规网络 |
| **4** | `path:"20_wiki/debug"` | AI 自动生成未审核（L1~L3） | **琥珀橙** | `#F59E0B` | **警示色**，快速定位待审核节点 |
| **5** | `path:"00_architecture"` | 人类权威架构总纲 | **深紫色** | `#8B5CF6` | 沉稳权威，锁定全库核心骨架 |
| **6** | `path:"10_inbox"` | 待消化原始缓冲区 | **中性灰** | `#9CA3AF` | 低调降噪，未结构化原始素材 |

### 4.2 图谱显示与过滤参数（防视觉噪音）

1. 开启有向箭头（关键）：在图谱设置 ➔ 显示（Display） 中，必须开启 箭头（Arrows），直观验证 L1 ➔ L2 ➔ L3 ➔ L2 ➔ L4 ➔ Architecture 的单向金字塔流向（若出现双向箭头，说明违反了 1.2 引用规则）。
2. 默认隐藏孤立原始文件：在图谱设置 ➔ 过滤器（Filters） 中，建议勾选 孤立文件（Orphans）关闭，或添加 -path:"10_inbox"，避免未消化的原始文档占据画布中心。
3. 层级标签辅助着色（可选）：在日常排查特定语义边时，可临时添加分组规则 tag:#rel/enables 或 tag:#rel/conflicts 高亮特定因果链路。

## 5. 基于20-wiki的检索

5.1 三级向量索引策略（Multi-Vector Indexing）

针对不同层级的文本密度与查询意图，入库时采用差异化切块与嵌入策略，避免长文稀释语义：

| 索引库 | 索引目标层 | 提取规则 | 承接查询类型 |
| :--- | :--- | :--- | :--- |
| **宏观全景索引** | L4 (`ontology/`) | 提取 `## 闭环总结` 下的 `[!abstract]` 单行摘要 | 全局架构综述（如 *“组织流水线规模弹性的完整解决方案是什么？”*） |
| **核心语义索引（主力）** | L2 (`labeling/`)<br>L3 (`relating/`) | • L2 提取 `## 核心定义` 下的 `[!quote]` 单行判据；<br>• L3 提取 `## 关系语义` 下的 `[!note]` 单行断言 | 概念定义、方案选型、因果归因（如 *“背压控制怎么防止下游超时？”*） |
| **长尾细节索引** | L1 (`information/`) | 提取 `## 核心摘要` 单行 Callout，并对 `## 原始切片明细` 按 `###` 子标题分块 | 源码行号、具体参数阈值、报错现场还原（如 *“LLM profile 配置在哪个文件第几行？”*） |


5.2 元数据前置过滤（Pre-filtering）

在执行向量相似度计算前，先基于路径与 YAML 原生属性做硬过滤（Where 条件），大幅缩小检索空间：
• 生命周期隔离（路径解析）：从物理路径 20_wiki/<stage>/<layer>/ 自动解析 stage。生产环境默认过滤 stage IN ('gold', 'release')，彻底屏蔽 debug/ 区的未验证实验产物。
• 领域与粒度过滤（YAML 标量）：
	• 查概念时过滤 label_type（如限定 failure_mode 排查故障，或限定 mechanism 寻找架构方案）；
	• 查因果链时过滤 relationship_type（如限定 mitigates / enables）及边权重 [degree >= 0.8]；
	• 溯源代码或特定业务域时过滤 domain、topic 与 source 前缀（如 source LIKE 'repo:knowledge-engine%'）。

5.3 四大典型检索场景与 GraphRAG 邻域扩展链路

检索器（KnowledgeRetriever）根据用户提问意图，自动路由到对应的入口层，并利用文件底部的原生双链执行零额外 LLM 调用的确定性图谱扩展：

场景 1：概念定义与方案查询（入口：L2 ➔ 扩展：L3 + L1）

• 典型提问：“什么是组织流水线的背压控制？具体怎么落地？”
• 检索路径：
	1. L2 命中：核心语义索引命中 lbl_backpressure.md（获取一句话判据与触发阈值）；
	2. 1-Hop 向下细化：正则解析底部 **发出关系** 中的 [[rel_schema_cardinality_refines_backpressure]] 等细化边，自动拉取关联的实现节点（如 lbl_schema_cardinality_constraint）；
	3. 1-Hop 溯源佐证：解析底部 **溯源切片** 中的 [[info_organization_design_flaws]]，提取对应代码片段作为落地示例喂给回答模型。

场景 2：故障归因与因果链推理（入口：L2/L3 ➔ 扩展：L3 多跳 + L1）

• 典型提问：“为什么 3.3 关系建模超时会导致整轮提取的标签全部丢失？”
• 检索路径：
	1. L2/L3 命中：匹配故障节点 lbl_output_truncation 及相关 blocks / causal 关系边；
	2. 多跳因果遍历：沿 L3 关系边的 label_1_id ➔ label_2_id 方向追踪传导路径（读取 ## 传导路径 段落），串联出完整故障链；
	3. 证据对齐：读取 L3 ## 置信度依据 引用的 L1 切片，向用户输出有据可查的根因分析。

场景 3：全局架构设计与综述问答（入口：L4 ➔ 扩展：L2 集群 + L3 拓扑）

• 典型提问：“总结一下我们在组织流水线稳定性与超时治理上的整体演进方案。”
• 检索路径：
	1. L4 命中：宏观全景索引直接命中 ont_organization_scalability.md；
	2. 子图批量装载：直接读取 L4 ## 逻辑拓扑 与 ## 演进与约束（获取全局方案状态表与验收标准），若上下文窗口允许，按 YAML 中的 label_ids 批量加载核心 L2 节点的单行定义作为补充，无需再做全库盲搜。

场景 4：代码行号与配置明细排查（入口：L1 ➔ 反向向上聚合：L2）

• 典型提问：“DeepSeek-v4-Flash-SZ 在 8192 max_tokens 下的实测结果是什么？profile 配置在哪？”
• 检索路径：
	1. L1 命中：长尾细节索引直接命中 info_llm_config_isolation.md 下的 ### 1. knowledge profile 独立化 切片块，精准返回配置表与 llm_factory.py:86；
	2. 向上升维提示：读取该 L1 文件底部的 **提炼概念**（[[lbl_model_per_role]]）与 **归属架构**，在回答具体细节的同时，附带给出对应的架构设计原则链接供用户延伸阅读。
