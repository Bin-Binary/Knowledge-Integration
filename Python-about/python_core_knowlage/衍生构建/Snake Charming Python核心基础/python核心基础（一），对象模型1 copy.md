# Python核心基础（一）：对象模型

## 引言

在 Java 中，`int` 是原始类型，`Integer` 才是对象——两套机制，两套API，两套心智模型。在 C++ 中，值语义与引用语义的切换靠 `&` 和 `*` 手动标注，编译器不会替你记住。在 Go 中，结构体和方法是松耦合的，反射是事后补充的工具，而非设计的一等公民。

Python 做了一个足够激进的决定：**一切皆 `PyObject`**。

整数是对象，函数是对象，类本身也是对象，甚至连 `type` 这个造物者——其类型也指向自身。这并非修辞上的"皆对象"，而是 CPython 层面每个值都共享同一个 `ob_refcnt + ob_type` 头部，`type()`、`id()`、`dir()` 对 `int` 和自定义 class 一视同仁。这种**结构级统一**的直接后果是：反射、序列化、鸭子类型、装饰器这些在其他语言中需要特殊机制或绕道实现的能力，在 Python 中是对象模型的自然推论，而非语言的补丁。

但统一有代价。为了让 `int` 也戴上 `PyObject` 的帽子，每个整数至少背负 16 字节的对象头部开销；为了让赋值统一为引用绑定，`is` 与 `==` 的含混成了 Python 最经典的陷阱之一，可变对象的共享修改风险也如影随形。这不是缺陷，而是 Python 在**类型一致性**与**语义折中**之间的工程权衡——它选择了统一性的优先，承受了代价的可预期。

理解对象模型，不只是知道"Python 里万物皆对象"这句话。它是读懂 Python 一切行为的起点：为什么赋值不产生拷贝？为什么 `len()` 是内置函数而非方法？为什么装饰器能装饰任何可调用对象？为什么 `type` 的 type 是 `type` 自身？这些问题的答案都回溯到同一个根——`PyObject` 的统一契约。

本文将追踪一个对象从**创建、绑定、使用到销毁**的完整生命周期，用可运行的代码逐步揭开 `PyObject` 内部结构的每一层——你将亲眼看到 `ob_type` 如何让类型查询统一起来，`ob_refcnt` 如何主导生死，以及"一切皆对象"在运行时究竟意味着什么。

### Python 的四个语言定位，根植于对象模型

人们常说 Python 是"解释型、动态类型、强类型、面向对象"的语言。这四个标签并非独立的语言特性，而是 **`PyObject` 统一契约的四个投影**：

| 语言定位 | 对象模型根因 | 体现 |
|:---|:---|:---|
| **解释型** | 对象在运行时创建，运行时查 `ob_type` 决定行为 | 没有 AOT 编译期类型特化，每次 `obj.attr` 都要走 `ob_type → MRO` 查找 |
| **动态类型** | 变量不是类型容器，只是名字标签；类型信息在对象的 `ob_type` 上 | `x = 42; x = "hi"` 合法——`x` 只是换了个绑定，`ob_type` 从 `int` 切到 `str` |
| **强类型** | `ob_type` 决定了对象能参与什么操作，隐式转换严格受限 | `"3" + 4` → TypeError，不会像 JS 那样靠编译器暗转 |
| **面向对象** | 一切值都是 `PyObject` 实例，类也是 `type` 的实例 | `type(42)`, `type(len)`, `type(int)` 同一条查询路径 |

**动态类型的根因**：变量（名字）不存储类型信息，类型跟随对象走。当 `x = 42`，名字空间中记录的是 `x → PyObject*`（一个指针），而非 `x: int = 42`（一个类型化的存储槽）。类型标注 `x: int = 42` 只是 `__annotations__` 中的一个条目，解释器在运行时完全忽略。所以 `x` 可以随时重新绑定为另一个不同类型的对象——名字只是标签，换贴不涉及任何类型系统约束。

```python
x = 42
print(type(x), id(x))          # <class 'int'> 140...

x = "hello"                    # 重新绑定, ob_type 从 int → str
print(type(x), id(x))          # <class 'str'> 140...（不同对象）

# 名字 x 的"类型"从未改变——它根本没有类型, 只有当前绑定的对象有类型
```

**强类型的根因**：`ob_type` 指向的 `PyTypeObject` 严格定义了操作槽位。`"3" + 4` 失败不是因为编译器检查，而是运行时 `str.__add__` 发现右操作数的 `ob_type` 不是 `str`，返回 `PyNotImplemented`，最终走到 `TypeError`。这与 JS 的 `"3" + 4 → "34"` 形成对比——JS 选择隐式调用 `toString()`/`valueOf()` 强转，Python 选择让 `PyTypeObject` 的槽位严格匹配，不做隐式跨类型转换。

```python
"3" + 4     # TypeError: can only concatenate str (not "int") to str
int("3") + 4    # 7 — 显式转换是程序员的责任, 不是类型系统的
```

理解这四个定位都回溯到 `PyObject`，能让你不再把它们当作独立的"语言特点"来记忆，而是看到它们是**同一个结构决策的四个命名**——统一对象模型的运行时成本是解释执行和动态查找（解释型 + 动态类型的代价），收益是类型安全的统一和一切皆对象的反射能力（强类型 + 面向对象的收益）。

---

## 一、对象的创建

### 1.1 每个对象都戴同一顶帽子

Python 中创建一个对象，无论是在字面量中写 `42`，还是调用 `int(42)`，亦或是 `class Foo: pass` 产生一个类对象——CPython都在堆上分配一块内存，其开头永远是同一个头部结构：

```
PyObject                           ← 16 字节 (64位系统)
├── ob_refcnt  (Py_ssize_t, 8B)   ← 引用计数，决定对象生死
└── ob_type    (PyTypeObject*, 8B) ← 类型指针，决定对象是什么

PyVarObject                        ← 继承 PyObject + 8 字节
├── ob_refcnt  (Py_ssize_t, 8B)
├── ob_type    (PyTypeObject*, 8B)
└── ob_size    (Py_ssize_t, 8B)    ← 元素数量（非字节数）

PyLongObject (int)                 ← 继承 PyObject, 定长
├── [PyObject 头部, 16B]
└── ob_digit[] (digit数组, 变长)   ← 30-bit digit, 每个占 4B

PyUnicodeObject (str, PEP 393)     ← 继承 PyVarObject
├── [PyVarObject 头部, 24B]
├── hash         (Py_hash_t, 8B)   ← 缓存的哈希值
├── state        (1B, 位域)        ← ASCII/紧凑/内联标志
├── length       (Py_ssize_t, 8B) ← UTF-8 字节长度
├── utf8         (char*, 8B)      ← UTF-8 编码缓存(惰性)
└── 数据区: ASCII=1B/char, UCS1/UCS2/UCS4 按需选择

PyListObject (list)                ← 继承 PyVarObject
├── [PyVarObject 头部, 24B]
├── ob_item      (PyObject**, 8B)  ← 指向指针数组的指针
└── allocated    (Py_ssize_t, 8B)  ← 已分配槽位数 ≥ ob_size
    数据区: ob_item[0..allocated-1], 每个槽位8B指针
```

上面这张结构图列出了四个 C 结构体。在进入实验之前，需要理解它们之间的关系——这是读懂全文的基石：

```
               PyObject (16B 头部, 所有对象共用)
               ├── ob_refcnt  ← 谁在持有我
               └── ob_type    ← 我是什么类型
                    │
          ┌─────────┼──────────────┐
          ↓         ↓              ↓
    定长对象      变长对象      类型对象
  PyLongObject  PyVarObject  PyTypeObject
  (int/float)   (str/list/    (int/str/list
                  tuple)       这些类本身)
       │            │              │
  继承PyObject  继承PyObject   也是一个PyObject
  只加有效载荷  +ob_size       +几十个槽位(slot)
                 (元素数量)     = 类型的能力清单
```

**三个结构体的关系**：

- **`PyObject`** — 最小公共头部，不管你是整数、字符串还是函数，前 16 字节永远是 `ob_refcnt + ob_type`。`id()` 返回的就是这块内存的起始地址。
- **`PyVarObject`** — 在 `PyObject` 基础上多 8 字节的 `ob_size`，记录元素个数。`str`、`list`、`tuple` 都继承它来表示"我包含多少东西"。
- **`PyTypeObject`** — 类型对象自身（如 `int`、`str`、`list` 这些类）。它**也是一个 `PyObject`**（也有 `ob_refcnt` 和 `ob_type`——`int` 的 `ob_type` 指向 `type`），但额外携带了几十个**槽位（slot）**，每个槽位是一个函数指针，定义该类型的能力。

**槽位 = 类型的能力清单**。一个对象能做什么，不是由对象自身的内存决定的，而是由其 `ob_type` 指向的 `PyTypeObject` 中的槽位决定的：

| 槽位 | 含义 | 有槽位的类型 | 无槽位的类型 | 效果 |
|:---|:---|:---|:---|:---|
| `tp_call` | 可调用(函数/类) | `int`、`str`、自定义函数 | `42`、`"hi"` | `int("42")` 成功，`42()` TypeError |
| `tp_hash` | 可哈希(dict key) | `str`、`tuple`、`int` | `list`、`dict` | `hash("hi")` 成功，`hash([])` TypeError |
| `sq_ass_item` | 索引赋值(原地修改) | `list`、`dict` | `str`、`tuple` | `L[0]=1` 成功，`s[0]="H"` TypeError |
| `tp_weaklistoffset` | 支持弱引用 | `list`、`dict`、自定义类 | `int`、`str`、`tuple` | `weakref.ref([])` 成功，`weakref.ref(42)` TypeError |

一个关键推论：**Python 层面看到的 `TypeError`，大多是 C 层面槽位为 NULL 的运行时检测**——不是编译器拒绝，而是 `ob_type` 指向的 `PyTypeObject` 没有实现那个操作的槽位。

> 日常编程中，`sys.getrefcount()` 和 `sys.getsizeof()` 是间接观测头部字段的标准方式。但在 CPython 上，你可以用 `ctypes` **直接读取** `ob_refcnt` 和 `ob_type` 的原始内存——这能让你亲眼确认"一切皆 PyObject"不是口号，而是内存中的物理事实。

**实验 0：用 ctypes 直接观测 PyObject 头部**

```python
import ctypes
import sys

class PyObject(ctypes.Structure):
    _fields_ = [
        ("ob_refcnt", ctypes.c_ssize_t),
        ("ob_type", ctypes.c_void_p),
    ]

class PyVarObject(PyObject):
    _fields_ = [
        ("ob_size", ctypes.c_ssize_t),
    ]

obj = [1, 2, 3]
addr = id(obj)
py_obj = PyObject.from_address(addr)
print(f"ob_refcnt = {py_obj.ob_refcnt}")   # 2 (obj + 临时引用)
print(f"ob_type   = {hex(py_obj.ob_type)}")
print(f"type()    = {type(obj)}")           # <class 'list'>

py_var = PyVarObject.from_address(addr)
print(f"ob_size   = {py_var.ob_size}")      # 3 (3个元素)

b = obj                                     # INCREF
print(f"INCREF后  ob_refcnt = {py_obj.ob_refcnt}")   # 3

del b                                       # DECREF
print(f"DECREF后  ob_refcnt = {py_obj.ob_refcnt}")   # 2
```

`id(obj)` 返回的正是 `PyObject` 在堆上的起始地址——`ctypes` 从该地址读取前 8 字节就是 `ob_refcnt`，接下来 8 字节就是 `ob_type`。`ob_type` 的值与 `id(type(obj))` 相等，因为 `type()` 本质上就是解引用这个指针。

> **注意**：`ctypes.from_address()` 不会增加引用计数，如果对象被回收后再访问该内存会导致段错误。仅在交互式实验中使用，不要在生产代码中依赖此技术。

**实验 0b：验证 ob_type = id(type(obj))**

```python
class PyTypeObject(ctypes.Structure):
    _fields_ = [
        ("ob_refcnt", ctypes.c_ssize_t),
        ("ob_type", ctypes.c_void_p),
        ("tp_name", ctypes.c_char_p),       # 类型名字符串
    ]

obj = 42
addr = id(obj)
py_hdr = PyObject.from_address(addr)

# ob_type 指向的地址 = int 类型对象的地址
type_addr = py_hdr.ob_type
print(f"ob_type 地址       = {hex(type_addr)}")
print(f"id(type(42)) 地址  = {hex(id(int))}")
print(f"两者相等: {type_addr == id(int)}")     # True

# 从类型对象地址读取 tp_name
type_obj = PyTypeObject.from_address(type_addr)
print(f"tp_name = {type_obj.tp_name}")          # b'int'
```

`type()` 不是魔法，它只是返回 `ob_type` 指针所指向的 `PyTypeObject`。而 `isinstance()` 则沿该指针指向的 `PyTypeObject` 的 `tp_mro` 链做遍历检查。整个类型系统的运行时行为，都建立在 `ob_type` 这一个指针之上。

**实验 1：最小对象的头部开销**

```python
import sys

print(sys.getsizeof(0))       # 28 — 一个 int 值为 0，却占 28 字节
print(sys.getsizeof(False))   # 28 — bool 继承自 int，同尺寸
print(sys.getsizeof(None))    # 16 — Python 中最轻的对象，仅头部
```

`None` 的 16 字节就是 `PyObject` 头部的代价——`ob_refcnt`（8字节）+ `ob_type`（8字节，64位系统），没有任何有效载荷。而 `int` 的 28 字节 = 16 字节头部 + 12 字节数值存储（CPython 的 int 采用 30-bit digit 数组，即使值为 0 也至少占一份）。

这就是统一的代价：**在 C 中一个 int 占 4 字节，在 Python 中至少 28 字节**。换回的是 `type(0)`, `type(None)`, `type(AnyClass)` 走的同一条代码路径。

**实验 2：定长 vs 变长——PyVarObject 的 ob_size**

```python
import sys

s1 = "a"
s2 = "ab"
print(sys.getsizeof(s1))          # 50
print(sys.getsizeof(s2))          # 51 — 多1字节，ob_size增长
print(sys.getsizeof(s2) - sys.getsizeof(s1))  # 1

print(sys.getsizeof([]))          # 56 — 空list，仅有PyVarObject头部
print(sys.getsizeof([1]))         # 64 — 增长8字节(一个指针)
```

`str` 的 `ob_size` 按字节增长（PEP 393 紧凑存储），`list` 按指针槽位增长（每个元素 8 字节指针）。`sys.getsizeof()` 返回的是**对象自身占用的内存**，不含其引用的其他对象——`[1]` 的 64 字节不含 int 对象 `1` 的 28 字节。

#### PEP 393 紧凑存储：str 为什么不可修改的底层闭环

上面的实验揭示了一个关键差异：`str` 直接在 `PyVarObject` 头部之后存储字符数据，而 `list` 在头部之后存储的是**指向其他对象的指针**。这不是偶然，而是两种根本不同的数据组织方式。

PEP 393 的设计：CPython 根据字符串内容自动选择最省内存的编码层级——纯 ASCII 字符串用 1 字节/字符（UCS1/Latin-1），含 BMP 字符用 2 字节/字符（UCS2），含补充字符用 4 字节/字符（UCS4）。数据**内联**在 `PyUnicodeObject` 结构体尾部，没有任何间接指针：

```
PyUnicodeObject 实例 (ASCII 字符串 "hi"):
┌──────────────────────────────────────┐
│ ob_refcnt = 1                        │ ← PyObject 头部
│ ob_type   → <class 'str'>            │
│ ob_size   = 2                        │ ← PyVarObject 扩展
│ hash      = -454810826               │
│ state     = 0x1F (ASCII|紧凑|内联)   │
│ length     = 2                       │
│ utf8      = NULL (与数据区共享,惰性) │
├──────────────────────────────────────┤
│ 'h' (0x68) │ 'i' (0x69)             │ ← 数据内联在结构体尾部!
└──────────────────────────────────────┘   每字符仅 1 字节

PyListObject 实例 (列表 [42, "hi"]):
┌──────────────────────────────────────┐
│ ob_refcnt = 1                        │ ← PyObject 头部
│ ob_type   → <class 'list'>           │
│ ob_size   = 2                        │ ← PyVarObject 扩展
│ ob_item   ──────────────────────────╂──→ [ptr0, ptr1, ...]
│ allocated = 2                        │       │      │
└──────────────────────────────────────┘       ↓      ↓
                                         PyLongObject  PyUnicodeObject
                                         (28 字节)    (56 字节)
```

**这就是 str 不可修改的底层根因**：数据内联在结构体中，意味着字符串的内存大小在创建时就固定了。如果允许原地修改，就会面临两个不可调和的矛盾：

1. **长度改变问题**：将 `"hi"` 修改为 `"hello"` 需要扩展内存，但结构体后面紧跟着的可能是其他对象的数据，无法原地扩张——这与 `list` 的 `ob_item` 指针可以 realloc 到新位置完全不同。
2. **编码层级改变问题**：将纯 ASCII 的 `"hi"` 修改为含中文的 `"hi你"`，需要从 UCS1（1B/char）切换到 UCS4（4B/char），整个数据区需要重新编码和重新分配——这根本不是"原地修改"能完成的。

而 `list` 的数据区存储的是定长指针（始终 8 字节），追加元素只是 realloc 指针数组，无需移动已有元素指向的对象，编码格式也永远不变——这就是 `list` 能做到可变的物理前提。

```python
import sys

s = "a"
print(sys.getsizeof(s))              # 50 — 头部49B + 数据1B

s_cn = "你"
print(sys.getsizeof(s_cn))           # 76 — 头部49B + 数据4B(UCS4)

L = [42, "hi"]
print(sys.getsizeof(L))              # 72 — 头部56B + 2个指针16B
print(sys.getsizeof(L[0]))           # 28 — int 42 自身的内存，不含在 list 中
```

**更一般的规律**：内联存储的对象必然不可变。这个规律不止适用于 `str`：

| 类型 | 数据存储方式 | 可变性 | 根因 |
|:---|:---|:---|:---|
| `str` | 内联在结构体尾部 | 不可变 | 长度/编码固定，无法原地扩展或切换 |
| `bytes` | 内联在结构体尾部 | 不可变 | 同 str，固定长度字节序列 |
| `tuple` | 内联在结构体尾部 | 不可变 | 定长指针数组，ob_size 不可变 |
| `int` | 内联在结构体尾部 | 不可变 | digit 数组长度不能原地改变 |
| `float` | 内联固定 8 字节 | 不可变 | 固定大小，无需扩展 |
| `list` | ob_item 指针指向独立数组 | 可变 | 可 realloc 指针数组，元素指针定长 |
| `dict` | 哈希表独立分配 | 可变 | 可重组哈希表，slot 大小固定 |
| `bytearray` | 独立缓冲区 | 可变 | 可 realloc 缓冲区，元素定长1B |

共同的模式是：**数据区的内存布局是否允许在不移动结构体本身的前提下改变大小**。内联数据做不到，间接指针（list）或独立缓冲区（bytearray）可以。不可变不是 Python 的任性限制，而是内存组织方式的物理约束在 `PyTypeObject` 层面的制度化：`sq_ass_item = NULL` 只是将"做不到"变成了"不允许"。

### 1.2 类型对象的创建——type 造万物

当你在代码中写 `class MyClass: pass` 时，Python 做了什么？它调用了 `type`，或者说调用了 `type.__call__`，而 `type` 自身也是一个 `PyObject`——只不过它的 `ob_type` 指向自己。

**实验 3：元循环闭合——type 的 type 是 type**

```python
print(type(42))         # <class 'int'>
print(type(int))        # <class 'type'>    — int 是 type 的实例
print(type(type))       # <class 'type'>    — type 是自己的实例
print(type(type(type))) # <class 'type'>    — 无限回归，终止于 type
```

这条链构成了 Python 对象图的**二分结构**：

```
实例层                    类型层
  42  ──ob_type──→  int  ──ob_type──→  type
                                 ↑           │
                                 └───────────┘ (自指)
```

永远只有两层：每个实例指向其类型，类型指向 `type`，`type` 指向自身。不存在第三层，也不需要第三层。这不是巧合，而是元类系统的设计边界——**`type` 是元循环闭合点**。

**实验 4：PyTypeObject 的字段——类型对象存了什么**

```python
print(int.__name__)          # 'int'        ← tp_name
print(int.__basicsize__)     # 28           ← tp_basicsize
print(int.__mro__)           # (int, object) ← MRO 继承链
print(callable(int))         # True         ← tp_call 存在
print(callable(42))          # False        ← int 实例无 tp_call
```

`__name__`, `__basicsize__`, `__mro__` 对应 C 层面 `PyTypeObject` 的 `tp_name`, `tp_basicsize`, `tp_mro` 字段。而 `callable()` 检查的是 `tp_call` 槽位是否非空——类型对象有（可以 `int("42")` 调用），实例对象没有。

### 1.3 创建的拦截——元类

类型对象的创建并非不可定制。Python 允许通过元类拦截 `type.__new__` 和 `type.__init__`，这是对象模型在**类型层**的控制权交接点。

```python
class Meta(type):
    def __new__(mcs, name, bases, namespace):
        print(f"创建类: {name}, 命名空间键: {list(namespace.keys())}")
        cls = super().__new__(mcs, name, bases, namespace)
        print(f"类对象id: {id(cls)}, 类型: {type(cls)}")
        return cls

class User(metaclass=Meta):
    role = "default"

# 输出:
# 创建类: User, 命名空间键: ['role', '__module__', '__qualname__']
# 类对象id: 140..., 类型: <class '__main__.Meta'>
```

`Meta.__new__` 在 `type.__new__` 之前执行，此时类对象尚未诞生——这是你能在对象创建前介入的唯一时机。一旦 `super().__new__()` 返回，`PyObject` 已在堆上分配完毕，`ob_type` 已指向 `Meta` 而非 `type`。

---

## 二、绑定——名字与对象的关系

### 2.1 名字空间、绑定与解绑

在 §1 中我们看到了对象如何被**创建**到堆上。但对象创建后，代码如何找到它？答案涉及两个核心概念：**名字空间**和**绑定**。

#### 名字空间 = 一个 dict

名字空间（namespace）就是一个普通的 dict，键是变量名（`str`），值是对象引用（`PyObject*`）。你在 Python 中写的每一次 `x = ...`，本质上都是对这个 dict 的一次写操作：

```python
x = 42
# 等价于: current_namespace['x'] = <PyObject at 0x...>  (int 42)

print(globals())   # 模块级名字空间: {'x': 42, '__name__': '__main__', ...}
```

Python 有多层名字空间，每层对应一个 dict，按 LEGB 顺序查找（详见 §2.4）。当前只需记住：**名字空间是对象和代码之间的桥梁——代码通过名字找到对象，对象通过被名字引用而存活。**

#### 绑定 = 名字贴上对象 + refcnt +1；解绑 = 名字撕下 + refcnt -1

对象在堆上，名字在名字空间 dict 中。**绑定**就是将两者关联起来：

```
名字空间 dict                堆上的对象
┌──────────────┐            ┌──────────────┐
│ 'a' ──────────╂────────→  │ ob_refcnt: 1 │  ← 绑定: refcnt += 1 (INCREF)
│ 'b' ──────────╂───────→  │ ob_type: int │
│              │            │ ob_digit: 42 │
└──────────────┘            └──────────────┘
```

- **绑定**（`a = 42`）：在名字空间中写入 `'a' → 42号对象`，对象的 `ob_refcnt` 加 1
- **解绑**（`del a` 或函数返回）：从名字空间中移除 `'a'`，对象的 `ob_refcnt` 减 1
- **重新绑定**（`a = 99`）：旧对象 refcnt - 1，新对象 refcnt + 1，名字 `'a'` 指向新对象

关键在于：**名字不是盒子，而是标签。** 一个对象可以贴多个标签（多个名字绑定同一对象），一个标签也可以随时换贴到另一个对象上。对象本身不存储"我叫什么名字"——名字是单向的，从名字空间指向对象。

### 2.2 赋值不是拷贝

上面说绑定 = 名字指向对象 + INCREF，没有拷贝。这不是省略，而是事实——Python 的赋值语句 **从不复制数据**：

```python
import sys

a = [1, 2, 3]
print(sys.getrefcount(a))  # 2 (a + getrefcount参数)

b = a                      # 绑定同一对象，INCREF
print(sys.getrefcount(a))  # 3
print(id(a) == id(b))      # True — 同一内存地址

c = [1, 2, 3]              # 新建对象，值相同但身份不同
print(a == c)              # True  — __eq__ 值比较
print(a is c)              # False — id() 不同，不同对象
```

`a is b` 为 `True`，因为 `is` 比较的是 `id()`——CPython 中即 `ob_type` 前面的内存地址（本质是指针比较）。`a == c` 为 `True`，因为 `==` 走的是 `__eq__` 方法——值比较，用户可自定义。

**实验 6：小整数池——编译期优化对 is 的影响**

```python
a = 256; b = 256
print(a is b)    # True  — 小整数池 [-5, 256] 缓存同一对象

a = 500; b = 500
print(a is b)    # False — 超出缓存范围，各建新对象
print(a == b)    # True  — 值相等
```

小整数池是 CPython 的实现细节，不是语言规范。但理解它却能解释一个令人困惑的现象：**同样写 `a is b`，有时 `True` 有时 `False`**。根因在于 `is` 比较的是对象身份（地址），而非值——编译器缓存了 `256`，没缓存 `500`。

### 2.3 可变 vs 不可变——引用语义的补丁与防线

赋值统一为引用绑定，意味着多个名字可以指向同一个 `PyObject`。这带来了一个核心风险：**如果一个对象允许原地修改，所有引用都会看到变化**。

```python
a = [1, 2]
b = a
b.append(3)
print(a)  # [1, 2, 3] — a 也变了！
```

`a` 和 `b` 指向同一个 `PyObject`，`append` 原地修改了 `ob_size` 和底层数组，所有引用都能看到变化。

那 Python 为什么不把所有对象都做成不可变，彻底消灭共享修改风险？因为**不可变有不可变的代价**——每次"修改"都必须创建新对象，对频繁更新的数据结构（如列表追加、字典插入）这意味着大量内存分配与复制，性能不可接受。

所以 Python 选择了**分区治理**：将数据对象分为可变和不可变两类，让程序员按场景选择。

#### 不可变对象的三大收益

**收益 1：哈希性——dict/set 的基石**

```python
print(hash(42))          # 42
print(hash("hello"))     # -7185670356144213527
print(hash((1, 2)))      # 3713081631934410656

print(hash([1, 2]))      # TypeError: unhashable type: 'list'
print(hash({1, 2}))      # TypeError: unhashable type: 'set'
```

`hash()` 要求对象在其生命周期内返回不变的哈希值。如果 list 可作为 dict 的 key，原地追加一个元素后哈希值变化，bucket 定位失效，字典直接崩坏。因此 **可变对象必须禁止哈希**——这不是建议，而是 `PyTypeObject` 层面的硬约束：可变类型的 `tp_hash` 槽位被设为 `_PyObject_HashNotImplemented`，调用即抛 `TypeError`。

**收益 2：常量折叠与 intern——编译期优化**

```python
a = 1000
b = 1000
print(a is b)   # 交互模式下通常 False

def f():
    x = 1000
    y = 1000
    print(x is y)  # 可能 True — 同一代码块常量折叠

f()
```

CPython 编译器可以对不可变对象做常量折叠（co_consts 合并）和字符串 intern——因为值不会变，多个引用共享同一对象是安全的。对可变对象做同样优化则是灾难：两个变量"碰巧"共享同一 list，一方修改另一方就遭殃。

小整数池（[-5, 256]）是同一逻辑的运行时版本：解释器启动时预创建这些 int 对象并缓存，所有代码共享——这之所以安全，正因为 int 不可变。

**收益 3：天然线程安全——无需锁即可共享读**

```python
from threading import Thread

SAFE_DATA = "constant"   # 不可变，多线程可安全读取

UNSAFE_DATA = [1, 2, 3]  # 可变，多线程并发 append 竞态
```

不可变对象在创建后状态不改变，多线程同时读取不需要加锁。GIL 保证的是字节码层面的原子性，不保证逻辑层面的线程安全——对可变对象的复合操作（check-then-act）仍需显式同步。

#### CPython 层面如何实现不可变

不可变不是靠程序员自觉，而是 `PyTypeObject` 槽位的硬限制：

| 槽位 | 不可变类型 (str, tuple) | 可变类型 (list, dict) |
|:---|:---|:---|
| `tp_hash` | 实现哈希函数 | `_PyObject_HashNotImplemented` → TypeError |
| `sq_ass_item` (索引赋值) | NULL → TypeError | 实现赋值逻辑 |
| `sq_ass_slice` (切片赋值) | NULL → TypeError | 实现赋值逻辑 |
| `mp_ass_subscript` (键赋值) | NULL → TypeError | 实现赋值逻辑 |

```python
t = (1, 2, 3)
t[0] = 10    # TypeError: 'tuple' object does not support item assignment
              # CPython: sq_ass_item 为 NULL, 走 PyErr_Format 报错

s = "hello"
s[0] = "H"  # TypeError: 'str' object does not support item assignment

L = [1, 2, 3]
L[0] = 10    # 成功 — sq_ass_item 指向 list_ass_item 实现
```

对不可变对象的原地修改操作，在 C 层面被槽位空指针拦截，根本进入不到赋值逻辑。这不是 Python 层的 `raise`，而是类型协议层的硬拒绝。

#### 设计闭环：因与补丁

现在可以看到完整的设计逻辑链：

```
赋值统一为引用绑定（因）
  → 多引用可指向同一对象（效果）
    → 可变对象的共享修改风险（代价）
      → 不可变分区作为安全防线（补丁）
        → 不可变带来哈希性/常量折叠/线程安全（收益）
          → 可变保留给需要原地更新的场景（分区治理）
```

可变/不可变**不是**绑定语义的区别（绑定对两者一视同仁），而是对象自身是否开放原地修改的写槽位——这个决定在 `PyTypeObject` 创建时就固化了，是类型设计层面的选择，而非运行时的限制。

不可变对象"修改"时创建新对象的行为，正是引用绑定语义的安全出口：

```python
s1 = "hello"
s2 = s1              # s1, s2 指向同一 str
s2 = s2 + " world"   # 新建 str, s2 重新绑定; s1 不受影响
print(s1)            # "hello"
```

`s2 = s2 + " world"` 并非原地修改，而是计算右值产生新 str 对象，再让 `s2` 重新绑定——等价于 `DECREF 旧对象 + INCREF 新对象 + 名字重绑定`。旧对象 `s1` 的引用计数不受影响，因此 `s1` 仍然输出 `"hello"`。

### 2.4 作用域、调用栈与名字空间——对象何时被解绑

§2.1 介绍了名字空间是 dict，绑定是名字贴上对象。但 Python 不是只有一个名字空间——不同区域有不同的名字空间，这就引出了**作用域**的概念。

#### 作用域 = 名字的可见范围

作用域规定了一个名字在**哪些代码区域**可以被找到。Python 用 LEGB 四层作用域，对应四个 dict：

```
作用域层级        名字空间 dict        可见范围
──────────────────────────────────────────────────
L (Local)        函数的 f_locals      当前函数体内
E (Enclosing)    外层函数的 f_locals  内层闭包函数
G (Global)       模块的 __dict__      整个 .py 文件
B (Built-in)     builtins.__dict__    所有代码
```

当 Python 遇到一个名字 `x`，按 L → E → G → B 的顺序查找 dict，第一个命中就返回。不同作用域的同名变量互不干扰：

```python
x = "global"       # G 层: 模块 __dict__['x'] = "global"

def f():
    x = "local"    # L 层: f_locals['x'] = "local"，遮蔽 G 层但不修改它
    print(x)       # "local" — L 层先命中

f()
print(x)           # "global" — G 层不受影响
```

注意：**作用域是规则（去哪找），名字空间是数据（里面有什么）**。作用域回答"这个名字该查哪个 dict"，名字空间回答"这个 dict 里面有哪些键值对"。

理解作用域后，"对象何时被解绑"就变成了一个精确的问题：**对象被哪个作用域的名字空间持有？那个作用域什么时候消失？**

我们已知道赋值 = 绑定 + INCREF，`del` = 解绑 + DECREF。但对象最常见的解绑时机不是显式 `del`，而是**函数返回时栈帧销毁**——L 层名字空间整体消失，所有局部对象的 refcnt 集体减 1。

#### 函数调用 = 创建栈帧 + 新建名字空间

每次函数调用，CPython 做三件事：

1. 创建一个栈帧对象（`PyFrameObject`），压入调用栈
2. 为该栈帧分配本地名字空间（`f_locals`，一个 dict）
3. 将实参绑定到形参名——每个绑定对应一次 INCREF

```python
import sys

def observe(x):
    print(f"  进入函数: x 的 refcnt = {sys.getrefcount(x)}")
    y = x                       # INCREF
    print(f"  绑定 y 后: x 的 refcnt = {sys.getrefcount(x)}")
    return y                    # 返回值 INCREF 给调用者

obj = [1, 2]
print(f"调用前: obj 的 refcnt = {sys.getrefcount(obj)}")
result = observe(obj)           # 实参→形参绑定, INCREF
print(f"调用后: obj 的 refcnt = {sys.getrefcount(obj)}")

# 输出:
# 调用前: obj 的 refcnt = 2
#   进入函数: x 的 refcnt = 3    (obj + x + getrefcount参数)
#   绑定 y 后: x 的 refcnt = 4   (obj + x + y + getrefcount参数)
# 调用后: obj 的 refcnt = 2      (函数返回, 栈帧销毁, x/y 的 DECREF 完成)
```

函数返回时，栈帧被销毁，`f_locals` 中所有名字对应的对象被 DECREF——这就是为什么 `x` 和 `y` 的引用在调用后消失。

#### 用栈帧对象直接观测

`sys._getframe()` 可以获取当前栈帧，`f_locals` 就是当前名字空间：

```python
import sys

def demo(a, b):
    c = a + b
    frame = sys._getframe()
    print(f"本地名字空间: {frame.f_locals}")
    print(f"调用者: {frame.f_back.f_code.co_name}")
    print(f"栈深度: {frame.f_lineno}")
    return c

x = 10; y = 20
demo(x, y)
# 本地名字空间: {'a': 10, 'b': 20, 'c': 30, 'frame': <frame ...>}
# 调用者: <module>
```

`f_locals` 是一个真实的 dict，键是名字（str），值是对象引用。函数内每一次赋值，本质上都是对这个 dict 的写操作。

#### LEGB 查找演示

上面用表格介绍了 LEGB 四层，这里用嵌套函数展示逐层查找：

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        print(x)          # "local" — L 层命中
    inner()
    print(x)              # "enclosing" — L 层无(内层函数的L不在此), E 层命中

outer()
print(x)                  # "global" — L/E 层皆无, G 层命中
```

如果删去 `inner` 中的 `x = "local"`，`print(x)` 会找到 E 层的 `"enclosing"`；如果连同 `outer` 中的也删去，则找到 G 层的 `"global"`。注意 LEGB 查找与 §3.2 的属性查找（`__dict__ → MRO`）逻辑同构——都是"从近到远逐层查 dict"。

#### 闭包——E 层如何跨越栈帧存活

按理说，`outer()` 返回后其栈帧应该销毁，`enclosing` 层的变量应该消失。但闭包推翻了这个预期：

```python
def make_counter():
    count = 0               # Enclosing 变量
    def increment():
        nonlocal count
        count += 1           # 跨栈帧修改 E 层变量
        return count
    return increment         # 返回闭包函数

counter = make_counter()     # make_counter 栈帧已销毁
print(counter())             # 1 — count 仍然活着
print(counter())             # 2
```

闭包之所以能工作，是因为 Python 将 E 层变量存入 **Cell 对象**（`PyCellObject`），而非直接存在栈帧的 `f_locals` 中。Cell 对象是独立于栈帧的堆上对象，闭包函数持有它的引用——栈帧销毁时 Cell 不销毁，enclosing 变量就跨越了栈帧的生命周期。

```python
print(counter.__closure__)    # (<cell at 0x...: int object at 0x...>,)
print(counter.__closure__[0].cell_contents)  # 2 — Cell 中保存的值
```

`__closure__` 是闭包函数持有的 Cell 元组，每个 Cell 包装一个被捕获的 enclosing 变量。这是 Python 对象模型解决"函数栈帧生命周期 < 闭包生命周期"矛盾的方案——**将变量的存储从栈帧剥离到堆上的 Cell 对象，用引用计数管理其生死**。

#### 名字空间是对象生命周期的枢纽约束

现在可以将对象绑定/解绑的完整图景补全：

```
全局层:   模块 __dict__  ← 进程生命周期, 对象随进程存活
函数层:   栈帧 f_locals  ← 调用生命周期, 函数返回即 DECREF
闭包层:   Cell 对象      ← 闭包函数的生命周期, 栈帧销毁后仍存活
容器层:   list/dict 等   ← 容器对象的生命周期, 持有即存活
```

对象何时被 DECREF，取决于它被**哪一层名字空间**持有。同一个对象可以同时出现在多个层——全局 dict 有它、函数参数有它、列表容器有它——`ob_refcnt` 是所有层引用的总和，只有全部释放，对象才会析构。

---

## 三、使用——类型查询与属性查找

### 3.1 type() 统一了什么

在 Java 中，`int.getClass()` 编译不过——原始类型没有类。在 Python 中：

```python
print(type(42))        # <class 'int'>
print(type("hello"))   # <class 'str'>
print(type(len))       # <class 'builtin_function_or_method'>
print(type(int))       # <class 'type'>
print(type(type))      # <class 'type'>
```

一切有效，无需特判。因为每个 `PyObject` 的 `ob_type` 都指向某个 `PyTypeObject`，`type()` 只需解引用这个指针。**统一的类型查询能力，是 Python 鸭子类型和反射的基础设施**——你可以对任意对象调用 `type()`, `isinstance()`, `dir()`，而不必关心它是内置的还是用户定义的。

### 3.2 属性查找——二级检索 + MRO 上溯

当你写 `obj.attr`，Python 的查找顺序是：

```
1. obj.__dict__           ← 实例字典
2. type(obj).__dict__     ← 类型字典
3. MRO 上溯各基类 __dict__ ← 继承链
4. 找不到 → AttributeError
```

**实验 7：观测二级查找**

```python
class A:
    x = 10           # 类属性，存于 type(a).__dict__

a = A()
print(a.x)                       # 10 — 从 type(a).__dict__ 找到
print(a.__dict__)                 # {} — 实例字典为空
print("x" in type(a).__dict__)   # True

a.x = 20                         # 在实例字典中新建条目（遮蔽类属性）
print(a.__dict__)                 # {'x': 20}
print(a.x)                        # 20 — 实例字典优先
print(A.x)                        # 10 — 类属性不受影响
```

`a.x = 20` 并没有修改 `A.__dict__` 中的 `x`，而是在 `a.__dict__` 中新增了条目，遮蔽了类属性——这是 Python 属性查找的**实例优先**规则。删除实例属性后，类属性重新可见：

```python
del a.x
print(a.x)   # 10 — 回退到类属性
```

**实验 8：MRO 链与 issubclass**

```python
class B(A):
    y = 20

b = B()
print(b.y)                # 20 — B.__dict__
print(b.x)                # 10 — A.__dict__ (MRO 上溯)
print(B.__mro__)          # (B, A, object)
print(isinstance(b, A))   # True — 遍历 MRO 检查
print(issubclass(B, A))   # True
```

`isinstance()` 和 `issubclass()` 的实现就是沿 MRO 链做 O(n) 遍历。`__mro__` 元组在类创建时由 C3 线性化算法计算，此后缓存不变——动态改继承不会更新已有类的 MRO。

### 3.3 边界——查找失败的传播

当属性查找穿透整条 MRO 链仍未命中时，Python 不会静默返回 `None`，而是抛出 `AttributeError`——这是对象模型在**实例层**的控制权交接点，与元类在类型层的拦截形成对偶。

```python
a = A()
a.nonexistent  # AttributeError: 'A' object has no attribute 'nonexistent'
```

但 `__getattr__` 可以拦截这个异常，在查找失败后提供兜底——这本质上是把"边界"变成"钩子"：

```python
class Safe:
    def __getattr__(self, name):
        return f"<missing: {name}>"

s = Safe()
print(s.anything)  # "<missing: anything>"
```

---

## 四、消亡——引用计数与析构

### 4.1 ob_refcnt 主导生死

`PyObject` 没有 GC 线程定期扫描。它用最朴素的机制管理内存：**引用计数**。每次绑定 +1（INCREF），每次解绑 -1（DECREF），归零即死。

**实验 9：追踪引用计数的完整变化**

```python
import sys

a = [1, 2]                          # 新对象, refcnt = 1
print(sys.getrefcount(a))            # 2 (a + 临时参数)

b = a                                # INCREF, refcnt = 2 (a + b)
print(sys.getrefcount(a))            # 3

c = a                                # INCREF, refcnt = 3 (a + b + c)
print(sys.getrefcount(a))            # 4

del b                                # DECREF, refcnt = 2 (a + c)
print(sys.getrefcount(a))            # 3

c = None                             # DECREF, refcnt = 1 (仅 a)
print(sys.getrefcount(a))            # 2
```

> 注意：`sys.getrefcount()` 返回值比你预期多 1，因为函数调用本身把对象作为参数又产生了一个临时引用。

### 4.2 归零之后——tp_dealloc

当 `ob_refcnt` 降为 0，CPython 立即调用 `tp_dealloc`——这是类型对象上的析构槽位，Python 层面对应 `__del__` 方法。

**实验 10：观测对象析构时机**

```python
class Tracker:
    def __init__(self, name):
        self.name = name
        print(f"[创建] {self.name}, id={id(self)}")

    def __del__(self):
        print(f"[析构] {self.name}, 资源释放")

a = Tracker("A")   # [创建] A, id=140...
b = a               # INCREF
del a               # DECREF, 但 ob_refcnt > 0
print("a 已删除，但对象还活着")
del b               # DECREF → ob_refcnt = 0 → __del__
print("对象已析构")

# 输出:
# [创建] A, id=140...
# a 已删除，但对象还活着
# [析构] A, 资源释放
# 对象已析构
```

`del a` 删除的是名字绑定（名字空间中移除 `'a'`），不是删除对象。对象只有在引用计数归零时才销毁——**`del` 是解绑，不是析构**。

### 4.3 循环引用——引用计数的失效区

引用计数管不了循环引用。两个对象互相引用，各自的 `ob_refcnt` 永远不为 0，却可能已无外部可达——这是引用计数的**失效区**，由分代 GC 补救。

```python
import gc

class Node:
    def __init__(self, name):
        self.name = name
        self.partner = None

gc.disable()                    # 关闭GC，孤立引用计数行为

a = Node("A")
b = Node("B")
a.partner = b                   # A→B
b.partner = a                   # B→A, 循环形成

del a; del b                    # 删除外部引用, 但 A↔B 互相引用, refcnt 不归零
print(f"垃圾对象数: {len(gc.garbage)}")  # 取决于GC是否回收

gc.enable()
collected = gc.collect()        # 强制分代GC
print(f"回收对象数: {collected}")
```

分代 GC 从根集（全局变量、调用栈等）出发做可达性分析，不可达的循环引用会被回收。这是 Python 内存管理的**双轨制**：引用计数处理常规情况（即时、高效），分代 GC 兜底处理循环引用（延迟、批量）。

### 4.4 强引用与弱引用——引用的两种强度

到目前为止，我们讨论的所有引用——赋值、传参、容器持有——都是**强引用**（strong reference）。强引用使 `ob_refcnt` 增加，直接决定对象存活。但 Python 对象模型还提供了第二种引用强度：**弱引用**（weak reference），它不增加 `ob_refcnt`，对象依然可以归零析构。

这不是一个边缘特性，而是对象模型在"引用计数失效区"的**结构性补丁**——弱引用既是对循环引用问题的预防性设计，也是缓存/观察者模式的基础设施。

#### 强引用 vs 弱引用的机制对比

```
强引用 (赋值/容器/传参):
  b = a                   → ob_refcnt += 1
  del b                   → ob_refcnt -= 1
  对象在 refcnt > 0 期间保证存活

弱引用 (weakref):
  import weakref
  r = weakref.ref(a)      → ob_refcnt 不变!
  r()                     → 返回 a (若存活) 或 None (若已析构)
  对象随时可能析构, 弱引用自动失效
```

**实验 11：弱引用不阻止对象析构**

```python
import weakref

class Data:
    def __init__(self, name):
        self.name = name
    def __del__(self):
        print(f"[析构] {self.name}")

obj = Data("cache")
ref = weakref.ref(obj)           # 创建弱引用, refcnt 不变

print(ref())                      # <Data object> — 对象仍活着
del obj                           # refcnt 归零 → 析构
print(ref())                      # None — 弱引用自动失效
```

#### 弱引用的实现原理

弱引用如何在不增加 `ob_refcnt` 的前提下知道对象是否存活？CPython 在 `PyTypeObject` 中维护了一个**弱引用链表**（`tp_weaklistoffset` 指向的位置）。每个对象创建时，该链表为空；每次创建弱引用，就在链表中插入一个 `PyWeakReference` 节点；对象析构时（`tp_dealloc` 中），遍历该链表将所有弱引用标记为失效。

```
对象存活时:
  PyObject ──tp_weaklist──→ [weakref1] → [weakref2] → NULL
                              ↓            ↓
                           ref1()=obj   ref2()=obj

对象析构后:
  PyObject 已释放
  [weakref1].callback = None   [weakref2].callback = None
  ref1() → None                ref2() → None
```

这也解释了为什么并非所有类型都支持弱引用——只有 `tp_weaklistoffset` 不为 0 的类型才能创建弱引用。`int`、`str`、`tuple` 等内置不可变类型不支持弱引用（`tp_weaklistoffset = 0`），因为它们的实例通常是小整数池/驻留字符串等共享对象，弱引用的失效时机无法与对象的实际生命周期对齐。

```python
import weakref

print(weakref.ref(42))      # TypeError: cannot create weak reference to 'int' object
print(weakref.ref("hello")) # TypeError: cannot create weak reference to 'str' object

print(weakref.ref([1, 2]))  # <weakref at 0x...; to 'list' at 0x...>  — list 支持
```

#### weakref 与循环依赖——预防性设计

4.3 节展示了分代 GC 回收循环引用的**事后补救**。但弱引用提供了一条**事前预防**的路径：用弱引用代替强引用构建双向关系，从根源上消除循环。

```python
import weakref

class Parent:
    def __init__(self):
        self.children = []              # 强引用: 持有子对象

    def add_child(self, child):
        self.children.append(child)
        child._parent_ref = weakref.ref(self)  # 弱引用: 子→父不构成循环

class Child:
    def __init__(self):
        self._parent_ref = None         # 弱引用存储

    @property
    def parent(self):
        ref = self._parent_ref
        return ref() if ref else None   # 通过弱引用访问父对象

p = Parent()
c = Child()
p.add_child(c)

print(c.parent)                        # <Parent object> — 通过弱引用仍可访问
del p                                   # Parent 析构成功! 无循环阻止
print(c.parent)                        # None — 弱引用自动失效
```

Parent → Child 是强引用（`children` 列表），Child → Parent 是弱引用（`_parent_ref`）。这条链**不构成循环**——当外部对 `Parent` 的最后一个强引用消失，`Parent` 的 `ob_refcnt` 归零，正常析构；`Child` 持有的弱引用自动失效。

这是 Python 对象模型处理"双向关系"的标准设计模式：

```
强引用方向:  Parent ──children──→ Child    (拥有关系, 决定生命周期)
弱引用方向:  Child ──parent_ref──→ Parent  (访问关系, 不决定生命周期)

vs. 全强引用(循环):
  Parent ──children──→ Child
  Child ──parent─────→ Parent     ← 循环! 需 GC 兜底回收
```

**常见的弱引用应用场景**：

| 场景 | 说明 | 弱引用类型 |
|:---|:---|:---|
| 缓存 | `functools.lru_cache` 如果强引用缓存值会阻止缓存对象释放 | `weakref.WeakKeyDictionary` |
| 观察者模式 | 主题持有观察者的弱引用，观察者销毁后自动移除 | `weakref.WeakSet` |
| 父子关系 | 子对象弱引用父对象，避免循环引用 | `weakref.ref` |
| 循环引用预防 | 双向关系中，非拥有方用弱引用 | `weakref.ref` / `WeakKeyDictionary` |

弱引用是对象模型从"只有强引用"进化到"引用分级"的设计决策。它不是 GC 的替代品（GC 仍然兜底全强引用的循环），而是在**设计层面**消除了许多本不该存在的循环——让引用计数的"失效区"在源头被压缩。

---

## 五、全生命周期总览

将上述环节串联，一个对象的完整生命周期如下：

```
创建:  type.__call__ → 分配内存 → 初始化 PyObject 头部 (ob_refcnt=1, ob_type=...)
   ↓                        ↓
   │                   PyVarObject: +ob_size (定长对象无此字段)
   │                   内联数据 vs 间接指针 → 决定可变/不可变
   ↓
绑定:  赋值/传参 → 名字空间写入
       ┌─ 强引用: INCREF → ob_refcnt += 1 → 持有对象存活
       │   ├─ 全局层: 模块 __dict__ (进程生命周期)
       │   ├─ 函数层: 栈帧 f_locals (调用生命周期, 返回即 DECREF)
       │   ├─ 闭包层: Cell 对象 (闭包函数生命周期, 跨栈帧存活)
       │   └─ 容器层: list/dict 等 (容器对象生命周期)
       └─ 弱引用: 不 INCREF → 不决定对象存活 → 对象析构时自动失效
           用途: 缓存/观察者/父子关系(防循环引用)
   ↓
使用:  type(obj) 解引用 ob_type
       obj.attr  → __dict__ → MRO 上溯
       a == b    → __eq__ 值比较
       a is b    → id() 身份比较
       可变对象: 开放写槽位(sq_ass_item) → 原地修改 → 所有引用可见
       不可变对象: 写槽位 NULL → "修改"即新建 → 旧引用不受影响
         根因: 内联数据无法原地扩展/切换编码 (str/tuple/bytes/int)
   ↓
解绑:  函数返回(栈帧销毁) / del / 重新赋值 → DECREF (强引用)
       弱引用: 对象析构时遍历 tp_weaklist 标记失效
   ↓
析构:  ob_refcnt == 0 → tp_dealloc / __del__ → 释放内存
       ┌─ 正常路径: 引用计数即时回收
       └─ 失效区: 循环引用 (互相强引用, refcnt 不归零)
           ├─ 事前预防: 弱引用替代非拥有方强引用 → 消除循环
           └─ 事后补救: 分代 GC 可达性分析 → 批量回收
```

每个环节的机制都回溯到 `PyObject` 的两个头部字段——`ob_type` 决定对象是什么（类型查询、属性查找、可调用判断、可变/不可变的写权限、是否支持弱引用），`ob_refcnt` 决定对象是否还活着（绑定/解绑/析构，强引用增加、弱引用不增加）。名字空间是两者交汇的枢纽：`ob_type` 中的 `tp_hash`/`sq_ass_item`/`tp_weaklistoffset` 等槽位决定了对象能否作为 dict key、能否原地修改、能否被弱引用；而 `ob_refcnt` 追踪的正是各个名字空间层和容器对对象的强引用持有数。这就是"一切皆对象"的工程实质：**一个 16 字节的头部契约，统一了 Python 世界的数据总线**。

---

## 六、常见陷阱

### 陷阱 1：用 is 代替 == 做值比较

```python
a = 500; b = 500
if a is b:            # 错误！应为 a == b
    print("相等")
# 不会执行，因为 500 不在小整数池中
```

**原因**：`is` 比较对象身份（`id()` 地址），`==` 比较值（`__eq__`）。小整数池让 `256 is 256` 为 True 掩盖了问题，但超出缓存范围立即暴露。

**避免**：仅当确需判断"是否同一对象"时用 `is`（如 `if x is None`），其余一律用 `==`。

### 陷阱 2：函数内修改可变参数影响调用者

```python
def add_item(item, cache=[]):   # 危险！默认值是同一 list 对象
    cache.append(item)
    return cache

print(add_item("a"))   # ['a']
print(add_item("b"))   # ['a', 'b'] — 上次调用的影响残留
```

**原因**：默认参数在函数定义时求值一次，`cache` 绑定到同一个 list 对象。每次调用不新建 list，而是复用同一 `PyObject`。

**避免**：用 `None` 作为哨兵，函数体内创建新对象：

```python
def add_item(item, cache=None):
    if cache is None:
        cache = []
    cache.append(item)
    return cache
```

### 陷阱 3：混淆 del 与析构

```python
a = [1, 2, 3]
b = a
del a          # 以为 list 被销毁了
print(b)       # [1, 2, 3] — 对象还在，b 仍持有引用
```

**原因**：`del` 删除名字绑定（DECREF），不等于销毁对象。只有 `ob_refcnt` 归零才触发析构。

**避免**：如果需要确保资源释放，使用 `with` 语句和上下文管理器（`__enter__`/`__exit__`），不要依赖 `__del__`。

---

## 七、自测题目

**题目 1**：以下代码输出什么？解释原因。

```python
a = 1000
b = 1000
print(a is b)

def f():
    x = 1000
    y = 1000
    print(x is y)

f()
```

**题目 2**：以下代码中 `sys.getrefcount(obj)` 返回值是多少？列出所有持有引用的来源。

```python
import sys
obj = [1]
alias = obj
container = [obj]
print(sys.getrefcount(obj))
```

**题目 3**：`type(int)` 和 `type(42)` 分别返回什么？画出 `42` 的 `ob_type` 指向链，说明为什么这条链会在 `type` 处终止。

---

<details>
<summary>参考答案</summary>

**题目 1**：交互模式下 `a is b` 通常为 `False`（超出小整数池）。但函数 `f` 内 `x is y` **可能**为 `True`——CPython 在同一代码块内对不可变字面量做常量折叠（intern），`x` 和 `y` 可能指向同一对象。这进一步说明 `is` 的结果依赖实现优化，不应用于值比较。

**题目 2**：返回 `4`。引用来源：`obj`（1）+ `alias`（共享同一对象，也算1，但 getrefcount 计的是对象上的引用总数而非名字数）+ `container[0]`（1）+ `getrefcount(obj)` 的临时参数（1）= 4。注意 `obj` 和 `alias` 名字虽多，但都指向同一个 list，`ob_refcnt` 记录的是指向该对象的引用总数。

**题目 3**：`type(int)` → `<class 'type'>`，`type(42)` → `<class 'int'>`。`42` 的 `ob_type` → `int` 的 `ob_type` → `type` 的 `ob_type` → `type`（自指闭合）。链在 `type` 处终止，因为 `type` 是自身元类，`type.__class__ is type`——这是元循环闭合点，避免无限回归。

</details>

---

## 八、对象模型的解释力——22个表象疑惑的统一回溯

理解对象模型的最大收益，不是记住几个字段名，而是获得一个**统一的解释框架**：表面上千差万别的 Python 行为，回溯到 `PyObject` 的两个头部字段 + `PyTypeObject` 的槽位 + 名字空间的绑定/解绑，就不再是散落的知识点，而是同一个根上长出的枝叶。

下表汇总了本文已经覆盖的和未展开的常见疑惑，统一标注其对象模型根因：

| # | 表象疑惑 | 对象模型根因 | 本文章节 |
|:--|:---|:---|:---|
| 1 | 为什么赋值不产生拷贝？ | 赋值 = 名字绑定 + INCREF，`PyObject` 层面没有拷贝逻辑 | §2.2 |
| 2 | 为什么 `is` 和 `==` 结果不同？ | `is` = `id()` 指针比较，`==` = `__eq__` 值比较，分属对象身份与对象值 | §2.2 |
| 3 | 为什么 `256 is 256` 为 True 而 `500 is 500` 不一定？ | 小整数池缓存了 [-5, 256] 的 `PyObject`，`is` 比较的是对象地址 | §2.2 |
| 4 | 为什么 `a = []; b = a; b.append(1)` 后 `a` 也变了？ | `a`/`b` 指向同一 `PyObject`，list 的 `sq_ass_item` 开放原地修改 | §2.3 |
| 5 | 为什么 dict 的 key 不能是 list？ | list 可变 → `tp_hash = _PyObject_HashNotImplemented` → `TypeError` | §2.3 |
| 6 | 为什么 `str` 不可修改？ | PEP 393 数据内联在结构体尾部，长度/编码无法原地改变 | §1.1 |
| 7 | 为什么 `tuple` 不可变却能做 dict key？ | 不可变 → `tp_hash` 实现了哈希函数 → 可以做 key | §2.3 |
| 8 | 为什么 `sys.getsizeof([1])` 不含 `1` 的内存？ | list 数据区存指针（8B），int 是独立 `PyObject`，`getsizeof` 只计自身 | §1.1 |
| 9 | 为什么 `type(type)` 是 `type`？ | 元循环闭合：`type.ob_type` 指向自身，避免无限回归 | §1.2 |
| 10 | 为什么装饰器能装饰任何可调用对象？ | `callable()` 检查 `tp_call` 槽位，函数/类/自定义对象统一 | 引言 |
| 11 | 为什么 `len()` 是内置函数而非方法？ | `len(obj)` 调用 `obj.__len__()`——通过 `ob_type` 统一分派，保证协议一致性 | 引言 |
| 12 | 为什么函数返回后局部变量消失？ | 栈帧销毁 → `f_locals` 中所有名字 DECREF → 引用计数归零 | §2.4 |
| 13 | 为什么闭包变量能跨越函数调用存活？ | E 层变量存入 Cell 对象（堆上），独立于栈帧，引用计数管理 | §2.4 |
| 14 | 为什么 `del` 不等于析构？ | `del` = 名字解绑 + DECREF，对象析构由 `ob_refcnt == 0` 触发 | §4.2 |
| 15 | 为什么循环引用不会被引用计数回收？ | 循环引用中各方 `ob_refcnt` 永远不为零，需分代 GC 可达性分析兜底 | §4.3 |
| 16 | 为什么弱引用不阻止对象析构？ | 弱引用不增加 `ob_refcnt`，对象析构时遍历弱引用链表标记失效 | §4.4 |
| 17 | 为什么 `int`/`str` 不支持弱引用？ | `tp_weaklistoffset = 0`，小整数池/驻留字符串的过期时机无法与弱引用对齐 | §4.4 |
| 18 | 为什么 Python 是动态类型？ | 变量只是名字标签，类型信息在对象的 `ob_type` 上，不在变量上 | 引言 |
| 19 | 为什么 Python 是强类型？ | 操作在 `PyTypeObject` 槽位严格匹配，不做隐式跨类型转换 | 引言 |
| 20 | 为什么 `True + 1 == 2`？ | `bool` 继承自 `int`，`True` 的值为 1——`ob_type` 指向 `int` 的子类 | §1.1 |
| 21 | 为什么 `None` 只有 16 字节？ | `None` 是 `PyObject` 裸实例，无有效载荷（无 ob_digit、无 ob_item） | §1.1 |
| 22 | 为什么 `__slots__` 能节省内存？ | 禁用 `__dict__`，属性存入预定义的偏移量槽位，省去 dict 开销 | §3.2 |
| 23 | 为什么浅拷贝后修改子列表会影响原列表？ | 浅拷贝只复制容器骨架（新 PyObject），内部指针照搬原对象，可变元素仍共享 | §2.3 |
| 24 | 为什么深拷贝对不可变对象不创建副本？ | 不可变对象的 `sq_ass_item` 等写槽位为 NULL，共享即安全，复制只是浪费 | §2.3 |
| 25 | 为什么不同类型的对象能用于同一个函数？ | 鸭子类型：操作走 `ob_type` 槽位分派，有槽位即有能力，与类型名无关 | §3.4 |
| 26 | 为什么 Python 内置操作（for/len/+）不查 isinstance？ | 内置操作直接查 C 层槽位（tp_iter/sq_length/nb_add），是极致的鸭子类型 | §3.4 |
| 27 | 为什么同名的 `draw()` 方法可能语义不同？ | 鸽子洞问题：鸭子类型只查方法名是否存在，无法区分语义，靠命名约定缓解 | §3.4 |

每一个疑惑都不是独立的知识点——它们的答案都回溯到 `PyObject` 的 `ob_refcnt`（生死）和 `ob_type`（身份与能力）两个字段，以及 `PyTypeObject` 的槽位矩阵和名字空间的绑定/解绑机制。对象模型就是 Python 的元语言：**理解它，其他一切是从它推出的定理，而非需要分别记忆的公理**。
