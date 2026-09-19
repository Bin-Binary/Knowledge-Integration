# Python异常体系 5W2H 问答档案
> 依据：[python-exceptions-framenet.md](./python-exceptions-framenet.md) ＋ [python-exceptions-gapfill.md](./python-exceptions-gapfill.md)
> 协议：qa-5w2h v1（7 问 / 20 子模式 / 聚合形态 / 5 条横向机制）

## 标记图例
- ✅ 锚定（有片段/事实/关系条目直接支撑）
- ◐ 弱推（词汇级或间接支撑）
- ⚠️ 外部（为真但本语料无锚）｜ ⚠️ 缺口（语料未覆盖）
- ❗ 纠偏（误解清单命中）

## What 是什么

### 问1：Python 的异常是什么？

异常是派生自 `BaseException` 的类的实例，用来表示错误状态、沿调用栈传播、被 except 拦截处置。

> 🔍 **拆解**
> - **S1** 派生自 BaseException 的类的实例 → ✅ 片段1
> - **S2** 表示错误状态 → ◐ 词汇级（类名含 "errors"，未直说）
> - **S2** 沿调用栈传播 → ⚠️ 外部（为真，本语料无锚；锚定替代：可被打包成异常组同时传播多个错误 ✅ 片段12）
> - **S2** 被 except 拦截处置 → ✅ 片段4-5

### 问2：异常不是什么？（边界追问）

异常不都是错误——`SystemExit`、`GeneratorExit` 是控制流信号，绕过 Exception 直达根基类；警告也不是异常，它不终止程序。

> 🔍 **拆解**
> - **S附** 异常不都是错误：SystemExit、GeneratorExit 绕过 Exception → ✅ 片段3 ＋ gapfill缺口1（官方："技术上不是错误"）
> - **S附** 警告不是异常、不终止程序 → ✅ 片段14（❗误解8 纠偏）

## Who 谁

### 问3：谁负责管理用户自定义异常？

`Exception`——所有用户自定义异常都应当派生自它，而不是直接继承 BaseException。

> 🔍 **拆解**
> - **W1** 用户异常基类槽 → Exception → ✅ 片段2
> - **❗误解检查** 不应直接继承 BaseException → 命中误解1，纠偏已附

### 问4：异常组能包装谁？

`BaseExceptionGroup` 能包装任意 BaseException 实例；`ExceptionGroup` 只能包装 Exception 实例。

> 🔍 **拆解**
> - **W1** 包装对象槽（异常组使用框架）→ 两者范围不同 → ✅ 片段12-13（❗误解7 纠偏）

### 问5：ZeroDivisionError 的父类是谁？

`ArithmeticError`——它与 OverflowError、FloatingPointError 同为 ArithmeticError 的子类。

> 🔍 **拆解**
> - **W2** ZeroDivisionError —【子类】→ ArithmeticError → ✅ 片段8

### 问6：异常组使用框架在语义上依赖谁？

异常继承框架——这是全部 13 条框架关系中唯一的 Inheritance 边：异常组机制是继承体系的子类型，并新增多异常打包语义。

> 🔍 **拆解**
> - **W2** 框架作实体：异常组使用框架 —【Inheritance】→ 异常继承框架 → ✅ 关系表第二组

### 问7：系统退出类异常有哪些？

`KeyboardInterrupt`、`SystemExit`、`GeneratorExit`——三者都直接继承 BaseException，不经过 Exception。

> 🔍 **拆解**
> - **W3** 系统异常基类槽成员集合 → ✅ 片段3

### 问8：异常体系顶层是什么格局？

根基是 BaseException，其下三大支：Exception（普通与用户自定义异常）、系统退出三异常（直达根）、异常组支（ExceptionGroup 双继承 Exception 与 BaseExceptionGroup）。

> 🔍 **拆解**
> - **W3** 入口框架全景读法 → ✅ 事实1/2/3/8（片段1-3、12-13）

## When 何时

### 问9：什么时候抛 ZeroDivisionError？

当除法或取模运算的第二个参数为 0 时。

> 🔍 **拆解**
> - **T1** 触发条件槽（异常触发场景框架）→ ✅ 片段7

### 问10：except 匹配与异常传播，谁先谁后？

本主题语料为静态分类规范，不含 Precedes 时序锚，此问在本语料内无法回答——运行时的先后顺序请查阅官方 Tutorial 8（Errors and Exceptions）。

> 🔍 **拆解**
> - **T2** Precedes 边为空（13 条关系无一 Precedes）→ 无锚 → 早退条款触发

## Where 何地

### 问11：FileNotFoundError 在继承结构中处于什么位置？

在 OSError 之下——路径为：BaseException → Exception → OSError → FileNotFoundError。

> 🔍 **拆解**
> - **L1** 层级路径 → ✅ 片段2、片段10

### 问12：异常在运行过程中于何处被处理？

本语料为静态规范文档，未覆盖异常在运行过程中的处理位置——建议查阅 Tutorial 8 与官方调试文档。

> 🔍 **拆解**
> - **L2** 运行时位置 → 无锚 → 早退条款触发

## How 如何

### 问13：except 分支怎么排？

1. 子类分支在前；2. 父类分支在后——父类写在前会使子类分支永不执行。

> 🔍 **拆解**
> - **H1** 捕获顺序槽 → ✅ 片段4-5（❗误解3 纠偏：捕获的是子类，不是父类）

### 问14：怎么给异常追加上下文信息？

调用 `add_note(note)`——为异常追加注释文本，回溯打印时自动展示；note 必须为字符串，Python 3.11 起可用。

> 🔍 **拆解**
> - **H1** 操作方法槽 → ✅ 片段11；字符串与版本约束 → ✅ gapfill缺口4（PEP 678）

### 问15：异常组是怎么工作的？

`BaseExceptionGroup` 把多个 BaseException 实例打包成一个组、同时传播多个错误；`ExceptionGroup` 继承它和 Exception 的双重身份，但只能装 Exception 实例。

> 🔍 **拆解**
> - **H2** 机制事实 → ✅ 片段12-13

### 问16：如何设计自定义异常？

① 继承 `Exception`（不是 BaseException）；② 命名以 "Error" 结尾；③ 必要时从多个异常基类组合派生；④ 实例自动携带 args / __traceback__，可用 add_note() 附加上下文。警戒线：直接继承 BaseException 是常见错误。构造器设计与消息格式规范：未见于本语料与补全资料。

> 🔍 **拆解**
> - **H3** 合成式（无锚点产物，多产物合成）→ ① ✅ 片段2 ② ③ ✅ gapfill缺口6（Tutorial ＋ PEP 8）④ ✅ 片段11
> - **H3** 警戒线 → ❗误解1
> - **H3** 构造器设计/消息规范 → ⚠️ 缺口（诚实声明）

### 问17：如何根据异常快速定位问题？

第一层读类型：ZeroDivisionError→除零、TypeError→类型不匹配，LookupError 家族→查找域问题；第二层辨易混：TypeError（运行时类型不匹配）vs NotImplementedError（设计上未实现、待子类覆写）；第三层读回溯：__traceback__ 存储回溯信息。回溯解读与调试工作流：未覆盖，请查阅调试文档。

> 🔍 **拆解**
> - **H3** 类型→问题映射 → ✅ 事实5/6（片段6-10）
> - **H3** 易混判定 → ✅ gapfill缺口2
> - **H3** 回溯载体 → ✅ 片段11
> - **H3** 回溯解读/调试工作流 → ⚠️ 缺口（早退声明）

## How much 多少

### 问18：OSError 有多少个子类？

主文档列举 3 个（部分列举）；完整清单为 12 个，其中 ConnectionError 之下再分 4 个网络子类。

> 🔍 **拆解**
> - **Q1** 精确度阶梯：主文档 → ◐ 部分列举（片段10）→ gapfill → ✅ 完整清单 12 个（缺口5）

### 问19：__traceback__ 有多重要？

核心——删除该槽后"异常对象携带什么信息"的刻画不再完整；它同时是 add_note() / with_traceback() 的作用对象。

> 🔍 **拆解**
> - **Q2** 核心度标注：核心属性槽 = 核心 → ✅ 框架表（判定依据：删除测试）

### 问20：这套异常文档讲了多少？

7 个子框架＋1 个入口框架、9 条事实、13 条框架关系（Using×11 / Inheritance×1 / See also×1）、6 条缺口全部补全（6/6 ✅）、8 条误解、14 个语料片段。

> 🔍 **拆解**
> - **Q3** 统计汇总 → ✅ 文档自身统计

## Why 为何

### 问21：为什么 except 捕获不了子类？

前提为假——except 恰恰**能**捕获子类，捕获不了的是**父类**。

> 🔍 **拆解**
> - **Y0** 前提校验："捕获不了子类" 与事实4 矛盾 → 前提为假 → 纠偏止步（❗误解3 反向）
> - （不进入 Y1-Y3）

### 问22：为什么会抛 TypeError？

因为操作或函数被作用于类型不恰当的对象。

> 🔍 **拆解**
> - **Y1** 触发条件的因果读法 → ✅ 片段6

### 问23：为什么 GeneratorExit 不继承 Exception？

官方理由：它在技术上不是错误，因此直接继承 BaseException 而非 Exception。

> 🔍 **拆解**
> - **Y2** 设计理据 → 主文档未说明（缺口1）→ gapfill → ✅ Built-in Exceptions · GeneratorExit 条目（官方原话）

### 问24：为什么自定义异常应当继承 Exception？

教程明确规定所有用户自定义异常应当派生自 Exception；PEP 8 另约定异常命名以 "Error" 结尾。

> 🔍 **拆解**
> - **Y3** 规范理由 → ✅ gapfill缺口6（Tutorial · User-defined Exceptions ＋ PEP 8 · Exception Names）

## 覆盖度自检

| 子模式 | 例题 | 子模式 | 例题 |
|---|---|---|---|
| S1 / S2 / S附 | 问1 / 问1 / 问2 | H1 / H2 / H3 | 问13-14 / 问15 / 问16-17 |
| W1 / W2 / W3 | 问3-4 / 问5-6 / 问7-8 | Q1 / Q2 / Q3 | 问18 / 问19 / 问20 |
| T1 / T2 | 问9 / 问10（早退示范） | Y0 / Y1 / Y2 / Y3 | 问21 / 问22 / 问23 / 问24 |
| L1 / L2 | 问11 / 问12（早退示范） | | |

20/20 子模式全覆盖；早退示范 3 例（T2、L2、H3 部分缺口）；前提校验示范 1 例；精确度阶梯示范 1 例。