# Python内建对象体系 FrameNet 语义框架标注文档
> 文档结构：##说明 → ##原文和翻译 → ##事实 → ##缺口 → ##误解 → ##Python内建对象体系框架 → ##Python内建对象体系框架间关系

## 说明
1. 本文件基于Python 3.14官方文档 builtins/index.txt，采用**FrameNet框架语义学**进行建模。
2. 框架元素FE为抽象语义槽；**事实为槽填充客观内容；缺口是从原始语料推导出来的知识缺失点；误解是基于语料推导的学习者可能产生的错误理解**。
3. 原文与翻译一一对应，原文后紧跟中文翻译；
4. 框架关系使用FrameNet标准9种关系标签：`Inheritance`、`Perspective on`、`Using`、`Subframe`、`Precedes`、`Causative of`、`Inchoative of`、`Metaphor`、`See also`；
5. 原始语料定位记录原文出处、片段位置与参考链接。

## 原文和翻译
> 来源：Python 3.14 官方文档 — Built-in Functions (https://docs.python.org/3.14/library/builtins.html)

1.
> Original: Python comes with a number of built-in functions and classes.
> 翻译：Python附带若干内建函数和内建类。

2.
> Original: The built-in classes include data types that would normally be considered part of the "core" of a language, such as numbers and lists. For these types, the Python language core defines the form of literals and places some constraints on their semantics, but does not fully define the semantics.
> 翻译：内建类包括通常被视为语言"核心"部分的数据类型，如数字和列表。对于这些类型，Python语言核心定义了字面量的形式并对其语义施加了一些约束，但并未完全定义其语义。

3.
> Original: The built-ins also include functions and exceptions --- objects that can be used by all Python code without the need of an "import" statement. Some of these are defined by the core language, but many are not essential for the core semantics and are only described here.
> 翻译：内建对象还包括函数和异常——所有Python代码无需"import"语句即可使用的对象。其中一部分由核心语言定义，但许多对核心语义并非必需，仅在此处描述。

4.
> Original: In addition to the built-ins, Python provides an extensive importable standard library, see The Python standard library.
> 翻译：除内建对象外，Python还提供可导入的标准库，见Python标准库。

5.
> Original: [Built-in Types 章节] Truth Value Testing; Boolean Operations --- "and", "or", "not"; Comparisons; Numeric Types --- "int", "float", "complex"; Boolean Type - "bool"; Iterator Types; Sequence Types --- "list", "tuple", "range"; Text and Binary Sequence Type Methods Summary; Text Sequence Type --- "str"; Binary Sequence Types --- "bytes", "bytearray", "memoryview"; Set Types --- "set", "frozenset"; Mapping Types --- "dict"; Context Manager Types; Type Annotation Types --- Generic Alias, Union; Other Built-in Types; Special Attributes; Integer string conversion length limitation.
> 翻译：[内建类型章节] 真值测试；布尔运算——"and"、"or"、"not"；比较；数值类型——"int"、"float"、"complex"；布尔类型——"bool"；迭代器类型；序列类型——"list"、"tuple"、"range"；文本与二进制序列类型方法摘要；文本序列类型——"str"；二进制序列类型——"bytes"、"bytearray"、"memoryview"；集合类型——"set"、"frozenset"；映射类型——"dict"；上下文管理器类型；类型注解类型——泛型别名、联合类型；其他内建类型；特殊属性；整数字符串转换长度限制。

6.
> Original: Built-in Constants [及子项] Constants added by the "site" module.
> 翻译：内建常量[及子项] 由"site"模块添加的常量。

7.
> Original: Built-in Functions.
> 翻译：内建函数。

8.
> Original: Built-in Exceptions [及子项] Exception context; Inheriting from built-in exceptions; Base classes; Concrete exceptions; Warnings; Exception groups; Exception hierarchy.
> 翻译：内建异常[及子项] 异常上下文；继承自内建异常；基类；具体异常；警告；异常组；异常层次结构。

9.
> Original: Thread Safety Guarantees [及子项] Thread safety levels; Thread safety for list objects; Thread safety for dict objects; Thread safety for set objects; Thread safety for bytearray objects; Thread safety for memoryview objects.
> 翻译：线程安全保证[及子项] 线程安全级别；list对象的线程安全；dict对象的线程安全；set对象的线程安全；bytearray对象的线程安全；memoryview对象的线程安全。

10.
> Original: Time complexity of operations on built-in types [及子项] list; tuple; dict; set, frozenset; str, bytes, bytearray; memoryview; range; Notes.
> 翻译：内建类型操作的时间复杂度[及子项] list；tuple；dict；set、frozenset；str、bytes、bytearray；memoryview；range；备注。

## 事实
> 全部从Python 3.14官方文档builtins/index.txt提取的客观事实，作为框架FE的填充值，属于分析中间产物

1. Python附带若干内建函数和内建类（←片段1）
2. 内建类包括通常被视为语言"核心"的数据类型，如数字和列表（←片段2）
3. 对内建类型，Python语言核心定义字面量形式并施加语义约束，但未完全定义语义（←片段2）
4. 内建对象包括函数和异常——所有Python代码无需import即可使用（←片段3）
5. 部分内建对象由核心语言定义；许多对核心语义非必需，仅在builtins章节描述（←片段3）
6. 除内建对象外，Python还提供可导入的标准库（←片段4）
7. 内建类型包含16个子主题：真值测试、布尔运算、比较、数值类型、布尔类型、迭代器类型、序列类型、文本与二进制序列方法摘要、文本序列类型、二进制序列类型、集合类型、映射类型、上下文管理器类型、类型注解类型、其他内建类型、特殊属性、整数字符串转换长度限制（←片段5）
8. 数值类型包含int、float、complex三种（←片段5）
9. 序列类型包含list、tuple、range三种（←片段5）
10. 二进制序列类型包含bytes、bytearray、memoryview三种（←片段5）
11. 集合类型包含set、frozenset两种（←片段5）
12. 映射类型为dict（←片段5）
13. 类型注解类型包含Generic Alias和Union（←片段5）
14. 内建常量包含由site模块添加的常量（←片段6）
15. 内建函数为独立章节（←片段7）
16. 内建异常包含7个子主题：异常上下文、继承自内建异常、基类、具体异常、警告、异常组、异常层次结构（←片段8）
17. 线程安全保证涵盖6类对象：list、dict、set、bytearray、memoryview，并定义线程安全级别（←片段9）
18. 时间复杂度涵盖8类对象：list、tuple、dict、set/frozenset、str/bytes/bytearray、memoryview、range（←片段10）

## 缺口
> 从原始语料分析得出的**知识缺口**：语料没有明确说明、缺少定义、边界模糊的点，属于分析中间产物

1. "内建"的精确定义未给出——何种对象有资格成为built-in？仅凭"无需import"是否充分？（相关片段1、3）
2. 片段2指出核心语言"未完全定义"内建类型语义，但"完全定义"的边界是什么、由谁补全未说明（相关片段2）
3. "Other Built-in Types"（其他内建类型）具体包含哪些类型未列出（相关片段5）
4. "Special Attributes"（特殊属性）的范畴和成员未列举（相关片段5）
5. 内建函数章节的函数清单及数量未在index中给出（相关片段7）
6. 内建异常的完整层次结构仅提到标题，未展示实际继承树（相关片段8）
7. "Exception context"的具体含义（`__context__` vs `__cause__`）未在index中说明（相关片段8）
8. 线程安全级别的具体分级标准（如"安全"/"不安全"/"部分安全"）未定义（相关片段9）
9. "Constants added by the site module"具体包含哪些常量未列出（相关片段6）
10. "Integer string conversion length limitation"的限制阈值和理由未在index中说明（相关片段5）

## 误解
> 从原始语料推导的学习者**潜在错误理解**，属于分析中间产物

1. 误解"所有内建对象的语义都由Python语言核心完全定义"——片段2明确说核心语言"未完全定义"语义，读者可能忽略此限定（←片段2诱导）
2. 误解"内建类型等同于标准库类型"——片段4明确区分了built-ins和标准库，前者无需import，后者需import（←片段4诱导）
3. 误解"所有内建对象对核心语义都是必需的"——片段3明确说"许多并非核心语义必需"（←片段3诱导）
4. 误解"内建类型的线程安全性统一为安全或不安全"——片段9以对象为单位分别讨论线程安全，暗示安全级别因类型而异（←片段9诱导）
5. 误解"时间复杂度对所有类型都一样"——片段10按类型分别列出时间复杂度，表明不同类型操作效率不同（←片段10诱导）
6. 误解"bool是独立于int的数值类型"——index将Boolean Type单独列出而非归入Numeric Types，但Python中bool实为int子类，学习者可能忽略此关系（←片段5诱导）

## Python内建对象体系框架
|框架名称|刻画描述|框架元素（FE）及填充|原始事实语料|原始语料定位|
|---|---|---|---|---|
|内建对象体系入口框架|主题级根锚点：Python内建对象体系的整体构成维度与导航聚合|`主题对象`（核心）: Python内建对象体系<br>`类型维度`（核心）: Python附带的数据类型系统，含数值、序列、集合、映射、布尔等16个子领域——内建类型框架<br>`常量维度`（核心）: 无需导入即可使用的固定值对象——内建常量框架<br>`函数维度`（核心）: 无需导入即可调用的内建函数集合——内建函数框架<br>`异常维度`（核心）: 内建异常类的层次结构、基类、具体异常与警告——内建异常框架<br>`线程安全维度`（外围）: 各内建类型在多线程环境下的安全保证与级别——线程安全框架<br>`性能维度`（外围）: 各内建类型操作的时间复杂度——操作复杂度框架|1, 2, 3, 7, 14, 15, 16, 17, 18|原文片段1‑10；参考链接：https://docs.python.org/3.14/library/builtins.html|
|内建类型框架|Python内建数据类型的分类体系，涵盖数值、序列、集合、映射等类型|`类型集合`（核心）: 16个类型子领域（真值测试、布尔运算、比较、数值类型、布尔类型、迭代器类型、序列类型、文本与二进制方法摘要、文本序列类型、二进制序列类型、集合类型、映射类型、上下文管理器类型、类型注解类型、其他内建类型、特殊属性）<br>`字面量形式`（核心）: 由Python语言核心定义<br>`语义约束`（核心）: 由核心语言施加部分约束，但未完全定义<br>`核心地位`（外围）: 通常被视为语言"核心"部分的数据类型|2, 3, 7, 8, 9, 10, 11, 12, 13|原文片段2‑5；参考链接：https://docs.python.org/3.14/library/builtins.html|
|内建常量框架|Python内建常量对象，包括固定值常量与site模块动态添加的常量|`常量集合`（核心）: 无需import即可使用的固定值对象<br>`site扩展`（外围）: 由site模块添加的常量|14|原文片段6；参考链接：https://docs.python.org/3.14/library/builtins.html|
|内建函数框架|Python内建函数集合，所有代码无需import即可直接调用|`函数集合`（核心）: 无需import语句即可被所有Python代码使用的函数<br>`定义来源`（外围）: 部分由核心语言定义，部分非核心语义必需|4, 5, 15|原文片段3、7；参考链接：https://docs.python.org/3.14/library/builtins.html|
|内建异常框架|Python内建异常类的组织结构，包含基类、具体异常、警告与异常组|`异常组织`（核心）: 含7个子主题——异常上下文、继承自内建异常、基类、具体异常、警告、异常组、异常层次结构<br>`层次结构`（核心）: 异常类以继承层次组织<br>`继承来源`（外围）: 用户自定义异常需继承自内建异常|16|原文片段8；参考链接：https://docs.python.org/3.14/library/builtins.html|
|线程安全框架|各内建类型在多线程环境下的安全保证，按对象类型分别讨论|`安全级别`（核心）: 线程安全分级体系<br>`适用对象`（核心）: list、dict、set、bytearray、memoryview五类对象|17|原文片段9；参考链接：https://docs.python.org/3.14/library/builtins.html|
|操作复杂度框架|各内建类型操作的时间复杂度，按类型分别列出|`复杂度分布`（核心）: 按类型分别列出的时间复杂度<br>`适用类型`（核心）: list、tuple、dict、set/frozenset、str/bytes/bytearray、memoryview、range|18|原文片段10；参考链接：https://docs.python.org/3.14/library/builtins.html|

## Python内建对象体系框架间关系
> FrameNet标准关系：`Inheritance`（继承）、`Perspective on`（视角化）、`Using`（使用/依赖）、`Subframe`（子框架）、`Precedes`（先行）、`Causative of`（致使）、`Inchoative of`（起始）、`Metaphor`（隐喻）、`See also`（参见）

**第一组：子框架 → 入口框架**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|内建类型框架|`Using`|内建对象体系入口框架|填充`类型维度`槽；预设前提：Python语言核心定义字面量形式和部分语义约束|
|内建常量框架|`Using`|内建对象体系入口框架|填充`常量维度`槽；预设前提：常量为无需import的固定值对象|
|内建函数框架|`Using`|内建对象体系入口框架|填充`函数维度`槽；预设前提：函数为无需import即可调用的对象|
|内建异常框架|`Using`|内建对象体系入口框架|填充`异常维度`槽；预设前提：异常为无需import的错误处理对象|
|线程安全框架|`Using`|内建对象体系入口框架|填充`线程安全维度`槽；预设前提：内建类型在多线程环境下需安全保证|
|操作复杂度框架|`Using`|内建对象体系入口框架|填充`性能维度`槽；预设前提：内建类型操作的执行效率因类型而异|

**第二组：子框架之间**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|线程安全框架|`Using`|内建类型框架|预设前提：线程安全保证针对内建类型对象（list、dict、set、bytearray、memoryview），需以内建类型的存在和定义为前提|
|操作复杂度框架|`Using`|内建类型框架|预设前提：时间复杂度分析对象为内建类型（list、tuple、dict等），需以内建类型的存在和定义为前提|
|内建常量框架|`See also`|内建类型框架|常量与类型存在领域相关性（如True/False为bool类型的实例、None为单独类型），但不满足强关系的判定条件|
|内建异常框架|`See also`|内建类型框架|异常类本身是type的子类/实例，与类型体系存在领域相关性，但不满足强关系判定条件|
