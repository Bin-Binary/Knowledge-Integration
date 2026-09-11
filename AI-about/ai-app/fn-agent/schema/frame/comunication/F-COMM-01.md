# F-COMM-01 入口路由框架

> 版本：v1.2-draft | 状态：设计阶段
> 替代：F-COMM-00(已废弃)、F-COMM-01 v1.1-candidate(评估后退回)

## 1.定位与职责

入口路由框架——对话入口的意图分流器。每轮对话有且仅有一个F-COMM-01实例，职责是**判定话轮去向并产出路由结果**：

|路由结果|动作|激活框架?|
|---|---|---|
|phatic|礼貌回应|否|
|ood|引导回域内|否|
|in_domain|激活目标框架+前景化力量|是|

**不做的事：**
- 不承载域事件内容（无message嵌入，无frame嵌套）
- 不执行业务逻辑
- 不追踪执行结果

> 为什么只路由：F-COMM-00把控制面(路由)与数据面(事件承载)混装，导致需要embedding_depth/recursion_limit防递归、message既当路由信号又当内容容器。拆开后入口是路由器，域框架是事件本身，通过快照链`in_response_to`衔接而非嵌入，零递归风险。

## 2.转移图式

```
communicator --[utterance]--> addressee
     Agent         Theme         Goal
```

- **Agent**=communicator：发起方，INI缺省填充ENT-GUEST
- **Theme**=utterance：话轮原文，路由判定的输入（非事件载体）
- **Goal**=addressee：接收方，入口场景实例层缺省注入为系统自身

## 3.核心FE

### communicator
- 语义角色：Agent
- 类型：entity_ref
- 候选实体：ENT-HUMAN | ENT-SYSTEM | ENT-GROUP
- 缺省：INI(上游无信息)→ENT-GUEST
- qualia投射：Agentive（施成特质——谁发起的）
- note：qualia投射保留但入口层不依赖其推理，仅记录供下游域框架参考

### addressee
- 语义角色：Goal
- 类型：entity_ref
- 候选实体：ENT-HUMAN | ENT-SYSTEM | ENT-GROUP
- qualia投射：Telic（目的特质——对话指向谁）
- note：不限定system——转告场景Addressee=ENT-GROUP；入口场景"恒为自身"是实例层缺省注入，非类型约束

### utterance
- 语义角色：Theme
- 类型：string
- note：话轮原文，禁止拼接qualia。作为路由判定输入，不承载语义结构

> utterance取代F-COMM-00的message：message同时承载力量枚举和嵌入frame实例，违反单一职责。入口层只需原始文本做路由判定，语义结构由意图识别产出并直接落入驻域框架的intent快照。

## 4.外围FE

|FE|类型|说明|
|---|---|---|
|medium|entity_ref [ENT-SYSTEM, ENT-GROUP]|通信通道；qualia=Constitutive，决定force缺省解读(如IM通道更偏request)|
|topic|string|话题关键词，辅助路由判定|
|language|string|语言标识|
|source|entity_ref [ENT-HUMAN, ENT-SYSTEM]|转告链原始说话者(非communicator时使用)|

## 5.路由规则

入口框架唯一的行为逻辑——对话轮分类：

```
utterance → [路由判定] → routing_outcome ∈ {phatic, ood, in_domain}
```

### phatic（寒暄）
- 动作：respond
- 行为：礼貌回应，不激活框架，不调工具
- 实例：routing_outcome=phatic，force/target_frame_schema_id均无

### ood（越界）
- 动作：guide
- 行为：礼貌引导回域内，不激活框架，不调域工具
- 实例：routing_outcome=ood，force/target_frame_schema_id均无

### in_domain（域内）
- 动作：activate
- 行为：激活目标框架，按force选择执行路径
- 实例：routing_outcome=in_domain，force + target_frame_schema_id必填

> ood vs unclear的边界：ood="连域都不是"，直接引导；unclear="域内但信息不足"，激活澄清框架追问——二者不在同一判定层。unclear是in_domain下的力量，不是路由分支。

## 6.前景化操作

`routing_outcome=in_domain`时，路由结果附加前景化信息：

### force（力量类型）

|力量|执行路径|读写性|说明|
|---|---|---|---|
|request|执行子图|写|用户请求行动，选择工具/API完成任务|
|question|只读子图|读|检索/推断信息型答案，不执行有副作用的操作|
|statement|记录/确认|只写上下文|断言事实/状态，更新上下文即可|
|commitment|待办追踪|写意图|约束说话者自身未来行动，记录但不立即执行|
|unclear|澄清子图|读|域内但FE填充不足，激活澄清框架追问/确认|

force决定目标框架走哪条执行路径，是父图编排的核心输入（设计文档5.1编排主循环的分流依据）。

### target_frame_schema_id

激活的目标框架类型ID，如`03_quality_gate_create_schema`。

- force=unclear时，target为域内澄清/确认框架
- force=commitment时，target为F-COMM-01-Commitment（参见F-COMM-01-Commitment.md）

## 7.实例模板

每轮对话实例化一次。实例是入口框架的唯一产出，记录在快照链中。

### 必填字段
- frame_instance_id：uuid4
- frame_schema_id：const "F-COMM-01"
- communicator：Agent FE值
- utterance：原始话轮
- routing_outcome：phatic | ood | in_domain

### 条件必填
当routing_outcome=in_domain时：
- force：五种力量之一
- target_frame_schema_id：目标框架schema ID

### 可选字段
- in_response_to：前序入口实例ID（多轮对话链）
- addressee、medium、topic、language、source：外围FE
- created_at：ISO8601时间戳

### 快照链形态

```
[1] F-COMM-01#uuid-a   {utterance:"帮我搭门禁", routing_outcome:in_domain, force:request, target:03_quality_gate_create_schema}
[2] 03_quality_gate_create#uuid-b  {agent, patient, means, ...}  in_response_to=uuid-a
[3] 03_quality_gate_create#uuid-b  recorded {result:[...]}
```

- 快照[1]回答"路由了什么、前景化了哪个力量"
- 快照[2]回答"域事件具体是什么"
- in_response_to使二者双向追溯，无递归、无嵌入、无冗余

> 意图识别是跨两步的过程：(1)分类→落F-COMM-01实例；(2)FE填充→落域frame intent实例。入口框架只记录第一步，第二步自然落在被激活的域框架上。

## 8.与F-COMM-00的断裂点

|维度|F-COMM-00|F-COMM-01 v1.2|理由|
|---|---|---|---|
|message|oneOf(opaque/embedded frame)|删除→utterance|路由器不承载事件内容|
|框架嵌入|embedding_depth=2, recursion_limit|删除|入口与域框架是快照链相邻节点，非父子|
|force_dispatch|结构化(deontic/readonly/answer_linkage)|简化为force枚举+执行路径表|入口只需产出力量信号，结构化标记由父图在编排层消费|
|message_resolution|3态(force_resolved/pending_clarify/opaque_final)|删除→routing_outcome|路由结果取代力量解析状态|
|medium|core_fe + qualia=Constitutive|peripheral_fe + 保留qualia|入口层medium不参与路由核心逻辑，降为外围|
|unclear|路由分支|in_domain的force|域内信息不足≠越界，应激活澄清框架而非拒绝|

## 9.开放问题

> TODO: force=commitment的目标框架是否统一定义为F-COMM-01-Commitment，还是允许指向任意域框架（由该域框架自行处理commitment语义）？当前暂按统一指向F-COMM-01-Commitment。

> TODO: 多意图拆解（一句话含多个请求）——当前设计单实例单force，是否需要支持force为数组？暂按单一force，多意图由父图在意图识别阶段拆为多个F-COMM-01实例。

> TODO: routing判定是否需要置信度字段？若LLM判定"可能是phatic也可能是ood"，是否记录置信度供父图决策？暂不记录，判定逻辑内部消化，输出必须收敛为单一routing_outcome。
