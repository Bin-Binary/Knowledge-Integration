# Python内置函数 FrameNet 语义框架标注文档
> 文档结构：##说明 → ##原文和翻译 → ##事实 → ##缺口 → ##误解 → ##Python内置函数框架 → ##Python内置函数框架间关系

## 说明
1. 本文件基于 Python 3.14 官方文档 `builtins/functions.txt`（https://docs.python.org/3/library/functions.html），采用**FrameNet框架语义学**进行建模。
2. 框架元素FE为抽象语义槽；**事实为槽填充客观内容；缺口是从原始语料推导出来的知识缺失点；误解是基于语料推导的学习者可能产生的错误理解**。
3. 原文与翻译一一对应，原文后紧跟中文翻译；
4. 框架关系使用FrameNet标准9种关系标签：`Inheritance`、`Perspective on`、`Using`、`Subframe`、`Precedes`、`Causative of`、`Inchoative of`、`Metaphor`、`See also`；
5. 原始语料定位记录原文出处、片段位置与参考链接。
6. 本次分析未启用可选项（缺口补全 / HTML统一视图）。
7. 问答档案（qa-5w2h 技能产出）：见 Python内置函数-qa.md

## 原文和翻译
> 来源：Python 3.14 官方文档 builtins/functions.txt（https://docs.python.org/3/library/functions.html）

1.
> Original: The Python interpreter has a number of functions and types built into it that are always available. They are listed here in alphabetical order.
> 翻译：Python 解释器内置了许多始终可用的函数和类型。它们在此按字母顺序排列。

2.
> Original: abs(number, /) — Return the absolute value of a number. The argument may be an integer, a floating-point number, or an object implementing "__abs__()". If the argument is a complex number, its magnitude is returned.
> 翻译：abs(number, /) — 返回一个数的绝对值。参数可以是整数、浮点数或实现了 "__abs__()" 方法的对象。如果参数是复数，则返回其模。

3.
> Original: aiter(async_iterable, /) — Return an asynchronous iterator for an asynchronous iterable. Equivalent to calling "x.__aiter__()". Note: Unlike "iter()", "aiter()" has no 2-argument variant. Added in version 3.10.
> 翻译：aiter(async_iterable, /) — 返回一个异步可迭代对象的异步迭代器。等价于调用 "x.__aiter__()"。注意：与 "iter()" 不同，"aiter()" 没有两参数变体。3.10 版新增。

4.
> Original: all(iterable, /) — Return True if all elements of the iterable are true (or if the iterable is empty). Equivalent to: (for loop returning False on first falsy element, True otherwise).
> 翻译：all(iterable, /) — 如果可迭代对象的所有元素都为真（或可迭代对象为空），则返回 True。等价于：（遇到第一个假值元素即返回 False，否则返回 True 的 for 循环）。

5.
> Original: awaitable anext(async_iterator, /) / awaitable anext(async_iterator, default, /) — When awaited, return the next item from the given asynchronous iterator, or default if given and the iterator is exhausted. This is the async variant of the "next()" builtin. This calls "__anext__()" method, returning an awaitable. If default is given, it is returned if the iterator is exhausted, otherwise "StopAsyncIteration" is raised. Added in version 3.10.
> 翻译：awaitable anext(async_iterator, /) / awaitable anext(async_iterator, default, /) — 被等待时，从给定异步迭代器返回下一个元素；若提供了 default 且迭代器已耗尽，则返回 default。这是 "next()" 内置函数的异步变体。调用 "__anext__()" 方法，返回一个可等待对象。若提供了 default，迭代器耗尽时返回之；否则抛出 "StopAsyncIteration"。3.10 版新增。

6.
> Original: any(iterable, /) — Return True if any element of the iterable is true. If the iterable is empty, return False.
> 翻译：any(iterable, /) — 如果可迭代对象中有任何元素为真，则返回 True。如果可迭代对象为空，返回 False。

7.
> Original: ascii(object, /) — As repr(), return a string containing a printable representation of an object, but escape the non-ASCII characters in the string returned by repr() using \x, \u, or \U escapes.
> 翻译：ascii(object, /) — 与 repr() 类似，返回包含对象可打印表示的字符串，但对 repr() 返回字符串中的非 ASCII 字符使用 \x、\u 或 \U 转义。

8.
> Original: bin(integer, /) — Convert an integer number to a binary string prefixed with "0b". The result is a valid Python expression. If integer is not a Python int object, it has to define an "__index__()" method.
> 翻译：bin(integer, /) — 将整数转换为以 "0b" 为前缀的二进制字符串。结果是有效的 Python 表达式。如果 integer 不是 Python int 对象，它必须定义 "__index__()" 方法。

9.
> Original: class bool(object=False, /) — Return a Boolean value, i.e. one of True or False. The argument is converted using the standard truth testing procedure. The bool class is a subclass of int. It cannot be subclassed further. Its only instances are False and True.
> 翻译：class bool(object=False, /) — 返回布尔值，即 True 或 False 之一。参数通过标准真值测试过程转换。bool 类是 int 的子类。它不能被进一步子类化。其仅有的实例是 False 和 True。

10.
> Original: breakpoint(*args, **kws) — This function drops you into the debugger at the call site. Specifically, it calls sys.breakpointhook(), passing args and kws straight through. By default, sys.breakpointhook() calls pdb.set_trace() expecting no arguments. The behavior can be changed with the PYTHONBREAKPOINT environment variable. Raises an auditing event "builtins.breakpoint". Added in version 3.7.
> 翻译：breakpoint(*args, **kws) — 此函数在调用点进入调试器。具体地，它调用 sys.breakpointhook()，直接传递 args 和 kws。默认地，sys.breakpointhook() 调用 pdb.set_trace()。行为可通过 PYTHONBREAKPOINT 环境变量改变。触发审计事件 "builtins.breakpoint"。3.7 版新增。

11.
> Original: class bytearray(source=b'') / class bytearray(source, encoding, errors='strict') — Return a new array of bytes. The bytearray class is a mutable sequence of integers in the range 0 <= x < 256. Source can be a string (with encoding), an integer (size), a buffer interface object, or an iterable of integers.
> 翻译：class bytearray(source=b'') / class bytearray(source, encoding, errors='strict') — 返回新的字节数组。bytearray 类是 0 <= x < 256 范围内的可变整数序列。source 可以是字符串（需 encoding）、整数（大小）、缓冲区接口对象或整数可迭代对象。

12.
> Original: class bytes(source=b'') / class bytes(source, encoding, errors='strict') — Return a new bytes object which is an immutable sequence of integers in the range 0 <= x < 256. bytes is an immutable version of bytearray. Bytes objects can also be created with literals.
> 翻译：class bytes(source=b'') / class bytes(source, encoding, errors='strict') — 返回新的 bytes 对象，是 0 <= x < 256 范围内的不可变整数序列。bytes 是 bytearray 的不可变版本。bytes 对象也可用字面量创建。

13.
> Original: callable(object, /) — Return True if the object argument appears callable, False if not. If this returns True, it is still possible that a call fails, but if it is False, calling object will never succeed. Classes are callable; instances are callable if their class has a __call__() method. Added in version 3.2 (brought back).
> 翻译：callable(object, /) — 如果对象参数看起来可调用，返回 True，否则返回 False。返回 True 时调用仍可能失败，但返回 False 时调用绝不会成功。类是可调用的；实例在其类有 __call__() 方法时可调用。3.2 版恢复。

14.
> Original: chr(codepoint, /) — Return the string representing a character with the specified Unicode code point. This is the inverse of ord(). The valid range for the argument is from 0 through 1,114,111 (0x10FFFF). ValueError will be raised if outside that range.
> 翻译：chr(codepoint, /) — 返回指定 Unicode 码位的字符字符串。这是 ord() 的逆函数。参数有效范围是 0 到 1,114,111 (0x10FFFF)。超出范围将抛出 ValueError。

15.
> Original: @classmethod — Transform a method into a class method. A class method receives the class as an implicit first argument. Can be called on the class or on an instance. Class methods are different than C++ or Java static methods.
> 翻译：@classmethod — 将方法转换为类方法。类方法以类作为隐式第一个参数。可在类或实例上调用。类方法不同于 C++ 或 Java 的静态方法。

16.
> Original: compile(source, filename, mode, flags=0, dont_inherit=False, optimize=-1) — Compile the source into a code or AST object. Code objects can be executed by exec() or eval(). source can be a string, bytes, or AST object. mode can be 'exec', 'eval', or 'single'. Raises SyntaxError or ValueError if invalid. Raises auditing event "compile".
> 翻译：compile(source, filename, mode, flags=0, dont_inherit=False, optimize=-1) — 将源码编译为代码对象或 AST 对象。代码对象可被 exec() 或 eval() 执行。source 可以是字符串、字节串或 AST 对象。mode 可以是 'exec'、'eval' 或 'single'。无效时抛出 SyntaxError 或 ValueError。触发审计事件 "compile"。

17.
> Original: class complex(number=0, /) / class complex(string, /) / class complex(real=0, imag=0) — Convert a single string or number to a complex number, or create a complex number from real and imaginary parts. If argument is a string, must contain real/imaginary part; if a number, delegates to __complex__(), falls back to __float__() then __index__(). If all arguments omitted, returns 0j.
> 翻译：class complex(number=0, /) / class complex(string, /) / class complex(real=0, imag=0) — 将单个字符串或数字转换为复数，或从实部和虚部创建复数。若参数为字符串，须含实部/虚部；若为数字，委托 __complex__()，回退 __float__() 再 __index__()。若省略所有参数，返回 0j。

18.
> Original: delattr(object, name, /) — This is a relative of setattr(). The arguments are an object and a string. The string must be the name of one of the object's attributes. The function deletes the named attribute, provided the object allows it. delattr(x, 'foobar') is equivalent to del x.foobar. name need not be a Python identifier.
> 翻译：delattr(object, name, /) — 这是 setattr() 的相关函数。参数为对象和字符串。字符串必须是对象某个属性的名称。函数删除该属性（前提是对象允许）。delattr(x, 'foobar') 等价于 del x.foobar。name 不必是 Python 标识符。

19.
> Original: class dict(**kwargs) / class dict(mapping, /, **kwargs) / class dict(iterable, /, **kwargs) — Create a new dictionary. The dict object is the dictionary class.
> 翻译：class dict(**kwargs) / class dict(mapping, /, **kwargs) / class dict(iterable, /, **kwargs) — 创建新字典。dict 对象是字典类。

20.
> Original: dir() / dir(object, /) — Without arguments, return the list of names in the current local scope. With an argument, attempt to return a list of valid attributes for that object. If the object has __dir__(), this method will be called. The resulting list is sorted alphabetically. dir() is supplied primarily as a convenience for use at an interactive prompt.
> 翻译：dir() / dir(object, /) — 无参数时，返回当前局部作用域的名称列表。有参数时，尝试返回该对象的有效属性列表。若对象有 __dir__() 方法则调用之。结果列表按字母排序。dir() 主要作为交互式提示的便利工具提供。

21.
> Original: divmod(a, b, /) — Take two (non-complex) numbers as arguments and return a pair of numbers consisting of their quotient and remainder. For integers, result is (a // b, a % b). For floating-point, result is (q, a % b) where q is usually math.floor(a / b).
> 翻译：divmod(a, b, /) — 接受两个（非复数）数字作为参数，返回由商和余数组成的数对。对于整数，结果为 (a // b, a % b)。对于浮点数，结果为 (q, a % b)，其中 q 通常为 math.floor(a / b)。

22.
> Original: enumerate(iterable, start=0) — Return an enumerate object. The __next__() method returns a tuple containing a count (from start) and the values from iterating over iterable.
> 翻译：enumerate(iterable, start=0) — 返回一个枚举对象。__next__() 方法返回包含计数（从 start 开始）和迭代值的元组。

23.
> Original: eval(source, /, globals=None, locals=None) — Parse and evaluate source as a Python expression using globals and locals mappings. If globals dictionary does not contain __builtins__, a reference to builtins is inserted. Warning: This function executes arbitrary code. Calling it with untrusted input will lead to security vulnerabilities.
> 翻译：eval(source, /, globals=None, locals=None) — 使用 globals 和 locals 映射将 source 解析并求值为 Python 表达式。如果 globals 字典不含 __builtins__，会插入内置模块引用。警告：此函数执行任意代码。对不受信任的输入调用将导致安全漏洞。

24.
> Original: exec(source, /, globals=None, locals=None, *, closure=None) — This function supports dynamic execution of Python code. source must be either a string or a code object. The return value is None. If globals dictionary does not contain __builtins__, a reference to builtins is inserted. The closure argument specifies a closure--a tuple of cellvars. Warning: executes arbitrary code.
> 翻译：exec(source, /, globals=None, locals=None, *, closure=None) — 此函数支持 Python 代码的动态执行。source 必须是字符串或代码对象。返回值为 None。如果 globals 字典不含 __builtins__，会插入内置模块引用。closure 参数指定闭包——一个 cellvar 元组。警告：执行任意代码。

25.
> Original: filter(function, iterable, /) — Construct an iterator from those elements of iterable for which function is true. If function is None, the identity function is assumed (all false elements removed). filter(function, iterable) is equivalent to the generator expression (item for item in iterable if function(item)).
> 翻译：filter(function, iterable, /) — 从可迭代对象中 function 为真的元素构造迭代器。如果 function 为 None，假定恒等函数（移除所有假值元素）。filter(function, iterable) 等价于生成器表达式 (item for item in iterable if function(item))。

26.
> Original: class float(number=0.0, /) / class float(string, /) — Return a floating-point number constructed from a number or a string. If argument is a string, must conform to floatvalue grammar. If argument is an integer or float, return the same value. For a general Python object x, float(x) delegates to x.__float__(), falls back to x.__index__(). If no argument, returns 0.0.
> 翻译：class float(number=0.0, /) / class float(string, /) — 从数字或字符串构造浮点数。如果参数为字符串，须符合 floatvalue 文法。如果参数为整数或浮点数，返回相同值。对于一般 Python 对象 x，float(x) 委托 x.__float__()，回退 x.__index__()。若无参数，返回 0.0。

27.
> Original: format(value, format_spec='', /) — Convert a value to a formatted representation, as controlled by format_spec. The default format_spec is an empty string which usually gives the same effect as calling str(value). A call to format(value, format_spec) is translated to type(value).__format__(value, format_spec).
> 翻译：format(value, format_spec='', /) — 将值转换为格式化表示，由 format_spec 控制。默认 format_spec 为空字符串，通常与 str(value) 效果相同。format(value, format_spec) 调用被转换为 type(value).__format__(value, format_spec)。

28.
> Original: class frozenset(iterable=(), /) — Return a new frozenset object, optionally with elements taken from iterable. frozenset is a built-in class.
> 翻译：class frozenset(iterable=(), /) — 返回新的 frozenset 对象，可选地取 iterable 中的元素。frozenset 是内置类。

29.
> Original: getattr(object, name, /) / getattr(object, name, default, /) — Return the value of the named attribute of object. If the named attribute does not exist, default is returned if provided, otherwise AttributeError is raised. getattr(x, 'foobar') is equivalent to x.foobar. name need not be a Python identifier.
> 翻译：getattr(object, name, /) / getattr(object, name, default, /) — 返回对象命名属性的值。如属性不存在，提供 default 则返回之，否则抛出 AttributeError。getattr(x, 'foobar') 等价于 x.foobar。name 不必是 Python 标识符。

30.
> Original: globals() — Return the dictionary implementing the current module namespace. For code within functions, this is set when the function is defined and remains the same regardless of where the function is called.
> 翻译：globals() — 返回实现当前模块命名空间的字典。对于函数内的代码，这在函数定义时设置，无论函数在哪里被调用都保持不变。

31.
> Original: hasattr(object, name, /) — The arguments are an object and a string. The result is True if the string is the name of one of the object's attributes, False if not. (Implemented by calling getattr(object, name) and seeing whether it raises AttributeError.)
> 翻译：hasattr(object, name, /) — 参数为对象和字符串。如果字符串是对象某个属性的名称，返回 True，否则返回 False。（通过调用 getattr(object, name) 并检查是否抛出 AttributeError 实现。）

32.
> Original: hash(object, /) — Return the hash value of the object (if it has one). Hash values are integers used to quickly compare dictionary keys during a dictionary lookup. Numeric values that compare equal have the same hash value. For objects with custom __hash__(), hash() truncates the return value based on the host machine bit width.
> 翻译：hash(object, /) — 返回对象的哈希值（如果有的话）。哈希值是整数，用于字典查找时快速比较键。比较相等的数值具有相同的哈希值。对于自定义 __hash__() 的对象，hash() 根据宿主机位宽截断返回值。

33.
> Original: help() / help(request) — Invoke the built-in help system. If no argument, interactive help starts on the console. If argument is a string, looked up as module/function/class/keyword/topic name. If any other object, a help page on the object is generated. Added to built-in namespace by the site module.
> 翻译：help() / help(request) — 调用内置帮助系统。无参数时，在控制台启动交互式帮助。参数为字符串时，查找模块/函数/类/关键字/主题名。其他对象则生成该对象的帮助页面。由 site 模块添加到内置命名空间。

34.
> Original: hex(integer, /) — Convert an integer number to a lowercase hexadecimal string prefixed with "0x". If integer is not a Python int object, it has to define an __index__() method.
> 翻译：hex(integer, /) — 将整数转换为以 "0x" 为前缀的小写十六进制字符串。如果 integer 不是 Python int 对象，它必须定义 "__index__()" 方法。

35.
> Original: id(object, /) — Return the identity of an object. This is an integer guaranteed to be unique and constant for this object during its lifetime. Two objects with non-overlapping lifetimes may have the same id() value. CPython implementation detail: This is the address of the object in memory.
> 翻译：id(object, /) — 返回对象的标识。这是保证在对象生命周期内唯一且不变的整数。两个非重叠生命周期的对象可能有相同的 id() 值。CPython 实现细节：这是对象在内存中的地址。

36.
> Original: input() / input(prompt, /) — If prompt is present, it is written to standard output without a trailing newline. The function then reads a line from input, converts it to a string (stripping trailing newline), and returns that. When EOF is read, EOFError is raised.
> 翻译：input() / input(prompt, /) — 如果 prompt 存在，将其写入标准输出（不带尾随换行）。然后从输入读取一行，转换为字符串（剥离尾随换行）并返回。读到 EOF 时抛出 EOFError。

37.
> Original: class int(number=0, /) / class int(string, /, base=10) — Return an integer object constructed from a number or a string, or return 0 if no arguments. If argument defines __int__(), int(x) returns x.__int__(). If defines __index__(), returns x.__index__(). Base allowed: 0 and 2-36. int() no longer delegates to __trunc__() in 3.14.
> 翻译：class int(number=0, /) / class int(string, /, base=10) — 从数字或字符串构造整数对象，无参数时返回 0。若参数定义了 __int__()，int(x) 返回 x.__int__()。若定义了 __index__()，返回 x.__index__()。允许的进制：0 和 2-36。3.14 版 int() 不再委托 __trunc__()。

38.
> Original: isinstance(object, classinfo, /) — Return True if the object argument is an instance of the classinfo argument, or of a (direct, indirect, or virtual) subclass thereof. classinfo can be a tuple of type objects or a Union Type.
> 翻译：isinstance(object, classinfo, /) — 如果 object 参数是 classinfo 参数的实例（包括直接、间接或虚拟子类），返回 True。classinfo 可以是类型对象元组或 Union 类型。

39.
> Original: issubclass(class, classinfo, /) — Return True if class is a subclass (direct, indirect, or virtual) of classinfo. A class is considered a subclass of itself. classinfo may be a tuple of class objects or a Union Type.
> 翻译：issubclass(class, classinfo, /) — 如果 class 是 classinfo 的子类（直接、间接或虚拟），返回 True。类被视为自身的子类。classinfo 可以是类对象元组或 Union 类型。

40.
> Original: iter(iterable, /) / iter(callable, sentinel, /) — Return an iterator object. Without second argument, the single argument must support __iter__() or __getitem__(). If second argument sentinel is given, first argument must be callable; iterator calls it until sentinel is reached.
> 翻译：iter(iterable, /) / iter(callable, sentinel, /) — 返回迭代器对象。无第二参数时，单一参数须支持 __iter__() 或 __getitem__()。如果有第二参数 sentinel，第一参数须可调用；迭代器调用之直到返回 sentinel。

41.
> Original: len(object, /) — Return the length (the number of items) of an object. The argument may be a sequence or a collection. CPython detail: len raises OverflowError on lengths larger than sys.maxsize.
> 翻译：len(object, /) — 返回对象的长度（项数）。参数可以是序列或集合。CPython 细节：len 对大于 sys.maxsize 的长度抛出 OverflowError。

42.
> Original: class list(iterable=(), /) — Rather than being a function, list is actually a mutable sequence type.
> 翻译：class list(iterable=(), /) — list 实际上是可变序列类型，而非函数。

43.
> Original: locals() — Return a mapping object representing the current local symbol table. In optimized scopes (functions, generators, coroutines), each call returns a fresh dictionary; changes via returned dict are not written back. In other scopes, changes through the mapping object are visible as local variable changes. PEP 667.
> 翻译：locals() — 返回表示当前局部符号表的映射对象。在优化作用域（函数、生成器、协程）中，每次调用返回新字典；通过返回字典所做的更改不会写回。在其他作用域中，通过映射对象的更改可见为局部变量更改。PEP 667。

44.
> Original: map(function, iterable, /, *iterables, strict=False) — Return an iterator that applies function to every item of iterable. With multiple iterables, stops when shortest is exhausted. If strict=True and one iterable exhausted before others, ValueError is raised. Added strict parameter in 3.14.
> 翻译：map(function, iterable, /, *iterables, strict=False) — 返回将 function 应用于可迭代对象每个元素的迭代器。多个可迭代对象时，最短耗尽即停止。strict=True 时，一个先耗尽则抛出 ValueError。3.14 版新增 strict 参数。

45.
> Original: max(iterable, /, *, key=None) / max(iterable, /, *, default, key=None) / max(arg1, arg2, /, *args, key=None) — Return the largest item. key specifies ordering function; default specifies return if iterable empty. If multiple items are maximal, returns first encountered.
> 翻译：max(iterable, /, *, key=None) 等 — 返回最大项。key 指定排序函数；default 指定可迭代对象为空时的返回值。多个最大项时返回第一个遇到的。

46.
> Original: class memoryview(object) — Return a memory view object created from the given argument.
> 翻译：class memoryview(object) — 返回从给定参数创建的内存视图对象。

47.
> Original: min(iterable, /, *, key=None) / min(iterable, /, *, default, key=None) / min(arg1, arg2, /, *args, key=None) — Return the smallest item. key specifies ordering function; default specifies return if iterable empty. If multiple items are minimal, returns first encountered.
> 翻译：min(iterable, /, *, key=None) 等 — 返回最小项。key 指定排序函数；default 指定可迭代对象为空时的返回值。多个最小项时返回第一个遇到的。

48.
> Original: next(iterator, /) / next(iterator, default, /) — Retrieve the next item from the iterator by calling its __next__() method. If default is given, returned if iterator exhausted, otherwise StopIteration is raised.
> 翻译：next(iterator, /) / next(iterator, default, /) — 通过调用 __next__() 方法从迭代器获取下一项。有 default 则迭代器耗尽时返回之，否则抛出 StopIteration。

49.
> Original: class object — This is the ultimate base class of all other classes. It has methods common to all instances of Python classes. The constructor returns a new featureless object. object instances do not have __dict__ attributes.
> 翻译：class object — 这是所有其他类的终极基类。具有所有 Python 类实例共有的方法。构造函数返回一个无特征的新对象。object 实例没有 __dict__ 属性。

50.
> Original: oct(integer, /) — Convert an integer number to an octal string prefixed with "0o". The result is a valid Python expression. If integer is not a Python int object, it has to define an __index__() method.
> 翻译：oct(integer, /) — 将整数转换为以 "0o" 为前缀的八进制字符串。结果是有效的 Python 表达式。如果 integer 不是 Python int 对象，须定义 "__index__()" 方法。

51.
> Original: open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None) — Open file and return a corresponding file object. If the file cannot be opened, OSError is raised. Mode characters: r, w, x, a, b, t, +. Text mode returns io.TextIOWrapper; binary mode returns BufferedIOBase subclass.
> 翻译：open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None) — 打开文件并返回对应的文件对象。文件无法打开则抛出 OSError。模式字符：r、w、x、a、b、t、+。文本模式返回 io.TextIOWrapper；二进制模式返回 BufferedIOBase 子类。

52.
> Original: ord(character, /) — Return the ordinal value of a character. If argument is a one-character string, return the Unicode code point. If argument is a bytes or bytearray of length 1, return its single byte value. This is the inverse of chr().
> 翻译：ord(character, /) — 返回字符的序数值。参数为单字符字符串时返回 Unicode 码位；为长度 1 的 bytes/bytearray 时返回其单字节值。这是 chr() 的逆函数。

53.
> Original: pow(base, exp, mod=None) — Return base to the power exp; if mod present, return base to the power exp modulo mod. For int operands with mod, mod must be nonzero. If exp is negative and mod present, base must be relatively prime to mod. Allows modular inverse computation.
> 翻译：pow(base, exp, mod=None) — 返回 base 的 exp 次幂；若有 mod，返回 base**exp % mod。int 操作数带 mod 时，mod 须非零。exp 为负且 mod 存在时，base 须与 mod 互素。允许模逆计算。

54.
> Original: print(*objects, sep=' ', end='\n', file=None, flush=False) — Print objects to the text stream file, separated by sep and followed by end. file must have a write(string) method; defaults to sys.stdout. print() cannot be used with binary mode file objects.
> 翻译：print(*objects, sep=' ', end='\n', file=None, flush=False) — 将 objects 打印到文本流 file，以 sep 分隔、end 结尾。file 须有 write(string) 方法；默认 sys.stdout。print() 不可用于二进制模式文件对象。

55.
> Original: class property(fget=None, fset=None, fdel=None, doc=None) — Return a property attribute. fget for getting, fset for setting, fdel for deleting. The @property decorator creates read-only properties. Property objects have getter, setter, deleter methods usable as decorators. Added __name__ attribute in 3.13.
> 翻译：class property(fget=None, fset=None, fdel=None, doc=None) — 返回属性描述符。fget 获取、fset 设置、fdel 删除。@property 装饰器创建只读属性。属性对象有 getter、setter、deleter 方法可用作装饰器。3.13 版新增 __name__ 属性。

56.
> Original: class range(stop, /) / class range(start, stop, step=1, /) — Rather than being a function, range is actually an immutable sequence type.
> 翻译：class range(stop, /) / class range(start, stop, step=1, /) — range 实际上是不可变序列类型，而非函数。

57.
> Original: repr(object, /) — Return a string containing a printable representation of an object. For many types, attempts to return a string that would yield an object with the same value when passed to eval(). A class can control this by defining __repr__().
> 翻译：repr(object, /) — 返回包含对象可打印表示的字符串。对于许多类型，试图返回经由 eval() 可还原同值对象的字符串。类可通过定义 __repr__() 控制此行为。

58.
> Original: reversed(object, /) — Return a reverse iterator. The argument must have __reversed__() method or support the sequence protocol (__len__() and __getitem__()).
> 翻译：reversed(object, /) — 返回反向迭代器。参数必须有 __reversed__() 方法或支持序列协议（__len__() 和 __getitem__()）。

59.
> Original: round(number, ndigits=None) — Return number rounded to ndigits precision. If ndigits omitted, returns nearest integer. Rounding ties go toward even choice. For a general Python object, round delegates to number.__round__. The behavior for floats can be surprising due to binary representation.
> 翻译：round(number, ndigits=None) — 返回 number 四舍五入到 ndigits 精度的结果。省略 ndigits 时返回最接近的整数。平局时向偶数舍入。一般 Python 对象委托 number.__round__。浮点数的行为可能令人意外（因二进制表示）。

60.
> Original: class set(iterable=(), /) — Return a new set object, optionally with elements taken from iterable. set is a built-in class.
> 翻译：class set(iterable=(), /) — 返回新集合对象，可选地取 iterable 中的元素。set 是内置类。

61.
> Original: setattr(object, name, value, /) — The counterpart of getattr(). Assigns value to the attribute. setattr(x, 'foobar', 123) is equivalent to x.foobar = 123. name need not be a Python identifier.
> 翻译：setattr(object, name, value, /) — getattr() 的对应函数。将 value 赋给属性。setattr(x, 'foobar', 123) 等价于 x.foobar = 123。name 不必是 Python 标识符。

62.
> Original: class slice(stop, /) / class slice(start, stop, step=None, /) — Return a slice object representing the set of indices specified by range(start, stop, step). Slice objects are now hashable (3.12). Read-only attributes: start, stop, step.
> 翻译：class slice(stop, /) / class slice(start, stop, step=None, /) — 返回表示 range(start, stop, step) 指定索引集的切片对象。切片对象 3.12 起可哈希。只读属性：start、stop、step。

63.
> Original: sorted(iterable, /, *, key=None, reverse=False) — Return a new sorted list from the items in iterable. key specifies comparison key function. reverse reverses order. Sorted is guaranteed stable. The sort algorithm uses only "<" comparisons.
> 翻译：sorted(iterable, /, *, key=None, reverse=False) — 返回可迭代对象元素排序后的新列表。key 指定比较键函数。reverse 反转顺序。排序保证稳定。排序算法仅使用 "<" 比较。

64.
> Original: @staticmethod — Transform a method into a static method. A static method does not receive an implicit first argument. Similar to static methods in Java or C++.
> 翻译：@staticmethod — 将方法转换为静态方法。静态方法不接收隐式第一参数。类似于 Java 或 C++ 的静态方法。

65.
> Original: class str(*, encoding='utf-8', errors='strict') / class str(object) / class str(object, encoding, errors='strict') / class str(object, *, errors) — Return a str version of object. str is the built-in string class.
> 翻译：class str(...) — 返回对象的字符串版本。str 是内置字符串类。

66.
> Original: sum(iterable, /, start=0) — Sums start and the items of an iterable from left to right and returns the total. The iterable's items are normally numbers, and start value not allowed to be a string. Float summation uses higher accuracy algorithm (3.12). Complex summation specialization added (3.14).
> 翻译：sum(iterable, /, start=0) — 从左到右对 start 和可迭代对象的项求和并返回总和。可迭代对象的项通常为数字，start 值不允许为字符串。3.12 版浮点求和使用更高精度算法。3.14 版新增复数求和专门化。

67.
> Original: class super / class super(type, object_or_type=None, /) — Return a proxy object that delegates method calls to a parent or sibling class of type. Useful for accessing inherited methods that have been overridden. The __mro__ attribute lists method resolution search order. Zero-argument super() works inside class definitions. super objects are now picklable and copyable (3.14).
> 翻译：class super / class super(type, object_or_type=None, /) — 返回将方法调用委托给 type 的父类或兄弟类的代理对象。用于访问被覆盖的继承方法。__mro__ 属性列出方法解析搜索顺序。零参数 super() 在类定义内工作。3.14 版 super 对象可 pickle 和 copy。

68.
> Original: class tuple(iterable=(), /) — Rather than being a function, tuple is actually an immutable sequence type.
> 翻译：class tuple(iterable=(), /) — tuple 实际上是不可变序列类型，而非函数。

69.
> Original: class type(object, /) / class type(name, bases, dict, /, **kwargs) — With one argument, return the type of an object. With three arguments, return a new type object (dynamic class creation). isinstance() is recommended for testing type. The three-argument form does not call the metaclass __prepare__ method.
> 翻译：class type(object, /) / class type(name, bases, dict, /, **kwargs) — 单参数时，返回对象的类型。三参数时，返回新的类型对象（动态类创建）。推荐 isinstance() 测试类型。三参数形式不调用元类 __prepare__ 方法。

70.
> Original: vars() / vars(object, /) — Return the __dict__ attribute for a module, class, instance, or any other object with __dict__. Without an argument, vars() acts like locals(). TypeError raised if object doesn't have __dict__.
> 翻译：vars() / vars(object, /) — 返回模块、类、实例或其他有 __dict__ 属性的对象的 __dict__。无参数时，vars() 行为类似 locals()。对象无 __dict__ 时抛出 TypeError。

71.
> Original: zip(*iterables, strict=False) — Iterate over several iterables in parallel, producing tuples. By default stops when shortest is exhausted. strict=True raises ValueError if lengths differ. With single iterable, returns 1-tuples; with no arguments, empty iterator. Added strict in 3.10.
> 翻译：zip(*iterables, strict=False) — 并行迭代多个可迭代对象，生成元组。默认最短耗尽即停止。strict=True 时长度不同抛出 ValueError。单可迭代对象返回 1-元组；无参数返回空迭代器。3.10 版新增 strict。

72.
> Original: __import__(name, globals=None, locals=None, fromlist=(), level=0) — This is an advanced function invoked by the import statement. Direct use is discouraged in favor of importlib.import_module(). When name is "package.module", the top-level package is returned unless fromlist is non-empty. Level specifies absolute vs relative imports.
> 翻译：__import__(name, globals=None, locals=None, fromlist=(), level=0) — 由 import 语句调用的高级函数。不推荐直接使用，推荐 importlib.import_module()。当 name 为 "package.module" 时，除非 fromlist 非空，否则返回顶层包。level 指定绝对导入 vs 相对导入。

## 事实
> 全部从 Python 3.14 官方文档 builtins/functions.txt 提取的客观事实，作为框架FE的填充值，属于分析中间产物

1. Python 解释器内置了许多始终可用的函数和类型（←片段1）
2. 内置函数按字母顺序排列（←片段1）
3. abs() 返回数的绝对值；参数可接受整数、浮点数或实现 __abs__() 的对象；复数参数返回模（←片段2）
4. aiter() 返回异步迭代器，等价于调用 x.__aiter__()；无两参数变体；3.10版新增（←片段3）
5. all() 当可迭代对象所有元素为真或可迭代对象为空时返回 True（←片段4）
6. any() 当可迭代对象任意元素为真时返回 True；空可迭代对象返回 False（←片段6）
7. anext() 是 next() 的异步变体，调用 __anext__()，返回 awaitable；耗尽时返回 default 或抛出 StopAsyncIteration（←片段5）
8. ascii() 返回对象可打印表示字符串，非 ASCII 字符以 \x/\u/\U 转义（←片段7）
9. bin() 将整数转为 "0b" 前缀二进制字符串；非 int 对象须定义 __index__()（←片段8）
10. bool 是 int 的子类，不可再子类化，仅有 True/False 两个实例（←片段9）
11. breakpoint() 调用 sys.breakpointhook() 进入调试器；默认调用 pdb.set_trace()；行为可由 PYTHONBREAKPOINT 环境变量控制（←片段10）
12. bytearray 是 0<=x<256 的可变整数序列；source 可为字符串+编码、整数大小、缓冲区对象、整数可迭代对象（←片段11）
13. bytes 是 0<=x<256 的不可变整数序列，是 bytearray 的不可变版本（←片段12）
14. callable() True 时调用仍可能失败，False 时绝不会成功；类可调用；实例有 __call__() 时可调用（←片段13）
15. chr() 将 Unicode 码位转为字符字符串，是 ord() 的逆；有效范围 0–0x10FFFF（←片段14）
16. @classmethod 装饰器将方法转为类方法，隐式第一参数为类本身（←片段15）
17. compile() 将源码编译为代码或 AST 对象；mode 可为 'exec'/'eval'/'single'（←片段16）
18. complex() 可从字符串、数字或实部虚部构造复数；委托链 __complex__()→__float__()→__index__()（←片段17）
19. delattr() 删除对象命名属性，等价于 del 语句；name 不必是 Python 标识符（←片段18）
20. dict 是内置字典类，支持 kwargs/mapping/iterable 三种构造方式（←片段19）
21. dir() 无参数返回局部作用域名称列表；有参数返回对象属性列表；主要作为交互式便利工具（←片段20）
22. divmod() 返回 (商, 余数) 数对；整数时为 (a//b, a%b)；不接受复数（←片段21）
23. enumerate() 返回 (计数, 值) 元组的迭代器，计数从 start 开始（←片段22）
24. eval() 解析并求值 Python 表达式；globals 不含 __builtins__ 时自动插入；对不受信任输入使用有安全风险（←片段23）
25. exec() 动态执行 Python 代码；返回 None；支持 closure 参数（←片段24）
26. filter() 对可迭代对象中 function 为真的元素构造迭代器；function 为 None 时移除假值（←片段25）
27. float() 从数字或字符串构造浮点数；委托链 __float__()→__index__()；默认返回 0.0（←片段26）
28. format() 将值转为格式化表示；调用 type(value).__format__(value, format_spec)（←片段27）
29. frozenset 是内置不可变集合类（←片段28）
30. getattr() 返回命名属性值；属性不存在时返回 default 或抛出 AttributeError（←片段29）
31. globals() 返回当前模块命名空间字典；函数内定义时设置后不变（←片段30）
32. hasattr() 通过调用 getattr() 检测属性是否存在（←片段31）
33. hash() 返回对象哈希值（整数）；比较相等的数值哈希相同；对自定义 __hash__() 截断（←片段32）
34. help() 调用内置帮助系统；由 site 模块添加到内置命名空间（←片段33）
35. hex() 将整数转为 "0x" 前缀十六进制字符串；非 int 须定义 __index__()（←片段34）
36. id() 返回对象标识（生命期内唯一整数）；CPython 中为内存地址（←片段35）
37. input() 读取用户输入并返回字符串；EOF 时抛出 EOFError（←片段36）
38. int() 从数字或字符串构造整数；支持 0 与 2-36 进制；3.14版不再委托 __trunc__()（←片段37）
39. isinstance() 检测对象是否为某类的实例；classinfo 可为元组或 Union 类型（←片段38）
40. issubclass() 检测类是否为某类的子类；类被视为自身子类（←片段39）
41. iter() 可从可迭代对象或（callable, sentinel）对创建迭代器（←片段40）
42. len() 返回对象长度；CPython 对超 sys.maxsize 长度抛出 OverflowError（←片段41）
43. list 是可变序列类型（←片段42）
44. locals() 返回当前局部符号表映射对象；优化作用域中改动不写回（←片段43）
45. map() 将函数应用于可迭代对象每个元素；3.14版新增 strict 参数（←片段44）
46. max()/min() 返回最大/最小项；支持 key 和 default 参数；多个极值返回首个（←片段45/47）
47. memoryview() 返回内存视图对象（←片段46）
48. next() 通过 __next__() 获取迭代器下一项；迭代器耗尽时返回 default 或抛出 StopIteration（←片段48）
49. object 是所有类的终极基类；实例无 __dict__ 属性（←片段49）
50. oct() 将整数转为 "0o" 前缀八进制字符串；非 int 须定义 __index__()（←片段50）
51. open() 打开文件返回文件对象；支持 r/w/x/a/b/t/+ 模式组合（←片段51）
52. ord() 返回字符序数值/Unicode码位；是 chr() 的逆函数（←片段52）
53. pow(base, exp, mod) 返回幂运算结果；带 mod 时高效计算模幂；支持模逆计算（←片段53）
54. print() 将对象打印到文本流；sep/end/file/flush 为关键字参数；不可用于二进制文件（←片段54）
55. property() 返回属性描述符，管理属性的获取/设置/删除（←片段55）
56. range 是不可变序列类型（←片段56）
57. repr() 返回对象可打印表示字符串；类可通过 __repr__() 控制（←片段57）
58. reversed() 返回反向迭代器；参数须有 __reversed__() 或支持序列协议（←片段58）
59. round() 四舍五入；平局向偶数舍入；委托 __round__）（←片段59）
60. set 是内置可变集合类（←片段60）
61. setattr() 设置对象属性值；name 不必是 Python 标识符（←片段61）
62. slice() 返回切片对象；3.12 起可哈希；有 start/stop/step 只读属性（←片段62）
63. sorted() 返回排序后新列表；保证稳定排序；仅使用 "<" 比较（←片段63）
64. @staticmethod 装饰器将方法转为静态方法，不接收隐式第一参数（←片段64）
65. str 是内置字符串类（←片段65）
66. sum() 对可迭代对象求和；start 不允许为字符串；3.12版浮点求和精度提升（←片段66）
67. super() 返回代理对象委托方法调用到父类/兄弟类；依赖 __mro__ 顺序（←片段67）
68. tuple 是不可变序列类型（←片段68）
69. type() 单参数返回对象类型；三参数动态创建新类型/类（←片段69）
70. vars() 返回 __dict__ 属性；无参数时行为类似 locals()（←片段70）
71. zip() 并行迭代多个可迭代对象；默认最短耗尽停止；strict=True 时长度不匹配抛出 ValueError（←片段71）
72. __import__() 由 import 语句调用；不推荐直接使用，推荐 importlib.import_module()（←片段72）

## 缺口
> 从原始语料分析得出的**知识缺口**：语料没有明确说明、缺少定义、边界模糊的点，属于分析中间产物

1. 内置函数的完整精确数量未在语料中给出（需从表格自行计数，约71个）（相关片段1）
2. 各内置函数的 CPython 底层实现机制（C API 对应关系）完全未提及（相关片段1）
3. @classmethod 和 @staticmethod 装饰器在多继承钻石图中的具体解析顺序未说明（相关片段15/64）
4. compile() 生成的代码对象的具体内部结构和属性未说明（相关片段16）
5. complex() 在 3.14 版弃用将复数作为 real/imag 参数的具体迁移路径未说明（相关片段17）
6. exec()/eval() 中 __builtins__ 覆盖"不是安全机制"的具体绕过方式未详述（相关片段23/24）
7. locals() 在优化作用域中"改动不写回"的具体边界条件（如闭包变量）未详述（相关片段43）
8. open() 的各 error handler 的精确行为（如 surrogateescape 的字节映射范围）虽列出但未深入解释（相关片段51）
9. pow(base, exp, mod) 的具体算法（模幂运算的高效实现方式）未提及（相关片段53）
10. super() 在多继承协作调用中的完整设计模式（cooperative multiple inheritance 最佳实践）仅有引用链接但未展开（相关片段67）
11. __import__() 的 fromlist 和 level 参数的详细交互语义未完全展开（相关片段72）
12. hash() 对于无 __hash__() 的对象（如可变容器）的默认行为未在此文档中说明（相关片段32）
13. 各内置类型构造函数（bool/bytes/bytearray/complex/float/int/str）的 __dunder__ 委托链优先级在版本间的变更细节未系统整理（相关片段2/9/12/17/26/37）
14. round() "向偶数舍入"规则在金融/统计领域的具体影响未说明（相关片段59）

## 误解
> 从原始语料推导的学习者**潜在错误理解**，属于分析中间产物

1. 误认为 aiter() 与 iter() 一样有两参数变体——原文明确指出 aiter() 没有（←片段3诱导）
2. 误认为 callable() 返回 True 就保证调用不会失败——原文明确说 True 时调用仍可能失败（←片段13诱导）
3. 误认为 bool 可以被继承——原文明确说"不能被进一步子类化"（←片段9诱导）
4. 误认为 dir() 返回完整的属性列表——原文说"结果不一定完整"，且主要是交互便利工具（←片段20诱导）
5. 误认为 eval() 中覆盖 __builtins__ 可以安全限制代码执行——原文警告"这不是安全机制：执行的代码仍可访问所有内置函数"（←片段23诱导）
6. 误认为 filter() 和 map() 返回列表——它们返回的是迭代器，不是列表（←片段25/44诱导，原文说"构造迭代器"）
7. 误认为 round(2.675, 2) 结果为 2.68——原文明确说结果是 2.67，因为浮点数不能精确表示十进制小数（←片段59诱导）
8. 误认为 sum() 可以拼接字符串——原文明确说"start 值不允许为字符串"（←片段66诱导）
9. 误认为 zip() 返回列表——原文说返回迭代器（←片段71诱导，原文说"zip() is lazy"）
10. 误认为 object 实例可以赋任意属性——原文说 object 实例没有 __dict__ 属性（←片段49诱导）
11. 误认为 id() 对两个同时存在的不同对象总是返回不同值——原文说"两个非重叠生命周期的对象可能有相同的 id() 值"（←片段35诱导）
12. 误认为 type() 三参数形式等价于 class 语句——原文说三参数形式不调用元类 __prepare__ 方法，有差异（←片段69诱导）
13. 误认为 isinstance()/issubclass() 只接受单个类型——原文说 classinfo 可以是元组或 Union 类型（←片段38/39诱导）
14. 误认为 hash() 对自定义 __hash__() 返回完整值——原文说 hash() 会根据宿主机位宽截断（←片段32诱导）
15. 误认为 int() 在 3.14 仍使用 __trunc__() 回退——3.14 版已移除 __trunc__() 委托（←片段37诱导）
16. 误认为 print() 可以写二进制文件——原文说"不可用于二进制模式文件对象"（←片段54诱导）
17. 误认为 locals() 在函数中通过返回字典修改可影响局部变量——优化作用域中不会写回（←片段43诱导）

## Python内置函数框架
|框架名称|刻画描述|框架元素（FE）及填充|原始事实语料|原始语料定位|
|---|---|---|---|---|
|Python内置函数入口框架|主题级根锚点：聚合所有内置函数的维度构成，导航至各子框架|`主题对象`（核心）: Python 解释器内置函数和类型集合<br>`数值运算维度`（核心）: 对数值执行绝对值/幂/商余/四舍五入/求和等运算的函数族——数值运算框架<br>`类型构造维度`（核心）: 从各种输入构造内置数据类型实例的函数/类族——类型构造框架<br>`迭代处理维度`（核心）: 创建/操作/消费迭代器与可迭代对象的函数族——迭代处理框架<br>`属性操作维度`（核心）: 获取/设置/检测/删除对象属性的函数族——属性操作框架<br>`类型检测维度`（核心）: 检测对象类型与继承关系的函数族——类型检测框架<br>`代码执行维度`（核心）: 编译/动态执行/求值 Python 代码的函数族——代码执行框架<br>`字符串表示维度`（核心）: 生成对象字符串/格式化表示的函数族——字符串表示框架<br>`进制转换维度`（核心）: 在整数与各进制字符串间转换的函数族——进制转换框架<br>`作用域内省维度`（核心）: 查看当前命名空间/模块/局部变量等作用域信息的函数族——作用域内省框架<br>`IO操作维度`（核心）: 执行输入/输出/文件操作的函数族——IO操作框架<br>`类方法装饰维度`（外围）: 定义类方法/静态方法/属性描述符的装饰器族——类方法装饰框架<br>`调试与帮助维度`（外围）: 提供调试断点和帮助系统的函数族——调试与帮助框架|1. 内置函数始终可用（事实1）2. 按字母顺序排列（事实2）|原文片段1–72；参考链接：https://docs.python.org/3/library/functions.html|
|数值运算框架|对数值执行数学运算的内置函数集合|`操作数`（核心）: 数值类型对象（int/float/complex）<br>`运算结果`（核心）: 运算返回值（绝对值、幂、商余对、舍入值、总和）<br>`运算规则`（核心）: 特定数学规则（绝对值/幂运算/coercion/向偶舍入/左到右求和）<br>`辅助参数`（外围）: mod（pow模运算）、ndigits（round精度）、start（sum初始值）|3. abs()返回绝对值 21. divmod()返回商余对 53. pow()幂运算 59. round()四舍五入 66. sum()求和|原文片段2/21/53/59/66；参考链接：https://docs.python.org/3/library/functions.html|
|类型构造框架|从各种输入构造内置数据类型实例的函数和类|`输入源`（核心）: 构造函数的输入（字符串/数字/可迭代对象）<br>`目标类型`（核心）: 要构造的内置类型（bool/int/float/complex/str/bytes/bytearray/list/tuple/dict/set/frozenset/range/memoryview/slice/object）<br>`转换委托链`（核心）: __dunder__ 方法委托序列（如 __complex__()→__float__()→__index__()）<br>`构造参数`（外围）: 编码/进制/格式等辅助参数|9–12/17/19/26/28/37/42/46/49/56/60/62/65/68/69|原文片段9–12/17/19/26/28/37/42/46/49/56/60/62/65/68/69；参考链接：https://docs.python.org/3/library/functions.html|
|迭代处理框架|创建、操作和消费迭代器与可迭代对象的函数集合|`可迭代源`（核心）: 被处理的可迭代对象或异步可迭代对象<br>`迭代器产出`（核心）: 返回的迭代器或异步迭代器<br>`迭代控制`（核心）: 条件函数（filter/map）、哨兵值（iter两参数形式）、strict标志（map/zip）<br>`终止条件`（核心）: 迭代耗尽行为（StopIteration/StopAsyncIteration/default返回）<br>`枚举偏移`（外围）: start参数（enumerate）|4–6/22/25/40/41/44/45/47/48/58/71|原文片段4–6/22/25/40/41/44/45/47/48/58/71；参考链接：https://docs.python.org/3/library/functions.html|
|属性操作框架|获取/设置/检测/删除对象属性的函数集合|`目标对象`（核心）: 被操作属性的对象<br>`属性名称`（核心）: 属性名字符串（不必为Python标识符）<br>`属性值`（核心）: 要设置的值（setattr）或获取的值（getattr）<br>`默认值`（外围）: 属性不存在时的回退值（getattr default）<br>`存在性结果`（外围）: 属性是否存在的布尔结果（hasattr）|18/29/31/61|原文片段18/29/31/61；参考链接：https://docs.python.org/3/library/functions.html|
|类型检测框架|检测对象类型与继承关系的函数集合|`被检测对象`（核心）: 待检测的对象或类<br>`类型标准`（核心）: 目标类型/类型元组/Union类型<br>`判断结果`（核心）: 布尔结果（True/False）<br>`继承范围`（外围）: 直接/间接/虚拟子类均算|38/39/13|原文片段38/39/13；参考链接：https://docs.python.org/3/library/functions.html|
|代码执行框架|编译/动态执行/求值Python代码的函数集合|`代码源`（核心）: 源码字符串/字节串/AST对象/代码对象<br>`执行环境`（核心）: globals和locals命名空间映射<br>`执行模式`（核心）: 'exec'/'eval'/'single'编译模式<br>`安全风险`（核心）: 执行不受信任代码的安全漏洞警告<br>`闭包`（外围）: closure参数（exec的cellvar元组）|16/23/24|原文片段16/23/24；参考链接：https://docs.python.org/3/library/functions.html|
|字符串表示框架|生成对象字符串和格式化表示的函数集合|`输入对象`（核心）: 被表示的对象<br>`表示格式`（核心）: repr()/ascii()/format()等格式化方式<br>`格式规格`（外围）: format_spec控制字符串|7/27/57|原文片段7/27/57；参考链接：https://docs.python.org/3/library/functions.html|
|进制转换框架|在整数与各进制字符串表示间转换的函数集合|`整数值`（核心）: 输入的整数对象<br>`进制字符串`（核心）: 带前缀的进制字符串（0b/0o/0x）<br>`进制基数`（核心）: 目标进制（2/8/10/16）<br>`dunder委托`（外围）: __index__()方法（非int对象）|8/34/37/50|原文片段8/34/37/50；参考链接：https://docs.python.org/3/library/functions.html|
|作用域内省框架|查看当前命名空间/模块/局部变量等作用域信息的函数集合|`命名空间`（核心）: 返回的映射对象/字典（globals/locals/vars/dir）<br>`作用域类型`（核心）: 模块级/函数级/类级/优化作用域<br>`可变性`（核心）: 返回对象是否可写回（优化作用域不可写回）<br>`属性列表`（外围）: dir()返回的属性名排序列表|20/30/31/43/70|原文片段20/30/31/43/70；参考链接：https://docs.python.org/3/library/functions.html|
|IO操作框架|执行输入/输出/文件操作的函数集合|`文件路径`（核心）: 要打开的文件路径/文件描述符<br>`打开模式`（核心）: r/w/x/a/b/t/+ 模式组合<br>`编码处理`（核心）: encoding/errors/newline 参数<br>`IO对象`（核心）: 返回的文件对象类型（TextIOWrapper/BufferedIOBase子类等）<br>`缓冲策略`（外围）: buffering参数<br>`输出流`（外围）: print()的file参数|36/51/54|原文片段36/51/54；参考链接：https://docs.python.org/3/library/functions.html|
|类方法装饰框架|定义类方法/静态方法/属性描述符的装饰器和描述符类|`方法类型`（核心）: 类方法/静态方法/属性描述符<br>`隐式参数`（核心）: 类方法接收类（cls）vs 静态方法无隐式参数<br>`访问器`（核心）: property的fget/fset/fdel<br>`装饰形式`（外围）: @classmethod/@staticmethod/@property装饰器语法|15/55/64|原文片段15/55/64；参考链接：https://docs.python.org/3/library/functions.html|
|调试与帮助框架|提供调试断点和交互帮助系统的函数集合|`调试入口`（核心）: breakpoint()调用 sys.breakpointhook()进入调试器<br>`环境配置`（核心）: PYTHONBREAKPOINT 环境变量控制调试行为<br>`帮助内容`（核心）: help()返回的帮助信息（模块/函数/类/关键字）<br>`审计事件`（外围）: 触发的审计事件|10/33|原文片段10/33；参考链接：https://docs.python.org/3/library/functions.html|

## Python内置函数框架间关系
> FrameNet标准关系：`Inheritance`（继承）、`Perspective on`（视角化）、`Using`（使用/依赖）、`Subframe`（子框架）、`Precedes`（先行）、`Causative of`（致使）、`Inchoative of`（起始）、`Metaphor`（隐喻）、`See also`（参见）

**第一组：子框架 → 入口框架**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|数值运算框架|`Using`|Python内置函数入口框架|填充`数值运算维度`槽；数值运算函数的成立以"Python解释器内置函数始终可用"为前提|
|类型构造框架|`Using`|Python内置函数入口框架|填充`类型构造维度`槽；类型构造函数/类的成立以"Python解释器内置"为前提|
|迭代处理框架|`Using`|Python内置函数入口框架|填充`迭代处理维度`槽；迭代处理函数的成立以"Python解释器内置"为前提|
|属性操作框架|`Using`|Python内置函数入口框架|填充`属性操作维度`槽；属性操作函数的成立以"Python解释器内置"为前提|
|类型检测框架|`Using`|Python内置函数入口框架|填充`类型检测维度`槽；类型检测函数的成立以"Python解释器内置"为前提|
|代码执行框架|`Using`|Python内置函数入口框架|填充`代码执行维度`槽；代码执行函数的成立以"Python解释器内置"为前提|
|字符串表示框架|`Using`|Python内置函数入口框架|填充`字符串表示维度`槽；字符串表示函数的成立以"Python解释器内置"为前提|
|进制转换框架|`Using`|Python内置函数入口框架|填充`进制转换维度`槽；进制转换函数的成立以"Python解释器内置"为前提|
|作用域内省框架|`Using`|Python内置函数入口框架|填充`作用域内省维度`槽；作用域内省函数的成立以"Python解释器内置"为前提|
|IO操作框架|`Using`|Python内置函数入口框架|填充`IO操作维度`槽；IO操作函数的成立以"Python解释器内置"为前提|
|类方法装饰框架|`Using`|Python内置函数入口框架|填充`类方法装饰维度`槽；类方法装饰器的成立以"Python解释器内置"为前提|
|调试与帮助框架|`Using`|Python内置函数入口框架|填充`调试与帮助维度`槽；调试与帮助函数的成立以"Python解释器内置"为前提|

**第二组：子框架之间**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|进制转换框架|`Using`|类型构造框架|进制转换函数（bin/hex/oct）的输出为字符串类型，依赖类型构造框架中 str/int 类的构造能力；int(string, base) 可从进制字符串反向构造整数|
|字符串表示框架|`Using`|类型构造框架|repr()/format()/ascii() 的输出对象为 str 类型，依赖类型构造框架中 str 类的定义；且 format() 查找 type(value).__format__() 涉及类型的属性查找|
|代码执行框架|`Using`|迭代处理框架|exec()/eval() 在解析代码中的 for/推导式时隐式创建和使用迭代器；compile() 编译的代码可包含迭代操作|
|代码执行框架|`Using`|作用域内省框架|exec()/eval() 依赖 globals/locals 命名空间映射，且 globals()/locals() 的返回值可作为 exec/eval 的参数传入|
|属性操作框架|`Using`|类型检测框架|hasattr() 通过调用 getattr() 实现；getattr()/setattr()/delattr() 操作涉及对象的类型属性查找路径|
|迭代处理框架|`Subframe`|类型构造框架|iter()/next()/filter()/map()/enumerate()/reversed() 等迭代器常作为类型构造的输入源（如 list(iter(f))）；迭代消费是类型构造的一个子阶段|
|迭代处理框架|`Precedes`|类型构造框架|迭代处理框架（产生迭代器）在时序上先于类型构造框架（从迭代器消费元素构造容器）|
|类型检测框架|`Using`|类型构造框架|isinstance()/issubclass() 检测的类型对象正是类型构造框架中 type() 动态创建或内置类型实例化所得的类型|
|调试与帮助框架|`Using`|作用域内省框架|help() 需查找模块/类/函数等命名空间信息；breakpoint() 在调试时需查看 locals/globals|
|IO操作框架|`Using`|字符串表示框架|print() 调用 str() 将对象转为字符串再输出；open() 的文本模式涉及编码解码|
