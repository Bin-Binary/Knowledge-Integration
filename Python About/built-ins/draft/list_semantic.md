- [Lists are mutable sequences, typically used to store collections of homogeneous items (where the precise degree of similarity will vary by application).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 序列、可变、容器

- [Lists may be constructed in several ways:](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 构造、多入口

- [Using a pair of square brackets to denote the empty list: [] ](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 字面量、空容器

- [Using a list comprehension: [x for x in iterable] ](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 推导式、逐项生成

- [Using the type constructor: list() or list(iterable)](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 构造器、转换

- [The constructor builds a list whose items are the same and in the same order as iterable's items.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 同项、保序、收集

- [iterable may be either another sequence, a container that supports iteration, or an iterator object.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 可迭代、鸭子类型

- [If iterable is already a list, a copy is made and returned, similar to iterable[:].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 副本、新对象

- [If iterable is already a list, a copy is made and returned, similar to iterable[:].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 副本、新对象

- [For example, list('abc') returns ['a', 'b', 'c'] and list((1, 2, 3)) returns [1, 2, 3].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 逐项、拆分

- [If no argument is given, the constructor creates a new, empty list [].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 空容器

- [Many other operations also produce lists, including the sorted() built-in function.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 默认结果容器

- [Lists implement all of the common and mutable sequence operations.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 全能序列、读、写

- [Lists also provide the following additional method: sort(*, key=None, reverse=None)](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 原地排序、仅限关键字参数

- [This method sorts the list in place, using only < comparisons between items.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 原地、全序

- [Exceptions are not suppressed - if any comparison operation fails, the entire sort operation will fail (and the list will likely be left in a partially modified state). ](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 异常传播、整体失败、非原子性

- [key specifies a function of one argument that is used to extract a comparison key from each list element (for example, key=str.lower).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 比较键、投影

- [The key corresponding to each item in the list will be calculated once and then used for the entire sorting process.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 一次性计算

- [The default value, None, means that list items are sorted directly without calculating a separate key value.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 元素即键

- [reverse is a boolean value. If set to True, then the list elements are sorted as if each comparison were reversed.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 反转比较、降序

- [This method modifies the sequence in place for economy of space when sorting a large sequence.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 原地、空间效率

- [To remind users that it operates by side effect, it does not return the sorted sequence (use sorted() to construct a new sorted list from an iterable).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 副作用、无返回值、sorted() 替代

- [The sort() method is guaranteed to be stable.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 稳定、相等保序

- [CPython implementation detail: While a list is being sorted, the effect of attempting to mutate, or even inspect, the list is undefined.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#lists) -> 实现细节、未定义行为、读写禁区

list语义总集：序列、可变、容器、字面量、推导式、构造器、保序、副本、鸭子类型、全能序列、原地、投影、稳定、副作用、未定义行为 