# Python异常体系 缺口扩展资料

> 本文件为 generate-frame 可选项①产出，与主文档 `python-exceptions-framenet.md` 同级，被其「##缺口」章节引用。
> 补全资料仅来自官方/权威源；独立呈现，**不进入主文档事实清单与框架表FE填充**。

## 来源与红线声明
- 来源白名单：官方文档 > PEP > 官方语言参考/库参考 > 官方教程 > 领域权威标准
- 补全状态三档：✅已补全 / ◐部分补全 / ❌未找到权威资料
- 与原文冲突时以 ⚠️冲突提示 单独标注，不改动主文档事实

## 补全表

|缺口编号|补全资料|权威来源与定位|补全状态|
|---|---|---|---|
|缺口1|`GeneratorExit` 在生成器或协程被关闭时抛出（见 `generator.close()` / `coroutine.close()`）；直接继承 `BaseException` 而非 `Exception`，官方理由是"它在技术上不是错误"（not an error）|Python 官方文档 Built‑in Exceptions — GeneratorExit 条目|✅已补全|
|缺口2|`NotImplementedError` 派生自 `RuntimeError`，用于用户自定义基类中"要求子类必须覆写的抽象方法"。判定标准：类型不匹配→`TypeError`；设计上未实现、待子类覆写→`NotImplementedError`|Python 官方文档 Built‑in Exceptions — NotImplementedError 条目|✅已补全|
|缺口3|Python 3.11 新增 `except*` 子句：按叶子异常类型对异常组**拆分匹配**，同一次引发的异常组可被多个 `except*` 子句分别处理；每个叶子异常至多匹配一个子句；未匹配部分重组为新异常组继续传播；普通 `except` 对异常组按整体类型匹配、无法拆分子组；`except` 与 `except*` 不可在同一 try 语句混用|PEP 654 — Exception Groups and except*；Python Tutorial — Exception Groups；What's New in Python 3.11|✅已补全|
|缺口4|`add_note(note)` 为 Python 3.11 新增：`note` 必须为 `str`，追加到 `__notes__`（字符串列表，首次调用时创建）；异常回溯打印时自动展示；3.11 之前版本无此机制|PEP 678 — Enriching Exceptions with Notes；Built‑in Exceptions — BaseException.add_note|✅已补全|
|缺口5|`OSError` 子类全集：`BlockingIOError`、`ChildProcessError`、`ConnectionError`（含 `BrokenPipeError`、`ConnectionAbortedError`、`ConnectionRefusedError`、`ConnectionResetError`）、`FileExistsError`、`FileNotFoundError`、`InterruptedError`、`IsADirectoryError`、`NotADirectoryError`、`PermissionError`、`ProcessLookupError`、`TimeoutError`；`OSError` 以两个以上参数构造时携带 `errno`/`strerror`，具体子类由 `errno` 值决定|Python 官方文档 Built‑in Exceptions — OSError 及其子类条目|✅已补全|
|缺口6|①自定义异常类通常应派生自 `Exception`（官方教程明确）；②异常命名以 "Error" 结尾（教程与 PEP 8 命名约定一致）；③必要时可从多个异常基类组合派生|Python Tutorial — User‑defined Exceptions；PEP 8 — Exception Names|✅已补全|

## 冲突提示区
本轮无与原文冲突条目。


