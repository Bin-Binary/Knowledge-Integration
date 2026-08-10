# Python核心基础知识 — 逻辑大纲

> Step 6 衍生品 | 来源: 演进模型_python_core | 用途: 技术文档写作导航

---

## 第0章: 世界观 — 一切皆对象

### 0.1 Python的设计哲学
- The Zen of Python: 可读性 > 简洁性 > 性能
- 语言定位: 解释型、动态类型、强类型、面向对象

### 0.2 对象模型: id/type/value 三元组
- 一切数据都是对象, 变量是引用绑定
- id()返回内存地址, type()返回类型对象
- 可变 vs 不可变: 原地修改 vs 创建新对象
- is(身份比较) vs ==(值比较)

### 0.3 名字绑定与引用语义
- 赋值是名字绑定, 不是值拷贝
- 引用计数: 每次绑定INCREF, 每次解绑DECREF
- 调用栈与名字空间

---

## 第1章: 基石 — 基本数据类型

### 1.1 数值: int/float/complex/bool
- int: 任意精度, 30-bit digit数组
- float: IEEE 754双精度, 64-bit
- bool: int子类, True=1/False=0
- complex: 实部+虚部
- 运算符与魔术方法

### 1.2 文本: str/bytes/bytearray
- str: Unicode码点序列, PEP 393灵活存储
- bytes: 0-255不可变序列
- bytearray: 0-255可变序列
- 编解码: encode/decode

### 1.3 None与切片
- None: 单例, 表示"无值"
- 切片: [start:stop:step] 子序列提取

---

## 第2章: 容器 — 复合数据结构

### 2.1 序列: list与tuple
- list: 动态指针数组, 可变
- tuple: 定长不变数组, 可哈希
- 通用操作: 索引/切片/拼接/成员检查

### 2.2 映射: dict
- 开放寻址哈希表
- O(1)平均查找/插入/删除
- Python 3.7+ 保持插入顺序
- 扩容策略与墓碑

### 2.3 集合: set与frozenset
- set: 无序哈希集合, 可变
- frozenset: 不可变, 可哈希
- 集合运算: & | - ^

### 2.4 哈希与容器协议
- hash()与可哈希对象
- __len__/__getitem__/__contains__ 鸭子协议

---

## 第3章: 骨架 — 控制流

### 3.1 条件分支: if/elif/else
- 真值测试规则(__bool__ / __len__)
- 短路求值 (and/or)
- 三元表达式

### 3.2 循环: for / while / break / continue / else
- for: 迭代器消费
- while: 条件循环
- break/continue/else: 控制流精确操控

### 3.3 模式匹配: match/case
- 字面量/解构/类匹配/守卫条件
- 与switch语句的对比

---

## 第4章: 力量 — 函数与作用域

### 4.1 函数定义与调用
- def创建PyFunctionObject
- 参数系统: 位置/关键字/默认/*args/**kwargs
- return返回值
- lambda: 匿名函数

### 4.2 作用域: LEGB规则
- Local → Enclosing → Global → Built-in
- global / nonlocal 声明
- 闭包: Cell对象捕获自由变量

### 4.3 常用内置函数
- len/range/enumerate/zip/map/filter/sorted
- type/isinstance/issubclass
- print/input/open

---

## 第5章: 引擎 — 迭代与生成

### 5.1 迭代器协议
- __iter__/__next__/StopIteration
- for x in obj 的底层工作流
- 自定义迭代器

### 5.2 生成器与yield
- yield: 暂停+保留状态
- send/throw/close: 双向通信
- yield from: 委派子生成器

### 5.3 推导式
- 列表/集合/字典 推导式
- 生成器表达式
- 嵌套推导式

---

## 第6章: 结构 — 面向对象

### 6.1 类与实例
- class: 创建类型对象
- __init__/__new__ 创建实例
- self: 实例方法的绑定

### 6.2 继承与MRO
- 单继承/多继承
- C3线性化算法
- super()委托

### 6.3 描述符与属性
- 描述符协议: __get__/__set__/__delete__
- property: 内置数据描述符
- classmethod/staticmethod
- __slots__: 内存优化

### 6.4 魔术方法
- __str__/__repr__/__eq__/__hash__
- 运算符重载(__add__/__lt__等)

---

## 第7章: 分布 — 模块与包

### 7.1 模块
- .py文件=模块, __dict__=名字空间
- import流程: 搜索→加载→缓存
- sys.modules缓存机制

### 7.2 包与导入
- __init__.py与命名空间
- 绝对导入 vs 相对导入
- __all__: 公开接口声明

### 7.3 __name__与入口
- __name__ == "__main__"
- 脚本 vs 库的双重身份

---

## 第8章: 保安 — 异常与资源管理

### 8.1 异常层次结构
- BaseException → Exception → 具体异常
- raise: 主动抛出
- 异常链: raise X from Y

### 8.2 try/except/else/finally
- except匹配: isinstance检查
- finally: 始终执行的清理
- else: 无异常时执行

### 8.3 上下文管理器
- __enter__/__exit__ 协议
- with语句: RAII Python版
- contextlib.contextmanager

---

## 第9章: 门户 — 文件与I/O

### 9.1 文件操作 open()
- 文件模式: r/w/a/x + b/t
- 文本I/O vs 二进制I/O
- 缓冲与编码

### 9.2 标准流 stdin/stdout/stderr
- print() → sys.stdout.write
- input() → sys.stdin.readline
- 重定向: 替换sys.stdout

---

## 第10章: 魔法 — 高级特性

### 10.1 装饰器
- @语法糖: f = decorator(f)
- 装饰器工厂: @d(args)
- functools.wraps: 元信息保持
- 应用场景: 日志/计时/缓存/权限

### 10.2 注解与类型提示
- __annotations__字典
- typing模块
- from __future__ import annotations

### 10.3 f-string
- f"{expr}" 内嵌表达式
- 格式说明符 .2f / >10 / %
- 调试模式 f"{x=}"

---

## 第11章: 底层 — 内存与执行模型

### 11.1 引用计数与GC
- ob_refcnt: 引用计数
- 分代GC: gen0/1/2, 阈值触发
- 浅拷贝 vs 深拷贝

### 11.2 GIL: 全局解释器锁
- 单线程字节码执行保证
- I/O时释放, CPU密集无加速
- 替代方案: multiprocessing / C扩展

### 11.3 编译与执行
- 源码→AST→字节码→PVM
- .pyc缓存
- dis.dis()查看字节码
