# 内置常量 FrameNet 语义框架标注文档
> 文档结构：##说明 → ##原文和翻译 → ##事实 → ##缺口 → ##误解 → ##内置常量框架 → ##内置常量框架间关系

## 说明
1. 本文件基于 Python 3.14 官方文档 `builtins/constants.txt`，采用**FrameNet框架语义学**进行建模。
2. 框架元素FE为抽象语义槽；**事实为槽填充客观内容；缺口是从原始语料推导出来的知识缺失点；误解是基于语料推导的学习者可能产生的错误理解**。
3. 原文与翻译一一对应，原文后紧跟中文翻译；
4. 框架关系使用FrameNet标准9种关系标签：`Inheritance`、`Perspective on`、`Using`、`Subframe`、`Precedes`、`Causative of`、`Inchoative of`、`Metaphor`、`See also`；
5. 原始语料定位记录原文出处、片段位置与参考链接。
6. 本次分析启用可选项：**②HTML统一视图**——[内置常量-framenet.html](./内置常量-framenet.html)。
7. 问答档案（qa-5w2h 技能产出）：见 [内置常量-qa.md](./内置常量-qa.md)

## 原文和翻译
> 来源：Python 3.14 官方文档 builtins/constants.txt

1.
> Original: A small number of constants live in the built-in namespace. They are:
> 翻译：少量常量存在于内置命名空间中。它们是：

2.
> Original: False — The false value of the "bool" type. Assignments to "False" are illegal and raise a "SyntaxError".
> 翻译：False —— "bool" 类型的假值。对 "False" 赋值是非法的，会引发 "SyntaxError"。

3.
> Original: True — The true value of the "bool" type. Assignments to "True" are illegal and raise a "SyntaxError".
> 翻译：True —— "bool" 类型的真值。对 "True" 赋值是非法的，会引发 "SyntaxError"。

4.
> Original: None — An object frequently used to represent the absence of a value, as when default arguments are not passed to a function. Assignments to "None" are illegal and raise a "SyntaxError". "None" is the sole instance of the "NoneType" type.
> 翻译：None —— 一个常用于表示值缺失的对象，例如函数的默认参数未被传递时。对 "None" 赋值是非法的，会引发 "SyntaxError"。"None" 是 "NoneType" 类型的唯一实例。

5.
> Original: NotImplemented — A special value which should be returned by the binary special methods (e.g. "__eq__()", "__lt__()", "__add__()", "__rsub__()", etc.) to indicate that the operation is not implemented with respect to the other type; may be returned by the in-place binary special methods (e.g. "__imul__()", "__iand__()", etc.) for the same purpose. It should not be evaluated in a boolean context. "NotImplemented" is the sole instance of the "types.NotImplementedType" type.
> 翻译：NotImplemented —— 一个应由二元特殊方法（如 "__eq__()"、"__lt__()"、"__add__()"、"__rsub__()" 等）返回的特殊值，以指示该操作相对于另一类型未实现；也可由就地二元特殊方法（如 "__imul__()"、"__iand__()" 等）为同一目的返回。不应在布尔上下文中对其求值。"NotImplemented" 是 "types.NotImplementedType" 类型的唯一实例。

6.
> Original: When a binary (or in-place) method returns "NotImplemented" the interpreter will try the reflected operation on the other type (or some other fallback, depending on the operator). If all attempts return "NotImplemented", the interpreter will raise an appropriate exception. Incorrectly returning "NotImplemented" will result in a misleading error message or the "NotImplemented" value being returned to Python code.
> 翻译：当二元（或就地）方法返回 "NotImplemented" 时，解释器会尝试对另一类型执行反射操作（或根据运算符采取其他回退方案）。如果所有尝试都返回 "NotImplemented"，解释器会引发适当的异常。错误地返回 "NotImplemented" 将导致误导性的错误消息或将 "NotImplemented" 值返回给 Python 代码。

7.
> Original: "NotImplemented" and "NotImplementedError" are not interchangeable. This constant should only be used as described above; see "NotImplementedError" for details on correct usage of the exception.
> 翻译："NotImplemented" 和 "NotImplementedError" 不可互换。此常量只能按上述描述使用；关于该异常的正确用法详见 "NotImplementedError"。

8.
> Original: Changed in version 3.9: Evaluating "NotImplemented" in a boolean context was deprecated. Changed in version 3.14: Evaluating "NotImplemented" in a boolean context now raises a "TypeError". It previously evaluated to "True" and emitted a "DeprecationWarning" since Python 3.9.
> 翻译：版本 3.9 变更：在布尔上下文中对 "NotImplemented" 求值已被弃用。版本 3.14 变更：在布尔上下文中对 "NotImplemented" 求值现在会引发 "TypeError"。此前它求值为 "True"，且自 Python 3.9 起发出 "DeprecationWarning"。

9.
> Original: Ellipsis — The same as the ellipsis literal "...", an object frequently used to indicate that something is omitted. Assignment to "Ellipsis" is possible, but assignment to "..." raises a "SyntaxError". "Ellipsis" is the sole instance of the "types.EllipsisType" type.
> 翻译：Ellipsis —— 与省略号字面量 "..." 相同，一个常用于指示某些内容被省略的对象。对 "Ellipsis" 赋值是可能的，但对 "..." 赋值会引发 "SyntaxError"。"Ellipsis" 是 "types.EllipsisType" 类型的唯一实例。

10.
> Original: __debug__ — This constant is true if Python was not started with an "-O" option. See also the "assert" statement.
> 翻译：__debug__ —— 如果 Python 未以 "-O" 选项启动，此常量为真。另见 "assert" 语句。

11.
> Original: The names "None", "False", "True" and "__debug__" cannot be reassigned (assignments to them, even as an attribute name, raise "SyntaxError"), so they can be considered "true" constants.
> 翻译：名称 "None"、"False"、"True" 和 "__debug__" 不能被重新赋值（对它们的赋值，即使作为属性名，也会引发 "SyntaxError"），因此它们可以被视为"真正的常量"。

12.
> Original: The "site" module (which is imported automatically during startup, except if the "-S" command-line option is given) adds several constants to the built-in namespace. They are useful for the interactive interpreter shell and should not be used in programs.
> 翻译："site" 模块（在启动时自动导入，除非给定 "-S" 命令行选项）向内置命名空间添加了若干常量。它们对交互式解释器 shell 有用，不应在程序中使用。

13.
> Original: quit(code=None) / exit(code=None) — Objects that when printed, print a message like "Use quit() or Ctrl-D (i.e. EOF) to exit", and when accessed directly in the interactive interpreter or called as functions, raise "SystemExit" with the specified exit code.
> 翻译：quit(code=None) / exit(code=None) —— 打印时显示类似 "Use quit() or Ctrl-D (i.e. EOF) to exit" 的消息，在交互式解释器中直接访问或作为函数调用时，以指定的退出码引发 "SystemExit"。

14.
> Original: help — Object that when printed, prints the message "Type help() for interactive help, or help(object) for help about object.", and when accessed directly in the interactive interpreter, invokes the built-in help system.
> 翻译：help —— 打印时显示消息 "Type help() for interactive help, or help(object) for help about object."，在交互式解释器中直接访问时，调用内置帮助系统。

15.
> Original: copyright / credits — Objects that when printed or called, print the text of copyright or credits, respectively.
> 翻译：copyright / credits —— 打印或调用时分别显示版权或致谢文本。

16.
> Original: license — Object that when printed, prints the message "Type license() to see the full license text", and when called, displays the full license text in a pager-like fashion (one screen at a time).
> 翻译：license —— 打印时显示消息 "Type license() to see the full license text"，调用时以分页方式（一次一屏）显示完整许可证文本。

## 事实
> 全部从 Python 3.14 官方文档 builtins/constants.txt 提取的客观事实，作为框架FE的填充值，属于分析中间产物

1. 少量常量存在于内置命名空间中。（←片段1）
2. False 是 bool 类型的假值。（←片段2）
3. 对 False 赋值非法，会引发 SyntaxError。（←片段2）
4. True 是 bool 类型的真值。（←片段3）
5. 对 True 赋值非法，会引发 SyntaxError。（←片段3）
6. None 常用于表示值的缺失，例如函数默认参数未传递时。（←片段4）
7. 对 None 赋值非法，会引发 SyntaxError。（←片段4）
8. None 是 NoneType 类型的唯一实例。（←片段4）
9. NotImplemented 应由二元特殊方法（如 __eq__()、__lt__()、__add__()、__rsub__() 等）返回，以指示操作未实现。（←片段5）
10. NotImplemented 也可由就地二元特殊方法（如 __imul__()、__iand__() 等）返回以指示操作未实现。（←片段5）
11. NotImplemented 不应在布尔上下文中求值。（←片段5）
12. NotImplemented 是 types.NotImplementedType 类型的唯一实例。（←片段5）
13. 当二元/就地方法返回 NotImplemented 时，解释器尝试反射操作或其他回退方案。（←片段6）
14. 若所有尝试均返回 NotImplemented，解释器引发适当异常。（←片段6）
15. 错误地返回 NotImplemented 会导致误导性错误消息或 NotImplemented 值返回给 Python 代码。（←片段6）
16. NotImplemented 和 NotImplementedError 不可互换。（←片段7）
17. NotImplemented 常量仅应按上述二元/就地特殊方法返回值的方式使用。（←片段7）
18. 在布尔上下文中求值 NotImplemented 自 Python 3.9 起被弃用。（←片段8）
19. 自 Python 3.14 起，在布尔上下文中求值 NotImplemented 引发 TypeError；此前求值为 True 并发出 DeprecationWarning。（←片段8）
20. Ellipsis 与省略号字面量 "..." 相同，常用于指示内容被省略。（←片段9）
21. 对 Ellipsis 赋值是可能的，但对 "..." 赋值引发 SyntaxError。（←片段9）
22. Ellipsis 是 types.EllipsisType 类型的唯一实例。（←片段9）
23. __debug__ 在 Python 未以 "-O" 选项启动时为真。（←片段10）
24. __debug__ 与 assert 语句相关联。（←片段10）
25. None、False、True、__debug__ 不可被重新赋值（即使作为属性名也引发 SyntaxError），可视为"真正的常量"。（←片段11）
26. site 模块在启动时自动导入（除非 -S 选项），向内置命名空间添加若干常量。（←片段12）
27. site 模块添加的常量对交互式解释器 shell 有用，不应在程序中使用。（←片段12）
28. quit/exit 打印时显示退出提示消息；直接访问或调用时以指定退出码引发 SystemExit。（←片段13）
29. help 打印时显示帮助提示消息；直接访问时调用内置帮助系统。（←片段14）
30. copyright/credits 打印或调用时显示版权或致谢文本。（←片段15）
31. license 打印时显示许可证提示消息；调用时以分页方式显示完整许可证文本。（←片段16）

## 缺口
> 从原始语料分析得出的**知识缺口**：语料没有明确说明、缺少定义、边界模糊的点，属于分析中间产物

1. NotImplemented 的"反射操作"具体机制未详细说明——解释器如何选择反射方法、回退方案的优先级链未交代。（相关片段6）
2. "适当异常"的具体类型未说明——当所有尝试均返回 NotImplemented 时，解释器引发何种异常取决于什么？（相关片段6）
3. Ellipsis 的具体使用场景未展开——除"指示省略"外，在切片语法（如 a[..., 0]）、类型存根（... 作为函数体）等场景未提及。（相关片段9）
4. __debug__ 在 "-O" 选项启动时的具体值为假值还是 False 未明确。（相关片段10）
5. __debug__ 与 assert 语句的具体联动机制未说明——-O 选项下 assert 语句被跳过的关系仅以"See also"暗示。（相关片段10）
6. site 模块添加的常量"不应在程序中使用"的原因未说明——为何不适合程序使用？可能在 -S 选项下不可用？（相关片段12）
7. Ellipsis 与 "..." 的区别仅提及赋值行为不同，其语义等价性和运行时行为完全一致未明确交代。（相关片段9）
8. NotImplemented 在布尔上下文中"不应求值"的历史演进（3.9 弃用→3.14 TypeError）的前因后果未展开——为何当初允许求值为 True？（相关片段8）

## 误解
> 从原始语料推导的学习者**潜在错误理解**，属于分析中间产物

1. 认为 Ellipsis 也不可赋值——原文只说对 "..." 赋值引发 SyntaxError，对 Ellipsis 名字赋值是可能的。（←片段9诱导）
2. 将 NotImplemented 等同于 NotImplementedError——原文明确声明二者不可互换，前者是二元特殊方法的返回值常量，后者是应抛出的异常。（←片段7诱导，"名称相似性"诱导）
3. 认为 NotImplemented 在布尔上下文中求值为 False——原文指出不应在布尔上下文中求值，且 3.14 起会引发 TypeError；历史行为是求值为 True 而非 False。（←片段5+8诱导，"Not"前缀暗示假值）
4. 认为所有内置常量都不可赋值——原文只说 None/False/True/__debug__ 不可赋值，Ellipsis 和 NotImplemented 是可以赋值的。（←片段11诱导）
5. 认为 quit/exit 可以在程序中使用——原文明确说 site 模块添加的常量不应在程序中使用。（←片段12+13诱导）
6. 认为 __debug__ 是一个可以在运行时修改的变量——原文声明它是不可重新赋值的真正常量。（←片段10+11诱导）
7. 认为对 "..." 的赋值限制与对 Ellipsis 的限制相同——实际上对 Ellipsis 名字赋值合法，只有对 "..." 字面量赋值引发 SyntaxError。（←片段9诱导）

## 内置常量框架

| 框架名称 | 刻画描述 | 框架元素（FE）及填充 | 原始事实语料 | 原始语料定位 |
|---|---|---|---|---|
| 内置常量入口框架 | 主题级根锚点：Python 内置命名空间中常量的分类体系与聚合导航 | `主题对象`（核心）: Python 内置常量<br>`布尔值维度`（核心）: 布尔类型的真/假值常量——布尔值框架<br>`空值标注维度`（核心）: 表示值缺失的单例标记——空值标注框架<br>`运算未实现信号维度`（核心）: 二元特殊方法返回的"操作未实现"信号常量——运算未实现信号框架<br>`省略指示维度`（核心）: 指示内容省略的标记常量——省略指示框架<br>`调试状态维度`（核心）: 反映解释器优化级别的真/假标志——调试状态框架<br>`交互辅助维度`（外围）: 由 site 模块添加、仅供交互式 shell 使用的辅助常量——交互辅助框架 | 1. 少量常量存在于内置命名空间中<br>25. None/False/True/__debug__ 不可重新赋值 | 原文片段1‑16；参考链接：https://docs.python.org/3.14/library/constants.html |
| 布尔值框架 | bool 类型的真/假值，不可赋值的真正常量 | `成员`（核心）: True（真值）和 False（假值）<br>`所属类型`（核心）: bool 类型<br>`赋值保护`（核心）: 赋值非法，引发 SyntaxError<br>`真正常量性`（外围）: 不可重新赋值，即使作为属性名 | 2. False 是 bool 类型的假值<br>3. 对 False 赋值非法，引发 SyntaxError<br>4. True 是 bool 类型的真值<br>5. 对 True 赋值非法，引发 SyntaxError<br>25. True/False 不可重新赋值 | 原文片段2‑3+11；参考链接：https://docs.python.org/3.14/library/constants.html |
| 空值标注框架 | 表示值缺失的不可赋值单例常量 | `常量值`（核心）: None<br>`语义角色`（核心）: 表示值缺失（如函数默认参数未传递）<br>`所属类型`（核心）: NoneType 的唯一实例<br>`赋值保护`（核心）: 赋值非法，引发 SyntaxError<br>`真正常量性`（外围）: 不可重新赋值 | 6. None 常用于表示值缺失<br>7. 对 None 赋值非法<br>8. None 是 NoneType 的唯一实例<br>25. None 不可重新赋值 | 原文片段4+11；参考链接：https://docs.python.org/3.14/library/constants.html |
| 运算未实现信号框架 | 二元/就地特殊方法返回的"操作未实现"信号常量，触发解释器反射/回退机制 | `常量值`（核心）: NotImplemented<br>`触发条件`（核心）: 二元特殊方法（__eq__/__lt__/__add__/__rsub__等）或就地特殊方法（__imul__/__iand__等）对另一类型未实现操作时返回<br>`解释器行为`（核心）: 解释器尝试反射操作或其他回退方案；全部返回 NotImplemented 则引发异常<br>`布尔上下文禁忌`（核心）: 不应在布尔上下文中求值；3.14 起引发 TypeError<br>`所属类型`（核心）: types.NotImplementedType 的唯一实例<br>`赋值保护`（外围）: 可赋值（非真正常量）<br>`易混淆异常`（外围）: 不可与 NotImplementedError 互换<br>`错误后果`（外围）: 错误返回导致误导性错误消息或 NotImplemented 值泄漏<br>`版本演进`（外围）: 3.9 弃用布尔求值→3.14 引发 TypeError（此前求值为 True） | 9‑19 全部事实 | 原文片段5‑8；参考链接：https://docs.python.org/3.14/library/constants.html |
| 省略指示框架 | 与省略号字面量等价的标记常量，指示内容省略 | `常量值`（核心）: Ellipsis<br>`字面量等价`（核心）: 与 "..." 字面量相同<br>`语义角色`（核心）: 指示内容被省略<br>`所属类型`（核心）: types.EllipsisType 的唯一实例<br>`赋值不对称性`（核心）: 对 Ellipsis 名字赋值合法，对 "..." 字面量赋值引发 SyntaxError | 20. Ellipsis 与 "..." 相同，指示省略<br>21. Ellipsis 可赋值，"..." 不可<br>22. Ellipsis 是 EllipsisType 唯一实例 | 原文片段9；参考链接：https://docs.python.org/3.14/library/constants.html |
| 调试状态框架 | 反映 Python 解释器优化级别的不可赋值标志常量 | `常量值`（核心）: __debug__<br>`真值条件`（核心）: Python 未以 -O 选项启动时为真<br>`关联语句`（核心）: 与 assert 语句相关联<br>`真正常量性`（外围）: 不可重新赋值 | 23. __debug__ 未以 -O 启动时为真<br>24. __debug__ 与 assert 相关<br>25. __debug__ 不可重新赋值 | 原文片段10+11；参考链接：https://docs.python.org/3.14/library/constants.html |
| 交互辅助框架 | 由 site 模块自动添加到内置命名空间的交互式 shell 辅助对象 | `提供者`（核心）: site 模块（启动时自动导入，-S 选项除外）<br>`适用范围`（核心）: 交互式解释器 shell，不应在程序中使用<br>`退出辅助`（核心）: quit/exit——打印退出提示，调用时引发 SystemExit<br>`帮助辅助`（核心）: help——打印帮助提示，直接访问时调用内置帮助系统<br>`信息辅助`（外围）: copyright/credits——打印版权或致谢文本<br>`许可辅助`（外围）: license——打印许可证提示，调用时分页显示许可证 | 26‑31 全部事实 | 原文片段12‑16；参考链接：https://docs.python.org/3.14/library/constants.html |

## 内置常量框架间关系
> FrameNet标准关系：`Inheritance`（继承）、`Perspective on`（视角化）、`Using`（使用/依赖）、`Subframe`（子框架）、`Precedes`（先行）、`Causative of`（致使）、`Inchoative of`（起始）、`Metaphor`（隐喻）、`See also`（参见）

**第一组：子框架 → 入口框架**
| 源框架 | FrameNet关系 | 目标框架 | 关系释义 |
|---|---|---|---|
| 布尔值框架 | `Using` | 内置常量入口框架 | 填充`布尔值维度`槽；布尔值框架的语义成立以内置命名空间中存在常量为前提 |
| 空值标注框架 | `Using` | 内置常量入口框架 | 填充`空值标注维度`槽；空值标注框架的语义成立以内置命名空间中存在常量为前提 |
| 运算未实现信号框架 | `Using` | 内置常量入口框架 | 填充`运算未实现信号维度`槽；运算未实现信号框架的语义成立以内置命名空间中存在常量为前提 |
| 省略指示框架 | `Using` | 内置常量入口框架 | 填充`省略指示维度`槽；省略指示框架的语义成立以内置命名空间中存在常量为前提 |
| 调试状态框架 | `Using` | 内置常量入口框架 | 填充`调试状态维度`槽；调试状态框架的语义成立以内置命名空间中存在常量为前提 |
| 交互辅助框架 | `Using` | 内置常量入口框架 | 填充`交互辅助维度`槽；交互辅助框架的语义成立以内置命名空间中存在常量为前提，且预设 site 模块自动导入机制 |

**第二组：子框架之间**
| 源框架 | FrameNet关系 | 目标框架 | 关系释义 |
|---|---|---|---|
| 布尔值框架 | `See also` | 调试状态框架 | __debug__ 的真/假语义依赖布尔值概念，但二者不构成继承或子框架关系——布尔值框架刻画 bool 类型常量，调试状态框架刻画优化级别标志 |
| 运算未实现信号框架 | `See also` | 布尔值框架 | NotImplemented 在布尔上下文的行为涉及布尔求值，但二者功能角色不同——运算未实现信号框架刻画运算协商机制，布尔值框架刻画真假值 |
| 调试状态框架 | `Inheritance` | 布尔值框架 | __debug__ 在 -O 未启动时为 true（bool 真值），与 bool 类型的真/假值概念一致；布尔值框架的 FE（成员、所属类型）可对应到调试状态框架（__debug__ 成员、真值条件关联 bool）——调试状态具名常量是布尔值概念在优化级别场景的具体化 |
| 交互辅助框架 | `See also` | 空值标注框架 | quit/exit 的 code 参数默认为 None，二者存在值引用关系，但功能角色完全不同——交互辅助框架刻画 shell 辅助对象，空值标注框架刻画值缺失标记 |

> 未使用的关系类型：`Perspective on`（无一框架是另一框架的特定视角化）、`Subframe`（无一框架是另一框架的子阶段）、`Precedes`（无时序先后关系）、`Causative of`（无致使关系）、`Inchoative of`（无状态起始关系）、`Metaphor`（无隐喻映射）——宁缺毋滥。
