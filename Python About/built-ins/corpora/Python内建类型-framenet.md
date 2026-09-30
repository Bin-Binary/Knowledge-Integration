# Python内建类型 FrameNet 语义框架标注文档
> 文档结构：##说明 → ##原文和翻译 → ##事实 → ##缺口 → ##误解 → ##Python内建类型框架 → ##Python内建类型框架间关系

## 说明
1. 本文件基于Python 3.14官方文档 builtins/stdtypes.txt，采用**FrameNet框架语义学**进行建模。
2. 框架元素FE为抽象语义槽；**事实为槽填充客观内容；缺口是从原始语料推导出来的知识缺失点；误解是基于语料推导的学习者可能产生的错误理解**。
3. 原文与翻译一一对应，原文后紧跟中文翻译；
4. 框架关系使用FrameNet标准9种关系标签：`Inheritance`、`Perspective on`、`Using`、`Subframe`、`Precedes`、`Causative of`、`Inchoative of`、`Metaphor`、`See also`；
5. 原始语料定位记录原文出处、片段位置与参考链接。
6. 本文档为`Python内建对象体系-framenet.md`中"内建类型框架"的**下钻展开**，对stdtypes章节进行细粒度框架建模。

## 原文和翻译
> 来源：Python 3.14 官方文档 — Built-in Types (https://docs.python.org/3.14/library/stdtypes.html)

1.
> Original: By default, an object is considered true unless its class defines a `__bool__()` method that returns `False` or a `__len__()` method that returns zero.
> 翻译：默认情况下，对象被视为真，除非其类定义了返回`False`的`__bool__()`方法或返回零的`__len__()`方法。

2.
> Original: Here are most of the built-in objects considered false: constants defined to be false: `None` and `False`; zero of any numeric type: `0`, `0.0`, `0j`; empty sequences and collections: `''`, `()`, `[]`, `{}`, `set()`, `range(0)`.
> 翻译：以下为被视为假的大多数内建对象：定义为假的常量：`None`和`False`；任何数值类型的零：`0`、`0.0`、`0j`；空序列和空集合：`''`、`()`、`[]`、`{}`、`set()`、`range(0)`。

3.
> Original: Boolean Operations — and, or, not. `x and y`: if *x* is false, then *x*; else *y*. `x or y`: if *x* is true, then *x*; else *y*. `not x`: if *x* is false, then `True`; else `False`.
> 翻译：布尔运算——and、or、not。`x and y`：若x为假，则返回x；否则返回y。`x or y`：若x为真，则返回x；否则返回y。`not x`：若x为假，则返回True；否则返回False。

4.
> Original: Comparisons: `<`, `>`, `==`, `>=`, `<=`, `!=`; `is`, `is not`; `in`, `not in`. All comparison operators have the same priority, which is lower than that of all numeric operators. Comparisons can be chained arbitrarily. `x < y <= z` is equivalent to `x < y and y <= z`, except that *y* is evaluated only once.
> 翻译：比较运算：<、>、==、>=、<=、!=；is、is not；in、not in。所有比较运算符具有相同优先级，低于所有数值运算符。比较可以任意链式组合。`x < y <= z`等价于`x < y and y <= z`，但y只求值一次。

5.
> Original: Integers have unlimited precision.
> 翻译：整数具有无限精度。

6.
> Original: Floating point numbers are usually implemented using double in C. Information about the precision and internal representation of floating point numbers for the specific machine can be found in `sys.float_info`.
> 翻译：浮点数通常使用C的double实现。关于特定机器浮点数精度和内部表示的信息可在`sys.float_info`中找到。

7.
> Original: Complex numbers have a real and imaginary part, each of which is a floating point number.
> 翻译：复数有实部和虚部，各为浮点数。

8.
> Original: The bitwise operations `&`, `|`, `^`, `~`, `<<`, `>>` only make sense for integers. The result of bitwise operations is computed as though carried out in two's complement with an infinite number of sign bits.
> 翻译：位运算&、|、^、~、<<、>>仅对整数有意义。位运算的结果按无限符号位的二进制补码进行计算。

9.
> Original: class bool([x]): Return a Boolean value, i.e. one of `True` or `False`. *x* is converted using the standard *truth testing procedure*. `bool` is a subclass of `int`.
> 翻译：class bool([x])：返回布尔值，即True或False之一。x通过标准真值测试过程转换。bool是int的子类。

10.
> Original: Iterator types: The iterator object itself must support `__iter__()` returning the iterator object itself, and `__next__()` returning the next value. Once the iterator is exhausted, `__next__()` must raise `StopIteration`.
> 翻译：迭代器类型：迭代器对象自身必须支持返回迭代器对象本身的`__iter__()`和返回下一个值的`__next__()`。迭代器耗尽后，`__next__()`必须抛出StopIteration。

11.
> Original: Generator types: Generator iterators are created by the `yield` statement. They implement `__iter__()` and `__next__()`. The `send()`, `throw()` and `close()` methods are unique to generators.
> 翻译：生成器类型：生成器迭代器由yield语句创建。它们实现了`__iter__()`和`__next__()`。send()、throw()和close()是生成器独有的方法。

12.
> Original: Sequence types — list, tuple, range. Common sequence operations support: `in`, `not in`, `+` (concatenation), `*` (repetition), `s[i]`, `s[i:j]`, `s[i:j:k]`, `len(s)`, `min(s)`, `max(s)`, `s.index(x)`, `s.count(x)`.
> 翻译：序列类型——list、tuple、range。公共序列操作支持：in、not in、+（拼接）、*（重复）、s[i]、s[i:j]、s[i:j:k]、len(s)、min(s)、max(s)、s.index(x)、s.count(x)。

13.
> Original: Immutable sequence types: The only operation that immutable sequence types generally implement that is not also implemented by mutable sequence types is support for the `hash()` built-in. Such support allows immutable sequences to be used as `dict` keys and `set` elements.
> 翻译：不可变序列类型：不可变序列类型通常实现而可变序列类型不实现的唯一操作是对`hash()`内建函数的支持。此支持允许不可变序列用作dict键和set元素。

14.
> Original: Mutable sequence types: In addition to common sequence operations, mutable sequences support `s[i] = x`, `del s[i]`, `s[i:j] = t`, `del s[i:j]`, `s.append(x)`, `s.clear()`, `s.copy()`, `s.extend(t)`, `s *= n`, `s.insert(i, x)`, `s.pop([i])`, `s.remove(x)`, `s.reverse()`.
> 翻译：可变序列类型：除公共序列操作外，可变序列支持s[i]=x、del s[i]、s[i:j]=t、del s[i:j]、s.append(x)、s.clear()、s.copy()、s.extend(t)、s*=n、s.insert(i,x)、s.pop([i])、s.remove(x)、s.reverse()。

15.
> Original: class list([iterable]): Lists are mutable sequences, typically used to store collections of homogeneous items.
> 翻译：class list([iterable])：列表是可变序列，通常用于存储同类项的集合。

16.
> Original: class tuple([iterable]): Tuples are immutable sequences, typically used to store collections of heterogeneous data. Tuples are also commonly used for record-keeping where a sequence of heterogeneous but related data is desired.
> 翻译：class tuple([iterable])：元组是不可变序列，通常用于存储异构数据的集合。元组也常用于需要一系列异构但相关数据的记录场景。

17.
> Original: class range(stop) / range(start, stop[, step]): The range type represents an immutable sequence of numbers and is commonly used for looping a specific number of times in `for` loops. Ranges implement all of the common sequence operations except concatenation and repetition.
> 翻译：class range(stop)/range(start,stop[,step])：range类型表示不可变的数字序列，常用于for循环中指定次数的循环。range实现了除拼接和重复之外的所有公共序列操作。

18.
> Original: Text Sequence Type — str: Strings are immutable sequences of Unicode code points.
> 翻译：文本序列类型——str：字符串是Unicode码位的不可变序列。

19.
> Original: str.capitalize(), str.casefold(), str.center(), str.count(), str.encode(), str.endswith(), str.expandtabs(), str.find(), str.format(), str.format_map(), str.index(), str.isalnum(), str.isalpha(), str.isascii(), str.isdecimal(), str.isdigit(), str.isidentifier(), str.islower(), str.isnumeric(), str.isprintable(), str.isspace(), str.istitle(), str.isupper(), str.join(), str.ljust(), str.lower(), str.lstrip(), str.maketrans(), str.partition(), str.removeprefix(), str.removesuffix(), str.replace(), str.rfind(), str.rindex(), str.rjust(), str.rpartition(), str.rsplit(), str.rstrip(), str.split(), str.splitlines(), str.startswith(), str.strip(), str.swapcase(), str.title(), str.translate(), str.upper(), str.zfill().
> 翻译：str.capitalize()、str.casefold()、str.center()、str.count()、str.encode()、str.endswith()、str.expandtabs()、str.find()、str.format()、str.format_map()、str.index()、str.isalnum()、str.isalpha()、str.isascii()、str.isdecimal()、str.isdigit()、str.isidentifier()、str.islower()、str.isnumeric()、str.isprintable()、str.isspace()、str.istitle()、str.isupper()、str.join()、str.ljust()、str.lower()、str.lstrip()、str.maketrans()、str.partition()、str.removeprefix()、str.removesuffix()、str.replace()、str.rfind()、str.rindex()、str.rjust()、str.rpartition()、str.rsplit()、str.rstrip()、str.split()、str.splitlines()、str.startswith()、str.strip()、str.swapcase()、str.title()、str.translate()、str.upper()、str.zfill()。

20.
> Original: f-strings: A formatted string literal or f-string is a string literal that is prefixed with 'f' or 'F'. These strings may contain replacement fields, which are expressions delimited by curly braces `{}`. While other string literals always have a constant value, formatted strings are expressions evaluated at runtime.
> 翻译：f-字符串：格式化字符串字面量或f-string是以'f'或'F'为前缀的字符串字面量。这些字符串可包含替换字段，即由大括号`{}`分隔的表达式。其他字符串字面量总有常量值，而格式化字符串是在运行时求值的表达式。

21.
> Original: t-strings: A t-string is a string template prefixed with 't' or 'T'. Unlike f-strings, t-strings are not evaluated at creation; they return a `Template` object that provides access to the string's static parts and the interpolation expressions.
> 翻译：t-字符串：t-string是以't'或'T'为前缀的字符串模板。与f-string不同，t-string在创建时不求值；它们返回一个`Template`对象，提供对字符串静态部分和插值表达式的访问。

22.
> Original: Binary Sequence Types — bytes, bytearray, memoryview. The core built-in types for manipulating binary data are bytes and bytearray. They are supported by memoryview which uses the buffer protocol to access the memory of other binary objects without needing to make a copy.
> 翻译：二进制序列类型——bytes、bytearray、memoryview。操作二进制数据的核心内建类型是bytes和bytearray。memoryview使用缓冲区协议访问其他二进制对象的内存而无需复制。

23.
> Original: class bytes([source[, encoding[, errors]]]): Bytes objects are immutable sequences of single bytes. Since many major binary protocols are based on the ASCII text encoding, bytes objects offer several methods that are only valid when processing ASCII-compatible data.
> 翻译：class bytes([source[,encoding[,errors]]])：bytes对象是单字节的不可变序列。由于许多主要二进制协议基于ASCII文本编码，bytes对象提供了若干仅在处理ASCII兼容数据时有效的方法。

24.
> Original: class bytearray([source[, encoding[, errors]]]): bytearray objects are a mutable counterpart to bytes objects. There is no dedicated literal syntax for bytearray; they are always created by calling the constructor.
> 翻译：class bytearray([source[,encoding[,errors]]])：bytearray对象是bytes对象的可变对应物。bytearray没有专用的字面量语法；它们总是通过调用构造函数创建。

25.
> Original: class memoryview(obj): A memoryview has the notion of an element and the notion of a format, as set by the originating object. For the basic operation of accessing and assigning items, memoryview objects support the buffer protocol to access the memory of other binary objects without needing to make a copy.
> 翻译：class memoryview(obj)：memoryview具有由原始对象设置的元素概念和格式概念。对于访问和赋值项的基本操作，memoryview对象支持缓冲区协议以访问其他二进制对象的内存而无需复制。

26.
> Original: Set Types — set, frozenset. A set object is an unordered collection of distinct hashable objects. Common uses include membership testing, removing duplicates from a sequence, and computing mathematical operations such as intersection, union, difference, and symmetric difference.
> 翻译：集合类型——set、frozenset。set对象是不同可哈希对象的无序集合。常见用途包括成员测试、去重以及计算交集、并集、差集和对称差集等数学运算。

27.
> Original: The set classes also provide the following mathematical operations: `|` (union), `&` (intersection), `-` (difference), `^` (symmetric difference), and relation operators `<`/`<=`/`>`/`>=` (subset/superset tests).
> 翻译：集合类还提供以下数学运算：|（并集）、&（交集）、-（差集）、^（对称差集），以及关系运算符</<=/>/>=（子集/超集测试）。

28.
> Original: class dict(**kwarg) / dict(mapping, **kwarg) / dict(iterable, **kwarg): A mapping object maps hashable values to arbitrary objects. Mappings are mutable objects. The only special operation on a mapping is key access: `d[key]`. Dictionaries preserve insertion order. Note that updating a key does not affect the order. Adding and deleting keys does affect the order — the inserted key is moved to the end.
> 翻译：class dict(**kwarg)/dict(mapping,**kwarg)/dict(iterable,**kwarg)：映射对象将可哈希值映射到任意对象。映射是可变对象。映射的唯一特殊操作是键访问：d[key]。字典保留插入顺序。注意更新键不影响顺序。添加和删除键会影响顺序——插入的键被移到末尾。

29.
> Original: Dictionary view objects: The objects returned by `dict.keys()`, `dict.values()` and `dict.items()` are view objects. They provide a dynamic view on the dictionary's entries, which means that when the dictionary changes, the view reflects these changes. Keys views are set-like since their entries are unique and hashable.
> 翻译：字典视图对象：`dict.keys()`、`dict.values()`和`dict.items()`返回的对象是视图对象。它们提供字典条目的动态视图，即当字典变化时，视图反映这些变化。键视图是类集合的，因为其条目唯一且可哈希。

30.
> Original: Context Manager Types: Python's `with` statement supports the concept of a runtime context. This is implemented using a pair of methods that allow user-defined classes to define a runtime context that is entered before the statement body is executed and exited when the statement body ends: `__enter__(self)` and `__exit__(self, exc_type, exc_value, traceback)`.
> 翻译：上下文管理器类型：Python的with语句支持运行时上下文的概念。这通过一对方法实现，允许用户自定义类定义在语句体执行前进入、语句体结束时退出的运行时上下文：`__enter__(self)`和`__exit__(self,exc_type,exc_value,traceback)`。

31.
> Original: Generic Alias Type: Type aliases like `list[int]` are created by subscripting a generic class or type. Such aliases are primarily intended for type annotations. The `__args__` attribute of a generic alias returns the tuple of type arguments. The `__origin__` attribute returns the aliased generic class.
> 翻译：泛型别名类型：如`list[int]`的类型别名通过对泛型类或类型进行下标操作创建。此类别名主要用于类型注解。泛型别名的`__args__`属性返回类型参数元组。`__origin__`属性返回被别名的泛型类。

32.
> Original: Union Type: A union object holds the value of the "|" (bitwise or) operation on multiple type objects. `X | Y` means either X or Y. It is equivalent to `typing.Union[X, Y]`. Union objects are now instances of `typing.Union` (changed in 3.14).
> 翻译：联合类型：联合对象持有多个类型对象上"|"（按位或）操作的值。`X | Y`表示X或Y。它等价于`typing.Union[X, Y]`。联合对象现在是`typing.Union`的实例（3.14变更）。

33.
> Original: Other Built-in Types — Modules: The only special operation on a module is attribute access: `m.name`. Module attributes can be assigned to. Functions: Function objects are created by function definitions. The only operation on a function object is to call it: `func(args)`. Methods: Methods are functions that are called using the attribute notation.
> 翻译：其他内建类型——模块：模块的唯一特殊操作是属性访问：m.name。模块属性可以被赋值。函数：函数对象由函数定义创建。函数对象的唯一操作是调用：func(args)。方法：方法是使用属性记法调用的函数。

34.
> Original: Special Attributes: `object.__dict__`, `instance.__class__`, `class.__name__`, `class.__bases__`, `class.__mro__`, `class.__doc__`, `class.__module__`, etc.
> 翻译：特殊属性：object.__dict__、instance.__class__、class.__name__、class.__bases__、class.__mro__、class.__doc__、class.__module__等。

35.
> Original: Integer string conversion length limitation: Converting between integers and strings in non-power-of-two bases has a time complexity that is super-linear in the number of digits. A denial-of-service vulnerability (CVE-2020-10735) exists. By default, this conversion is limited to 4300 digits. The limit can be inspected and changed via `sys.get_int_max_str_digits()` and `sys.set_int_max_str_digits()`.
> 翻译：整数字符串转换长度限制：在非2的幂次进制下进行整数与字符串之间转换的时间复杂度相对于位数是超线性的。存在拒绝服务漏洞（CVE-2020-10735）。默认情况下，此转换限制为4300位数字。该限制可通过sys.get_int_max_str_digits()和sys.set_int_max_str_digits()进行检查和更改。

## 事实
> 全部从Python 3.14官方文档builtins/stdtypes.txt提取的客观事实，作为框架FE的填充值，属于分析中间产物

1. 默认情况下对象被视为真，除非定义了返回False的`__bool__()`或返回零的`__len__()`（←片段1）
2. 被视为假的内建对象包括：None、False、0、0.0、0j、''、()、[]、{}、set()、range(0)（←片段2）
3. 布尔运算and/or返回其操作数之一（非布尔值），not返回布尔值True或False（←片段3）
4. and为短路运算：x假则返回x；or为短路运算：x真则返回x（←片段3）
5. 比较运算符8种：<、>、==、>=、<=、!=、is/is not、in/not in，优先级相同且低于数值运算符（←片段4）
6. 比较可链式组合，等价于and连接但中间值仅求值一次（←片段4）
7. 整数int具有无限精度（←片段5）
8. 浮点数float通常用C的double实现，精度信息在sys.float_info（←片段6）
9. 复数complex有实部和虚部，各为浮点数（←片段7）
10. 位运算&、|、^、~、<<、>>仅对整数有意义，按无限符号位补码计算（←片段8）
11. bool是int的子类，True和False是其唯二实例（←片段9）
12. 迭代器协议：`__iter__()`返回自身，`__next__()`返回下一值或抛出StopIteration（←片段10）
13. 生成器由yield创建，实现迭代器协议，额外有send()、throw()、close()（←片段11）
14. 公共序列操作包括：in/not in、+/、索引s[i]、切片s[i:j:k]、len/min/max/index/count（←片段12）
15. 不可变序列额外支持hash()，使其可用作dict键和set元素（←片段13）
16. 可变序列额外支持项赋值、项删除、切片赋值、切片删除、append/clear/copy/extend/insert/pop/remove/reverse（←片段14）
17. list是可变序列，通常存储同类项（←片段15）
18. tuple是不可变序列，通常存储异构数据，常用于记录（←片段16）
19. range是不可变数字序列，不支持拼接和重复，常用于for循环（←片段17）
20. str是Unicode码位的不可变序列（←片段18）
21. str提供近50种方法，涵盖大小写变换、查找替换、分割拼接、格式化、分类判断等（←片段19）
22. f-string是以f/F为前缀的格式化字符串字面量，替换字段在运行时求值（←片段20）
23. t-string是以t/T为前缀的字符串模板，创建时返回Template对象不求值（3.14新增）（←片段21）
24. bytes是不可变的单字节序列；bytearray是其可变对应物，无字面量语法（←片段23、24）
25. memoryview通过缓冲区协议无复制地访问其他二进制对象的内存（←片段22、25）
26. set是不同可哈希对象的无序可变集合；frozenset是其不可变版本（←片段26）
27. 集合运算：|并集、&交集、-差集、^对称差集；关系运算：子集/超集测试（←片段27）
28. dict将可哈希值映射到任意对象，保留插入顺序，更新键不影响顺序，添加/删除键影响顺序（←片段28）
29. dict.keys()/values()/items()返回动态视图对象，反映字典变化；keys视图和items视图（当值可哈希时）是类集合的（←片段29）
30. 上下文管理器通过`__enter__`/`__exit__`方法实现with语句的运行时上下文（←片段30）
31. 泛型别名list[int]等由下标操作创建，`__args__`返回类型参数，`__origin__`返回原泛型类（←片段31）
32. 联合类型X|Y等价于typing.Union[X,Y]，3.14起联合对象是typing.Union的实例（←片段32）
33. 模块仅支持属性访问m.name；函数对象仅支持调用func(args)；方法是用属性记法调用的函数（←片段33）
34. 特殊属性包括__dict__、__class__、__name__、__bases__、__mro__、__doc__、__module__等（←片段34）
35. 整数字符串转换在非2幂次进制下为超线性复杂度，默认限制4300位，可调（←片段35）

## 缺口
> 从原始语料分析得出的**知识缺口**：语料没有明确说明、缺少定义、边界模糊的点，属于分析中间产物

1. `__bool__()`和`__len__()`同时存在时的优先级未明确说明——语料仅说"__bool__() returns False OR __len__() returns zero"，但若两者同时定义且结果矛盾呢？（相关片段1）
2. "被视为假"的清单用"most of"限定——哪些内建对象被视为假但未列出？自定义类的假值规则仅暗示未展开（相关片段2）
3. 布尔运算and/or对非布尔操作数的返回语义（返回操作数本身而非True/False）虽已说明，但学习者常将其与"返回布尔值"混淆，语料未强调此区别的后果（相关片段3）
4. 浮点数"通常"用C double——"通常"暗示存在例外，但未说明何种实现不用double（相关片段6）
5. 复数不支持整数类型的位运算、float的as_integer_ratio()等——语料零散提及，未系统总结复数的运算限制（相关片段7）
6. 生成器的send()/throw()/close()的具体语义和协议仅在stdtypes中简要提及，详细定义在yield表达式文档中（相关片段11）
7. str的近50种方法的分类体系（大小写、查找、替换、分割、格式化、判断）未在语料中显式分组，需读者自行归纳（相关片段19）
8. t-string作为Python 3.14新增特性，其Template对象的完整API和行为规范未在stdtypes中展开（相关片段21）
9. bytes/bytearray的"ASCII兼容方法"在非ASCII数据上的行为（如静默截断或抛异常）未系统说明（相关片段23）
10. memoryview的cast()/tolist()/toreadonly()/release()等高级操作的完整语义未充分展开（相关片段25）
11. dict视图的"动态性"在迭代时修改字典会引发RuntimeError，但"安全修改"的边界（如仅更新值不增删键是否安全）未明确（相关片段29）
12. 集合要求元素可哈希，但"可哈希"的精确定义（`__hash__`+`__eq__`契约、哈希不变性要求）在stdtypes中未完整给出（相关片段26）
13. 泛型别名和联合类型的运行时行为与类型检查器行为的差异未系统讨论（相关片段31、32）
14. 模块的`__dict__`是命名空间的实现细节还是接口保证未明确（相关片段33）
15. 整数字符串转换限制中"非2幂次进制"的技术原因（超线性复杂度的数学根源）未展开（相关片段35）

## 误解
> 从原始语料推导的学习者**潜在错误理解**，属于分析中间产物

1. 误解"and/or运算总是返回True或False"——and/or返回操作数之一，仅not返回布尔值。`3 and 5`返回5而非True（←片段3诱导）
2. 误解"所有空对象都是False"——语料用"most of"限定，少数自定义对象可能即使为空也为真（如重写了`__bool__`）（←片段2诱导）
3. 误解"链式比较从左到右依次求值"——链式比较等价于and连接但中间值仅求值一次，求值语义与独立比较不同（←片段4诱导）
4. 误解"浮点数能精确表示所有小数"——C double为IEEE 754双精度，存在0.1+0.2≠0.3等精度问题，但语料未强调（←片段6诱导）
5. 误解"bool是与int独立的类型"——bool是int的子类，True==1、False==0，可参与算术运算（←片段9诱导）
6. 误解"range返回列表"——range是惰性不可变序列，不存储所有值，与Python 2的xrange类似但类型不同（←片段17诱导）
7. 误解"bytes是str的二进制版本"——bytes是字节序列，str是Unicode码位序列，两者语义模型不同；bytes的一些方法仅在ASCII兼容时有效（←片段18、23诱导）
8. 误解"字典视图是快照"——视图是动态的，字典修改后视图立即反映变化；迭代视图时修改字典可能引发RuntimeError（←片段29诱导）
9. 误解"set是无序的所以不保证任何顺序"——3.7起dict保证插入顺序，但set仍无序，然而CPython的set实现对固定数据结构有确定性迭代顺序（非保证但可观察）（←片段26诱导）
10. 误解"f-string和t-string功能相同"——f-string在创建时求值返回str，t-string返回Template对象延迟求值，语义完全不同（←片段20、21诱导）
11. 误解"`is`比较值相等性"——`is`比较对象身份（同一性），`==`比较值相等性；`a == b`为True不保证`a is b`为True（←片段4诱导）
12. 误解"所有可迭代对象都是迭代器"——可迭代对象实现`__iter__()`返回迭代器，迭代器实现`__next__()`；list是可迭代对象但不是迭代器（←片段10、12诱导）

## Python内建类型框架
|框架名称|刻画描述|框架元素（FE）及填充|原始事实语料|原始语料定位|
|---|---|---|---|---|
|真值判定框架|Python对象真/假值的判定规则与假值清单|`默认规则`（核心）: 对象默认为真，除非定义`__bool__()`返回False或`__len__()`返回零<br>`假值清单`（核心）: None、False、0/0.0/0j、''/()/{}/set()/range(0)<br>`协议层级`（外围）: `__bool__`优先于`__len__`|1, 2|片段1‑2；stdtypes.txt L21‑48|
|布尔运算框架|and/or/not三个布尔运算符的短路语义与返回值规则|`and语义`（核心）: x假→返回x；x真→返回y（短路）<br>`or语义`（核心）: x真→返回x；x假→返回y（短路）<br>`not语义`（核心）: x假→True；x真→False<br>`返回类型`（外围）: and/or返回操作数之一（非布尔），not返回布尔值|3|片段3；stdtypes.txt L49‑79|
|比较运算框架|8种比较运算符的优先级、链式求值语义与身份/包含比较|`运算符集`（核心）: <>==>=<=!=、is/is not、in/not in<br>`优先级`（核心）: 所有比较同优先级，低于数值运算符<br>`链式语义`（核心）: 链式比较等价and连接但中间值仅求值一次<br>`身份vs值`（外围）: is比较对象身份，==比较值相等性|4|片段4；stdtypes.txt L80‑136|
|整数类型框架|无限精度整数的运算、位运算与方法集|`精度`（核心）: 无限精度<br>`位运算`（核心）: &|^~<<>>按无限符号位补码<br>`方法集`（核心）: bit_count/bit_length/conjugate/denominator/as_integer_ratio/is_integer/real/imag/numerator<br>`构造方式`（外围）: 字面量、int()构造|5, 8, 10|片段5、8、9；stdtypes.txt L137‑324|
|浮点类型框架|IEEE 754双精度浮点数的实现、限制与方法集|`实现`（核心）: 通常C double，细节在sys.float_info<br>`方法集`（核心）: as_integer_ratio/is_integer/conjugate/hex/fromhex<br>`精度限制`（核心）: IEEE 754有限精度，存在舍入误差<br>`特殊值`（外围）: inf、-inf、nan|6|片段6；stdtypes.txt L499‑591|
|复数类型框架|复数的实部/虚部构成与运算限制|`构成`（核心）: 实部和虚部各为浮点数<br>`属性`（核心）: real、imag、conjugate()<br>`运算限制`（外围）: 不支持位运算、//运算、as_integer_ratio等|7|片段7；stdtypes.txt L592‑609|
|布尔类型框架|bool作为int子类的双重身份|`父类型`（核心）: bool是int的子类<br>`实例`（核心）: True和False为唯二实例<br>`算术参与`（外围）: True==1、False==0，可参与算术运算<br>`转换协议`（外围）: bool(x)使用标准真值测试过程|9|片段9；stdtypes.txt L707‑731|
|迭代器协议框架|迭代器的`__iter__`/`__next__`协议与StopIteration|`__iter__`（核心）: 返回迭代器对象自身<br>`__next__`（核心）: 返回下一值或抛出StopIteration<br>`耗尽语义`（核心）: 一旦耗尽，后续调用永久抛出StopIteration<br>`与可迭代区别`（外围）: 可迭代实现`__iter__`返回迭代器，迭代器额外实现`__next__`|10|片段10；stdtypes.txt L732‑780|
|生成器类型框架|yield创建的生成器迭代器的扩展方法|`创建方式`（核心）: 由yield语句创建<br>`迭代器协议`（核心）: 实现`__iter__`和`__next__`<br>`独有方法`（核心）: send()、throw()、close()|11|片段11；stdtypes.txt L781‑791|
|序列公共操作框架|所有序列类型共享的操作集|`成员测试`（核心）: in/not in<br>`拼接与重复`（核心）: +（拼接）、*（重复）<br>`索引与切片`（核心）: s[i]、s[i:j]、s[i:j:k]<br>`聚合`（核心）: len/min/max/index/count<br>`可迭代性`（外围）: 所有序列可迭代|12|片段12；stdtypes.txt L800‑977|
不可变性增值框架|不可变序列类型额外提供的hash支持|`hash支持`（核心）: 实现hash()使其可用作dict键和set元素<br>`与可变区别`（核心）: 这是不可变序列实现而可变序列不实现的唯一额外操作<br>`可哈希条件`（外围）: 元素也必须可哈希|13|片段13；stdtypes.txt L978‑991|
|可变性增值框架|可变序列类型额外提供的修改操作集|`项操作`（核心）: s[i]=x、del s[i]、s[i:j]=t、del s[i:j]<br>`修改方法`（核心）: append/clear/copy/extend/insert/pop/remove/reverse<br>`重复赋值`（外围）: s*=n|14|片段14；stdtypes.txt L992‑1101|
|列表类型框架|list作为可变序列的同类项集合|`可变性`（核心）: 可变序列<br>`用途`（核心）: 通常存储同类项<br>`排序`（核心）: list.sort()原地排序<br>`构造`（外围）: list()或[]字面量|15|片段15；stdtypes.txt L1102‑1187|
|元组类型框架|tuple作为不可变序列的异构数据记录|`不可变性`（核心）: 不可变序列<br>`用途`（核心）: 通常存储异构数据，用于记录<br>`hash支持`（核心）: 可用作dict键和set元素（若元素可哈希）<br>`构造`（外围）: tuple()或()字面量|16|片段16；stdtypes.txt L1188‑1234|
|range类型框架|range作为不可变数字序列的惰性循环工具|`不可变性`（核心）: 不可变数字序列<br>`惰性`（核心）: 不存储所有值，按需计算<br>`操作限制`（核心）: 不支持+拼接和*重复<br>`构造`（外围）: range(stop)或range(start,stop[,step])|17|片段17；stdtypes.txt L1235‑1351|
|字符串类型框架|str作为Unicode码位不可变序列的近50种方法体系|`本质`（核心）: Unicode码位的不可变序列<br>`方法分类`（核心）: 大小写变换(capitalize/casefold/lower/upper/swapcase/title)、查找替换(find/rfind/index/rindex/replace/removeprefix/removesuffix)、分割拼接(split/rsplit/splitlines/partition/rpartition/join)、格式化(format/format_map/maketrans/translate)、分类判断(isalnum/isalpha/isascii/isdecimal/isdigit/isnumeric/isidentifier/islower/isupper/isspace/istitle/isprintable)、对齐填充(center/ljust/rjust/zfill/strip/lstrip/rstrip/expandtabs)、编码(encode)<br>`编码`（外围）: str.encode()转为bytes|18, 19|片段18‑19；stdtypes.txt L1449‑2495|
|f-string框架|f/F前缀的运行时求值格式化字符串字面量|`前缀`（核心）: f或F<br>`替换字段`（核心）: {}分隔的表达式，运行时求值<br>`与常量字面量区别`（核心）: 非常量，是运行时表达式<br>`格式规格`（外围）: 支持格式说明符、转换标志|20|片段20；stdtypes.txt L2496‑2614|
|t-string框架|t/T前缀的延迟求值字符串模板（3.14新增）|`前缀`（核心）: t或T<br>`返回类型`（核心）: 返回Template对象而非str<br>`延迟求值`（核心）: 创建时不求值，提供静态部分和插值表达式的访问<br>`与f-string区别`（核心）: f-string立即求值返回str，t-string延迟返回Template|21|片段21；stdtypes.txt L2615‑2649|
|bytes类型框架|bytes作为不可变单字节序列及其ASCII方法|`不可变性`（核心）: 不可变单字节序列<br>`字面量`（核心）: b'...'或b"..."<br>`ASCII方法`（核心）: 提供仅在ASCII兼容数据上有效的方法<br>`与str转换`（外围）: bytes.decode()转str|23|片段23；stdtypes.txt L2821‑3800+|
|bytearray类型框架|bytearray作为bytes的可变对应物|`可变性`（核心）: bytes的可变对应物<br>`无字面量`（核心）: 没有专用字面量语法，只能用构造函数<br>`方法集`（核心）: 具有与bytes相同的操作加上可变修改方法|24|片段24；stdtypes.txt L3800‑4531|
|memoryview类型框架|memoryview通过缓冲区协议无复制共享二进制内存|`缓冲区协议`（核心）: 使用buffer protocol访问其他二进制对象的内存<br>`零复制`（核心）: 不需要复制数据即可操作<br>`元素与格式`（核心）: 具有由原始对象设置的元素概念和格式概念|22, 25|片段22、25；stdtypes.txt L4532‑4780+|
|集合类型框架|set/frozenset的可哈希元素无序集合与数学运算|`元素约束`（核心）: 元素必须是可哈希的<br>`无序性`（核心）: 无序集合<br>`可变/不可变`（核心）: set可变、frozenset不可变<br>`数学运算`（核心）: |并集、&交集、-差集、^对称差集<br>`关系运算`（外围）: </<=/>/>=子集/超集测试|26, 27|片段26‑27；stdtypes.txt L4532‑4779|
|映射类型框架|dict将可哈希键映射到任意值并保留插入顺序|`键约束`（核心）: 键必须可哈希<br>`映射语义`（核心）: 键→值的映射<br>`插入顺序`（核心）: 保留插入顺序，更新键不影响顺序，添加/删除键影响顺序<br>`字典推导`（外围）: {k: v for ...}语法|28|片段28；stdtypes.txt L4780‑5056|
|字典视图框架|dict.keys()/values()/items()的动态视图对象|`动态性`（核心）: 视图反映字典变化<br>`键视图类集合`（核心）: keys视图唯一且可哈希，items视图在值可哈希时亦类集合<br>`可迭代`（核心）: 支持迭代、len、in、reversed<br>`mapping属性`（外围）: .mapping返回原始字典的只读代理<br>`迭代安全`（外围）: 迭代时增删条目可能引发RuntimeError|29|片段29；stdtypes.txt L5057‑5160|
|上下文管理器框架|`__enter__`/`__exit__`方法实现with语句的运行时上下文|`__enter__`（核心）: 进入上下文，返回上下文对象<br>`__exit__`（核心）: 退出上下文，接收异常信息(exc_type,exc_value,traceback)<br>`异常处理`（核心）: `__exit__`返回True则抑制异常|30|片段30；stdtypes.txt L5161‑5234|
|泛型别名框架|list[int]等下标操作创建的类型注解别名|`创建方式`（核心）: 对泛型类/类型进行下标操作<br>`__args__`（核心）: 类型参数元组<br>`__origin__`（核心）: 被别名的原泛型类<br>`用途`（外围）: 主要用于类型注解|31|片段31；stdtypes.txt L5235‑5548|
|联合类型框架|X|Y语法的多类型联合类型注解|`语法`（核心）: X|Y等价typing.Union[X,Y]<br>`运算规则`（核心）: 联合扁平化、冗余去除、顺序无关、Optional=|None<br>`isinstance支持`（核心）: 支持isinstance/issubclass检查<br>`运行时限制`（外围）: 含参数化泛型时isinstance受限；含前向引用需用字符串|32|片段32；stdtypes.txt L5549‑5660|
|其他内建类型框架|模块、函数、方法等非数据类型内建对象|`模块`（核心）: 仅支持属性访问m.name<br>`函数`（核心）: 仅支持调用func(args)<br>`方法`（核心）: 用属性记法调用的函数<br>`可调用性`（外围）: 函数和方法都可调用|33|片段33；stdtypes.txt L5661‑5843|
|特殊属性框架|对象的内省属性集|`实例属性`（核心）: __dict__、__class__<br>`类属性`（核心）: __name__、__bases__、__mro__、__doc__、__module__<br>`函数属性`（外围）: __name__、__doc__、__module__、__code__、__defaults__等|34|片段34；stdtypes.txt L5844‑5880|
|整数字符串转换限制框架|防止DoS攻击的转换长度限制机制|`超线性复杂度`（核心）: 非2幂次进制下整数↔字符串转换为超线性<br>`默认限制`（核心）: 4300位十进制数字<br>`可调`（核心）: sys.get/set_int_max_str_digits()检查和修改<br>`安全考量`（外围）: CVE-2020-10735拒绝服务漏洞|35|片段35；stdtypes.txt L5881‑6068|

## Python内建类型框架间关系
> FrameNet标准关系：`Inheritance`（继承）、`Perspective on`（视角化）、`Using`（使用/依赖）、`Subframe`（子框架）、`Precedes`（先行）、`Causative of`（致使）、`Inchoative of`（起始）、`Metaphor`（隐喻）、`See also`（参见）

**第一组：数值类型族内部关系**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|布尔类型框架|`Inheritance`|整数类型框架|bool是int的子类，继承int的算术语义并增加布尔真值语义|
|整数类型框架|`Perspective on`|浮点类型框架|整数和浮点数是数值的不同精度视角，int为无限精度而float为有限精度|
|浮点类型框架|`Using`|复数类型框架|复数的实部和虚部各为浮点数，复数的构成依赖浮点类型|

**第二组：序列类型族内部关系**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|不可变性增值框架|`Inheritance`|序列公共操作框架|不可变序列在公共操作基础上增加hash()支持|
|可变性增值框架|`Inheritance`|序列公共操作框架|可变序列在公共操作基础上增加修改操作集|
|列表类型框架|`Using`|可变性增值框架|list是可变序列，使用可变序列的修改操作|
|元组类型框架|`Using`|不可变性增值框架|tuple是不可变序列，使用不可变序列的hash()支持|
|range类型框架|`Using`|不可变性增值框架|range是不可变序列，但放弃了+拼接和*重复|
|字符串类型框架|`Using`|不可变性增值框架|str是不可变序列，额外提供近50种文本处理方法|
|bytes类型框架|`Using`|不可变性增值框架|bytes是不可变序列，额外提供ASCII兼容的字节操作方法|
|bytearray类型框架|`Using`|可变性增值框架|bytearray是可变序列，组合了bytes的方法和可变修改方法|

**第三组：二进制序列族内部关系**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|bytearray类型框架|`Perspective on`|bytes类型框架|bytearray是bytes的可变视角，拥有相同操作集加上修改能力|
|memoryview类型框架|`Using`|bytes类型框架|memoryview通过缓冲区协议访问bytes对象的内存|
|memoryview类型框架|`Using`|bytearray类型框架|memoryview通过缓冲区协议访问bytearray对象的内存|

**第四组：集合与映射族内部关系**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|集合类型框架|`Using`|真值判定框架|集合的成员测试依赖in运算，in运算结果的真值由真值判定框架决定|
|映射类型框架|`Using`|真值判定框架|dict的成员测试同理|
|字典视图框架|`Subframe`|映射类型框架|字典视图是dict附属的动态观察机制，是映射类型的子功能|
|字典视图框架|`Using`|集合类型框架|keys视图和items视图支持集合运算，复用集合的数学操作语义|

**第五组：格式化族内部关系**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|t-string框架|`Inchoative of`|f-string框架|t-string是f-string的延迟求值变体，从"立即求值"到"延迟求值"的起始态关系|
|f-string框架|`Using`|字符串类型框架|f-string求值结果为str，使用字符串的格式化能力|

**第六组：迭代器族内部关系**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|生成器类型框架|`Inheritance`|迭代器协议框架|生成器实现迭代器协议并扩展send/throw/close方法|
|迭代器协议框架|`Using`|序列公共操作框架|迭代器为序列（及所有可迭代对象）提供逐元素访问机制|

**第七组：类型注解族内部关系**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|联合类型框架|`Perspective on`|泛型别名框架|联合类型是对泛型组合的另一种视角——X|Y vs Union[X,Y]|
|泛型别名框架|`Using`|整数类型框架|泛型别名的`__origin__`指向原始泛型类，如list[int]的__origin__为list|

**第八组：跨族关系**
|源框架|FrameNet关系|目标框架|关系释义|
|---|---|---|---|
|布尔运算框架|`Using`|真值判定框架|and/or/not运算依赖对象的真/假值判定|
|比较运算框架|`Using`|真值判定框架|比较结果为True/False，is/in等比较的真值由真值判定框架解释|
|布尔运算框架|`Precedes`|比较运算框架|布尔运算优先级低于比较运算，在表达式中比较先于布尔运算执行|
|上下文管理器框架|`See also`|迭代器协议框架|两者都是通过协议方法(__enter__/__exit__ vs __iter__/__next__)定义行为的语言设施|
|特殊属性框架|`See also`|其他内建类型框架|模块的__dict__、函数的__name__等是跨类型的内省机制|
|整数字符串转换限制框架|`Using`|整数类型框架|转换限制机制直接作用于int与str之间的转换操作|
