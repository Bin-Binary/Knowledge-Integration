**Check（检查）**
*定义*: 刻画是否存在检查(引导Agent某些事件必须检查)/事件结果是否符合指标，适用：子事件是同质的、无内部结构、只关心存在/计数
*Core FE*: [Check/检查、Mertric/指标、Event/事件]
*Peripheral FE*：[Distributive/分配、Collective/累积]
*高频词元(LUs)*: [check、verify、validate、test、audit]
*Distributive*: 检查语义作用于每个事件 -> 每项指标都达标
*Collective*: 检查语义作用于整体事件集 -> N项中 ≥ M项通过即放行

Check（检查框架）
│
├── 框架关系: New
├── Act FE 定值: None
├── 事件类型: None
│
├── Core FE:
│   ├── Check/检查          (NEW) 填充约束: 检查本身
│   ├── Mertric/指标        (NEW) 填充约束: Set<SoA>, mertric1...mertricN（指标集合ID）
│   └── Event/事件          (inherited) 填充约束: Set<SoA>, evnt1...eventN（被检查的事件集）
│
├── Peripheral FE:
│   ├── Distributive/分配   (NEW) 填充约束: ???
│   └── Configuration/配置   (NEW, qualia Constitutive) 填充约束: ???
│
└── 高频词元: 检查、验证、测试、审核、达标
**Choosing（选择）**
*定义*: 刻画认知者从备选项中选出一个。
*Core FE*: [Cognizer/认知者、Chosen/被选中的、Alternatives/备选集]
*Peripheral FE*: [Basis/选择依据、Manner/方式、Purpose/选择目的]
*高频词元(LUs)*: [choose、select、pick、decide、opt、elect、prefer]

**Check_choosing（检查选择）**
*定义*: 刻画是某些事件否存在选择/选择是否符合指标、适用：事件中必须存在选择、选择结果必须符合指标
*Core FE*: [Check/检查、Mertric/指标、Event/事件、Cognizer/认知者、Chosen/被选中的、Alternatives/备选集]
*Peripheral FE*：[Distributive/分配、Collective/累积、Basis/选择依据、Manner/方式、Purpose/选择目的]
*高频词元(LUs)*: [choose、select、pick、decide、opt、elect、prefer]

Check_choosing（检查选择）
│
├── 框架关系: 继承Check
├── Act FE 定值: None
├── 事件类型: None
│
├── Core FE:
│   ├── Check/检查            (inherited) 填充约束: 检查本身
│   ├── Mertric/指标          (inherited) 填充约束: Set<SoA>, mertric1...mertricN（指标集合ID）
│   ├── Check/检查            (inherited) 填充约束: 检查本身
│   ├── Cognizer/认知者       (inherited) 填充约束: 包含/可获取Mertric的实体/角色
│   ├── Chosen/被选中的       (inherited) 填充约束: Set<SoA>, chosen1...chosenN（被选中的选项集）
│   └── Alternatives/备选集   (inherited) 填充约束: Set<SoA>, alternatives1...alternativesN（备选项选项集）
│
├── Peripheral FE:
│   ├── Distributive/分配   (NEW) 填充约束: ???
│   ├── Basis/选择依据       (inherited) 填充约束: 团队习惯/约束
│   ├── Manner/方式         (inherited) 填充约束: None
│   ├── Purpose/选择目的       (inherited) 填充约束: 团队目标/需求
│   └── Configuration/配置   (NEW, qualia Constitutive) 填充约束: ???
│
└── 高频词元: 