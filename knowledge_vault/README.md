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


模板 A：L1 原始符号切片 (information/)
```markdown
---
artifact_layer: information
info_id: info_organization_design_flaws
stage: debug
trace_id: tr_session_20261124
tags: [layer/information, domain/architecture, topic/backpressure]
derived_labels: [lbl_schema_cardinality_constraint, lbl_windowed_relation_building, lbl_backpressure, lbl_partial_persistence]
architecture_ref: Internal_Knowledge_Architecture
---

# 组织流水线设计逻辑缺陷分析

## 核心摘要
> [!abstract] 一句话摘要
> 组织流水线存在 6 个设计缺陷（P0×2 / P1×2 / P2×2），核心问题是缺乏背压控制与部分持久化机制。

## 原始切片明细
（...具体诊断正文...）

## 遗留问题
- 需补充各阶段背压阈值的具体量化指标。

---
<!-- GRAPH_LINKS_START -->
**提炼概念**：[[lbl_schema_cardinality_constraint]] | [[lbl_windowed_relation_building]] | [[lbl_backpressure]] | [[lbl_partial_persistence]]  
**归属架构**：[[Internal_Knowledge_Architecture]]
<!-- GRAPH_LINKS_END -->

```


模板 B：L2 概念节点 (labeling/)
```markdown
---
artifact_layer: labeling
label_id: lbl_backpressure
label_type: mechanism
stage: debug
confidence: 0.95
tags: [layer/labeling, type/mechanism, domain/engineering, topic/backpressure]
source_infos: [info_organization_design_flaws]
outgoing_relations: [rel_backpressure_enables_partial_persistence]
parent_ontologies: [ont_organization_scalability]
---

# 背压控制（Backpressure）

## 核心定义
> [!quote] 一句话判据
> 背压控制是在流水线阶段之间设置规模门控，防止上游产物爆炸导致下游 LLM 调用超时。

## 触发判据
- 当上游单批次输出节点数超过阈值 $N > 50$ 时，强制挂起分发并触发流控。

## 边界与反例
- 仅适用于异步多阶段流水线，同步单步脚本无需引入背压状态机。

---
<!-- GRAPH_LINKS_START -->
**发出关系**：[[rel_backpressure_enables_partial_persistence]]  
**汇聚闭环**：[[ont_organization_scalability]]
<!-- GRAPH_LINKS_END -->

```

模板 C：L3 有向语义边 (relating/)
```markdown
---
artifact_layer: relating
relation_id: rel_backpressure_enables_partial_persistence
stage: debug
relationship_type: enables
label_1_id: lbl_backpressure
label_2_id: lbl_partial_persistence
degree: 0.9
tags: [layer/relating, rel/enables, domain/engineering]
parent_ontologies: [ont_organization_scalability]
---

# 背压 → 使能 → 部分持久化

## 关系语义
> [!note] 关系断言（`enables` / 置信度 0.9）
> 背压控制（正常路径预防规模爆炸）与部分持久化（异常路径保证中间产物不丢失）构成互补闭环。

## 传导路径
- `lbl_backpressure` 在上游拦截超限批次 ➔ 降低单次事务负载 ➔ 使能 `lbl_partial_persistence` 稳定落盘。

## 置信度依据
- 源自 `info_organization_design_flaws` 中的 P0 级故障复盘记录。

---
<!-- GRAPH_LINKS_START -->
**指向目标**：`lbl_backpressure` ➔ [[lbl_partial_persistence]]  
**汇聚闭环**：[[ont_organization_scalability]]
<!-- GRAPH_LINKS_END -->

```

模板 D：L4 知识闭环体 (ontology/)
```markdown
---
artifact_layer: ontology
complex_id: ont_stability_and_commit_strategy
stage: debug
tags: [layer/ontology, domain/architecture, topic/stability]
aggregated_labels: [lbl_stability_partitioning, lbl_config_transparency_chain]
evidence_infos: [info_stability_zones_analysis, info_llm_config_isolation]
architecture_ref: Internal_Knowledge_Architecture
---

# 稳定性分区与提交策略

## 闭环总结
> [!abstract] 一句话总结
> 单仓 repo 混合稳定接口与不稳定业务逻辑，按 DIP 纯净度分三批提交，不稳定模块 feature 隔离。

## 逻辑拓扑
graph TD
    A["稳定性分区提交 (lbl_stability_partitioning)"] --> B{DIP 纯净度}
    B -->|高| C[Batch 1: schemas/protocols/infra ➔ main]
    B -->|中| D[Batch 2: 有测试的组件 ➔ main + v0.1]
    B -->|低| E[Batch 3: 不稳定模块 ➔ feature branch]
    F["配置透传链 (lbl_config_transparency_chain)"] -->|supports| A

## 演进与约束
- 核心 Schema 变更必须经过 `release/` 人工审核后方可合入主干。

---
<!-- GRAPH_LINKS_START -->
**支撑总纲**：[[Internal_Knowledge_Architecture]]
<!-- GRAPH_LINKS_END -->

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

**全局门控矩阵**
| 约束维度 | 核心痛点（不加约束的后果） | 强制工程规则 | 校验 / 拦截机制 |
| :--- | :--- | :--- | :--- |
| **1. ID 命名与实体对齐** | 同一概念分裂成 `lbl_backpressure`、`lbl_back_pressure`、`lbl_backpressure_control`，导致图谱碎片化。 | • **正则铁律**：全局 ID 严格匹配 `^(info\|lbl\|rel\|ont)_[a-z0-9_]{3,60}$（全小写蛇形，禁连字符与中文）。<br>• **命名防冗余**：L2 禁止带 `_concept` / `_node` 后缀；L3 强制三段式 `rel_<label1>_<verb>_<label2>`。<br>• **存量优先复用**：抽取 L2 时注入存量高频 `label_id` 清单，语义相似度 `≥ 0.85` 强制归一化复用。 | 落盘前查全库（`gold ➔ release ➔ debug`）做实体对齐；命中存量则合并追加 `source_infos`，禁止新建文件。 |
| **2. L2 概念元类型受控** | LLM 把单次报错堆栈、代码行号或临时统计数字抽成概念节点，污染图谱。 | • **半开放受控**：概念名称开放增长，但每个 `lbl_` 必须归入 6 大标准概念元类型（写入 YAML `label_type` 与 `#type/` 标签），且必须具备跨文档复用价值。 | 不属于 6 大元类型或属于单次偶发事件（如具体行号/单次耗时）的候选词直接丢弃，仅保留在 L1 正文中。 |
| **3. L3 关系动词受控** | LLM 随意发明 `helps`、`assists`、`supports` 等同义动词，导致语义边无法聚合查询。 | • **封闭枚举词表**：`relationship_type` 仅允许从 8 个标准动词中选择：<br>`enables`（使能）、`requires`（依赖）、`blocks`（阻塞）、`conflicts`（冲突）、`mitigates`（缓解）、`refines`（细化）、`composed_of`（组成）、`analogous_to`（类比）。 | Pydantic / JSON Schema 强校验：不在枚举列表内的关系边直接拦截丢弃或通过同义映射表自动归并。 |
| **4. 规模基数与背压门控** | 单篇长文档抽出 30 个碎片概念，导致后续 L3 关系两两组合爆炸（$C_{30}^2 = 435$ 次调用）打爆超时。 | • **L1 ➔ L2 基数上限**：单次切片最多提取 `N ≤ 6` 个核心概念（宁缺毋滥）。<br>• **L2 ➔ L3 窗口上限**：单次关系构建窗口内，仅对关联度 Top-K 的节点对生成 L3 边（单批次新增 `rel_ ≤ 8` 条）。 | 超过阈值直接截断（保留置信度最高的 Top-N）并记录 Warning 日志，禁止无上限循环调用。 |
| **5. 晋升期防覆写与主键唯一** | 人类刚把 `lbl_xxx.md` 拖入 `release/` 并修订了定义，重跑同一份语料时引擎又在 `debug/` 生成同名旧版文件。 | • **全局唯一主键**：整个 `20_wiki/` 跨三个生命周期目录，同一个 `artifact_id` 只能存在一份物理文件。<br>• **只读高水位线**：只要某个 ID 已存在于 `release/` 或 `gold/`，引擎在 `debug/` 中严禁再次创建同名文件。 | 落盘前执行跨目录存在性检查：若已在 `release/` 或 `gold/` 存在，跳过创建，仅将增量双链变更写入异步待审队列（`.patch_queue.jsonl`）。 |

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
