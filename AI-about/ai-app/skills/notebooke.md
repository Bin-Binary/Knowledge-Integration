# 笔记
> 一切为了收敛Agent的基线行为 -BIN

以"上下文预填充"为例、记录工程落地实践。
背景：真实agent项目中，发送"创建一条流水线需要做什么"、Agent出现反复确认信息的现象(>3轮询问)
分析：任务需要大量必备上下文，而不同产品需要不同上下文集，只能逐轮向用户索要

**skill还是代码处理**
非直觉明显 — 直觉是按产品分类"列清单然后反问"，但不会想到"按角色预填充"
跨项目可复用 — 任何agent与用户交互的系统都存在此问题
非标准实践 — 当前无成熟文档覆盖此模式
涉及判断 — 不同产品需要不同上下文集，无法用正则/校验完全自动化
结论：需要创建判断"何时上下文已足够可以行动"的skil(技术/模式)、即产品与角色上下文无差集时可以开始行动。

**skill的类型**
是技术skill.
"按角色预填上下文"不只是思维模型，它有具体可执行的步骤；
可定义具体步骤：识别用户身份（代码实现） → 映射角色→ 上下文集 → 预填充 → agent据此行动

**测试的类型**
技术方法类技能（操作指南）
测试手段：
- 落地应用场景：能否正确使用该技术方法
- 变体场景：能否处理各类边界情况
- 信息缺失测试：指令是否存在漏洞
成功标准：**智能体可以在全新场景下正确运用该技术**

!!! note
    技术型的基线行为不是"知道但偷懒不做"，而是"不知道或不正确应用"。使用强约束类型的施压没有意义。

**该skill的职责**
只管"判断逻辑"——提取哪些角色信息填充上下文、填充后是否存在差集、不足时如何优雅追问。

**参考测试设计**
测试场景	验证目标
应用场景	给定一个新角色 + 新任务类型，agent能否正确映射该角色需要的上下文集？
变化场景	边界情况 — 用户跨角色、角色对应的上下文有重叠、任务需要罕见上下文时
缺失信息测试	指令中是否有遗漏：如角色未知时 fallback 策略、上下文仍不足时是否该追问


## TDD
红-绿-重构

### 红阶段：基线测试(记录失败)
在没有技能的情况下运行测试——观察并记录代理行为

该阶段有以下必要的过程：
- [√] 创建测试用例
- [√] 在没有技能的情况下运行 - 记录基线行为
- [√] 对基线行为现象分类

**基线行为现象分类参考**
新增skill前不涉及约束失效、输出变形、元素遗漏。可以观察到存在'条件依赖'失效现象，即代理行动前、未根据当前用户上下文推断必须信息。

---

### 绿阶段
这个阶段的目标是编写解决红阶段记录的基线行为的skill。

该阶段有以下必要的过程：
- [√] 编写最小技能
- [√] 验证绿

#### 编写SKILL.md
针对红阶段记录的基线行为、编写最小的解决skill。

**skill的结构**
Ⅰ. name和description是skill的强制字段

##### name和description
参考SDO

```markdown
---
name: Skill-Name-With-Hyphens
description: Use when [specific triggering conditions and symptoms]
---

# Skill Name

## Overview
What is this? Core principle in 1-2 sentences.

## When to Use
[Small inline flowchart IF decision non-obvious]

Bullet list with SYMPTOMS and use cases
When NOT to use

## Core Pattern (for techniques/patterns)
Before/after code comparison

## Quick Reference
Table or bullets for scanning common operations

## Implementation
Inline code for simple patterns
Link to file for heavy reference or reusable tools

## Common Mistakes
What goes wrong + fixes

## Real-World Impact (optional)
Concrete results
```

#### 验证绿
在有skill的技能的情况下运行相同场景，Agent的行为应该是符合预期的。如果基线行为仍然存在：技能不清晰或不完整。修改并重新测试。

**成功标准**
- 代理在行动前获取用户关联信息并注入上下文


## FAQ:
**1.** 不同产品需要不同上下文集：从哪来？版本迭代怎么更新？

**2.** 如何丰富角色信息

**3.** 技术类型、参考类型、模式类型是否都要TDD?

不是，TDD是测试维度的分类、强约束才需要。**内容&测试维度**对skill的分类如下：

**按内容性质分类**
| 类型 | 定义 |	例子|
| :---- | :---- |:---- |
| Technique | 具体可执行的步骤方法 | condition-based-waiting, root-cause-tracing |
| Pattern | 思维模型/看问题的方式 | flatten-with-flags, test-invariants |
| Reference | API 文档/语法参考 | office docs, command references |

**按测试方式分类**
|类型| 测试重点|	例子|
|:----|:----|:----|
|Discipline-Enforcing|	压力下是否遵守规则|	TDD, verification-before-completion|
|Technique|	能否正确应用方法|	condition-based-waiting|
|Pattern	|能否识别何时用/何时不用	|reducing-complexity|
|Reference|	能否找到并正确使用信息|	API 文档|

---
4. "对基线行为现象分类", 这是什么意思 按什么分类，分类后的产物是什么
**4.1 按什么分类**
按Agent基线行为的表现形式，分为4类：

| 基线行为类型 | Agent的行为特征 | 根因 |
| :---- | :---- | :---- |
| 1. 约束失效 |	知道规则，压力下跳过 | 竞争激励下选择偷懒 |
| 2. 输出变形 |	遵守了要求，但产出形状错误（臃肿、冗余、格式偏离）| 不知道"正确的产出长什么样" |
| 3. 元素遗漏 |	产出了对的东西，但漏了某个必要部分 | 结构中缺少"必填占位符" |
| 4. 条件依赖 | 本该根据条件走不同路径，却走了固定路径 | 缺少条件判断锚点 |

**4.2 为什么必须先分类**
不同失败类型需要完全不同的对抗手段，用错了会适得其反：

| 基线行为类型 | 正确手段 | 错误手段（会反噬） |
| :---- | :---- | :---- |
| 约束失效 | 禁止令 + 合理化借口表 + 红旗列表 | - |
| 输出变形 | 正向契约：定义输出"是什么"——由哪些部分、按什么顺序组成 | 禁止令（"不要冗余""不要复述"→ agent 反而更多） |
| 元素遗漏 | 结构化必填位：模板中预留 REQUIRED 槽位 | 文字提醒（"记得写XX"→ agent 仍然漏掉）|
| 条件依赖 | 条件锚点：可观测谓词触发（"如果 brief 存在，则引用它"） | 无条件规则 + 豁免条款（"除非...否则..."→ 豁免被忽略） |

> 文档的核心实验发现： 在dispatch-prompt的措辞测试中，用禁止令对抗输出变形，比不加任何指导的对照组还差——agent和禁止令"讨价还价"，反而产出更多冗余内容。

**4.3 分类后的产物**
分类的产物**不是分类本身**，而是**每种类型对应的对策形式**：
基线行为分类 → 对策形式选择 → 写入Skill 的具体内容

约束失效  → 禁止令 + rationalization table + red flags
输出变形  → 正向契约（recipe/contract）：声明输出 IS 什么
元素遗漏  → 结构化模板：REQUIRED 槽位
条件依赖  → 条件谓词：if [可观测条件] then [行为]

---
**5**. 为什么禁止类描述在格式类问题上会起反效果
在存在冲突目标（例如“保证提示词自完备”）时，智能体会对“不要做X”这类禁令做变通处理。在针对调度提示词的对照措辞测试中，使用禁止式写法的实验组，产生的无效内容显著多于使用正向范式的实验组，表现甚至差于无任何指导的对照组。应当针对你的场景做小规模验证，不要默认优先选用禁止式写法

---

**6.** Micro‑Test什么意思，是红绿重构的哪个阶段，和红阶段基线测试的在没有技能的情况下运行是什么关系
**6.1 Micro‑Test** 和Full Scenario区分，前者验证skill整体是否有效、**Micro‑Test验证skill措辞/wording是否有效**

**6.2 GREEN阶段的子步骤** ：
GREEN ─────────────────────────────────────
  │ 1. 写 skill（最小版本）
  │ 2. Micro-Test wording ← 在这里
  │ 3. Full scenario test（最终验证）

---

**7.为什么名称和描述是SKILL.md的强制字段、为什么总字符最大是1024个**

---

**8.除了name和description、技术类型、模式类型、参考类型的skill的结构有区别吗**

**8.1 正文结构区别**

通用模板中 `Core Pattern` 段仅标注适用于 `techniques/patterns`，三类型的侧重点不同：

| 段落 | Technique（技术型） | Pattern（模式型） | Reference（参考型） |
|---|---|---|---|
| 核心段落 | **Core Pattern** — Before/After 代码对比 + 具体步骤 | **Core Pattern** — 思维模型/心智框架阐述 | 无 Core Pattern，以 **Quick Reference** 为主体（API 表、语法速查） |
| Quick Reference | 常见操作速查表 | 认知决策表（何时用/何时不用） | 全量 API 签名、参数、返回值表格 |
| Code Examples | 必须有、完整可运行 | 可选（模式本身是思维工具） | 代码片段为主，覆盖常见用例 |
| Common Mistakes | 操作步骤易错点 | 误用/过度使用的场景 | API 陷阱、参数边界 |

**8.2 文件组织区别**

| 类型 | 典型目录结构 | 原因 |
|---|---|---|
| Technique | `SKILL.md` + `example.ts`（可复用工具/辅助代码） | 有可复用的代码工具需单独文件 |
| Pattern | 通常只有 `SKILL.md`（全部内联） | 以概念为主，无需重型参考 |
| Reference | `SKILL.md` + 多个重型参考文件（`pptxgenjs.md`、`ooxml.md` 等）+ `scripts/` | 100+ 行的 API 文档必须拆分为独立文件 |

**8.3 测试方式区别**

| 类型 | 测试方式 | 成功标准 |
|---|---|---|
| Technique | 应用场景（能否正确应用技术）、变体场景（边界处理）、信息缺失测试（指令有无缺口） | Agent 能在新场景中成功应用技术 |
| Pattern | 识别场景（能否识别模式适用）、应用场景（能否使用思维模型）、**反例场景（何时不用）** | Agent 正确判断何时/如何应用 |
| Reference | 检索场景（能否找到正确信息）、应用场景（能否正确使用找到的信息）、覆盖度测试（常见用例是否覆盖） | Agent找到并正确应用参考信息 |

**关键差异**：Patter型最独特——强调"何时不用"的反例测试，而Technique和Reference不需要；Reference 型最特殊——没有Core Pattern段，重型内容必须拆文件，且测试聚焦"检索"而非"判断"。

---
**9. SKILL.md的name和description有什么讲究、怎么写**
**9.1 使用第三人称和第二撰写description有什么区别**
