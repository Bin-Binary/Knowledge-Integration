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
为解决流水线分阶段异步执行时“下游节点尚未生成，导致上游双链无法填充”的问题，所有 Markdown 产物均采用 “YAML 强契约 + 尾部锚点条件渲染 + 渐进式增量回填” 机制落盘。
所有模板在正文结束的分割线 --- 下方，统一使用 <!-- GRAPH_LINKS_START --> 与 <!-- GRAPH_LINKS_END --> 包裹图谱双链区。
渲染规则：若某组双链数组为空，直接隐藏该行标题（禁止输出空 [[]] 或 无）

模板 A：L1 原始符号切片
```markdown
---
artifact_layer: information
info_id: info_organization_design_flaws
stage: debug
trace_id: tr_session_20261124
tags: [information, backpressure, label-extraction]
derived_labels: [lbl_schema_cardinality_constraint, lbl_windowed_relation_building, lbl_backpressure, lbl_partial_persistence]
architecture_ref: Internal_Knowledge_Architecture
---

# 组织流水线设计逻辑缺陷分析

> [!abstract] 摘要
> 6 个设计缺陷（P0×2 / P1×2 / P2×2），核心问题是“无背压、无部分持久化”。

（...具体诊断正文...）

---
<!-- GRAPH_LINKS_START -->
**提炼概念**：[[lbl_schema_cardinality_constraint]] | [[lbl_windowed_relation_building]] | [[lbl_backpressure]] | [[lbl_partial_persistence]]  
**归属架构**：[[Internal_Knowledge_Architecture]]
<!-- GRAPH_LINKS_END -->

```

模板 B：L2 概念节点
```markdown
---
artifact_layer: labeling
label_id: lbl_backpressure
stage: debug
tags: [labeling, engineering, backpressure]
source_infos: [info_organization_design_flaws]
outgoing_relations: [rel_backpressure_enables_partial_persistence]
parent_ontologies: [ont_organization_scalability]
---

# 背压控制（Backpressure）

> [!quote] 核心定义
> 在流水线阶段之间设置规模门控，防止上游产物爆炸导致下游 LLM 调用超时。

（...判据与细节...）

---
<!-- GRAPH_LINKS_START -->
**发出关系**：[[rel_backpressure_enables_partial_persistence]]  
**汇聚闭环**：[[ont_organization_scalability]]
<!-- GRAPH_LINKS_END -->

```

模板 C：L3 有向语义边
```markdown
---
artifact_layer: relating
relation_id: rel_backpressure_enables_partial_persistence
stage: debug
relationship_type: enables
label_1_id: lbl_backpressure
label_2_id: lbl_partial_persistence
degree: 0.9
tags: [relating, enables, backpressure, partial-persistence]
parent_ontologies: [ont_organization_scalability]
---

# 背压 → 使能 → 部分持久化

> [!note] 关系语义（`enables` / 置信度 0.9）
> **背压**（正常路径预防规模爆炸）与 **部分持久化**（异常路径保证中间产物不丢失）构成互补闭环。

---
<!-- GRAPH_LINKS_START -->
**指向目标**：`lbl_backpressure` ➔ [[lbl_partial_persistence]]  
**汇聚闭环**：[[ont_organization_scalability]]
<!-- GRAPH_LINKS_END -->

```

模板 D：L4 知识闭环体
```markdown
---
artifact_layer: ontology
complex_id: ont_stability_and_commit_strategy
stage: debug
tags: [ontology, stability, commit-strategy, dip]
aggregated_labels: [lbl_stability_partitioning, lbl_config_transparency_chain]
evidence_infos: [info_stability_zones_analysis, info_llm_config_isolation]
architecture_ref: Internal_Knowledge_Architecture
---

# 稳定性分区与提交策略

> [!abstract] 一句话总结
> 单仓 repo 混合稳定接口与不稳定业务逻辑，按 DIP 纯净度分三批提交，不稳定模块 feature 隔离。

## 逻辑拓扑（纯文本渲染，避免干扰图谱箭头）

graph TD
    A["稳定性分区提交 (lbl_stability_partitioning)"] --> B{DIP 纯净度}
    B -->|高| C[Batch 1: schemas/protocols/infra ➔ main]
    B -->|中| D[Batch 2: 有测试的组件 ➔ main + v0.1]
    B -->|低| E[Batch 3: 不稳定模块 ➔ feature branch]
    F["配置透传链 (lbl_config_transparency_chain)"] -->|supports| A

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

### 4.2 图谱降噪与巡检筛选语法

* **日常默认视角（已预置）**：`-file:README -path:"information/"`，自动隐藏索引文件与海量 L1 原始切片噪音，聚焦 L2~L4 知识网络。
* **全局骨架鸟瞰**：`-file:README (path:"ontology/" OR path:"00_architecture/")`，仅展示顶层架构与洋红色 L4 闭环体。
* **专项审核 AI 关系边**：`path:"debug/relating/"`，配合有向箭头集中排查引擎刚生成的 L3 语义边方向与合理性。
