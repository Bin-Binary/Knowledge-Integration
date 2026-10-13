# 概念
这个文档记录对框架语义学概念的理解
--

## 1 语义角色是什么

这里语义角色是对FE的理解
语义角色 → 把事件中形形色色的参与者，按其在事件意义中承担的功能归类后打上的标签
FrameNet的语义角色 = 框架元素（Frame Element, FE）
**下文的""场景""指框架实例，子场景指子框架实例**

### 1.1 语义（Semantics）是什么意思？

简而言之，语义就是“符号背后所代表的意思、概念和思想”。
• 文字和声音只是符号（比如拼音“shǔi”或者字形“水”），它们本身没有生命。
• 当这些符号映射到我们大脑中，让我们知道它指的是“一种无色无味、可以喝的液体”时，这个**背后所代表的意思、概念和思想，就是语义**
• 一句话总结： 语义解决的是“这个词、这句话到底在说什么”的问题。

### 1.2 角色（Role）是什么意思？
角色 → 在一个事件/场景中，参与者所扮演的功能位置，即"干什么的、起什么作用"


### 1.3 逻辑链
FE角色固定 → 填充对象自带语义 → 不同填充激活不同场景 → 框架:场景 = 1:N

### 1.4 一个例子
例如根据官方语料自定义构建的Python内置对象中的内建类型框架有以下FE：
类型集合（核心）；字面量形式（核心）；语义约束（核心）；核心地位（外围）。
刻画了Python内建事件场景，类型集合包含的语义包括数据类型、协议类型、类型构建类型

当"str"填充【类型集合】语义角色时，是数据类型场景、此时代表的语义是文本序列
当"int、float、complex"填充【类型集合】语义角色时，是数据类型场景、此时代表的语义是数字类型
当"迭代器"填充【类型集合】语义角色时，是协议类型场景、此时代表的语义是约定

### 1.5 总结的理解
**FE的填充对象本身可能自带语义**
填充对象本身可能就是一个独立的认知实体，自带一套完整的属性和行为特征。例如：
当str、dict或迭代器填充【类型集合】语义角色时，它们各自在Python里已经自带了“不可变序列”、“哈希表”或“协议流”的原生语义

**单FE只决定局部语义**
单FE填充决定该槽的局部语义，并可能代表不同的子场景、即可能触发子框架路由。例如只看【类型集合】一个FE的填充：
"str"填充 → 该槽局部语义：文本序列类型
"int、float、complex"填充 → 该槽局部语义：数字类型
"迭代器"填充 → 该槽局部语义：行为协议约定

**场景是联合涌现**
场景是全部核心FE联合填充（叠加填充对象本身自带的语义）的涌现结果
str→【类型集合】＋''…''→【字面量形式】＋序列约束→【语义约束】⇒ 涌现【文本序列场景】
迭代器→【类型集合】 ⇒ 触发子框架路由至【协议契约】

**框架和场景的关系是 1：N，由FE的填充对象激活不同场景**。
一个高阶框架（如【内建类型框架】）是一个宏观的“全景”，它可能包含了N种子场景。
不同填充对象可能路由到不同子框架，或作为实例变体留在本框架;
此外，同一填充对象的语义也可能随时间演变（如Python 3.7后dict从无序变为有序），激活不同的场景快照

**FE的语义角色定义固定，但填充对象的变化可能刻画不同的语义、从而表示不同的场景**，
角色的职能定义是固定槽位，但因为填充对象本身（可能自带语义），不同填充对象本身在履行相同职能时，可能刻画完全不同的场景。

例如： 
【类型集合】的语义角色定义是固定的 —— 承载Python运行时的具体类型实体
- str自带 “文本序列语义”，刻画的是 [数据表示场景]
- 迭代器自带 “惰性求值语义”，刻画的是 [行为协议场景]

### 一个框架的遇到的“场景爆炸与枚举困境”怎么办
当一个高阶框架（如【内建类型框架】）理论上可以映射出无数个动态场景，但在实际落地时不可能得到[水果框架]那样的具备高度统一的高阶框架。
此外，该高阶框架可能是有某个父框架，（如【内建类型框架】的父框架可能是【解释器框架】）。
从不完美的"元场景生成"-> 按需生成不完美的"派生场景"开始；无法描述时向上抽象，使用框架间关系关联。

### 场景怎么生成

这里场景包含两个意思：
1. 只关注FE语义定义的元场景，此时场景刻画的是框架自身的语义，而不指向任何具体填充对象。
2. 以及关注填充对象本身自带的语义的派生场景，此时场景刻画的是框架自身的语义叠加填充对象的语义，形成一个新的场景。
**两种实例化形态对照**
| | 元场景 | 派生场景 |
|---|---|---|
| 刻画对象 | 框架本身 | 填充对象——它在这个场景里是什么 |
| 认知行为 | 检索/规划（装载知识） | 识别/理解（执行填充） |
| 数学形态 | 场景**空间**（全部可能场景的集合） | 场景**点**（空间中一个实例） |

### 元场景：
生成不完美的"元场景"

**怎么对FE/框架进行高质量的职能定义**
向上抽象
直接描述说不清时，先向上抽象到认知上位，获得通用职责描述，再向下具体化回本FE。
上位标签是认知脚手架——帮人够到职责描述；够到后拆掉，FE名称和最终描述都是自己的，不保留上位标签。

```markdown
你是框架语义学专家，你被委派：

A.对某框架中的所有FE进行定义高质量的职能定义。
你决定：
1.先整体审视所有FE以获取全局认知
2.初步定义每个FE
3.你进行了思考，对每个FE向上抽象到认知上位，获得通用且高质量的职责描述 (你的工作经验告诉你这是有必要且可能重复多次的，但你知道，抽象到"够用"就行.
上位标签是认知脚手架——能帮助够到职责描述)
4.向下具体化回本FE。FE名称没有改变但此时FE的职能定义是高质量的，你选择了在高质量洁癖和"够用"间保持了平衡。
5.你习惯性地记录下了你此次的工作内容(
[xxx框架]的核心FE及其职能定义：
- 【xxxx】↑抽象→ xxx（xxx）→↓具体化→ xxx
- 【xxxx】↑抽象→ xxx（xxx）→↓具体化→ xxx
- 【xxxx】↑抽象→ xxx（xxx）→↓具体化→ xxx
)；通常情况下你会将该笔记放到了委派方指定的路径下；但有时出于限制，你只能将你的笔记内容告诉你的委托方。

B. 对某框架进行高质量的职能定义。
你决定：
1.整体审视你之前对该框架的高质量FE职能定义笔记
2.你做了一次轻度思考，你选择了在高质量洁癖和"够用"间保持平衡
3.你在你的笔记中找到了"[xxx框架]的核心FE及其职能定义"那一段，并在它的结尾追加了对该框架的职能定义
4.通常情况下你会将该笔记放到了委派方指定的路径下；但有时出于限制，你只能将你的笔记内容告诉你的委托方。
```

A:
[内建类型框架]的核心FE及其职能定义：
- 【类型集合】↑抽象→ 核心主体（负责承载实体的功能位置）→↓具体化→ 负责承载Python内建类型实体的功能位置
- 【字面量形式】↑抽象→ 表现符号（负责编译/展现的形式）→↓具体化→ 负责内建类型字面量语法的编译期实例化通道
- 【语义约束】↑抽象→ 边界判定（负责真伪与安全的护栏）→↓具体化→ 负责内建类型行为规范的约束

B:
元场景语义：从Python解释器视角刻画了不同功能的类，如何被实例化以及需要遵循哪些行为规范约束。

### 派生场景：
基于不完美的"元场景"，生成不完美的"派生场景"

1.从语料提取填充对象的自带语义：
```markdown
你是语言学家，你需要根据用户对语义的理解出发，从用户提供的一个主题（语料来源：用户直接提供语料/用户直接提供一个URL/你自己查找官方权威的文档）提取该主题的语义。
已知用户对语义的理解为：
"语义就是“符号背后所代表的意思、概念和思想”。
• 文字和声音只是符号（比如拼音“shǔi”或者字形“水”），它们本身没有生命。
• 当这些符号映射到我们大脑中，让我们知道它指的是“一种无色无味、可以喝的液体”时，这个**背后所代表的意思、概念和思想，就是语义**
• 一句话总结： 语义解决的是“这个词、这句话到底在说什么”的问题。

输出markdown文件（{主题}_semantic.md）/可直接复制的markdown文本（如果你不能直接输出文件），风格为原子风格，格式为：
- [{语料事实1}]({原文连接1}) -> {语义1}  
- [{语料事实2}]({原文连接2}) -> {语义2}
- .....
- [{语料事实n}]({原文连接n}) -> {语义n}

{主题}语义总集: {语义1}, {语义2}, ..., {语义n}

差的示例：
- [Lists are mutable sequences, typically used to store collections of homogeneous items (where the precise degree of similarity will vary by application).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> list 的语义是：一种可变的序列，通常用来存储同一类（或相似）元素的集合。 这里“符号”是 list 这个词，它背后代表的概念是“有顺序、可修改的容器”，而不是数学意义上的“列表”或日常用语中的“清单”。

- [Lists may be constructed in several ways: Using a pair of square brackets to denote the empty list: []; Using square brackets, separating items with commas: [a], [a, b, c]; Using a list comprehension: [x for x in iterable]; Using the type constructor: list() or list(iterable) ](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) ->  list 的语义还包含“可通过多种符号形式构造”这一层意思。 方括号 []、逗号分隔、列表推导式、类型构造器 list()，这些符号形式背后都指向同一个概念：一个按顺序排列的元素集合。

- [The constructor builds a list whose items are the same and in the same order as iterable's items. iterable may be either a sequence, a container that supports iteration, or an iterator object. If iterable is already a list, a copy is made and returned, similar to iterable[:]. ](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) ->  list 的语义是“从可迭代对象构建、保持元素顺序、并且对已有 list 会复制而非共享”。 这解决的是“list(iterable) 到底在说什么”的问题：它说的是“把 iterable 里的东西按原顺序装进一个新 list”。

好的示例：
- [Lists are mutable sequences, typically used to store collections of homogeneous items (where the precise degree of similarity will vary by application).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 序列、可变、容器

- [Lists may be constructed in several ways:](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 构造、多入口

- [Using a pair of square brackets to denote the empty list: [] ](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 字面量、空容器

- [Using a list comprehension: [x for x in iterable] ](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 推导式、逐项生成

- [Using the type constructor: list() or list(iterable)](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 构造器、转换

- [The constructor builds a list whose items are the same and in the same order as iterable's items.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 同项、保序、收集

- [iterable may be either another sequence, a container that supports iteration, or an iterator object.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 可迭代、鸭子类型

- [If iterable is already a list, a copy is made and returned, similar to iterable[:].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 副本、新对象

- [If iterable is already a list, a copy is made and returned, similar to iterable[:].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 副本、新对象

- [For example, list('abc') returns ['a', 'b', 'c'] and list((1, 2, 3)) returns [1, 2, 3].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 逐项、拆分

- [If no argument is given, the constructor creates a new, empty list [].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 空容器

- [Many other operations also produce lists, including the sorted() built-in function.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 默认结果容器

- [Lists implement all of the common and mutable sequence operations.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 全能序列、读、写

- [Lists also provide the following additional method: sort(*, key=None, reverse=None)](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 原地排序、仅限关键字参数

- [This method sorts the list in place, using only < comparisons between items.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 原地、全序

- [Exceptions are not suppressed - if any comparison operation fails, the entire sort operation will fail (and the list will likely be left in a partially modified state). ](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 异常传播、整体失败、非原子性

- [key specifies a function of one argument that is used to extract a comparison key from each list element (for example, key=str.lower).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 比较键、投影

- [The key corresponding to each item in the list will be calculated once and then used for the entire sorting process.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 一次性计算

- [The default value, None, means that list items are sorted directly without calculating a separate key value.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 元素即键

- [reverse is a boolean value. If set to True, then the list elements are sorted as if each comparison were reversed.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 反转比较、降序

- [This method modifies the sequence in place for economy of space when sorting a large sequence.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 原地、空间效率

- [To remind users that it operates by side effect, it does not return the sorted sequence (use sorted() to construct a new sorted list from an iterable).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 副作用、无返回值、sorted() 替代

- [The sort() method is guaranteed to be stable.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 稳定、相等保序

- [CPython implementation detail: While a list is being sorted, the effect of attempting to mutate, or even inspect, the list is undefined.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 实现细节、未定义行为、读写禁区

list语义总集：序列、可变、容器、字面量、推导式、构造器、保序、副本、鸭子类型、全能序列、原地、投影、稳定、副作用、未定义行为 

约束：
1. 禁止将示例直接作为输出
2. 语义去重：不能输出重复的语义
3. 禁止长语句描述：不能输出过长的语义描述，保持语义的简洁性

```
2. 语义选取
语义切片：使用FE的职能定义作为筛子从对象的语义总集中选取语义。
- 【类型集合】负责承载Python内建类型实体的功能位置 -> list语义总集 -> 序列、容器、副本、全能序列
- 【字面量形式】负责内建类型字面量语法的编译期无需构造器的实例化 -> list语义总集 -> 字面量、推导式、构造器、副本、原地、副作用
- 【语义约束】负责内建类型行为规范的约束 -> 可变、推导式、构造器、保序、鸭子类型、投影、稳定、未定义行为 

3. 从语料再挖掘场景
   - 代码：找填充对象的函数/方法
   - 文档：找填充对象的'谓词'描述
例如：list的






