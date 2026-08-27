# 基于框架语义学和生成词汇学的垂直领域Agent工程实践POC
以"流水线"为激活词、通常激活实体、身份或抽象概念场景

## 基于生产语料分布观察
框架从使用中归纳出来，不要内省出来！！！(一段很长的痛苦经历)
*实践建议：先共现后划分，先提取高频搭配、扁平化词汇，先做FE划分会因词元位置变化导致FE漂移*

**高频搭配**
从生产环境中清洗后得到作为候选FE的语料：
[skill、执行、查询、创建、启动、pipeline_id、URL、分支、记录、联调、版本、配置]
[clouddrag、包、监控、链接、状态、个人、天舟、构建、group_id、闪存、25B、scheme]
[部署、查看、Dorado、环境、子系统、下载、成功、触发、error、结果、OceanStor、自动]
[停止、job_id、出包、MCP、产物、arm、工具、debug、脚本、被动、运行、执行方案、任务、MR]

**谓词提取 -> Action FE候选**
*"流水线"做Patient/受事*
[执行、创建、查询、查看、启动、出包、配置、停止、监控、构建、部署、引用、获取、触发、下载]
*"流水线"做Agent/施事*
[运行、耗时、等待]
*"流水线"做Entity/实体*
[成功、完成、通过、失败、结束、恢复、~正在~、~异常~、暂停、中断、停止]
这些谓词实际上跨两类——状态类和过程类——语义角色不同

!!! 在实践操作中犯了错误
    "流水线成功"中，流水线是语法主语，但语义角色是Entity（处于某状态的实体），不是Agent（有意行动的施事）

**邻接论元候选清单**
[分支、pipeline_id、版本、group_id、job_id、执行方案、service_id、scheme_id]
*论元结构是连接核心事件（语义面）与句子外壳（句法面）的桥梁*
*必须是该事件发生不可或缺的参与者（Core Arguments），不出现则意义彻底改变*

**对比构式中的对照词 -> 邻接LU候选**
[可信、个人、被动、主动、天舟平台、不涉及、MR、动、创建个人联调分支、拉个人联调分支、分支]
[不是、基线、天舟平台拉个人联调分支、版本级、手动、日构建、确认创建个人分支、构建相关]
[创建天舟个人联调分支、个人联调分支、用于拉个人联调分支、构建参数、当天舟平台拉个人联调分支]
[子系统级、天舟个人联调分支、滚动、创建天舟平台个人联调分支、分支名称]

*X vs Y句式可以拉出一条对立或互补的语义轴*
*将共现的X和Y记录为强相关对偶节点 -> 自动联想或预测Y的存在*
*先共现后划分后，X vs Y加速FE的泛化和扩充*
*有些词汇在单独出现时含义模糊，但在X vs Y中语义会瞬间精确*

以下为AI评估：
```markdown
| 语义轴 | 对立项 | 可能的 FE/属性 |
|---|---|---|
| 归属 | 个人 vs 共享 | Ownership FE |
| 自动化 | 手动 vs 自动 | Automation FE |
| 粒度 | 子系统级 vs 版本级 | Granularity FE |
| 平台 | 天舟 vs 其他 | Platform FE |
| 频率 | 日构建 vs 触发构建 | Frequency FE |
| 部署策略 | 滚动 vs 其他 | Strategy FE |
| 主动性 | 主动 vs 被动 | Initiative FE |
| 可信度 | 可信 vs 不可信 | Trust FE |

这些语义轴非常有价值——它们可以作为流水线实体的属性维度（用 Pustejovsky 的 qualia 或 step 2b 的属性组织来归类），也可以作为外围 FE 附加到具体子框架上。
```
以下为AI评估生成词汇学：
```markdown
标题写的是"基于框架语义学和生成词汇学"，但正文中未见 Pustejovsky 的 qualia structure 应用。

建议补充 step 2b：对"流水线"这个实体用四维 qualia 组织属性：

Quale
维度
流水线的属性
Formal	它是什么	CI/CD 流水线（软件构建/部署流程的自动化编排）
Constitutive	由什么组成	stage（阶段）、job（任务）、step（步骤）、trigger（触发器）、变量、配置
Telic	用来做什么 / 行为倾向	自动构建、自动测试、自动部署、质量保障
Agentive	如何产生	由 Operator 创建、由 Scheme 定义、由 Template 派生

再结合上面从对比构式拉出的语义轴（归属、自动化、粒度……），归入对应 qualia 维度。这样"生成词汇学"组件才真正落地。
```
### 发现
从Action FE候选清单和邻接论元候选清单中发现流水线（pipeline）作为词元，根据语法位置唤起四个框架：
```markdown
1. Intentionally_act（受事位）：执行流水线、创建流水线、停止流水线……
   流水线 = Patient → 有人对流水线做有意图的行动

2. State（状态描述位）：流水线成功、流水线失败、流水线暂停……
   流水线 = Entity → 流水线处于某状态

3. Change（状态转换位）：流水线从运行变为暂停、流水线完成……
   流水线 = Entity → Initial_state → Final_state

4. Process / Activity（施事位）：流水线运行、流水线等待……
   流水线 = Agent / Process → 流水线在执行/进行
```
## 框架定义与FE清单

Event
 ├── Process        （加 Duration 维度）
 ├── Change         （加 Entity + Initial/Final_state）
 └── Activity       （加 Agent + Activity）
      └── Intentionally_act  （加 Purpose + Means，意向性约束）

| 框架ID | 框架名(EN/ZH) | 类型 | 父框架 | 关系 | Core FE 数 |
|---|---|---|---|---|---|
| F0 | Activity/行动框架| 抽象父框架 | — | — | 2 |

*核心FE随层级递增：每往下一层，框架就多出若干核心FE——因为更具体的框架需要更多角色才能定义*
*这是框架语义学的核心设计原则：框架越具体，核心FE越多；框架越一般，核心FE越少（退化为事件本身 + 外围环境信息）*
Event只需要一个核心FE（事件本身）；Intentionally_act需要四个（施事 + 行动 + 目的 + 手段）。

<!-- ### F0: Intentionally_act（流水线操作）

**定义**: 一个意图性行动框架：施事 Agent（Operator）对受事 Patient（Pipeline）执行某种自主性动作 Action，通过工具 Means（Scheme）在条件 Condition（Branch/Trigger/Version）下达成目标，并产生结果 Result（Outcome）。本框架为所有流水线操作子框架的抽象父框架，Action 不取定值。

**框架关系**: 顶层框架

**Core FE**:

| FE | 语义角色 | 填充物示例 |
|---|---|---| 
F0: Intentionally_act（流水线操作·父框架）
  Act 不取定值
  
  ├── F1: Create_pipeline（创建流水线）  Act = 创建
  ├── F2: Execute_pipeline（执行流水线）  Act = 执行
  ├── F3: Query_pipeline（查询流水线）    Act = 查询
  ├── F4: Configure_pipeline（配置流水线） Act = 配置
  ├── F5: Stop_pipeline（停止流水线）     Act = 停止
  └── F6: Deploy_pipeline（部署流水线）   Act = 部署

每个子框架继承 F0 的全部 FE，Act FE 取定值，并可能新增子框架专属 FE（如 F1 增加基于模板 Template FE；F2 增加执行方案 Scheme FE 为核心）
-->


---
## 附录
---
### 核心“通用”语义角色（FE） -> 所有框架共用的非核心FE
在“先共现后划分”阶段，最容易被高频介词洗出来的非核心元素：
[Purpose（主观目的/意图）、Means（手段）、Patient（受事）、Time（时间）、Place（地点）、result(结果)、Condition（条件）]

!!! Purpose（主观目的/意图）不是Goal（空间、数据或状态终点）
    Purpose: 意图（Intentionality）。施事者心智中想要达成的宏观愿望
    Goal:    终点（Boundedness）。动作在空间、数据流或状态转移上的落脚点
---
### 常用语义框架总览
**Using（使用工具）**
*定义*: 刻画施事通过工具作用于某对象以实现目的。
*Core FE*: [Agent/施事、Instrument/工具、Patient/受作用对象]
*Peripheral FE*: [Purpose/目的、Manner/方式、Means/手段]
*高频词元(LUs)*: [use、utilize、employ、wield、leverage、apply、operate]

**Choosing（选择）**
*定义*: 刻画认知者从备选项中选出一个。
*Core FE*: [Cognizer/认知者、Chosen/被选中的、Alternatives/备选集]
*Peripheral FE*: [Basis/选择依据、Manner/方式、Purpose/选择目的]
*高频词元(LUs)*: [choose、select、pick、decide、opt、elect、prefer]

**Processing_materials（材料加工）**
*定义*: 刻画原材料被加工转化为产品的过程。
*Core FE*: [Material/原材料、Product/产品]
*Peripheral FE*: [Agent/加工者、Means/加工手段、Time/时间、Place/地点]
*高频词元(LUs)*: [process、refine、manufacture、produce、fabricate、convert、treat]

**Communication（交流）**
*定义*: 刻画发送方向接收方传递信息。
*Core FE*: [Communicator/发送方、Addressee/接收方、Message/信息内容]
*Peripheral FE*: [Topic/主题、Medium/媒介、Manner/方式、Language/语言]
*高频词元(LUs)*: [say、tell、speak、communicate、inform、notify、convey、state]

**State（状态）**
*定义*: 刻画一个实体处于某种持续的状态。
*Core FE*: [Entity/实体、State/状态]
*Peripheral FE*: [Duration/持续时间、Time/时间、Place/地点]
*高频词元(LUs)*: [be、exist、remain、stay、stand、lie、rest]

**Event（事件）**
*定义*: 刻画某事在特定时间和地点发生。这是最一般的"发生"框架，不预设意向性、持续性或状态变化性。
*Core FE*: [Event/事件]
*Peripheral FE*：[Time/时间、Place/地点、Duration/持续时间、Frequency/频率、Manner/方式、Particular_iteration/特定实例]
*高频词元(LUs)*: [event、happen、occur、take place、come about、transpire、come off、befall]

**Process（过程）**
*定义*: 刻画一个过程在一段时间内展开。描述持续进行的事件，不预设特定施事或状态变化。
*Core FE*: [Process/过程]
*Peripheral FE*: [Duration/持续时间、Time/时间、Place/地点、Manner/方式、Rate/速率]
*高频词元(LUs)*: [process、proceed、unfold、develop、evolve、play out、go on、pan out]

**Change（变化）**
*定义*: 刻画一个实体从初始状态转变为终状态。
*Core FE*: [Entity/实体、Initial_state/初始状态、Final_state/终状态]
*Peripheral FE*: [Time/时间、Place/地点、Manner/方式、Cause/原因、Rate/速率]
*高频词元(LUs)*: [change、turn、become、transform、shift、convert、alter、modify、switch]

**Activity（活动）**
*定义*: 刻画施事参与一项活动。引入施事，但不预设意向性（可是有意的，也可以是无意的习惯性行为）。
*Core FE*: [Agent/施事、Activity/活动]
*Peripheral FE*: [Time/时间、Place/地点、Duration/持续时间、Manner/方式、Purpose/目的、Means/手段]
*高频词汇*: [do、engage in、perform、practice、work (at)、carry out、conduct、undertake]

**Intentionally_act（意图性行动）**
*定义*: 刻画施事带有意图的行动。在 Activity 之上增加意向性约束。
*Core FE*: [Agent/施事、Act/行动、Purpose/行动目的、Means/手段]
*Peripheral FE*: [Condition/条件、Goal/目标、Manner/方式]
*高频词汇*: [act、action、do、perform、carry out、execute、commit]


