
---

**Intentional_action（意图性行动）**
*定义*: 刻画一个带有主观意图、目标与手段的配置行动事件，连接实体与配置单元
*Core FE*: [action/行动]
*Peripheral FE*：None
*高频词元(LUs)*: [action/行动]

Intentional_action（意图性行动）
│
├── 继承自: Event
├── Act FE 定值: None
├── 事件类型: Quality_gate_setup / Custom_task_setup
│
├── Core FE:
│   ├── Agent/施事            (inherited) 填充约束: 人物或自动化系统
│   ├── Act/行动              (inherited) 填充约束: 配置/搭建
│   ├── Patient/受事          (inherited) 填充约束: Product/Version/Repository
│   ├── Purpose/目的          (inherited) 填充约束: 目标描述 (goal)
│   ├── Means/手段            (inherited) 填充约束: Instrument (Jenkins 等工具)
│   ├── Plan/计划             (NEW, qualia Constitutive) 填充约束: 分解步骤 (plan)
│   └── Result/结果           (inherited) 填充约束: 实际结果 (result)
│
├── Peripheral FE:
│   ├── Condition/条件        (inherited→保持外围) 填充约束: Branch/Version
│   ├── Configuration/配置    (NEW, qualia Constitutive) 填充约束: rules / task_config
│   ├── Goal/目标             (inherited)
│   └── Manner/方式           (inherited)
│
└── 高频词元: 配置、搭建、创建、构建

---

**Quality_gate_setup（配置门禁）**
*定义*: 刻画新版本门禁规则的配置事件，阻止低质量代码合并
*Core FE*: [gate/门禁]
*Peripheral FE*：None
*高频词元(LUs)*: [gate/门禁]

Quality_gate_setup（配置门禁）
│
├── 继承自: Intentional_action
├── Act FE 定值: fixed = configure
├── 事件类型: Quality_gate_setup
│
├── Core FE:
│   ├── Agent/事件            (inherited) 填充约束: Agent (执行者)
│   ├── Act/行动              (inherited, fixed = configure)
│   ├── Patient/受事          (inherited) 填充约束: QualityGate (待生效的门禁实体)
│   ├── Purpose/目的          (inherited) 填充约束: 确保分支满足规则 (如行覆盖率 >= 80%)
│   ├── Means/手段            (inherited) 填充约束: Jenkins / CI门禁工具
│   └── Result/结果           (inherited) 填充约束: 门禁规则生效
│
├── Peripheral FE:
│   ├── Condition/条件        (inherited) 填充约束: Branch / Version
│   ├── Configuration/配置    (inherited) 填充约束: rules [{metric, operator, threshold}]
│   ├── Source/来源           (inherited) 填充约束: 添加规则、绑定分支
│   ├── Goal/目标             (inherited)
│   └── Manner/方式           (inherited)
│
└── 高频词元: 配置、门禁、覆盖率、阈值、合并

---

# 垂直领域 Agent 门禁配置模型设计

## 1. 设计目标与背景

本模型面向持续集成（CI）领域的门禁配置管理，旨在解决以下核心问题：

- 历史配置存在大量非标准化差异，包括产品版本差异、代码仓配置差异、CIE 习惯差异以及文件组织差异。
- 新 Agent 需要基于这些历史数据，自动完成新版本产品的门禁搭建，具体包括：
  1. 确定需要配置哪些代码仓；
  2. 决定对哪些路径下的哪些文件做何处理（新建、覆盖、拆分或合并）；
  3. 明确文件内需要修改哪些位置、值是什么。

设计原则：

- **逻辑与物理分离**：用统一的语义模型描述门禁配置的逻辑内容，同时容忍物理文件组织的多样性。
- **意图与实体增强**：用意图性行动框架描述事件，用Qualia结构增强实体语义，支持推理与复用。
- **策略可配置**：将文件组织、模板渲染等生成策略独立成层，便于根据历史习惯或团队规范动态调整。
- **可扩展性**：分层设计允许在任意层插入新类型或新规则，不影响其他层。

---

## 2. 总体架构

模型采用五层架构，自底向上分别为：

1. **实体层（Entity Layer）**：描述参与门禁配置的核心实体及其Qualia结构。
2. **配置单元层（Config Unit Layer）**：逻辑上描述每个独立的门禁规则或自定义任务，与物理文件解耦。
3. **物理文件层（Physical File Layer）**：记录配置单元在文件系统中的实际存储位置和 CIE 习惯。
4. **意图性行动框架层（Intentional Action Layer）**：描述门禁搭建事件中的意图、动作、目标、参与者等。
5. **策略层（Strategy Layer）**：负责将逻辑配置单元映射为具体文件操作和内容修改。

此外，各层之间通过实体引用和关系关联，形成一个语义闭环。架构示意：

```
+-------------------------------+
|       策略层 (Strategy)        |  ← 生成决策、路径模板、文件渲染
+-------------------------------+
             ↑ 使用
+-------------------------------+
|  意图性行动框架层 (Event)      |  ← 事件描述、意图目标
+-------------------------------+
             ↑ 关联实体
+-------------------------------+
|     实体层 (Entity + Qualia)   |  ← 产品、代码仓、门禁实体等
+-------------------------------+
             ↑ 包含/引用
+-------------------------------+
|     配置单元层 (ConfigUnit)    |  ← 逻辑配置单元（规则、任务）
+-------------------------------+
             ↑ 映射到
+-------------------------------+
|    物理文件层 (PhysicalFile)   |  ← 文件路径、格式、行号、习惯
+-------------------------------+
```

---

## 3. 各层详细设计

### 3.1 实体层（Entity Layer）

采用 Qualia 结构增强实体描述，支持概念泛化和功能推理。核心实体包括：

- **产品（Product）**
- **产品版本（Version）**
- **代码仓（Repository）**
- **门禁实体（QualityGate）**
- **自定义任务（CustomTask）**（如编译、DT 等）
- **CIE 配置文件（Profile）**（可选，描述个人或团队习惯）

每个实体均包含四个 Qualia 角色：

| 角色 | 说明 | 示例（以"代码覆盖率门禁"为例） |
|------|------|--------------------------------|
| Formal | 类型与区别特征 | is_a: 质量保障机制；特征: 面向 main 分支，仅检查行覆盖率 |
| Constitutive | 内部构成 | 包含多个规则（指标、操作符、阈值） |
| Telic | 功能/目的 | 阻止覆盖率低于阈值的代码合并 |
| Agentive | 来源/创建方式 | 由张三在 Jenkins 中配置，关联事件 E001 |

**数据结构示例（JSON）**：

```json
{
  "entity_id": "QG_A_1.2_repo1",
  "type": "QualityGate",
  "qualia": {
    "formal": {
      "is_a": "QualityGate",
      "features": ["coverage", "main branch"]
    },
    "constitutive": {
      "rules": [
        {"metric": "line_coverage", "operator": ">=", "threshold": 0.8}
      ]
    },
    "telic": {
      "function": "Prevent low coverage merge",
      "purpose": "Maintain code quality"
    },
    "agentive": {
      "creator": "ZhangSan",
      "event_id": "E001",
      "method": "Jenkins UI",
      "time": "2024-05-10"
    }
  }
}
```

### 3.2 配置单元层（Config Unit Layer）

配置单元是逻辑上独立的门禁规则或自定义任务，与具体文件无关。它是跨历史数据对齐的核心键。

**属性**：

- `config_unit_id`：唯一标识
- `type`：类型（如 `coverage_gate`, `compile_task`, `dt_task`）
- `product` / `version`：所属产品版本
- `repo`：关联的代码仓（可多值）
- `rules`：规则列表（当 type 为门禁时）
- `task_config`：任务配置（当 type 为自定义任务时）
- `related_events`：关联的意图性行动事件 ID

**示例**：

```json
{
  "config_unit_id": "CU_A_1.2_repo1_cov",
  "type": "coverage_gate",
  "product": "A",
  "version": "1.2",
  "repo": "repo1",
  "rules": [
    {"metric": "line_coverage", "operator": ">=", "threshold": 0.8}
  ],
  "related_events": ["E001"]
}
```

**多代码仓情况**：一个配置单元可关联多个 repo，或拆分为多个配置单元，根据语义决定。若多个代码仓共享同一门禁规则，可使用一个配置单元并关联多个 repo。

### 3.3 物理文件层（Physical File Layer）

记录配置单元实际存放的文件、位置、格式和 CIE 习惯。**支持多对多关系**（一个文件包含多个配置单元，一个配置单元可能拆在多个文件）。

**属性**：

- `file_id`：文件唯一标识
- `path`：文件路径（相对于代码仓根）
- `format`：yaml/json/jenkinsfile等
- `contains_config_units`：包含的配置单元 ID 列表
- `created_by` / `cie_style`：记录 CIE 习惯（如 `split_files`, `merged`）
- `line_ranges`：每个配置单元在文件中的行号范围（可选）

**示例**：

```json
{
  "file_id": "F_A_1.2_repo1_ci",
  "path": "ci/gates/coverage.yml",
  "format": "yaml",
  "contains_config_units": ["CU_A_1.2_repo1_cov"],
  "cie_style": "merged",
  "line_ranges": [
    {"config_unit_id": "CU_A_1.2_repo1_cov", "start": 10, "end": 25}
  ]
}
```

### 3.4 意图性行动框架层（Intentional Action Layer）

（该层事件已在上文改写为 FE 条目：Intentional_action / Quality_gate_setup / Custom_task_setup）

### 3.5 策略层（Strategy Layer）

策略层是新增的、用于解决生成问题的关键组件。它负责回答"如何将逻辑配置单元转换为物理文件操作"。

**组件**：

1. **路径模板库（Path Templates）**  
   定义标准路径模式，例如：
   - 门禁：`ci/gates/{repo_name}.yml`
   - 自定义任务：`ci/tasks/{task_type}.yml`
   - 通用合并文件：`ci/gates/all.yml`
   支持占位符替换。

2. **文件组织偏好（File Organization Preferences）**  
   记录不同产品/团队/CIE 的拆分合并习惯。可通过历史物理层数据统计学习。示例：
   - 团队 X：每个门禁一个文件（split）
   - 团队 Y：所有门禁合并到一个 `gates.yml`（merged）
   - 团队 Z：自定义任务按类型拆分

   表示形式可为规则或概率模型。

3. **文件模板与渲染器（File Templates & Renderer）**  
   为每种文件格式定义模板，将配置单元的规则值渲染为实际文件内容。例如 YAML 模板：
   ```yaml
   gates:
     - name: {{ config_unit.type }}
       rules:
         {% for rule in config_unit.rules %}
         - metric: {{ rule.metric }}
           operator: {{ rule.operator }}
           threshold: {{ rule.threshold }}
         {% endfor %}
   ```
   渲染器根据配置单元数据填充模板，生成最终文本。

4. **补丁生成器（Patch Generator）**  
   当目标文件已存在时，对比生成内容与现有文件，生成最小修改补丁（新增、修改、删除字段）。可基于文本 diff 或结构化 diff。

**策略层工作方式**：

- 输入：配置单元 + 目标代码仓 + 上下文（产品版本、团队偏好）
- 输出：文件操作列表，每项包含：文件路径、操作类型（新建/覆盖/追加/修改）、内容或补丁。

---

## 4. 核心实体关系总结

- **产品（Product）** 1:N **版本（Version）**
- **版本（Version）** 1:N **代码仓（Repository）**
- **配置单元（ConfigUnit）** 属于 一个 **产品-版本**，可关联多个 **代码仓**
- **配置单元（ConfigUnit）** 可能对应 0..N 个 **门禁实体/任务实体**
- **配置单元（ConfigUnit）** 通过 **物理文件层** 映射到 1..N 个 **物理文件**
- **物理文件** 可包含 1..N 个 **配置单元**
- **意图性行动事件** 关联 多个 **配置单元** 和 **实体**
- **实体** 的 Agentive 角色可能引用 **事件**，形成闭环

---

## 5. 解决历史差异的具体机制

| 差异 | 解决机制 |
|------|----------|
| 产品/版本代码仓数量不同 | 实体层产品和版本与代码仓一对多关系；配置单元可关联多个 repo |
| 代码仓配置各有差异 | 每个代码仓可拥有独立的配置单元和规则 |
| CIE 习惯不同（拆分/合并） | 物理文件层记录文件组织方式；策略层包含文件组织偏好，可匹配习惯 |
| 一个文件包含多个事件 | 物理文件与配置单元多对多；事件与配置单元多对多，文件可包含多个配置单元从而涉及多个事件 |

---

## 6. 解决新版本门禁搭建的三个需求

针对用户提出的三个具体需求，模型提供如下机制：

### 需求1：配置哪些代码仓

- **方法**：查询实体层中产品 A 的历史版本（如 v1.1）关联的代码仓集合，作为默认候选；结合产品团队输入或版本变更说明，调整代码仓列表。
- **模型支持**：实体层明确 `Product -- Version -- Repository` 关系，且配置单元层记录了历史版本每个配置单元关联的 repo，可快速检索。

### 需求2：对哪些路径下的哪些文件做处理（新建/覆盖/拆分/合并）

- **方法**：
  1. 根据逻辑配置单元列表，查询策略层的路径模板，生成目标文件路径。
  2. 根据文件组织偏好（可从历史物理层学习或人工指定），决定每个配置单元是单独成文件还是合并到已有文件。
  3. 判断目标文件是否存在：若不存在则新建；若存在，根据策略决定覆盖或追加。
- **模型支持**：策略层提供路径模板和组织偏好；物理文件层提供现有文件状态（是否存在、包含哪些配置单元），用于决策。

### 需求3：文件内需要修改哪些地方，值是什么

- **方法**：
  1. 使用策略层的文件模板和渲染器，根据配置单元的规则值生成目标文件内容。
  2. 若文件已存在，调用补丁生成器，对比生成内容与现有内容，输出差异（修改位置、新值）。
  3. 文件模板和渲染器可根据历史同类文件训练或手工编写。
- **模型支持**：配置单元层保存了所有规则值；策略层的模板和渲染器将这些值转化为具体文件内容；补丁生成器定位具体修改位置。

---

## 7. 端到端工作流程

### 7.1 历史数据接入流程

1. 解析历史配置文件（物理文件层），提取配置单元，建立 `config_unit` 记录。
2. 识别配置单元涉及的实体（产品、代码仓、门禁），填充实体层及 Qualia 信息。
3. 关联意图性行动事件（可从提交记录、文档中抽取或人工标注）。
4. 记录物理文件位置、CIE 习惯等。
5. 学习文件组织偏好，存入策略层。

### 7.2 新版本门禁搭建流程

1. **事件创建**：在意图性行动框架层创建新事件，明确意图、目标、产品版本、代码仓候选。
2. **代码仓确定**：从实体层获取历史代码仓，结合业务输入确认最终列表。
3. **配置单元生成**：根据目标门禁类型和历史相似配置，生成待处理的配置单元（可复用已有配置单元或新建）。
4. **文件操作决策**：对每个配置单元，查询策略层：
   - 确定目标文件路径（路径模板）
   - 确定文件组织方式（拆分/合并）
   - 检查现有文件（物理文件层）
5. **内容生成**：使用文件模板渲染生成目标内容，若文件存在则生成补丁。
6. **执行与记录**：执行文件操作，将新生成的物理文件、配置单元、事件关联关系写回模型。

---

## 8. 模型扩展性

- **新门禁类型**：在配置单元层添加新 type，在策略层添加对应模板即可。
- **新文件格式**：在物理文件层扩展 format，在策略层实现对应渲染器。
- **多团队协作**：策略层的文件组织偏好可基于团队维度区分，实现个性化生成。
- **智能推荐**：利用历史数据训练机器学习模型，自动推荐文件路径、拆分策略，提升自动化程度。

---

## 9. 总结

本模型通过五层架构，将逻辑语义与物理实现解耦，同时保留意图和实体增强信息，有效解决了历史差异容忍和新版本自动生成的问题。核心亮点在于：

- **意图性行动框架**提供事件级语义，支撑解释和审计。
- **Qualia 实体增强**丰富实体静态语义，支持泛化与推理。
- **配置单元层**作为逻辑对齐核心，消除文件组织差异带来的干扰。
- **物理文件层**容纳历史习惯，实现多对多映射。
- **策略层**打通逻辑到物理的转换，实现可配置的自动生成。

该模型可直接作为垂直领域 Agent 的知识表示与生成基础，支持后续迭代优化。
