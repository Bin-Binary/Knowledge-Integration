---
# 基于框架语义学和生成词汇学的垂直领域Agent工程实践POC
核心思想: 从官方文档/生产日志抽取先建立基线Frame、持续使用真实语料迭代FrameNet
---
以"流水线"为激活词、通常激活实体、身份或抽象概念场景

## 基于生产语料分布观察
框架从使用中归纳出来，不要内省出来！！！(一段很长的痛苦经历)
*实践建议：先共现后划分，先提取高频搭配、扁平化词汇，先做FE划分会因词元位置变化导致FE漂移*

**高频搭配**
从原始语料统计，提取高频二元/三元搭配：谓词‑名词、谓词‑副词、谓词‑介词搭配，用来做后续LU、FE候选的种子，过滤噪声，筛选有框架唤起能力的搭配

交给AI处理，以下为提示词：
```markdown
你是高频搭配提取专家，你精通统计学和文本分析的理论。
擅长从文本中提取高频搭配。
你的任务是基于用户提供的原始语料、从原始语料中挖掘高频句法搭配，优先提取【谓词‑名词、谓词‑介词、谓词‑副词】，
并输出结构化表格到: ./references/corpus_processing/corpus_{时间戳}.md
约束：
1. 说明中内容仅为格式示范，搭配对和代表性例句必须从{原始语料}中提取，不得照搬样例
2. 输入槽位 {}、必须被真实内容替换
3. 仅输出下三张Markdown表格，不要添加解释或前言
4. 过滤无意义虚词、停用词
5. 只输出有实际语义的搭配，不要输出孤立词语
6. 时间戳精确到hour即可

以下为输出格式:
## 高频搭配提取
**高频搭配**
> 从原始语料统计，提取高频二元/三元搭配：谓词‑名词、谓词‑副词、谓词‑介词搭配，用来做后续LU、FE候选的种子，过滤噪声，筛选有框架唤起能力的搭配

*谓词‑名词*
| 搭配对 | 粗略共现频次 | 代表性例句 |
| :--- | :--- | :--- |
| {搭配对1} | {times1} | {example1} |

说明: 
    **关于谓词‑名词搭配表占位符说明**：
        搭配对1: 谓词‑名词
        times1: 粗略共现频次
        example1: 代表性例句

*谓词‑副词*
| 搭配对 | 粗略共现频次 | 代表性例句 |
| :--- | :--- | :--- |
| {搭配对2} | {times2} | {example2} |

说明: 
    **关于谓词‑副词搭配表占位符说明**：
        搭配对2: 谓词‑副词
        times2: 粗略共现频次
        example2: 代表性例句

*谓词‑介词*
| 搭配对 | 粗略共现频次 | 代表性例句 |
| :--- | :--- | :--- |
| {搭配对3} | {times3} | {example3} |

说明: 
    **关于谓词‑介词搭配表占位符说明**：
        搭配对3: 谓词‑介词
        times3: 粗略共现频次
        example3: 代表性例句

以下是原始语料 {原始语料}

```

例如：
从生产环境中清洗后得到作为候选FE的语料：


**谓词提取 -> Action FE候选**
识别高频搭配结果中承担事件/动作核心的谓词（动词、状态形容词）；针对每个谓词，提取句法邻接、参与该动作事件的短语，作为Action FE（动作框架元素）候选集合；仅输出候选，不做最终框架判定

交给AI处理，以下为提示词：
```markdown
你是谓词与框架元素候选提取专家，精通框架语义学、句法分析。
擅长从高频搭配结果中提取核心谓词并生成Action FE候选集合。
你的任务是基于高频搭配中间结果，从搭配对、代表性例句中识别核心谓词；围绕识别出的谓词，提取参与动作事件的短语作为Action FE候选；并追加输出结构化表格到: ./references/corpus_processing/corpus_{时间戳}.md
约束：
【重要生产实践约束】
所有输出仅作为后续归纳框架的原始候选素材
1. 谓词、Action FE候选、原句片段必须全部取自高频搭配中间结果内部的搭配与例句，不得引入外部文本，不得编造，不得照搬样例。
2. 输入槽位 {}、必须被真实内容替换。
3. 仅输出规定Markdown内容，不要添加解释、前言、思考过程。
4. 过滤修饰性定语、无关插入语、语气词；优先动作参与者、对象、目标、源点、终点类短语。
5. 只输出有实际语义的谓词与FE候选，过滤无意义成分。

输出格式:
## 谓词提取‑Action FE候选
**谓词提取 -> Action FE候选**
> 识别高频搭配结果中承担事件/动作核心的谓词（动词、状态形容词）；针对每个谓词，提取句法邻接、参与该动作事件的短语，作为Action FE（动作框架元素）候选集合；仅输出候选，不做最终框架判定

*谓词‑Action FE候选映射表*
| 原句片段 | 核心谓词 | Action FE候选清单 |
| :--- | :--- | :--- |
| {sent1} | {pred1} | {fe_candidate_1} |

说明: 
    **关于谓词‑Action FE候选映射表占位符说明**：
        sent1: 取自高频搭配中间结果内的代表性例句片段
        pred1: 识别得到的核心谓词
        fe_candidate_1: 多个FE候选使用分号;分隔

以下是高频搭配中间结果：{高频搭配中间结果}

```

!!! 在实践操作中犯了错误
    "流水线成功"中，流水线是语法主语，但语义角色是Entity（处于某状态的实体），不是Agent（有意行动的施事）

**邻接论元候选清单**
基于高频搭配结果，找出与目标谓词/LU直接关联的论元短语（主语、宾语、介宾成分等）；剔除修饰成分；输出句法层面论元候选集合，不做语义角色最终判定

交给AI处理，以下为提示词：
```markdown
你是句法论元抽取专家，精通依存句法、论元结构分析。
擅长基于高频搭配结果内的谓词/LU提取句法邻接的论元候选。
你的任务是基于高频搭配中间结果，针对搭配中出现的谓词/LU，找出句法直接关联的论元短语，产出邻接论元候选清单；并追加输出结构化表格到: ./references/corpus_processing/corpus_{时间戳}.md

约束：
【重要生产实践约束】
框架必须从真实语料使用中归纳，禁止内省式空想定义框架、FE、LU。

1. 论元候选、原句片段必须全部取自{高频搭配中间结果}内部的搭配与例句，不得引入外部文本，不得编造，不得照搬样例。
2. 输入槽位 {}、必须被真实内容替换。
3. 仅输出规定Markdown内容，不要添加解释、前言、思考过程。
4. 剔除单纯定语、语气词、插入语；只保留主语、宾语、介宾等论元成分。
5. 每条候选附带简要句法位置标记；只输出有实际语义的论元候选。

输出格式:
## 邻接论元候选清单
**邻接论元候选清单**
> 基于高频搭配结果，找出与目标谓词/LU直接关联的论元短语（主语、宾语、介宾成分等）；剔除修饰成分；输出句法层面论元候选集合，不做语义角色最终判定。

*邻接论元候选表*
| 目标单元(谓词/LU) | 原句片段 | 邻接论元候选[句法位置] |
| :--- | :--- | :--- |
| {unit1} | {sent1} | {arg_candidate_1} |

说明: 
    **关于邻接论元候选表占位符说明**：
        unit1: 来自高频搭配的目标谓词或者LU词汇单元
        sent1: 取自高频搭配中间结果内的代表性例句片段
        arg_candidate_1: 候选短语[句法位置]，多个候选使用分号;分隔；句法位置：主语/宾语/介宾

以下是高频搭配中间结果：{高频搭配中间结果}
```

[分支、pipeline_id、版本、group_id、job_id、执行方案、service_id、scheme_id]
*论元结构是连接核心事件（语义面）与句子外壳（句法面）的桥梁*
*必须是该事件发生不可或缺的参与者（Core Arguments），不出现则意义彻底改变*

**对比构式中的对照词 -> 邻接LU候选**
扫描高频搭配结果内的例句，识别X vs Y类对比构式（A比B、A相较于B、A而不是B、A胜过B等）；定位构式对照位置X、Y上的对照词/短语，作为邻接LU（词汇单元）候选集合；无对比构式则标记无

交给AI处理，以下为提示词：
```markdown
你是构式语义分析专家，精通对比构式识别、FrameNet词汇单元LU候选挖掘。
擅长从高频搭配结果的例句中识别X vs Y类对比句式，提取对照位置词汇生成邻接LU候选。
你的任务是基于上一步产出的【高频搭配中间结果】，扫描其内部代表性例句，识别对比构式，定位X、Y对照位置短语，生成邻接LU候选集合；并追加输出结构化表格到: ./references/corpus_processing/corpus_{时间戳}.md

约束：
【重要生产实践约束】
框架必须从真实语料使用中归纳，禁止内省式空想定义框架、FE、LU。
遵循：先共现后划分；本阶段只产出各类候选集合，**禁止执行正式FE划分、禁止框架匹配、禁止分配框架名称**；过早进行FE划分会因为词元句法位置变化引发FE漂移。所有输出仅作为后续归纳框架的原始候选素材。

1. 构式判定、对照词、原句片段必须全部取自高频搭配中间结果内部的搭配与例句，不得引入外部文本，不得编造，不得照搬样例
2. 输入槽位 {}、必须被真实内容替换。
3. 仅输出规定Markdown内容，不要添加解释、前言、思考过程。
4. 在高频搭配例句中无对比构式时，对照位置与LU候选字段填写“无”。
5. LU候选为可能唤起框架的词汇单元候选，不做最终LU判定。

输出格式:
## 对比构式‑邻接LU候选
**对比构式(X vs Y句式)中的对照词 -> 邻接LU候选**
> 扫描高频搭配结果内的例句，识别X vs Y类对比构式（A比B、A相较于B、A而不是B、A胜过B等）；定位构式对照位置X、Y上的对照词/短语，作为邻接LU（词汇单元）候选集合；无对比构式则标记无。

*对比构式‑邻接LU候选表*
| 原句片段 | 构式类型 | 对照位置X | 对照位置Y | 邻接LU候选 |
| :--- | :--- | :--- | :--- | :--- |
| {sent1} | {constr_type1} | {x1} | {y1} | {lu_candidate_1} |

说明: 
    **关于对比构式‑邻接LU候选表占位符说明**：
        sent1: 取自高频搭配中间结果内的代表性例句片段
        constr_type1: 构式类型，如“A比B”；无对比构式填“无”
        x1: 对照位置X短语；无填“无”
        y1: 对照位置Y短语；无填“无”
        lu_candidate_1: 多个LU候选使用分号;分隔；无填“无”

以下是高频搭配中间结果：{高频搭配中间结果}

```

*X vs Y句式可以拉出一条对立或互补的语义轴*
*将共现的X和Y记录为强相关对偶节点 -> 自动联想或预测Y的存在*
*先共现后划分后，X vs Y加速FE的泛化和扩充*
*有些词汇在单独出现时含义模糊，但在X vs Y中语义会瞬间精确*
*对比构式拉出的语义轴（归属、自动化、粒度……），归入对应qualia维度*
*语义轴价值——它们可以作为流水线实体的属性维度（用Pustejovsky的qualia的属性组织来归类），也可以作为外围FE附加到具体子框架上*

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
---
## 框架定义与FE清单
*先基于生产语料分布观察候选出一般框架作为父类框架、再进一步根据候选FE派生出具体领域内框架*
*核心FE随层级递增：每往下一层，框架就多出若干核心FE——因为更具体的框架需要更多角色才能定义*
*这是框架语义学的核心设计原则：框架越具体，核心FE越多；框架越一般，核心FE越少（退化为框架本身 + 外围环境信息）*
例如：Event只需要一个核心FE（事件本身）；Intentionally_act需要四个（施事 + 行动 + 目的 + 手段）
---
## 难点
1. 选取品文档还是生产日志作为语料抽取基线？
2. 基线和迭代语料冲突怎么办？
3. 怎么进行迭代？

### 候选父类清单
Event
 ├── Process        （加 Duration 维度）
 ├── Change         （加 Entity + Initial/Final_state）
 └── Activity       （加 Agent + Activity）
      └── Intentionally_act  （加 Purpose + Means，意向性约束）

| 框架ID | 框架名(EN/ZH) | 类型 | 父框架 | 关系 | Core FE 数 |
|---|---|---|---|---|---|
| F0 | Intentionally_act/意图性行动框架| 抽象父框架 | — | — | 2 |
| F1 | Change/变化框架 | 抽象父框架 | — | — | 3 |
| F3 | Activity/活动框架| 抽象父框架 | — | — | 2 |
| F4 | State/状态框架| 抽象父框架 | — | — | 2 |

### 派生框架
*重要的实操建议：非必要不派生框架、除非候选FE*
从每个子框架继承Fn的全部FE，必须新增子框架专属FE（如F1增加基于模板Template FE；F2增加执行方案 Scheme FE为核心），
#### F0的派生框架
```
语义不能是无意向的习惯性行为，例如、启动流水线
```
##### F0_create: Create_pipeline（创建流水线）
**定义**: 施事(Operator)意图性地创建一条新的流水线(Pipeline)。'创建'隐含从无到有(genesis)——Pipeline作为Patient从不存在到存在的意图
**落地难点**:
1. 无法确定加哪些FE
2. 无法确认哪些FE必须继承、哪些可以新增
3. 无法确定Patient的Qualia驱动领域发现
**理论/方法**
[框架派生](./frame_derive.md)

**落地难点的理论/方法实操**
1. 决定FE签名
例如：当Act取'create'后进行特征分析后确定事件类型为'Accomplishment'，明确了当前框架有[Agent、Patient、Result、Material/Source]FE签名

2. 继承父框架 FE:
| 父 FE | 类型 | 子 FE 处理 |
|---|---|---|
| Agent | Core | 继承为核心；填充约束细化 → Human_operator |
| Act | Core | 继承为核心；取定值 = create |
| Purpose | Core | 继承为核心 |
| Means | Core | 继承为核心；填充约束细化 → Template/Scheme/Copy |
| Condition | Peripheral | 待定（step 6 重新分类） |
| Goal | Peripheral | 继承为外围 |
| Manner | Peripheral | 继承为外围 |

3. 按事件类型签名补FE
diff已继承的FE和事件类型签名FE:
| 签名要求的 FE | 是否已继承 | 处理 |
|---|---|---|
| Agent | ✓ 已继承 | — |
| Patient | ✗ 父框架没有 Patient | **新增为核心** |
| Result | ✗ 父框架没有 Result | **新增为核心** |
| Material/Source | ✗ 父框架没有 | **新增为核心**（领域映射为 Template） |

4. 用Qualia发现领域FE
对Patient做qualia分析，找出与Act相关的维度

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

例如对"创建流水线":
*Qualia分析*
| Quale | 属性 | 与执行(Act)相关？ | → 候选 FE |
| :--- | :--- | :--- | :--- |
| Formal | 流水线是可寻址的自动化发布单元（人造物），具有唯一标识（pipeline_id/URL）并按类型固定阶段链形态（如微服务型 Source→Build→Alpha→Beta→Gamma→Production；组合服务型 Assemble→Package→Iota→Kappa→Lambda→Production），归属于云龙服务，一个服务下可有多条流水线 | 同类别成员：作为流水线操作/执行框架的受事(Patient)，被启动/停止/查询/创建/配置 | Pipeline, PipelineType, LifecycleStage, Service |
| Constitutive | 由阶段(Stage)→Job→任务(Task)递归构成；阶段配置含阶段名称、阶段类型、是否默认运行/总是运行、超时时间、触发类型（手动/成功/失败/总是）、工作项串/并行；支持参数化定义、通知(notify)与子流水线引用 | 构成决定流水线可执行性与执行路径（触发条件、串/并行、超时中止整条流水线） | Stage, Job, Task, Trigger, ConfigItem, SubPipeline, Parameter |
| Telic | 服务于自动化发布链路：自动出包（编译构建+静态检查+测试）、通过平台接口任务发布、配置云龙部署任务自动部署；通过质量门禁（110+检查项）管控各阶段出口质量，满足可信构建（可视化/可追溯/可重复）要求 | 直接服务执行——执行是流水线发挥"出包→部署"功效的载体 | Artifact, Gate, Metric, EvaluationResult, Outcome |
| Agentive | 由创建行为实例化产生：单独创建/使用模板创建/代码化(Yaml)创建/复制流水线；也可由配置推送事件或MR触发自动创建，服务初始化(CloudInit)可初始化创建 | 创建者与推送事件源决定流水线何时进入可执行状态 | Operator, Template, ConfigRepo, TriggerSource, PipelineType |

*子事件分解*
| 子事件阶段 | 协同的Qualia维度 | 语义融合逻辑 (Why) | 最终确定的领域 FE |
| :--- | :--- | :--- | :--- |
| **$e_1$ (过程阶段)** | **Agentive (施成)** | 探究流水线"始发原因"：由谁/什么创建而生成（操作者手工创建 / 模板 / 代码化YAML / 配置推送事件自动创建 / 基于流水线复制） | Operator, Template, ConfigRepo, TriggerSource——FE: 创建者/创建方式 |
| **$e_1$ (过程阶段)** | **Constitutive (构成)** | 探究装配物料：哪些阶段/Job/任务、参数与触发规则被组装进流水线定义 | Stage, Job, Task, Parameter, TriggerType——FE: 装配物料 |
| **$e_2$ (状态阶段)** | **Formal (形式)** | 探究流水线如何被识别：系统必须赋予唯一流水线ID与类型并挂载阶段链，以区别于其他实体 | PipelineID, PipelineType, LifecycleStage——FE: 识别特征 |
| **$e_2$ (状态阶段)** | **Telic (目的)** | 探究流水线诞生后的"生存意义"：处于任务默认勾选就绪待触发、被启动运行、向下游产出并被质量门禁判定的状态 | DefaultRun, RunStatus, Trigger, GateResult, Artifact——FE: 待运行与产出状态 |

*新增候选FE*
Formal：[Pipeline、PipelineType、LifecycleStage、Service]
Constitutive：[Stage、Job、Task、Trigger、ConfigItem、SubPipeline、Parameter]
Telic：[Artifact、Gate、Metric、EvaluationResult、Outcome]
Agentive：[Operator、Template、ConfigRepo、TriggerSource、PipelineType]

5. 候选FE验证

*语料验证*：回到语料，检查"创建流水线"的共现词是否覆盖了上述FE
*问题*：尚未做新的语料抽取、此处先人工确认
交给AI处理、以下为提示词：
```markdown
你是数据分析专家。
你的任务是对语料进行验证，要求为：回到语料集，检查激活词的共现词是否覆盖了上述FE。将结果结构化输出表格到: ./frame_net/frame/sub_frame_{name}/debug/candidate_fe_verification.md
约束：
1. 说明中内容仅为格式示范，属性和候选FE必须从{文档内容}中提取，不得照搬样例，除非文档确证相同语义
2. 输入槽位 {}、必须被真实内容替换
3. 仅输出下述一张Markdown表格，不要添加解释或前言

以下为输出格式:
| 候选 FE | 语料中的共现词 | 验证 |
| :--- | :--- | :--- |
例如：
| 候选 FE | 语料中的共现词 | 验证 |
| :--- | :--- | :--- |
| Pipeline | 人工确认 | ✓ |
| PipelineType | 人工确认 | ✓ |
| LifecycleStage | 人工确认 | ✓ |
....

```

*子框架对比*：把{sub_frame_{name}}与兄弟子框架并列，找出独有FE
交给AI处理、以下为提示词：
```markdown
你是边界定义专家。
你的任务是：把{sub_frame_{name}}与兄弟子框架并列，找出独有FE。将结果结构化追加输出表格到: ./frame_net/frame/{sub_frame_name}/debug/candidate_fe_verification.md的末尾
约束：
1. 例子中内容仅为格式示范，属性和候选FE必须从{文档内容}中提取，不得照搬样例，除非文档确证相同语义
2. 输入槽位 {}、必须被真实内容替换
3. 仅输出下述一张Markdown表格 + 发现，不要添加解释或前言

以下为输出格式:
*子框架对比*
| FE | {sub_frame_name} | {sub_frame_name_contrast} |
| :--- | :--- | :--- |
*发现*
[{FE_0}、{FE_1}、...、{FE_N}]是"{sub_frame_name}"独有的核心FE——因为没有[{FE_0}、{FE_1}、...、{FE_N}]，"{fe_name}"行为无法完成

例如：
*子框架对比*
| FE | create_frame | execute_frame | 
| :--- | :--- | :--- |
| Template | ✓ 核心 | ✗ |
| Pipeline_name | ✓ 核心 | ✗（用已有 ID）|
| Result（新实体）| ✓ 核心（新建的 pipeline） | △（执行结果）|
| Scheme | △ 外围 | ✓ 核心 |
...

*发现*
Template和Pipeline_name是Create独有的核心FE——因为没有模板和名称，"创建"行为无法完成。

....

```

6. 核心性重新分类
*问题*: 无检验标准、更倾向使用实际的生产语料 + anget自执行判断；如选后者、提示词也需要修改
对全部FE（继承 + 新增）做三项检验
交给AI处理、以下为提示词：
```markdown
你是分类专家。
你的任务是对{./frame_net/frame/{sub_frame_name}/debug/candidate_fe_verification.md}中的候选FE进行检验后分类，要求为：对全部FE（继承 + 新增）做三项检验。将结果结构化追加输出到: ./frame_net/frame/sub_frame_{name}/debug/candidate_fe_verification.md
约束：
1. 说明中内容仅为格式示范，属性和候选FE必须从{文档内容}中提取，不得照搬样例，除非文档确证相同语义
2. 输入槽位 {}、必须被真实内容替换
3. 仅输出下述一张Markdown表格，不要添加解释或前言

以下为输出格式:
| FE | 来源 | 必要性 | 句法必选 | 框架特有 | 判定 |
| :--- | :--- | :--- | :--- | :--- | :--- |
例如：
| FE | 来源 | 必要性 | 句法必选 | 框架特有 | 判定 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Agent | 继承 | ✓无施事则无创建 | ✓ | ✓ | Core |
| Patient | 新增（事件类型）| ✓ 无流水线则无创建 | ✓ | ✓ | Core |
| Template | 新增（qualia）| △ 模板可选 | △ | ✓ Create 独有 | Peripheral |
....

```
**Core FE**:
| FE | 语义角色 | 填充物示例 |
| operator | Agent/施事 |---| 
| crate | Act/行动 | "创建流水线" |
| {fill} | Purpose/行动目的 |---|
| {fill} | Means/手段 |---|
| Pipeline | Patient |---|
| Pipeline | Result |---|
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
