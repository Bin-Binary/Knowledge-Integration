- 文本序列类型 - str 在 Python 中，文本数据通过 str 对象（即字符串）进行处理 -> [Sequence, Type, Text]

- 字符串是不可变的Unicode码点序列 -> [Sequence, Type, Text]

- 字符串字面量有多种书写方式：单引号：'允许嵌入"双引号"' 双引号："允许嵌入'单引号'" 三引号：'''三个单引号'''，"""三个双引号""" -> [Diversity, Prohibiting_or_licensing]

- 作为单个表达式的一部分且仅在它们之间有空白字符的字符串字面量，将被隐式转换为一个单一的字符串字面量 -> [Part_whole, Cause_change]

- 字符串也可以通过 str 构造函数从其他对象创建 -> [Entity, Creating]

- 由于没有单独的字符类型，对字符串进行索引会产生长度为1的字符串 -> [Type, Creating, Dimension]

- 也没有可变字符串类型，但可以使用 `str.join()` 或 `io.StringIO` 来高效地从多个片段构建字符串 -> [Type, Cause_to_amalgamate, Building]

- 这(Debug specifier)通常对调试很有帮助 -> [Usefulness]

- 转换说明符 默认情况下，替换字段表达式的值会使用 str() 转换为字符串 -> [Undergo_transformation]

- Format specifier After the expression has been evaluated, it is formatted using the format() function (格式说明符 在表达式被求值之后，它将使用 format() 函数进行格式化) -> [Arranging, Encoding]

- This（the '%' operator） is also known as the string formatting or interpolation operator(这（'%'）也称为字符串格式化或插值运算符) -> [Being_named]

- Conversion flags (optional), which affect the result of some conversion types.（转换标志（可选），影响某些转换类型的结果。） -> [Objective_influence]

- Strings implement all of the common sequence operations, along with the additional methods described below.（字符串实现了所有常见的序列操作，以及以下描述的附加方法）-> [Commonality， Increment]

- Strings also support two styles of string formatting, one providing a large degree of flexibility and customization and the other based on C printf style formatting that handles a narrower range of types and is slightly harder to use correctly, but is often faster for the cases it can handle.（字符串还支持两种字符串格式化风格，一种提供了高度的灵活性和自定义能力，另一种则基于 C 语言 printf 风格的格式化，它处理的类型范围较窄，使用起来稍微复杂一些，但在它能处理的场景中通常速度更快。）-> [Cardinal_numbers，Frequency, Instance]

- str.capitalize() Return a copy of the string with its first character capitalized and the rest lowercased.（
str.capitalize() 返回字符串的副本，其首字母大写，其余字母小写。）-> [Duplication, Ordinal_numbers, Rest]

- Casefolding is similar to lowercasing but more aggressive because it is intended to remove all case distinctions in a string.(大小写折叠（Casefolding）与小写化类似，但更为激进，因为它旨在消除字符串中的所有大小写区别。) -> [Similarity, Removing]

- str.center(width, fillchar=' ', /)
Return centered in a string of length width. Padding is done using the specified fillchar (default is an ASCII space). The original string is returned if width is less than or equal to len(s).（返回一个长度为 width 的字符串，内容居中对齐。填充使用指定的 fillchar（默认为 ASCII 空格）。如果 width 小于或等于 len(s)，则返回原始字符串） -> [Dimension，Evaluative_comparison，Filling]

playbook:
- Dimension:
    Dimension -> width
    Object -> 字符串
    Measurement -> width值

- Filling：
    Agent -> 缺省、交给Cause驱动
    Theme -> fillchar指定
    Goal -> 大小为(Evaluative_comparison.Profiled_item - Evaluative_comparison.Standard_item)/2 的str两边 -> 奇偶情况? ->  发现缺口 -> 左偶右奇(认知缺口补全)
    Cause -> str的center事件

- Evaluative_comparison：
    Standard_item -> len(s)
    Profiled_item -> Dimension.Measurement
    Standard_attribute -> len(s)的值
    Profiled_attribute -> Dimension.Measurement的值
    Manner -> ? 发现缺口 -> Less_than_or_equal_to（小于或等于）(认知缺口补全)

- Identity comparisons
The operators is and is not test for an object’s identity: x is y is true if and only if x and y are the same object. An Object’s identity is determined using the id() function. x is not y yields the inverse truth value. （运算符 is 和 is not 用于测试对象的身份：x is y 为真当且仅当 x 和 y 是同一个对象。对象的身份可以通过 id() 函数来确定。x is not y 则返回相反的真值） -> [Identity，Correctness，Entity, Using, Creating, Negation]

playbook:
- Identity:
    Instance -> 用于测试对象
    Identity -> 标识对象的身份特征，文本未提及，为认知缺口需要看id（）-> 对象的身份标识在底层就是其内存地址。
事实：对象的身份标识时内存地址

- Correctness：
    Information -> 这里"事实匹配或不匹配的信息"，文本未提及，为认知缺口，需要看id（）-> 'is'语境下，校验的Information是引用的一致性（Reference Equality），即“这两个指针是否指向完全相同的内存块”，区别于 '=='比较的是数据内容是否相等
    Source -> 用于测试对象持有的正确/错误信息，文本未提及，需要看id（）-> 来自于 C 级别结构体底层的 id() 函数返回值（在 CPython 中，id(x) 直接返回对象指针的整数形式）
    Communicative_act -> "传达信息的交际行为"，文本未提及，为认知缺口，需查找资料 -> 断言反馈
    Topic -> 和Source互斥, 这里缺省
    Medium -> 信息所处的媒介, 文本未提及，为认知缺口，需查找资料 -> 系统的运行时内存（RAM）/ 进程的堆空间（Heap Memory）
事实：is 比较的信息是两个指针在内存媒介中是否引用的一致性，不关心其承载的数值或内容是否相同

- Entity：
    Entity -> 对象
    Constituent_parts -> 对象拥有特定内存地址
    Formational_cause -> "导致实体特征形成的行动", 文本未提及，为认知缺口，需查找资料 -> 内存分配与实例化
    Name -> 对象.name
    Type -> 对象.type
事实：对象的身份特征（内存地址）是在对象被分配内存并实例化被确定的

- Using:
    Agent -> 解释器
    Purpose -> 比较两个对象身份
    Manner -> 基于对象的内存地址（唯一标识符 ID）
    Place -> “Agent 使用 Instrument 的地点”, 文本未提及，为认知缺口，需查找资料 -> 虚拟机的执行引擎中（具体为 CPython 的字节码解释循环 _PyEval_EvalFrameDefault / ceval.c）。当字节码执行到 COMPARE_OP（且操作码为 is 或 is not）时，该处的逻辑被触发。
    Time -> "Agent 使用 Instrument 的时间", 使用"is"语法糖时
事实：当代码运行到 is 语法糖时，解释器会在**字节码执行引擎（ceval.c）**中，直接通过 C 语言的指针比较（op1 == op2）来快速判断两个对象的内存地址是否相同

- Creating:
    Created_entity -> True/False
    Creator -> 解释器
    Time -> 解释器启动初始化时就已经创建完毕（永生单例），此之后，代码中所进行的任何真值测试（如 if 判断、is 比较等）都不会再去创建新对象，直接返回单例
事实：使用"is"语法糖比较两个对象身份时,解释器会返回用于真值测试的单例bool对象

- Negation:
    Negated_proposition -> 对象的内存地址不等
    Factual_situation -> 对象的内存地址相等

事实：测试对象的身份不是测试内容

summary: 每当一个对象(Entity)被内存分配与实例化创建(Creating)时，在运行时内存中获得了一个唯一且不可变的身份标识，即内存起始地址（Identity）。
当程序运行到 is 或 is not 语法糖时，解释器（ceval.c）在（虚拟机执行引擎 _PyEval_EvalFrameDefault） 内部被激活。为了实现比较对象身份（Purpose），它通过C 语言指针直接对比（Manner）来调取底层的 id() 映射值（Source），判断两个变量是否引用一致。
这一行为属于典型的断言反馈的交际行为（Communicative_act），它的主题（Topic） 是将“引用一致性”这一状态信息（Information） 交付给上层的控制流。在此期间，解释器不会动态创建新对象 （Creating） 的动作，因为True/False早在解释器启动初始化的瞬间（Time） 就作为永生单例准备就绪；解释器此时仅做寻址交付，将相应的布尔单例压入求值栈顶。而一旦遇到 is not 运算符，整个判定则进入Negation（否定机制），如果实际物理情况（Factual_situation） 判定其地址不等，便会精准返回与 is 完全相反的真值。
**总之，is 比较的是身份；但对字面量，身份本身不可预测——所以实践上只在判 None、判单例时才敢相信它**
