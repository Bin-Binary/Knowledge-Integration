# Python异常体系 FrameNet 语义框架标注文档
> 文档结构：##说明 → ##原文和翻译 → ##事实 → ##缺口 → ##误解 → ##异常框架（Markdown表格） → ##异常框架间关系 → ##完整提示词

## 说明
1. 本文件基于Python官方内置异常文档，采用**FrameNet框架语义学**进行建模。
2. 框架元素FE为抽象语义槽；**事实为槽填充客观内容；缺口是从原始语料推导出来的知识缺失点；误解是基于语料推导的学习者可能产生的错误理解**。
3. 原文与翻译一一对应，原文后紧跟中文翻译；
4. 框架关系使用FrameNet标准关系标签：`Inheritance`、`Is a Punctualization of`、`Using`、`Parallels`；
5. 原始语料定位记录原文出处、片段位置与参考链接。

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
1. 异常根基类为 `BaseException`，所有异常实例必须继承它。
2. `Exception` 是普通内置异常、用户自定义异常的基类；系统退出异常不继承 `Exception`。
3. `KeyboardInterrupt`、`SystemExit`、`GeneratorExit` 直接继承 `BaseException`。
4. except 捕获**子类异常**，不能捕获父类异常；捕获顺序必须子类在前，父类在后。
5. `TypeError`：对象类型不匹配触发；`ZeroDivisionError`：除数为0触发。
6. 异常层级：`ArithmeticError` → `ZeroDivisionError`；`LookupError` → `IndexError`/`KeyError`；`OSError` → `FileNotFoundError`；`ValueError` → `UnicodeError`。
7. 异常对象内置属性：`args`、`__traceback__`、`__notes__`；内置方法：`with_traceback()`、`add_note()`。
8. `BaseExceptionGroup` 可以包装任意 `BaseException`；`ExceptionGroup` 只能包装 `Exception`。
9. `Warning` 为警告体系顶层基类；警告是非致命提示，不中断程序，独立于异常体系。

## 缺口
> 从原始语料分析得出的**知识缺口**：语料没有明确说明、缺少定义、边界模糊的点，属于分析中间产物
1. 原文没有明确说明 `GeneratorExit` 的完整继承行为细节。
2. 原文没有给出 `NotImplementedError` 与 `TypeError` 的区分判定标准。
3. 原文没有说明异常组在try‑except中的捕获匹配规则。
4. 原文没有说明 `__notes__` 属性的读写约束与版本兼容性。
5. 原文没有列举全部 `OSError` 的子类完整清单。
6. 原文没有说明用户自定义异常，除了继承 `Exception` 之外的最佳实践约束。

## 误解
> 从原始语料推导的学习者**潜在错误理解**，属于分析中间产物
1. 误以为用户自定义异常可以直接继承 `BaseException`。
2. 认为 `KeyboardInterrupt`、`SystemExit` 继承自 `Exception`。
3. 认为except捕获父类就可以捕获子类；写except时父类处理分支写在前，子类分支永远不会执行。
4. 将参数取值错误归为 `TypeError`，将类型错误归为 `ValueError`。
5. 认为所有异常类互相平级，不存在公共父类。
6. 不知道异常实例自带 `args`、`__traceback__`、`add_note()` 等属性方法。
7. 混淆 `ExceptionGroup` 和 `BaseExceptionGroup` 的包装对象范围。
8. 将Warning警告当成Exception异常，认为警告会终止程序运行。

## 异常框架（Markdown表格）
|框架名称|刻画描述|框架元素（FE）及填充|原始事实语料|原始语料定位|
|---|---|---|---|---|
|异常继承框架|刻画异常间的继承关系及基类规则|`根基类`: BaseException<br>`用户异常基类`: Exception<br>`系统异常基类`: KeyboardInterrupt/SystemExit/GeneratorExit<br>`异常组基类`: ExceptionGroup/BaseExceptionGroup|1. Python所有异常都必须是BaseException子类的实例。<br>2. Exception是所有非系统退出内置异常的父类；用户自定义异常应当继承Exception。<br>3. KeyboardInterrupt、SystemExit、GeneratorExit直接继承BaseException，不继承Exception。<br>4. ExceptionGroup继承Exception与BaseExceptionGroup；BaseExceptionGroup可以封装任意BaseException实例。|原文片段1‑3、12‑13；参考链接：Python Built‑in Exceptions|
|异常捕获逻辑框架|描述except子句对异常的捕获规则|`捕获对象`: 派生类异常<br>`捕获顺序`: 子类在前、父类在后|1. except子句匹配异常类时，可以捕获该类及其所有子类异常。<br>2. except不能捕获父类异常；编码时子类异常捕获分支必须写在父类捕获分支之前。|原文片段4‑5；参考链接：Python Errors and Exceptions|
|异常触发场景框架|刻画不同异常的具体触发条件|`触发条件`: 类型不匹配、除数为0、索引越界、键不存在等<br>`对应异常`: TypeError、ZeroDivisionError、IndexError、KeyError等|1. TypeError：操作/函数作用于类型不匹配对象时抛出。<br>2. ZeroDivisionError：算术运算除数为0抛出。<br>3. IndexError：序列索引无效；KeyError：字典键不存在。<br>4. 参数类型错误属于TypeError；参数取值错误属于ValueError。|原文片段6‑7；参考链接：Python Built‑in Exceptions|
|异常层级关系框架|描述具体异常间的父子层级结构|`父类异常`: ArithmeticError、LookupError、OSError、ValueError等<br>`子类异常`: ZeroDivisionError、IndexError、FileNotFoundError、UnicodeDecodeError等|1. ArithmeticError是ZeroDivisionError、OverflowError、FloatingPointError的父类。<br>2. LookupError是IndexError、KeyError的父类。<br>3. OSError包含FileNotFoundError、PermissionError、ConnectionError等子类。<br>4. UnicodeError是ValueError的子类。|原文片段8‑10；参考链接：Python Built‑in Exceptions|
|异常属性与方法框架|刻画异常对象的核心属性和操作方法|`核心属性`: args、__traceback__、__notes__<br>`操作方法`: with_traceback(tb)、add_note(note)|1. args：异常构造函数接收的参数元组。<br>2. __traceback__：存储异常回溯信息的可写字段。<br>3. with_traceback(tb)：为异常对象绑定回溯，返回当前异常实例。<br>4. add_note(note)：为异常追加注释文本，在异常回溯打印时展示。|原文片段11；参考链接：Python Built‑in Exceptions|
|异常组使用框架|描述用于同时传播多个异常的特殊机制|`异常组类型`: ExceptionGroup、BaseExceptionGroup<br>`包装对象`: 多个异常实例|1. BaseExceptionGroup用于打包、同时抛出多个BaseException类型异常。<br>2. ExceptionGroup继承BaseExceptionGroup与Exception，仅能封装Exception类型异常实例。|原文片段12‑13；参考链接：Python Exception Groups|
|警告体系框架|刻画独立于异常的非致命问题提示体系|`警告基类`: Warning<br>`具体警告类型`: DeprecationWarning、BytesWarning、ResourceWarning等|1. Warning是所有警告类型的顶层基类。<br>2. 警告不会终止程序执行，属于非致命提示，语义上独立于异常体系。|原文片段14；参考链接：Python warnings|

## 异常框架间关系
> FrameNet标准关系：`Inheritance`（继承）、`Is a Punctualization of`（实例化）、`Using`（使用/依赖）、`Parallels`（平行）

|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|异常层级关系框架|Is a Punctualization of|异常继承框架|源框架是抽象继承框架的实例化，把抽象继承规则落地到Python真实异常类父子关系|
|异常捕获逻辑框架|Using|异常继承框架|源框架语义成立，必须使用目标框架的继承语义作为前提，不继承框架本身|
|异常触发场景框架|Is a Punctualization of|异常层级关系框架|源框架为层级框架内的异常实体填充具体触发场景实例|
|异常属性与方法框架|Using|异常继承框架|源框架描述的对象集合，使用继承框架划定的BaseException实例范围|
|异常组使用框架|Inheritance|异常继承框架|源框架继承目标框架全部语义，同时新增多异常打包传播的扩展语义|
|警告体系框架|Parallels|异常继承框架|源框架与目标框架领域平行，属于独立语义分支，不存在依赖或继承|
