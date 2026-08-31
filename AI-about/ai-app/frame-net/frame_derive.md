---
# 子框架派生方法
---
## 核心困难
FrameNet本身没有给出"如何从父框架派生子框架"的操作手册。
FrameNet定义了框架关系（Inheritance/Subframe/Perspective_on等），但没有提供"给定父框架 + Act定值，如何确定子框架的FE清单的理论/方法。

关键缺失环节是：**Act取定值后，如何知道该加哪些新FE、提升哪些外围FE。下面给出一套组合方法。

## 理论基础：三个理论的组合
---
| 理论 | 提供什么 | 解决什么问题 |
|---|---|---|
| **Vendler 事件类型学**（1967） | Act取定值后，确定事件属于哪类（状态/活动/完成/成就） | **该加哪些 FE**——不同事件类型有不同的FE签名 |
| **FrameNet 框架继承规则** | 父子框架的FE传递约束 | **哪些FE必须继承、哪些可以新增/提升** |
| **Pustejovsky事件结构 + Qualia** | 事件的子事件分解 + 实体属性维度 | **Patient的qualia驱动领域FE发现** |

三者分工：Vendler识别"事件类型→FE 签名"；FrameNet继承识别"父子传递规则"；Pustejovsky识别"实体维度→领域 FE"。

## Vendler 事件类型：决定FE签名

这是最关键的理论。Vendler把动词/事件分为四类，**每类有固有FE签名**：

| 事件类型 | 特征 | FE 签名（固有角色） | 典型动词 |
|---|---|---|---|
| **State（状态）** | 持续、无变化、无目标 | Entity + State | be, exist, remain |
| **Activity（活动）** | 持续、有施事、无内在终点 | Agent + Activity + Duration | run, wait, do |
| **Accomplishment（完成）** | 持续、有施事、**有内在终点+产出** | Agent + Patient + **Result** + **Material/Source** | create, build, make, write |
| **Achievement（成就）** | 瞬时、有施事、**状态转换** | Agent + Patient + **Result**（瞬时） | start, stop, trigger, pause |

*Vender*
State（状态）
State的特征：[持续、无变化、无目标]
state的FE签名（固有角色）：[Entity、State]
state的典型动词：[be、exist、remain]

Activity（活动）
Activity的特征：[持续、有施事、无内在终点]
Activity的FE签名（固有角色）：[Agent、Activity、Duration]
Activity的典型动词：[run、wait、do]

Accomplishment（完成）
Activity的特征：[持续、有施事、有内在终点+产出]
Activity的FE签名（固有角色）：[Agent、Patient、Result、Material/Source]
Activity的典型动词：[creat、build、make、write]

Achievement（成就）
Achievement的特征：[瞬时、有施事、状态转换]
Achievement的FE签名（固有角色）：[Agent、Patient、Result(瞬时)]
Achievement的典型动词：[start、stop、trigger、pause]

**关键洞察**：当把Act从generic固定为某个动词（如 create），该动词的事件类型就决定了子框架**必须**有哪些FE

## FrameNet 框架继承规则
diff已继承的FE和事件类型签名FE
例如：
| 签名要求的 FE | 是否已继承 | 处理 |
|---|---|---|
| Agent | ✓ 已继承 | — |
| Patient | ✗ 父框架没有 Patient | **新增为核心** |
| Result | ✗ 父框架没有 Result | **新增为核心** |
| Material/Source | ✗ 父框架没有 | **新增为核心**（领域映射为 Template） |

## 事件的子事件分解和Qualia
用Qualia发现领域FE对Entry做qualia分析，找出与Act相关的维度
*v2 基于示例实体Entry（其生命周期的主事件为 Act）*
```markdown
你是语言学专家，你精通Pustejovsky的理论。
擅长事件的子事件分解和Qualia。
你的任务是基于文档内容/URL、对实体进行Qualia分析，并输出结构化表格到: ./references/qualia/qualia_{实体}.md
约束：
1. 说明中内容仅为格式示范，属性和候选FE必须从{文档内容}中提取，不得照搬样例，除非文档确证相同语义
2. 输入槽位 {}、必须被真实内容替换
3. 仅输出下述两张Markdown表格，不要添加解释或前言

以下为输出格式:
## Qualia分析
| Quale | 属性 | 与{主事件}相关？ | → 候选 FE |
| :--- | :--- | :--- | :--- |
| Formal | {fill_Formal_1} | {fill_Formal_2} | {fill_Formal_3} |
| Constitutive | {fill_Constitutive_1} | {fill_Constitutive_2} | {fill_Constitutive_3} |
| Telic | {fill_Telic_1} | {fill_Telic_2} | {fill_Telic_3} |
| Agentive | {fill_Agentive_1} | {fill_Agentive_2} | {fill_Agentive_3} |

说明: 
    **关于Qualia表占位符说明**：
        fill_Formal_1: Entry 是可寻址的工作单元，具有唯一标识与状态机（待触发/运行/完成/失败）
        fill_Formal_2: 同类别成员：Act 调度的对象
        fill_Formal_3: EntryIdentity, EntryState ; {约束1}
        fill_Constitutive_1: 由任务定义、入参、触发条件、执行上下文（凭证/环境）组成
        fill_Constitutive_2: 构成决定 Act 可执行性
        fill_Constitutive_3: TaskDef, Parameters, TriggerCondition; {约束1}
        fill_Telic_1: 承载请求上下文、驱动 Act 执行并记录结果以支持调度与回溯
        fill_Telic_2: 直接服务 Act
        fill_Telic_3: Context, Outcome, Retrieval; {约束1}
        fill_Agentive_1: 由触发事件（用户操作/定时/上游信号）实例化产生
        fill_Agentive_2: 事件源决定 Act 何时启动
        fill_Agentive_3: TriggerSource, Creator; {约束1}

## 子事件分解
| 子事件阶段 | 协同的Qualia维度 | 语义融合逻辑 (Why) | 最终确定的领域 FE |
| :--- | :--- | :--- | :--- |
| **$e_1$ (过程阶段)** | **Agentive (施成)** | 探究事件"始发原因"：Entry由谁/什么触发而生成 | {fill_e_1_Agentive} |
| **$e_1$ (过程阶段)** | **Constitutive (构成)** | 探究动作发生时的"装配物料"：是哪些任务定义与参数被组装进Entry | {fill_e_1_Constitutive} |
| **$e_2$ (状态阶段)** | **Formal (形式)** | 探究Entry如何被识别：系统必须赋予它区别于其他实体的特征（唯一ID+状态） | {fill_e_2_Formal} |
| **$e_2$ (状态阶段)** | **Telic (目的)** | 探究Entry诞生后的"生存意义"：处于等待被Act触发、在何环境运行的状态 | {fill_e_2_Telic} |
说明: 
    **关于子事件表结构**：
        子事件表固定为4行（e1-Agentive/Constitutive、e2-Formal/Telic）属于预设结构，
        若目标实体生命周期都符合"过程+状态"二元切分则保留，否则"行数可随子事件阶段增减"
    **关于子事件表占位符说明**：
        fill_e_1_Agentive: TriggerSource, BY_ACT——FE: 触发源; {约束1}
        fill_e_1_Constitutive: TaskDef, Parameters——FE: 装配物; {约束1}
        fill_e_2_Formal: EntryIdentity, EntryState——FE: 识别特征; {约束1}
        fill_e_2_Telic: Pending, RunEnvironment, Trigger——FE: 待运行环境; {约束1}

以下是实体 {实体}
以下是文档内容 {文档内容}

```

## 语料验证 + 同辈对比
语料验证：回到语料，检查"创建流水线"的共现词是否覆盖了上述 FE：

候选 FE
语料中的共现词
验证
Template	scheme、执行方案	✓
Pipeline_name/ID	pipeline_id（创建后产出）	✓
Configuration	分支、版本、配置	✓
Condition	分支、环境	✓

同辈对比：把 Create_pipeline 与兄弟子框架并列，找出独有 FE：

FE
Create
Execute
Query
Stop
Template	✓ 核心	✗	✗	✗
Pipeline_name	✓ 核心	✗（用已有 ID）	✗	✗
Result（新实体）	✓ 核心（新建的 pipeline）	△（执行结果）	✓（查询返回）	✓（停止状态）
Scheme	△ 外围	✓ 核心	✗	✗
Environment	✗	✓ 核心	✗	✗

发现：Template 和 Pipeline_name 是 Create 独有的核心 FE——因为没有模板和名称，"创建"行为无法完成。这正是 step 4 的 qualia Agentive 维度预测的。

Step 6：核心性重新分类
对全部 FE（继承 + 新增）做 step 4 的三项检验：

FE
来源
必要性？
句法必选？
框架特有？
判定
Agent	继承	✓ 无施事则无创建	✓	✓	Core
Act	继承（=create）	✓	✓	✓	Core
Patient	新增（事件类型）	✓ 无流水线则无创建	✓	✓	Core
Purpose	继承	✓	✓	✓	Core
Means	继承	✓	✓	✓	Core
Template	新增（qualia）	✓ 无模板则无法创建	✓	✓ Create 独有	Core
Result	新增（事件类型）	✓ 创建必产生结果	✓	△ 兄弟也有但填充不同	Core
Condition	继承→提升	△ 分支可选	△	△	Peripheral→提升为Core（若分支必选）或保持 Peripheral
Configuration	新增（qualia）	△ 可用模板默认值	△	✓	Peripheral
Goal	继承	✗	✗	✗	Peripheral
Manner	继承	✗	✗	✗	Peripheral

最终产出：Create_pipeline 框架
text

Create_pipeline（创建流水线）
│
├── 继承自: Intentionally_act
├── Act FE 定值: create
├── 事件类型: Accomplishment
│
├── Core FE:
│   ├── Agent/施事           (inherited) 填充约束: Human_operator with create permission
│   ├── Act/行动             (inherited, fixed = create)
│   ├── Patient/受事         (NEW, event type) 填充约束: Pipeline (not yet existing)
│   ├── Purpose/目的         (inherited) 填充约束: 发布/验证/联调
│   ├── Means/手段           (inherited) 填充约束: Template / Scheme
│   ├── Template/模板        (NEW, qualia Agentive) 填充约束: 模板ID
│   └── Result/结果          (NEW, event type) 填充约束: pipeline_id (新创建的)
│
├── Peripheral FE:
│   ├── Condition/条件       (inherited→保持外围) 填充约束: Branch / Version
│   ├── Configuration/配置   (NEW, qualia Constitutive) 填充约束: stages/jobs/steps
│   ├── Goal/目标            (inherited)
│   └── Manner/方式          (inherited)
│
└── 高频词元: create、新建、创建、初始化
快速参照：事件类型 → FE 签名 → 子框架模板
Act 定值
事件类型
必有 FE（除继承的 Agent+Act+Purpose+Means 外）
领域映射
create	Accomplishment	Patient + Result + Template/Material	创建流水线 → 新 pipeline_id
execute	Activity	Patient + Duration（无内在 Result）	执行流水线 → job_id
query	Achievement	Patient + Result（瞬时返回）	查询流水线 → 状态/记录
stop	Achievement	Patient + Result（状态转换）	停止流水线 → stopped 状态
configure	Accomplishment	Patient + Result + Config/Material	配置流水线 → 修改后配置
deploy	Accomplishment	Patient + Result + Target/Goal	部署流水线 → 部署产物
monitor	Activity	Patient + Duration + Target	监控流水线 → 监控数据流

用法：当你需要派生一个新子框架时——

查 Act 定值 → 上表得事件类型
事件类型给必有 FE 签名
继承父框架 FE
补签名要求的 FE
Qualia 补领域 FE
语料验证 + 同辈对比
核心性检验
整条链路从"不知道加什么 FE"变为"查表→补签名→qualia 补领域→验证"——FE 发现从猜测变为查表+验证。

总结：你需要的理论组合
理论
在派生中的角色
一步到位地解决
Vendler 事件类型学	Act 定值→事件类型→FE 签名	"该加哪些 FE"
FrameNet 继承规则	父子 FE 传递约束	"哪些必须继承、哪些可新增"
Pustejovsky Qualia	Patient 实体的属性维度→领域 FE	"领域特定的 FE 从哪来"
语料验证 + 同辈对比	经验校验 + 边界定义	"FE 是否完整、是否与兄弟区分"

四者缺一不可：Vendler 给骨架，继承给约束，Qualia 给血肉，语料给验证。单独用任何一个都不够——Vendler 不知领域细节，继承不知事件类型，Qualia 不知句法约束，语料不知理论签名。组合使用才能从"猜 FE"变为"推 FE"
