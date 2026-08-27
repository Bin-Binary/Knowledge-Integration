# 基于框架语义学和生成词汇学的垂直领域Agent工程实践POC
以"流水线"为激活词、通常激活实体、身份或抽象概念场景

## 基于生产语料分布观察
框架从使用中归纳出来，不要内省出来！！！(一段很长的痛苦经历)
*实践建议：先共现后划分，先提取高频搭配、扁平化词汇，先进行FE划分会因词元位置变化而导致FE变化*

**高频搭配**
[skill、执行、查询、创建、启动、pipeline_id、URL、分支、记录、联调、版本、配置]
[clouddrag、包、监控、链接、状态、个人、天舟、构建、group_id、闪存、25B、scheme]
[部署、查看、Dorado、环境、子系统、下载、成功、触发、error、结果、OceanStor、自动]
[停止、job_id、出包、MCP、产物、arm、工具、debug、脚本、被动、运行、执行方案、任务、MR]

**谓词提取 -> Action FE候选**
*"流水线"做受事*
[执行、创建、查询、启动、出包、配置、停止、监控、构建、部署、引用、获取]
*"流水线"做施事*
[成功、完成、通过、失败、结束、恢复、~正在~、运行、耗时、等待、~异常~、暂停、中断]

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

## 框架定义与FE清单
### 核心“通用”语义角色（FE） -> 所有框架共用的非核心FE
在“先共现后划分”阶段，最容易被高频介词洗出来的非核心元素：
[Purpose（主观目的/意图）、Means（手段）、Patient（受事）、Time（时间）、Place（地点）、result(结果)、Condition（条件）]

!!! Purpose（主观目的/意图）不是Goal（空间、数据或状态终点）
    Purpose: 意图（Intentionality）。施事者心智中想要达成的宏观愿望
    Goal:    终点（Boundedness）。动作在空间、数据流或状态转移上的落脚点

### 常用语义框架总览
**Using（使用工具）**
*定义*: 用来刻画Agent（FrameNet场景下指"施事语义角色"）的使用工具达成目的
*Core FE*: [Agent/施事、Instrument/工具、Purpose/使用目的]
*高频词元(LUs)*: [use、utilize、employ、wield、leverage]

**Act**
*定义*: 用来刻画Agent行动方法
*Core FE*: [Agent/施事、Act、Means]
*高频词元(LUs)*: [act、conduct、perform、execute]

**Intentionally_act（意图性行动）**
*定义*: 用来刻画Agent带有意图的行动
*Core FE*: [Purpose/行动目的、Agent/施事、Act]
*Peripheral FE*：[Condition]

**Choosing（选择与决策）**
*定义*: 分析Agent的推理过程和控制流切换
*Core FE*: [Cognizer/施事、Chosen/被选中的策略/X、Alternatives/备选集/Y、Possibility/选择依据]

**Processing_materials**
*定义*: 用于描述系统输入、解析（Parse）和输出（Generate）的过程
*Core FE*: [Agent/施事、Material/输入原材料/Patient、Product/最终形态/Goal、Alterer/触发加工的组件]
*高频词元(LUs)*: [compile、process]

**Communication（信息传递）**
*定义*: 用于处理Agent与外部环境、API或其他Agent交互的语料
*Core FE*: [Communicator/发送方、Addressee/接收方、Message/传递的内容]
*高频词元(LUs)*: [send、pass、pull、push]

| 框架ID | 框架名(EN/ZH) | 类型 | 父框架 | 关系 | Core FE 数 |
|---|---|---|---|---|---|
| F0 | Intentionally_act/意图性行动 | 抽象父框架 | — | — | 4 |
| F1 | Pipeline_Operation/流水线操作  | 子框架 | F0 | inheritance | 4 |
| F2_Pipeline_Stopping | Pipeline_Stopping/流水线停止 | 子框架 | F0_Pipeline_Operation | inheritance | 4 |

### F0: Intentionally_act（流水线操作）

**定义**: 一个意图性行动框架：施事 Agent（Operator）对受事 Patient（Pipeline）执行某种自主性动作 Action，通过工具 Means（Scheme）在条件 Condition（Branch/Trigger/Version）下达成目标，并产生结果 Result（Outcome）。本框架为所有流水线操作子框架的抽象父框架，Action 不取定值。

**框架关系**: 顶层框架

**Core FE**:

| FE | 语义角色 | 填充物示例 |
|---|---|---|
| Operator | Agent/施事 | 用户、数字人、云龙(自动) |
| Pipeline | Patient/受事 | pipeline_id, 流水线URL, 流水线名称 |
| Action | Action/动作 | 启动/停止/执行/查询/创建/配置 |
| Outcome | Result/结果 | 成功/失败/运行中/等待/已停止 |
