### 3.4 设计闭环:可变性选择的连锁反应

```
不可变对象可哈希 → 可用作字典键 → 字典键稳定性 → 
字典实现简化 → hash/eq方法协议 → ...

不可变对象不可修改 → 字符串拼接低效 → StringIO补偿 → 
字符串常量折叠优化 → 编译期优化机会 → ...

可变对象共享 → 副作用难以追踪 → 防御性拷贝文化 → 
copy/deepcopy协议 → 内存开销增加 → ...

可变对象并发不安全 → 需要加锁 → GIL简化锁管理 → 
GIL限制多线程性能 → multiprocessing补偿 → ... (见第六节)
```

---

## 四、容器设计:从实现到接口的哲学

> **Article 03核心回顾**:列表基于动态数组,字典基于哈希表,集合基于字典.ValuesView而非列表等实现细节体现性能考量.

### 4.1 列表:list的动态数组实现

#### 设计冲突:随机访问效率vs插入删除效率

**数据结构权衡**:
- **数组(Array)**:O(1)随机访问,O(n)插入删除
- **链表(Linked List)**:O(n)随机访问,O(1)插入删除(已知位置)

**约束**:
- Python主要场景是遍历和索引访问
- 内存局部性影响性能(数组缓存友好)
- C实现简单性

**选择**:动态数组(Dynamic Array/Resize Array)

```c
/* Objects/listobject.c */
typedef struct {
    PyObject_VAR_HEAD
    PyObject **ob_item;     /* 元素指针数组 */
    Py_ssize_t allocated;   /* 已分配容量 >= ob_size */
} PyListObject;

/* 容量增长策略 */
static int list_resize(PyListObject *self, Py_ssize_t newsize) {
    Py_ssize_t new_allocated;
    size_t num_allocated_bytes;
    
    /* 增长策略:new_allocated = newsize + (newsize >> 3) + (newsize < 9 ? 3 : 6) */
    /* 约1.125倍增长,平衡扩容频率和内存浪费 */
    new_allocated = (size_t)newsize + (newsize >> 3) + (newsize < 9 ? 3 : 6);
    
    num_allocated_bytes = new_allocated * sizeof(PyObject *);
    self->ob_item = (PyObject **)PyMem_Realloc(self->ob_item, num_allocated_bytes);
    self->allocated = new_allocated;
    return 0;
}
```

**增长策略分析**:
```python
# 列表容量增长实测
import sys

l = []
capacities = []
for i in range(64):
    l.append(i)
    capacities.append(sys.getsizeof(l))

# 容量序列:56, 64, 72, 88, 104, 120, 152, 184, ...
# 增长比例:≈1.125x
```

**摊销复杂度证明**:
```
假设容量增长序列:1, k, k^2, k^3, ...
总扩容成本:1 + k + k^2 + k^3 + ... + k^log_k(n) = O(k * n)
n次append总成本:O(n)插入 + O(k*n)扩容 = O(n)  (k是常数)
单次append摊销成本:O(n)/n = O(1)
```

**代价**:
1. **内存浪费**:容量可能远大于实际长度
```python
l = [1] * 1000
l.clear()
print(sys.getsizeof(l))  # 仍保留1000的容量
```

2. **插入删除代价**:中间位置插入需要移动后续所有元素
```python
l = list(range(100000))
# 头部插入:O(n)
l.insert(0, -1)  # 移动10万个元素
# 尾部插入:O(1)摊销
l.append(100000)
```

**补偿**:
1. **collections.deque**:双端队列,两端插入删除都是O(1)
```python
from collections import deque

d = deque(range(100000))
d.appendleft(-1)  # O(1)
d.append(100000)  # O(1)
```

2. **列表推导优化**:创建列表比循环append快
```python
# 慢:循环append
l = []
for i in range(10000):
    l.append(i * i)

# 快:列表推导
l = [i * i for i in range(10000)]
```

#### 列表AC即Append Complexity设计闭环

```
动态数组 → 尾部追加O(1)摊销 → 头部插入O(n) → deque补偿 → 
deque随机访问O(n) → 数据结构选择取决于用例 → ...
```

### 4.2 字典演进:从混乱到有序

> **Article 03详细讨论**了字典的内部实现,这里关注演进历史和设计决策.

#### Python 2.7及之前:无序字典

**实现**:纯哈希表,迭代顺序取决于哈希值和碰撞处理

```python
# Python 2.7
d = {'a': 1, 'b': 2, 'c': 3}
print(d.keys())  # 顺序不确定,可能['a', 'c', 'b']
```

**问题**:
1. **不确定性**:同一字典不同运行顺序可能不同(哈希随机化)
2. **测试困难**:字典相等但顺序不同导致测试失败
3. **序列化不稳定**:JSON序列化结果每次可能不同

**冲突**:字典的映射语义vs实现的迭代顺序暴露

**约束**:哈希表迭代顺序天然无序,强行排序增加开销

#### Python 3.6(实现细节):紧凑字典

**动机**:内存消耗和迭代性能优化

**设计**:分离键数组和值数组,

```c
/* Python 3.6内部的字典结构(简化) */
typedef struct {
    Py_ssize_t dk_size;        /* 哈希表大小 */
    Py_ssize_t dk_nentries;    /* 已用条目数 */
    char *dk_indices;          /* 索凑的索引数组 */
    PyDictKeyEntry *dk_entries;/* 键值对数组,插入顺序 */
} PyDictKeysObject;

/* 主要优势:
 * 1. 内存节省:只存实际键值对,稀疏部分只存索引
 * 2. 插入顺序遍历:遍历dk_entries即是插入顺序
 */
```

**内存对比**:
```python
# Python 2.7
# 字典每个条目:24字节(键指针+值指针+哈希值),即使空槽

# Python 3.6+
# 稀疏索引数组:1字节(小字典)或更多
# 密集键值对数组:24字节,仅实际条目
# 总体内存节省约20-50%
```

**Python 3.6行为**:实现有序,但语言规范未保证
```python
d = {}
d['a'] = 1
d['b'] = 2
d['c'] = 3
print(list(d))  # Python 3.6: ['a', 'b', 'c'] (实现细节)
```

#### Python 3.7+(PEP 509, 语言保证):有序字典

**决策**:将插入顺序保证写入语言规范

**冲突**:实现细节vs语言规范,未来实现可能改变

**约束**:社区广泛依赖3.6的有序行为,不保证会破坏代码

**选择**:Python 3.7将有序性提升为语言特性

**Python文档**:
> Dictionaries preserve insertion order as of Python 3.7. Updating a key does not affect the order. Keys added after deletion are inserted at the end.

**代价**:
1. **实现锁定**:未来优化必须保持有序性约束
2. **概念混淆**:字典是映射还是有序映射?

**补偿**:无序字典仍可通过其他方式实现
```python
# 如果真的需要无序字典
d = {'a': 1, 'b': 2, 'c': 3}
import random
items = list(d.items())
random.shuffle(items)
unordered_d = dict(items)
```

#### 字典设计的连锁反应

```
字典无序 → JSON序列化不稳定 → orjson等库提供排序选项 → 
有序字典成为规范 → 实现锁定 → 优化空间收窄 → ...

字典有序 → 替代OrderedDict? → defaultdict是否有序? → 
所有字典变体统一行为 → API设计简化 → ...
```

### 4.3 迭代器协议:惰性求值与内存效率

> **Article 06关联**:迭代器是生成器的基石,理解迭代协议是理解协程的前提.

#### 迭代器设计冲突

**场景**:遍历大数据集,内存不足以一次性加载

```python
# 传统方式:一次性创建列表
def squares(n):
    result = []
    for i in range(n):
        result.append(i * i)
    return result

# 问题:n=10^8时,内存消耗约800MB(每个整数28字节)

# 迭代器方式:惰性生成
def squares_iter(n):
    for i in range(n):
        yield i * i

# 优势:常量内存消耗(仅当前值)
```

**冲突**:便利性(列表,可重复遍历)vs效率(迭代器,一次性)

**约束**:
- 需要统一的遍历接口
- 与for循环兼容
- 支持无限序列

**选择**:迭代器协议(Iterator Protocol)

```python
# 迭代器协议
class MyIterator:
    def __iter__(self):
        return self
    
    def __next__(self):
        """返回下一个值,或抛出StopIteration"""
        if self.exhausted:
            raise StopIteration
        return self.next_value()

# iter()和next()函数
my_iter = MyIterator()
it = iter(my_iter)  # 调用__iter__
value = next(it)    # 调用__next__
```

**for循环的迭代器展开**:

```python
# for循环源码
for item in iterable:
    process(item)

# 翻译为迭代器协议
_iter = iter(iterable)
while True:
    try:
        item = next(_iter)
    except StopIteration:
        break
    process(item)
```

**代价**:
1. **一次性消费**:迭代器耗尽后无法重置
```python
it = squares_iter(10)
print(list(it))  # [0, 1, 4, 9, ...]
print(list(it))  # []  已耗尽!
```

2. **无长度信息**:迭代器可能无限,无法预知长度
```python
# len()不可用
it = squares_iter(1000000)
# len(it)  # TypeError
```

**补偿**:
1. **itertools.tee**:克隆迭代器(需缓存已消费值)
```python
from itertools import tee

it = squares_iter(10)
it1, it2 = tee(it)  # 克隆为两个迭代器
print(list(it1))    # [0, 1, 4, ...]
print(list(it2))    # [0, 1, 4, ...]
```

2. **列表缓存**:需要多次遍历时收集为列表
```python
it = squares_iter(10)
lst = list(it)  # 缓存到列表
# 可多次遍历lst
```

#### 内置类型的迭代器实现

**列表迭代器**:
```c
/* Objects/listobject.c */
typedef struct {
    PyObject_HEAD
    PyListObject *li;
    Py_ssize_t it_index;
} listiterobject;

static PyObject *listiter_next(listiterobject *it) {
    PyListObject *seq = it->li;
    Py_ssize_t i = it->it_index;
    if (i < PyList_GET_SIZE(seq)) {
        PyObject *item = PyList_GET_ITEM(seq, i);
        it->it_index = i + 1;
        Py_INCREF(item);
        return item;
    }
    return NULL;  /* StopIteration */
}
```

**字典迭代器**:遍历键数组(dk_entries)

```python
d = {'a': 1, 'b': 2}

# 默认遍历键
for key in d:
    print(key)  # 'a', 'b'

# 显式遍历键、值、键值对
for key in d.keys():
    print(key)
for value in d.values():
    print(value)
for key, value in d.items():
    print(key, value)
```

**字典视图(views)**:动态反映字典变化

```python
d = {'a': 1, 'b': 2}
keys_view = d.keys()

d['c'] = 3
print(list(keys_view))  # ['a', 'b', 'c'] 视图动态更新!
```

### 4.4 容器设计闭环总结

```
列表动态数组 → 随机访问O(1) → 中间插入O(n) → deque补偿 → 
deque随机访问O(n) → 根据场景选择容器 → 用户认知负担 → 
"只管用,Python已选好"哲学 → ...

字典哈希表 → O(1)查找 → 插入顺序无序 → Python 3.7有序 → 
实现锁定 → 优化空间受限 → ...

迭代器协议 → 惰性求值 → 内存效率 → 一次性消费 → 
tee补偿(内存换灵活性) → 权衡无处不在 → ...
```

---

## 五、作用域闭包:LEGB规则的演进

> **Article 05核心**:Python使用LEGB(Local,Enclosing,Global,Built-in)四层作用域,闭包通过Cell对象实现变量捕获。

### 5.1 LEGB规则:多层命名空间的查找链

#### 冲突:全局命名空间的污染与隔离

**C语言教训**:全局变量污染命名空间
```c
/* C语言:全局命名空间 */
int count;  // 全局变量
float count;  // 错误:重定义

/* 所有函数共享全局变量,易冲突 */
```

**Python的目标**:
- 模块隔离(每个模块独立命名空间)
- 函数隔离(局部变量不影响外部)
- 闭包支持(内函数访问外函数变量)

**LEGB查找顺序**:

```
Local(局部) → Enclosing(闭包外层) → Global(全局) → Built-in(内置)
```

**示例分析**:

```python
# LEGB演示
x = "global"  # Global

def outer():
    x = "enclosing"  # Enclosing
    
    def inner():
        x = "local"  # Local
        print(x)     # Local: "local"
    
    def inner_no_local():
        print(x)     # Enclosing: "enclosing"
    
    inner()
    inner_no_local()

outer()
print(x)  # Global: "global"

# Built-in
print(len)  # <built-in function len>
```

**C实现**(作用域查找):

```c
/* Python/ceval.c:LOAD_NAME操作码 */
TARGET(LOAD_NAME) {
    PyObject *name = GETITEM(names, oparg);
    PyObject *v;
    
    /* 1. Local */
    if (PyDict_CheckExact(f->f_locals)) {
        v = PyDict_GetItem(f->f_locals, name);
        if (v != NULL) {
            Py_INCREF(v);
            PUSH(v);
            DISPATCH;
        }
    }
    
    /* 2. Global */
    v = PyDict_GetItem(f->f_globals, name);
    if (v != NULL) {
        Py_INCREF(v);
        PUSH(v);
        DISPATCH;
    }
    
    /* 3. Built-in */
    v = PyDict_GetItem(f->f_builtins, name);
    if (v != NULL) {
        Py_INCREF(v);
        PUSH(v);
        DISPATCH;
    }
    
    /* 未找到:NameError */
    format_exc_check_arg(PyExc_NameError, NAME_ERROR_MSG, name);
    goto error;
}

/* 注意:Enclosing层在LOAD_DEREF操作码处理(闭包变量) */
```

#### 名字解析的静态分析

**Python的静态作用域(lexical scoping)**:定义时确定,非运行时

```python
def outer():
    x = 10
    def inner():
        return x  # 静态绑定到outer的x
    return inner

# x在outer的命名空间,inner定义时就能确定
```

**与动态作用域对比**(如早期Lisp):

```lisp
;; Emacs Lisp(动态作用域)
(let ((x 10))
  (let ((inner (lambda () x)))  ; x尚未绑定
    (let ((x 20))
      (funcall inner))))  ; 返回20(运行时查找x)
```

**Python**:
```python
x = 10
def inner():
    return x  # 静态绑定到全局x

x = 20
print(inner())  # 20(全局x已更新)

def outer():
    x = 10
    inner = lambda: x  # 静态绑定到outer的x
    x = 20
    return inner()

print(outer())  # 20(outer的x已更新)
```

### 5.2 global/nonlocal:显式声明打破默认规则

#### 冲突:函数内修改全局变量

**默认行为**:函数内赋值创建局部变量

```python
x = 10

def modify():
    x = 20  # 创建局部变量x,不修改全局x

modify()
print(x)  # 10,全局x未变
```

**需求**:有时需要修改全局变量(如计数器、配置)

**约束**:
- 不破坏默认的局部变量保护
- 显式声明优于隐式行为

**选择**:global声明

```python
x = 10

def modify_global():
    global x  # 声明x是全局变量
    x = 20

modify_global()
print(x)  # 20,全局x被修改
```

**字节码验证**:

```python
import dis

def with_global():
    global x
    x = 10

def without_global():
    x = 10

dis.dis(with_global)
# 2  0 LOAD_CONST    0 (10)
#    2 STORE_GLOBAL  0 (x)  ← STORE_GLOBAL操作码

dis.dis(without_global)
# 2  0 LOAD_CONST    0 (10)
#    2 STORE_NAME    0 (x)  ← STORE_NAME(局部)
```

#### nonlocal:修改闭包变量

**Python 2的限制**:只能读取闭包变量,无法修改

```python
# Python 2
def counter():
    count = 0
    def inc():
        count += 1  # UnboundLocalError!
        return count
    return inc
```

**问题分析**:
- `count += 1`展开为`count = count + 1`
- 右边的`count`读取闭包变量
- 左边的`count = ...`创建局部变量
- 由于`count`既是读取又是赋值,Python判定为局部变量
- 局部变量在赋值前读取,触发UnboundLocalError

**Python 3的解决方案**:nonlocal声明

```python
# Python 3
def counter():
    count = 0
    def inc():
        nonlocal count  # 声明count是闭包变量
        count += 1
        return count
    return inc

c = counter()
print(c())  # 1
print(c())  # 2
print(c())  # 3
```

**代价**:global和nonlocal增加认知负担

```python
# 三层嵌套的读写规则
x = "global"

def outer():
    x = "enclosing"
    
    def middle():
        x = "middle local"
        
        def inner():
            global x         # 全局的x
            nonlocal x        # 错误:无法确定是哪一层!
            # 语法错误:nonlocal只能绑定一层enclosing作用域
            pass
```

**正确用法**:

```python
x = "global"

def outer():
    x = "enclosing"
    
    def inner():
        nonlocal x  # 绑定到outer的x
        x = "modified"
    
    inner()
    print(x)  # "modified"

outer()
print(x)  # "global" 未被修改
```

### 5.3 Cell对象:闭包捕获的实现机制

> **Article 05深入讨论**:闭包变量通过Cell对象间接引用,实现多级函数共享同一变量。

#### 闭包变量的存储问题

**问题**:外函数返回后,局部变量应该销毁。但内函数(闭包)还需要访问这些变量。

**案例**:
```python
def outer():
    x = 10
    y = [1, 2, 3]
    
    def inner():
        return x, y  # 引用x和y
    
    return inner

# outer返回后,x和y的栈空间已释放
# 但inner还需要访问x和y!
```

**解决方案**:cell变量存储在堆上,而非栈上

```c
/* Include/cellobject.h */
typedef struct {
    PyObject_HEAD
    PyObject *ob_ref;  /* 指向实际对象 */
} PyCellObject;
```

**实现机制**:

1. 编译期识别闭包变量
2. 将外函数的闭包变量存储为cell对象
3. 内函数通过cell间接访问

**验证**:

```python
def outer():
    x = 10
    def inner():
        return x
    return inner

f = outer()

# 检查闭包
print(f.__closure__)  # (<cell at 0x...: int object at 0x...>,)
print(f.__closure__[0].cell_contents)  # 10

# 修改x(通过nonlocal)
def outer_mod():
    x = 10
    def inner():
        nonlocal x
        x += 1
        return x
    def get():
        return x
    return inner, get

inc, get = outer_mod()
print(get())  # 10
print(inc())  # 11
print(get())  # 11 (共享同一cell)
```

**C实现**(LOAD_DEREF操作码):

```c
/* Python/ceval.c */
TARGET(LOAD_DEREF) {
    PyObject *cell = freevars[oparg];  /* freevars是闭包变量数组 */
    PyObject *value = PyCell_GET(cell);  /* 获取cell内容 */
    if (value == NULL) {
        /* cell未初始化 */
        format_exc_unbound(tstate, co, oparg);
        goto error;
    }
    Py_INCREF(value);
    PUSH(value);
    DISPATCH;
}

TARGET(STORE_DEREF) {
    PyObject *value = POP();
    PyObject *cell = freevars[oparg];
    PyCell_SET(cell, value);  /* 设置cell内容 */
    Py_DECREF(value);
    DISPATCH;
}
```

### 5.4 作用域设计闭环

```
LEGB规则 → 局部变量默认保护 → 函数内无法修改全局 → 
global声明补偿 → global滥用降低代码质量 → 
"尽量避免全局变量"最佳实践 → ...

闭包需要访问外层变量 → 外层变量栈分配效率高 → 
外函数返回后栈失效 → Cell对象堆分配 → 
额外内存开销 → 闭包便利性补偿 → ...

Python 2无法修改闭包变量 → 使用可变对象绕过(list包装) → 
Python 3引入nonlocal → 特性增多 → 学习曲线上升 → 
但解决了实际问题 → ...
```

---

## 六、GIL:全局解释器锁的历史与未来

> **Article 12核心**:GIL是为了简化C扩展开发而引入的,它限制了多线程并行性能,催生了multiprocessing和asyncio等替代方案。

### 6.1 GIL的历史根源:1987-1992的决策

#### 时代背景:单核CPU时代

**1987年Python前身**:ABC语言的开发
**1991年Python 0.9.0发布**:运行在单核CPU系统上
**主流CPU**:Intel 80386, 80486(单核, 25-50 MHz)

**并行编程需求**:几乎没有(单核CPU多线程主要用于IO并发,非计算并行)

#### 技术根源:引用计数的并发问题

**核心冲突**:引用计数的并发修改

```c
/* 引用计数增加 */
#define Py_INCREF(op) ((void)(++(op)->ob_refcnt))

/* 引用计数减少 */
#define Py_DECREF(op) \
    if (--((op)->ob_refcnt) == 0) \
        _Py_Dealloc((PyObject *)(op))
```

**并发问题**:
```c
/* 线程A和线程B同时引用同一对象 */
/* 线程A执行Py_INCREF */
++(op)->ob_refcnt;  /* 假设refcnt=2, ++后=3 */

/* 线程B同时执行Py_INCREF */
++(op)->ob_refcnt;  /* 读取到2(而非3), ++后=3 */

/* 问题:两次INC但refcnt只增加1,最终为3而非4 */
/* 导致对象提前释放,use-after-free崩溃 */
```

#### 解决方案对比

| 方案 | 优点 | 缺点 | 选择 |
|-----|------|------|-----|
| **全局锁(GIL)** | 实现简单,C扩展兼容性好 | 多线程无法并行 | **Python的选择** |
| 原子操作 | 无锁性能高 | 移植性差,旧编译器支持不佳 | 未选择 |
| 细粒度锁 | 并行度高 | 实现复杂,死锁风险,性能开销大 | 未选择(早期尝试失败) |
| RC+GC混合 | 减少锁竞争 | 实现复杂,内存开销大 | 未选择 |

**GIL的实现**:

```c
/* Python 3.8+的GIL实现 */
struct _gil_runtime_runtime {
    /* 降低GIL竞争的机制 */
    volatile int gil_locked;       /* GIL是否被持有 */
    pthread_cond_t gil_cond;       /* 条件变量 */
    pthread_mutex_t gil_mutex;     /* 互斥锁 */
    int gil_drop_request;          /* 请求释放GIL */
    int gil_switch_number;         /* GIL切换次数 */
};

/* 获取GIL */
void PyEval_AcquireGil(void) {
    PyThreadState *tstate = _PyThreadState_Current;
    if (_PyInterpreterState_GetGilState(tstate->interp) == GIL_LOCKED) {
        /* GIL已被当前线程持有,递归获取 */
        return;
    }
    /* 阻塞等待GIL */
    pthread_mutex_lock(&gil_mutex);
    while (gil_locked) {
        pthread_cond_wait(&gil_cond, &gil_mutex);
    }
    gil_locked = 1;
    pthread_mutex_unlock(&gil_mutex);
}

/* 释放GIL */
void PyEval_ReleaseGil(void) {
    pthread_mutex_lock(&gil_mutex);
    gil_locked = 0;
    pthread_cond_signal(&gil_cond);  /* 唤醒等待线程 */
    pthread_mutex_unlock(&gil_mutex);
}
```

### 6.2 为什么不能移除GIL?历史的锁定

> **这是理解Python演进的关键**:早期决策锁定了后期选择的可行域。

#### 后期约束:兼容性重于性能

**约束1:C扩展生态**
- NumPy、Pandas等核心库依赖GIL简化开发
- 移除GIL需要重写所有C扩展
- 生态迁移成本远超Python 2→3

**约束2:单线程性能**
- 早期尝试移除GIL导致单线程性能下降40%
- 单线程场景远多于多线程场景
- 性能权衡:单线程场景更重要

**约束3:实现复杂度**
- 细粒度锁增加了数万行代码
- 死锁风险显著增加
- 维护成本过高

#### 实验历史:失败的尝试

**Greg Stein的自由线程实验(1996-1999)**:
- 移除GIL,实现细粒度锁
- 单线程性能下降40%
- C扩展需要大量修改
- 最终放弃,代码未合并

**结论**:移除GIL的代价(性能下降+兼容性破坏)远大于收益(多线程加速)。

### 6.3 PEP 703(2023):GIL移除的*又一次*尝试

> **历史可能在改变**:2023年PEP 703提议在Python 3.12+的构建选项中移除GIL。

#### PEP 703要点

**标题**:Making the Global Interpreter Lock Optional in CPython

**提议**:
1. 提供`--disable-gil`构建选项
2. 构建两个Python版本:传统GIL版本和无GIL版本
3. 无GIL版本引用计数使用原子操作
4. API兼容:大部分C扩展可以同时支持两种版本

**动机**:硬件趋势变化
- 多核CPU主流(4-64核常见)
- 单核性能增长放缓(摩尔定律放缓)
- 并行计算需求增加(机器学习、科学计算)

**实现技术**:

```c
/* 无GIL版本的引用计数 */
#ifdef Py_GIL_DISABLED
/* 原子引用计数 */
static inline void Py_INCREF(PyObject *op) {
    _Py_atomic_add_int(&op->ob_refcnt, 1);
}

static inline void Py_DECREF(PyObject *op) {
    if (_Py_atomic_sub_int(&op->ob_refcnt, 1) == 1) {
        _Py_Dealloc(op);
    }
}
#else
/* 传统GIL版本,非原子操作 */
#define Py_INCREF(op) ((void)(++(op)->ob_refcnt))
#define Py_DECREF(op) \
    if (--((op)->ob_refcnt) == 0) \
        _Py_Dealloc((PyObject *)(op))
#endif
```