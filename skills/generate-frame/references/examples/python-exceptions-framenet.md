# Python异常体系 FrameNet 语义框架标注文档
> 文档结构：##说明 → ##原文和翻译 → ##事实 → ##缺口 → ##误解 → ##异常框架 → ##异常框架间关系

## 说明
1. 本文件基于Python官方内置异常文档，采用**FrameNet框架语义学**进行建模。
2. 框架元素FE为抽象语义槽；**事实为槽填充客观内容；缺口是从原始语料推导出来的知识缺失点；误解是基于语料推导的学习者可能产生的错误理解**。
3. 原文与翻译一一对应，原文后紧跟中文翻译；
4. 框架关系使用FrameNet标准9种关系标签：`Inheritance`、`Perspective on`、`Using`、`Subframe`、`Precedes`、`Causative of`、`Inchoative of`、`Metaphor`、`See also`；
5. 原始语料定位记录原文出处、片段位置与参考链接。
6. 本次分析启用可选项：**①缺口补全**——独立文件 [python-exceptions-gapfill.md](./python-exceptions-gapfill.md)；**②HTML统一视图**——[python-exceptions-framenet.html](./python-exceptions-framenet.html)。

## 原文和翻译
> 来源：Python 官方文档 Built‑in Exceptions & Errors and Exceptions

1.
> Original: All exceptions must be instances of classes derived from `BaseException`.
> 翻译：所有异常必须是派生自 `BaseException` 的类的实例。

2.
> Original: `Exception` is the base class for all built‑in non‑system‑exiting exceptions. All user‑defined exceptions should be derived from this class.
> 翻译：`Exception` 是所有内置非系统退出类异常的基类。所有用户自定义异常都应当派生自该类。

3.
> Original: `KeyboardInterrupt`, `SystemExit` inherit directly from `BaseException`, not from `Exception`.
> 翻译：`KeyboardInterrupt`、`SystemExit` 直接继承自 `BaseException`，不继承 `Exception`。

4.
> Original: An except clause that names a class will catch that class and all its subclasses. It does not catch its superclasses.
> 翻译：命名某个类的except子句会捕获该类及其全部子类；**不会捕获它的父类**。

5.
> Original: When catching exceptions, more specific exception handlers should appear before more general ones.
> 翻译：捕获异常时，更具体的异常处理分支应当放在更通用的分支之前。

6.
> Original: `TypeError` is raised when an operation or function is applied to an object of inappropriate type.
> 翻译：当操作或函数作用于类型不恰当的对象时，抛出 `TypeError`。

7.
> Original: `ZeroDivisionError` is raised when the second argument of a division or modulo operation is zero.
> 翻译：除法或取模运算第二个参数为0时，抛出 `ZeroDivisionError`。

8.
> Original: `ArithmeticError` is the base class for all arithmetic errors, including `ZeroDivisionError`, `OverflowError`, `FloatingPointError`.
> 翻译：`ArithmeticError` 是所有算术错误的基类，包含 `ZeroDivisionError`、`OverflowError`、`FloatingPointError`。

9.
> Original: `LookupError` is the base class for `IndexError` and `KeyError`.
> 翻译：`LookupError` 是 `IndexError` 与 `KeyError` 的基类。

10.
> Original: `OSError` is the base class for system‑related errors, including `FileNotFoundError`, `PermissionError`, `ConnectionError`.
> 翻译：`OSError` 是系统相关错误的基类，包含 `FileNotFoundError`、`PermissionError`、`ConnectionError`。

11.
> Original: Exception instances have attributes: `args`, `__traceback__`, `__notes__`. Methods: `with_traceback()`, `add_note()`.
> 翻译：异常实例拥有属性：`args`、`__traceback__`、`__notes__`；方法：`with_traceback()`、`add_note()`。

12.
> Original: `BaseExceptionGroup` can wrap multiple `BaseException` instances to propagate multiple errors simultaneously.
> 翻译：`BaseExceptionGroup` 可以包装多个 `BaseException` 实例，实现多错误同时传播。

13.
> Original: `ExceptionGroup` is a subclass of both `Exception` and `BaseExceptionGroup`, it can only wrap `Exception` instances.
> 翻译：`ExceptionGroup` 同时继承 `Exception` 和 `BaseExceptionGroup`，仅可包装 `Exception` 实例。

14.
> Original: `Warning` is the base class for all warning types. Warnings do not terminate program execution, they are separate from exceptions.
> 翻译：`Warning` 是全部警告类型的基类。警告不会终止程序执行，与异常体系相互独立。

## 事实
> 全部从官方原文提取的客观事实，作为框架FE的填充值，属于分析中间产物
1. 异常根基类为 `BaseException`，所有异常实例必须继承它。（←片段1）
2. `Exception` 是普通内置异常、用户自定义异常的基类；系统退出异常不继承 `Exception`。（←片段2）
3. `KeyboardInterrupt`、`SystemExit`、`GeneratorExit` 直接继承 `BaseException`。（←片段3）
4. except 捕获**子类异常**，不能捕获父类异常；捕获顺序必须子类在前，父类在后。（←片段4‑5）
5. `TypeError`：对象类型不匹配触发；`ZeroDivisionError`：除数为0触发。（←片段6‑7）
6. 异常层级：`ArithmeticError` → `ZeroDivisionError`；`LookupError` → `IndexError`/`KeyError`；`OSError` → `FileNotFoundError`；`ValueError` → `UnicodeError`。（←片段8‑10）
7. 异常对象内置属性：`args`、`__traceback__`、`__notes__`；内置方法：`with_traceback()`、`add_note()`。（←片段11）
8. `BaseExceptionGroup` 可以包装任意 `BaseException`；`ExceptionGroup` 只能包装 `Exception`。（←片段12‑13）
9. `Warning` 为警告体系顶层基类；警告是非致命提示，不中断程序，独立于异常体系。（←片段14）

## 缺口
> 从原始语料分析得出的**知识缺口**：语料没有明确说明、缺少定义、边界模糊的点，属于分析中间产物
1. 原文没有明确说明 `GeneratorExit` 的完整继承行为细节。（相关片段3）
2. 原文没有给出 `NotImplementedError` 与 `TypeError` 的区分判定标准。（相关片段6）
3. 原文没有说明异常组在try‑except中的捕获匹配规则。（相关片段12‑13）
4. 原文没有说明 `__notes__` 属性的读写约束与版本兼容性。（相关片段11）
5. 原文没有列举全部 `OSError` 的子类完整清单。（相关片段10）
6. 原文没有说明用户自定义异常，除了继承 `Exception` 之外的最佳实践约束。（相关片段2）

> 缺口扩展资料（可选项①）：见 [python-exceptions-gapfill.md](./python-exceptions-gapfill.md)

## 误解
> 从原始语料推导的学习者**潜在错误理解**，属于分析中间产物
1. 误以为用户自定义异常可以直接继承 `BaseException`。（←片段2"应当派生自Exception"的正面规定反向诱导）
2. 认为 `KeyboardInterrupt`、`SystemExit` 继承自 `Exception`。（←片段3的例外陈述易被跳读）
3. 认为except捕获父类就可以捕获子类；写except时父类处理分支写在前，子类分支永远不会执行。（←片段4只正面陈述"捕获该类及其全部子类"，未先给出反例）
4. 将参数取值错误归为 `TypeError`，将类型错误归为 `ValueError`。（←片段6仅定义TypeError，未与ValueError对照）
5. 认为所有异常类互相平级，不存在公共父类。（←片段1的全称规定未显式画出层级全图）
6. 不知道异常实例自带 `args`、`__traceback__`、`add_note()` 等属性方法。（←片段11平铺罗列，易被忽略）
7. 混淆 `ExceptionGroup` 和 `BaseExceptionGroup` 的包装对象范围。（←片段12‑13两者并列出现）
8. 将Warning警告当成Exception异常，认为警告会终止程序运行。（←片段14"独立于异常体系"易被漏读）

## 异常框架
|框架名称|刻画描述|框架元素（FE）及填充|原始事实语料|原始语料定位|
|---|---|---|---|---|
|异常体系入口框架|主题级根锚点：聚合Python错误表示、传播、捕获与处置场景的构成维度，导航至各子框架|`主题对象`（核心）: Python异常体系（以BaseException为根的实例世界）<br>`继承结构维度`（核心）: 基类分工与派生规则——异常继承框架<br>`捕获规则维度`（核心）: except匹配与排序——异常捕获逻辑框架<br>`触发条件维度`（核心）: 各异常发生场景——异常触发场景框架<br>`层级清单维度`（核心）: 具体父子层级——异常层级关系框架<br>`对象操作维度`（核心）: 实例属性与方法——异常属性与方法框架<br>`复合机制维度`（核心）: 多异常打包传播——异常组使用框架<br>`相邻体系维度`（外围）: 独立于异常的警告机制——警告体系框架|1. 全部异常为BaseException派生实例；Exception管用户异常，系统异常直达根基类（事实1‑3）。<br>2. except按子类捕获且顺序敏感（事实4）。<br>3. 各异常有触发条件与父子层级（事实5‑6）。<br>4. 异常实例自带属性与方法（事实7）。<br>5. 异常组可打包多异常（事实8）。<br>6. 警告独立于异常体系（事实9）。|原文片段1‑14（主题全文）；参考链接：Python Built‑in Exceptions|
|异常继承框架|刻画异常间的继承关系及基类规则|`根基类`（核心）: BaseException<br>`用户异常基类`（核心）: Exception<br>`系统异常基类`（核心）: KeyboardInterrupt/SystemExit/GeneratorExit<br>`异常组基类`（外围）: ExceptionGroup/BaseExceptionGroup|1. Python所有异常都必须是BaseException子类的实例。<br>2. Exception是所有非系统退出内置异常的父类；用户自定义异常应当继承Exception。<br>3. KeyboardInterrupt、SystemExit、GeneratorExit直接继承BaseException，不继承Exception。<br>4. ExceptionGroup继承Exception与BaseExceptionGroup；BaseExceptionGroup可以封装任意BaseException实例。|原文片段1‑3、12‑13；参考链接：Python Built‑in Exceptions|
|异常捕获逻辑框架|描述except子句对异常的捕获规则|`捕获对象`（核心）: 派生类异常<br>`捕获顺序`（核心）: 子类在前、父类在后|1. except子句匹配异常类时，可以捕获该类及其所有子类异常。<br>2. except不能捕获父类异常；编码时子类异常捕获分支必须写在父类捕获分支之前。|原文片段4‑5；参考链接：Python Errors and Exceptions|
|异常触发场景框架|刻画不同异常的具体触发条件|`触发条件`（核心）: 类型不匹配、除数为0、索引越界、键不存在等<br>`对应异常`（核心）: TypeError、ZeroDivisionError、IndexError、KeyError等|1. TypeError：操作/函数作用于类型不匹配对象时抛出。<br>2. ZeroDivisionError：算术运算除数为0抛出。<br>3. IndexError：序列索引无效；KeyError：字典键不存在。<br>4. 参数类型错误属于TypeError；参数取值错误属于ValueError。|原文片段6‑7；参考链接：Python Built‑in Exceptions|
|异常层级关系框架|描述具体异常间的父子层级结构|`父类异常`（核心）: ArithmeticError、LookupError、OSError、ValueError等<br>`子类异常`（核心）: ZeroDivisionError、IndexError、FileNotFoundError、UnicodeDecodeError等|1. ArithmeticError是ZeroDivisionError、OverflowError、FloatingPointError的父类。<br>2. LookupError是IndexError、KeyError的父类。<br>3. OSError包含FileNotFoundError、PermissionError、ConnectionError等子类。<br>4. UnicodeError是ValueError的子类。|原文片段8‑10；参考链接：Python Built‑in Exceptions|
|异常属性与方法框架|刻画异常对象的核心属性和操作方法|`核心属性`（核心）: args、__traceback__、__notes__<br>`操作方法`（核心）: with_traceback(tb)、add_note(note)|1. args：异常构造函数接收的参数元组。<br>2. __traceback__：存储异常回溯信息的可写字段。<br>3. with_traceback(tb)：为异常对象绑定回溯，返回当前异常实例。<br>4. add_note(note)：为异常追加注释文本，在异常回溯打印时展示。|原文片段11；参考链接：Python Built‑in Exceptions|
|异常组使用框架|描述用于同时传播多个异常的特殊机制|`异常组类型`（核心）: ExceptionGroup、BaseExceptionGroup<br>`包装对象`（核心）: 多个异常实例|1. BaseExceptionGroup用于打包、同时抛出多个BaseException类型异常。<br>2. ExceptionGroup继承BaseExceptionGroup与Exception，仅能封装Exception类型异常实例。|原文片段12‑13；参考链接：Python Exception Groups|
|警告体系框架|刻画独立于异常的非致命问题提示体系|`警告基类`（核心）: Warning<br>`具体警告类型`（外围）: DeprecationWarning、BytesWarning、ResourceWarning等|1. Warning是所有警告类型的顶层基类。<br>2. 警告不会终止程序执行，属于非致命提示，语义上独立于异常体系。|原文片段14；参考链接：Python warnings|

## 异常框架间关系
> FrameNet标准关系：`Inheritance`（继承）、`Perspective on`（视角化）、`Using`（使用/依赖）、`Subframe`（子框架）、`Precedes`（先行）、`Causative of`（致使）、`Inchoative of`（起始）、`Metaphor`（隐喻）、`See also`（参见）

**第一组：子框架 → 入口框架**

|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|异常继承框架|Using|异常体系入口框架|填充`继承结构维度`槽；继承规则的刻画以入口框架聚合的异常场景为背景前提|
|异常捕获逻辑框架|Using|异常体系入口框架|填充`捕获规则维度`槽；捕获语义预设"异常可被表示与传播"（事实1、8）这一背景|
|异常触发场景框架|Using|异常体系入口框架|填充`触发条件维度`槽；触发场景以异常场景整体为背景|
|异常层级关系框架|Using|异常体系入口框架|填充`层级清单维度`槽；层级列举预设异常体系的存在|
|异常属性与方法框架|Using|异常体系入口框架|填充`对象操作维度`槽；属性方法刻画的对象范围由异常场景界定|
|异常组使用框架|Using|异常体系入口框架|填充`复合机制维度`槽；多异常打包预设单异常体系为背景|
|警告体系框架|Using|异常体系入口框架|填充外围槽`相邻体系维度`；本语料对警告的界定方式（"独立于异常体系"，片段14）以异常场景为对比前提|

**第二组：子框架之间**

|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|异常层级关系框架|Using|异常继承框架|具体层级（ArithmeticError→ZeroDivisionError等）的刻画以抽象继承规则为前提；父框架4个FE无法映射到层级框架2个FE，不满足Inheritance的FE对应判定，取Using|
|异常捕获逻辑框架|Using|异常继承框架|"except捕获该类及其全部子类"的语义必须以继承框架的IS‑A语义为前提；捕获框架不是继承体系的子类型|
|异常触发场景框架|Using|异常层级关系框架|触发场景附着于层级框架划定的具体异常实体之上，以层级结构为语义前提|
|异常属性与方法框架|Using|异常继承框架|属性与方法描述的对象集合，使用继承框架划定的BaseException实例范围|
|异常组使用框架|Inheritance|异常继承框架|异常组机制是继承体系的子类型并新增多异常打包扩展语义；FE对应：`异常组类型`↔`异常组基类`，其余父FE经继承链隐式对应（ExceptionGroup同时继承Exception与BaseExceptionGroup）|
|警告体系框架|See also|异常继承框架|警告与异常为领域相邻的独立姊妹体系：无依赖、无继承，仅值得对照查阅|

**未使用关系说明**（质量红线：宁缺毋滥）：`Perspective on`、`Subframe`、`Precedes`、`Causative of`、`Inchoative of`、`Metaphor` 在本主题无合格框架对——异常语料为静态分类与规则刻画，不存在复杂事件阶段序列（Subframe/Precedes前提）、状态‑变化对（Causative/Inchoative前提）、未视角化母框架（Perspective on前提）或跨域映射（Metaphor前提），不硬凑。



