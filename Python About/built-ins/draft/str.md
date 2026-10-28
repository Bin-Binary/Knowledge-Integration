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

- str.capitalize()
Return a copy of the string with its first character capitalized and the rest lowercased.
Changed in version 3.8: The first character is now put into titlecase rather than uppercase. This means that characters like digraphs will only have their first letter capitalized, instead of the full character. （返回一个字符串的副本，其中首字母大写，其余字母小写。
在3.8版本中更改：现在首字母被转换为首字母大写形式（titlecase），而不是全部大写。这意味着像双字母组合（digraphs）这样的字符只会将其首字母大写，而不是整个字符。） -> [Arriving, Duplication]

playbook:
    - Arriving:
        Theme: 新字符串对象
        Goal: Theme 到达的目的地，认知缺口，需查资料 -> 新的内存对象（副本所在堆位置）
        
        Source: 原字符串对象在堆内存中的存储位置/引用
        Path: 运动轨迹，认知缺口，需查资料 -> 深水区，后续了解：拷贝内存轨迹
        Manner: 运动的方式，认知缺口，需查资料 -> 新建完整副本，非原地修改
        Means: 运动的手段，认知缺口，需查资料 -> CPython的Unicode capitalize算法（先titlecase首字符，再str.lower() 处理其余部分）
        Mode_of_transportation: 交通方式，认知缺口，需查资料 -> CPython运行时 + 内存分配器（分配新对象、搬运数据到目标地址的底层机制）
        Time: 运动的时间，认知缺口，需查资料 -> 缺省
        
        Place: 运动的地点，认知缺口，需查资料 -> 堆内存区
        Cotheme: 同步移动的第二对象，，认知缺口，需查资料 -> 缺省
        New_situation: Theme 到达后 Goal 的状态，，认知缺口，需查资料 -> 新字符串对象占用堆内存，引用返回调用方（refcount=1）
        Depictive: Theme 到达时的状态，认知缺口，需查资料 -> 首字母大写、其余小写
        Purpose: 到达目的，认知缺口，需查资料 -> 缺省
        Frequency: 到达频率认知缺口，需查资料 -> 缺省
        Period_of_iterations: 重复到达的时间段，认知缺口，需查资料 -> 缺省

    - Duplication:
        Creator：解释器
        Original：原始字符串
        Copy：字符串副本

        Source: Original 所在位置，认知缺口，需查资料 -> 原字符串对象在堆内存中的存储位置（其引用被 capitalize 读取）
        Purpose: 目的，认知缺口，需查资料 -> 不改原串的安全规范化拷贝
        Time: 时间，认知缺口，需查资料 -> 缺省
        Place: 地点，认知缺口，需查资料 -> 缺省
        Instrument: 工具，认知缺口，需查资料 -> capitalize() 方法调用——解释器执行 LOAD_METHOD/CALL 字节码的调用机制
        Manner: 实现复制的方式，认知缺口，需查资料 -> 新建完整副本：非原地修改、非引用/视图共享；因 str 不可变无深/浅之分，等同全新构造
        Means: 实现复制的行手段，认知缺口，需查资料 -> CPython unicode_capitalize：按 PEP 393 紧凑表示分配新 Unicode 对象并拷贝字符数据（ASCII 常用快路径）
        Degree: 程度，认知缺口，需查资料 -> 全量：整串所有字符均被纳入复制与变换（无部分复制、无切片视图）
        Fidelity: Copy 与 Original 的匹配度，认知缺口，需查资料 -> 高保真：长度与字符序列完全一致，唯一差异是大小写映射（case mapping）变更

        Goal: Copy 复制到的目标位置，认知缺口，需查资料 -> 新分配的堆内存地址（紧凑型 PyUnicodeObject 所在位置）
        Characterization: Copy 的媒介特征，认知缺口，需查资料 -> 全新独立的不可变 str：紧凑单块内存布局、非切片非视图，内部按码点（UCS-1/2/4）编码
        Iterations: 复制次数，认知缺口，需查资料 -> 缺省
        Frequency: 复制频率，认知缺口，需查资料 -> 缺省
        Co-participant: 共同参与者，认知缺口，需查资料 -> 调用方（发起 capitalize 的宿主表达式 / 返回值的绑定目标），与 Creator(解释器) 共同参与完成复制

summary：str的capitalize方法实现了改变字符串首字母大写其余小写的效果。
经历两个阶段，阶段一、解释器拷贝原始str对象生成首字母大写其余小写的新str对象；阶段二、返回新str对象的内存地址引用。
每个阶段经历多个步骤，阶段一的步骤: 1.读取宿主引用 -> 2.方法寻找 -> 3. 移交控制权给Cpyhon运行时执行unicode_capitalize -> 4. 内存评估与空间分配 -> 5. 字符变换；
阶段二的步骤： 1. CPython运行时初始化新str对象引用计数为1 -> 2. 地址压栈，返回新str对象的堆内存虚拟地址引用(id()可见值)并压入栈顶 -> 3. 绑定/流转，地址引用返回给调用方

gap: 
1. 怎么读取对象引用 -> 解释器使用LOAD_FAST（局部变量读取）/LOAD_GLOBAL（全局变量读取）读取原始str对象在堆中的引用到栈顶；字面量"abc".capitalize() 走 LOAD_CONST
2. capitalize方法怎么寻找 -> 解释器通过对象引用执行LOAD_METHOD（读取对象的方法引用）,去str类及MRO查找capitalize方法
3. 控制权怎么移交给Cpython运行时 -> 运行CALL（处理“引用传递”与“引用计数”）指令，带入方法所需的堆内存地址引用
4. 内存评估与空间分配发生什么 -> unicode_capitalize读取原始str对象的长度和字符类型（基于PEP 393 的 UCS-1/2/4 紧凑表示布局）。内存分配器在堆内存区（Heap）中，开辟一块全新且独立的PyUnicodeObject 紧凑单块内存（Goal）
5. 字符变换怎么处理 -> 1.读取原始str对象首字符转换为Titlecase形式 2. 调用str.lower()处理其余字符，拷贝进新内存堆

- str.casefold()
Return a casefolded copy of the string. Casefolded strings may be used for caseless matching.

Casefolding is similar to lowercasing but more aggressive because it is intended to remove all case distinctions in a string. For example, the German lowercase letter 'ß' is equivalent to "ss". Since it is already lowercase, lower() would do nothing to 'ß'; casefold() converts it to "ss". (返回字符串的折叠大小写副本。折叠大小写的字符串可用于不区分大小写的匹配。
折叠大小写与转换为小写类似，但更为激进，因为它旨在消除字符串中的所有大小写差异。例如，德语小写字母 'ß' 等同于 "ss"。由于 'ß' 已经是小写，lower() 对其不会产生任何效果；而 casefold() 会将其转换为 "ss") -> [Arriving, Duplication]

基于已学习的Arriving, Duplication学习这个新方法，以下为预测：
playbook:
    - Duplication
        Original: 原始str对象的数据内容
        Copy: 新str对象
        Creator: 解释器

        Purpose: 消除str的数据内容大小写差异
        Time: 缺省
        Place: id()可见的虚拟堆内存
        Source: 原始str对象虚拟堆内地址引用
        Manner: 创建新str对象
        Means: unicode_casefold (更激进的映射表查表算法，多对一或一对多映射); 调用方和解释器配合调用casefold（）
        Instrument: 原str的引用定位 -> LOAD_GLOBAL/LOAD_FAST/LOAD_CONST; 调用方法定位-> LOAD_METHOD ; 控制权移交Cpyhon运行时-> CALL
        Degree: 整个原始str对象的数据内容
        Fidelity: 激进度：**打破原有的字符结构**，ß→ss、İ→i̇ 长度可增

        Goal: 新开辟的虚拟内存堆
        Characterization: PEP 393 的UCS-1/2/4紧凑表示布局
        Iterations: 缺省
        Frequency：缺省
        Co-participant：调用发-> str / 解释器

    - Arriving:
        Theme: 新str对象
        Goal: 新开辟的虚拟内存堆

        Path: id()可观测值(虚拟内存堆引用) -> 压入栈顶 -> 返回引用给调用方
        Source: 缺省
        Time: 复制并字符转换后
        Manner: 引用传递
        Means: CALL处理引用传递/引用计数
        Mode_of_transportation：和Means重叠，缺省

        Purpose: 返回新str的虚拟内存堆地址引用给调用方
        Depictive: 折叠态：字符内容全小写；可能字符膨胀
        New_situation: 引用计数=1/地址绑定->[字面量，局部变量，全局变量]
        Frequency: 1
        Period_of_iterations: 缺省
        Place: 缺省
        Cotheme: 缺省

summary: str的casefold()实现了字符串大小写差异消除的效果。
经历两个阶段，阶段一：复制原始str并字符转换为全部小写；阶段二：返回转换后的str给调用方。
每个阶段经历多个步骤：阶段一的步骤：1.原始str的引用定位（解释器调用LAOD_FAST/LOAD_GLOBAL/LOAD_CONST）-> 2.casefold方法定位(解释器调用LOAD_METHOD(沿着str类和MRO查找)) -> 3.控制权移交Cpyton运行时(CALL携带地址引用进行移交)，执行对应c函数(此处为认知缺口，但不继续深入) -> 4.创建新str对象(内存评估与空间分配) -> 5.字符转换（全小写）；
阶段二的步骤：1. 新str对象虚拟内存堆的地址返回-> 2.地址压栈（绑定）-> 3.返回引用给调用方

推测：casefold与capitalize的主要区别在Purpose, Depictive，Means内嵌的底层细节还有最重要的Fidelity：字符膨胀以及连锁的新str对象所需的物理内存空间（Goal），可能远大于原字符串。 CPython在底层必须动态计算并扩容单块连续内存

- str.count(sub[, start[, end]])
Return the number of non-overlapping occurrences of substring sub in the range [start, end]. Optional arguments start and end are interpreted as in slice notation.
If sub is empty, returns the number of empty strings between characters which is the length of the string plus one（返回在范围【start, end】内子字符串sub的不重叠出现次数。可选参数start和end的解释方式与切片表示法相同。 如果sub为空，则返回字符之间空字符串的数量，即字符串长度加一。）-> [Arriving, Dimension, --Negation--，Scrutiny]

playbook:
    - Negation1:
        Negated_proposition: sub子串不为空
        Factual_situation: sub字串为空

    - Negation2:
        Negated_proposition: 范围内sub子串不重叠
        Factual_situation: 范围内sub子串重叠

    - Dimension:
        Dimension: 数量
        Object: str
        Measurement: <=长度+1（Negation1.Negated_proposition） / =长度+1（Negation1.Factual_situation）
        Locus: 被[start, end]范围切片的后str

    **Arraving1是幻觉认知，count不切片、不复制、零字符串分配**
    - Arraving1：
        Theme: 被[start, end]范围切片的后str -> 更正: 规范化后的绝对索引边界, 即(window_ptr, window_len)
        Goal: 原始str -> 更正: 原始str在内存字节数组（char[]）上的安全检索边界
        Path: 认知缺口，以下从两个维度推测：1.堆 -> 栈？；2.命名空间？ ->更正: 控制流转移：由CALL字节码指令将这3个参数（sub, start, end）带入CPython底层的string_count函数
        Source: 原始str的地址引用
        Manner: 认知缺口，推测：读取str对象数据并执行strip()，返回执行后的str -> 更正: 只读内存视窗
        Means：认知缺口，推测：1.定位对象地址：LOAD_FAST/LAOD_GLOBAL/LOAD_CONST -> 2.定位调用方法：LOAD_METHOD, 沿着str类、MRO链查找strip() -> 3.控制权移交Cpython运行时并执行底层c函数：CALL -> 更正: 1.解释器依次执行LOAD_FAST/LOAD_GLOBAL和LOAD_ATTR定位到count方法 -> 2.执行CALL移交控制权给CPython运行时的内置C函数 -> 3. C函数内部调用索引规范化宏，将Python风格的start/end（可能是负数或 None）转化为原字符串绝对安全的 C 数组下标
        Mode_of_transportation: 原始str的地址引用
        New_situation: 原始str不变
        Depictive: 认知缺口，新的str对象(原始str的地址引用)/临时的变量？ -> 更正: 两个纯 C语言的 Py_ssize_t（长整型）数值。它们寄生在当前虚拟机的 C 级别调用栈（C Stack）中，不是 Python 堆中的对象
        Purpose：返回被[start, end]范围切片的后str，这里为缺口，不清楚Depictive -> 更正: 划定安全的、免拷贝的只读内存扫描区间
        Time/Place/Frequency/Period_of_iterations: 缺省

    - Arraving2：
        Theme: 计数后的数量,一个全新的、代表计数值的Python整数对象PyLongObject
        Goal: 切片的后str -> 更正：虚拟机当前栈帧的求值栈（Evaluation Stack）顶
        Path: 认知缺口，以下从两个维度推测：1.堆 -> 栈？；2.命名空间？ -> 更正：1.C 栈局部变量(Source) --> 2.堆内存对象封装 -->3.压入Python虚拟机的求值栈顶（Goal）
        Source: 认知缺口，Arraving1.Depictive导致的连锁影响 -> 更正: C 语言运行栈上的纯整数变量（Py_ssize_t）
        Manner: 认知缺口，Arraving1.Depictive导致的连锁影响 -> 推测和内置的compare函数有关 -> 更正：C语言循环遍历与累加
        Means：认知缺口，Arraving1.Depictive导致的连锁影响 -> 更正： 
        1. 如果子串（sub）为空（Negation1.Factual_situation），则不启动循环，利用算术运算直接生成数值 len + 1。
        2. 如果子串非空，利用 Fastsearch 算法在 Arriving1 划定的绝对边界区间内进行不重叠（Negation2.Negated_proposition）查表扫描，C 计数器累加。
        3. 扫描结束后，调用 PyLong_FromSsize_t() 将这个 C 计数器的数值包装（Box）为一个标准的 Python 整数对象

        Mode_of_transportation: 认知缺口，Arraving1.Depictive导致的连锁影响 -> 更正：虚拟机的求值栈
        New_situation: 不受影响 -> 更正： 创建的整数对象引用计数初始化为1，压入栈顶，随时准备返回给调用方
        Depictive: 符合 Dimension.Measurement 约束的一个独立整数实体
        Purpose：返回被不重叠计数
        Time/Place/Frequency/Period_of_iterations: 缺省

summary: 
推测：“Manner是读取str数据并执行strip()或返回切片后的后 str 新对象，Means是通过类似切片手段构造临时变量”
事实：count不切片、不复制、零字符串分配、也没有创建任何新的临时字符串对象
新认知：基于原始str进行的检索类(对象获取)操作除了通过创建(复制/构造/字面量)，还有“只读内存视窗”
|类型|代表方法|行为|
|:--|:--|:--|
|创建(复制/构造/字面量)| capitalize/ center（width > len）/ casefold/ 切片 |新对象，开辟新内存空间 |
|只读视窗(扫描)|count/ find/ startswith/ endswith/ in| 零分配、索引窗口直指缓冲 |
|同一性回传|center（width <= len）/ 小整数/ 空串| 复用既有对象 |

“只读内存视窗”：1.定位左窗口：str对象的首地址 + 偏移量 （window_ptr=str_ptr + start）-> 2.确定视窗大小：window_len = end - start

另外，这个方法的描述携带了不设预期结果的校验语义（计数结果），使用Scrutiny比Negation更好：
Scrutiny:
    Cognizer: 解释器
    Groud: 原str
    Instrument: 只读内存可视窗口    
    Phenomenon: sub子串
    Medium: 缺省

- str.encode(encoding='utf-8', errors='strict')
Return the string encoded to bytes.

encoding defaults to 'utf-8'; see Standard Encodings for possible values.

errors controls how encoding errors are handled. If 'strict' (the default), a UnicodeError exception is raised. Other possible values are 'ignore', 'replace', 'xmlcharrefreplace', 'backslashreplace' and any other name registered via codecs.register_error(). See Error Handlers for details.

For performance reasons, the value of errors is not checked for validity unless an encoding error actually occurs, Python Development Mode is enabled or a debug build is used （将字符串编码为字节。 
encoding 默认值为 'utf-8'；可参见标准编码以了解可能的取值。 
errors 控制编码错误的处理方式。如果设置为'strict'（默认值），则会引发 UnicodeError 异常。其他可能的取值包括 'ignore'、'replace'、'xmlcharrefreplace'、'backslashreplace' 以及通过 codecs.register_error() 注册的任何其他名称。详情请参阅错误处理器。 
出于性能考虑，除非实际发生编码错误、启用了 Python 开发模式或使用了调试版本，否则不会检查 errors 参数的有效性。） -> [Arriving, Translating]

- str.endswith(suffix[, start[, end]])
Return True if the string ends with the specified suffix, otherwise return False. suffix can also be a tuple of suffixes to look for. With optional start, test beginning at that position. With optional end, stop comparing at that position. Using start and end is equivalent to str[start:end].endswith(suffix) （如果字符串以指定的后缀结尾，则返回 True，否则返回 False。suffix 也可以是一个需要查找的后缀元组。如果提供了可选的 start 参数，则从该位置开始测试。如果提供了可选的 end 参数，则在该位置停止比较。使用 start 和 end 的效果等同于 str[start:end].endswith(suffix)） -> [Arriving, Scrutiny]
playbook:
    Arriving描绘布尔对象地址引用的移动轨迹：布尔对象是永生单例，获取方式为同一性回传。堆内地址 -> 栈
    Scrutiny描绘解释器（Cognizer）不带预期地使用内存视窗(Instrumnet)扫描原始str(Ground)中的suffix（Phenomenon）

## fast_lean 
- str.expandtabs(tabsize=8)
[Demension, Arriving, Duplication, Replacing, Contingency]
The Method's Profiling is Arriving's Depictive. The Theme's Demension's Measurement（length）is changed and '/t' is replaced by space wich number depend on the with Outcome what is decided by Determinant(tabsize), but it remain str object. 

- str.find(sub[, start[, end]])
Return the lowest index ......, Arriving.Theme 是一个int, 盲猜不创建、复用小整数池的int地址。
...the string where substring sub is found within the slice s[start:end].Optional arguments start and end are interpreted as in slice notation, Scrutiny.Phenomenon是sub子串, 返回的是int对象，slice应该是语法说明，不是真发生创建行为，采取内存视窗的方式获取str的内容到执行栈。

- str.index(sub[, start[, end]])
Like find(), but raise ValueError when the substring is not found, 和find明显差异在Arriving.Theme是int/异常对象，

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

- str.capitalize()
Return a copy of the string with its first character capitalized and the rest lowercased.
Changed in version 3.8: The first character is now put into titlecase rather than uppercase. This means that characters like digraphs will only have their first letter capitalized, instead of the full character. （返回一个字符串的副本，其中首字母大写，其余字母小写。
在3.8版本中更改：现在首字母被转换为首字母大写形式（titlecase），而不是全部大写。这意味着像双字母组合（digraphs）这样的字符只会将其首字母大写，而不是整个字符。） -> [Arriving, Duplication]

playbook:
    - Arriving:
        Theme: 新字符串对象
        Goal: Theme 到达的目的地，认知缺口，需查资料 -> 新的内存对象（副本所在堆位置）
        
        Source: 原字符串对象在堆内存中的存储位置/引用
        Path: 运动轨迹，认知缺口，需查资料 -> 深水区，后续了解：拷贝内存轨迹
        Manner: 运动的方式，认知缺口，需查资料 -> 新建完整副本，非原地修改
        Means: 运动的手段，认知缺口，需查资料 -> CPython的Unicode capitalize算法（先titlecase首字符，再str.lower() 处理其余部分）
        Mode_of_transportation: 交通方式，认知缺口，需查资料 -> CPython运行时 + 内存分配器（分配新对象、搬运数据到目标地址的底层机制）
        Time: 运动的时间，认知缺口，需查资料 -> 缺省
        
        Place: 运动的地点，认知缺口，需查资料 -> 堆内存区
        Cotheme: 同步移动的第二对象，，认知缺口，需查资料 -> 缺省
        New_situation: Theme 到达后 Goal 的状态，，认知缺口，需查资料 -> 新字符串对象占用堆内存，引用返回调用方（refcount=1）
        Depictive: Theme 到达时的状态，认知缺口，需查资料 -> 首字母大写、其余小写
        Purpose: 到达目的，认知缺口，需查资料 -> 缺省
        Frequency: 到达频率认知缺口，需查资料 -> 缺省
        Period_of_iterations: 重复到达的时间段，认知缺口，需查资料 -> 缺省

    - Duplication:
        Creator：解释器
        Original：原始字符串
        Copy：字符串副本

        Source: Original 所在位置，认知缺口，需查资料 -> 原字符串对象在堆内存中的存储位置（其引用被 capitalize 读取）
        Purpose: 目的，认知缺口，需查资料 -> 不改原串的安全规范化拷贝
        Time: 时间，认知缺口，需查资料 -> 缺省
        Place: 地点，认知缺口，需查资料 -> 缺省
        Instrument: 工具，认知缺口，需查资料 -> capitalize() 方法调用——解释器执行 LOAD_METHOD/CALL 字节码的调用机制
        Manner: 实现复制的方式，认知缺口，需查资料 -> 新建完整副本：非原地修改、非引用/视图共享；因 str 不可变无深/浅之分，等同全新构造
        Means: 实现复制的行手段，认知缺口，需查资料 -> CPython unicode_capitalize：按 PEP 393 紧凑表示分配新 Unicode 对象并拷贝字符数据（ASCII 常用快路径）
        Degree: 程度，认知缺口，需查资料 -> 全量：整串所有字符均被纳入复制与变换（无部分复制、无切片视图）
        Fidelity: Copy 与 Original 的匹配度，认知缺口，需查资料 -> 高保真：长度与字符序列完全一致，唯一差异是大小写映射（case mapping）变更

        Goal: Copy 复制到的目标位置，认知缺口，需查资料 -> 新分配的堆内存地址（紧凑型 PyUnicodeObject 所在位置）
        Characterization: Copy 的媒介特征，认知缺口，需查资料 -> 全新独立的不可变 str：紧凑单块内存布局、非切片非视图，内部按码点（UCS-1/2/4）编码
        Iterations: 复制次数，认知缺口，需查资料 -> 缺省
        Frequency: 复制频率，认知缺口，需查资料 -> 缺省
        Co-participant: 共同参与者，认知缺口，需查资料 -> 调用方（发起 capitalize 的宿主表达式 / 返回值的绑定目标），与 Creator(解释器) 共同参与完成复制

summary：str的capitalize方法实现了改变字符串首字母大写其余小写的效果。
经历两个阶段，阶段一、解释器拷贝原始str对象生成首字母大写其余小写的新str对象；阶段二、返回新str对象的内存地址引用。
每个阶段经历多个步骤，阶段一的步骤: 1.读取宿主引用 -> 2.方法寻找 -> 3. 移交控制权给Cpyhon运行时执行unicode_capitalize -> 4. 内存评估与空间分配 -> 5. 字符变换；
阶段二的步骤： 1. CPython运行时初始化新str对象引用计数为1 -> 2. 地址压栈，返回新str对象的堆内存虚拟地址引用(id()可见值)并压入栈顶 -> 3. 绑定/流转，地址引用返回给调用方

gap: 
1. 怎么读取对象引用 -> 解释器使用LOAD_FAST（局部变量读取）/LOAD_GLOBAL（全局变量读取）读取原始str对象在堆中的引用到栈顶；字面量"abc".capitalize() 走 LOAD_CONST
2. capitalize方法怎么寻找 -> 解释器通过对象引用执行LOAD_METHOD（读取对象的方法引用）,去str类及MRO查找capitalize方法
3. 控制权怎么移交给Cpython运行时 -> 运行CALL（处理“引用传递”与“引用计数”）指令，带入方法所需的堆内存地址引用
4. 内存评估与空间分配发生什么 -> unicode_capitalize读取原始str对象的长度和字符类型（基于PEP 393 的 UCS-1/2/4 紧凑表示布局）。内存分配器在堆内存区（Heap）中，开辟一块全新且独立的PyUnicodeObject 紧凑单块内存（Goal）
5. 字符变换怎么处理 -> 1.读取原始str对象首字符转换为Titlecase形式 2. 调用str.lower()处理其余字符，拷贝进新内存堆

- str.casefold()
Return a casefolded copy of the string. Casefolded strings may be used for caseless matching.
Casefolding is similar to lowercasing but more aggressive because it is intended to remove all case distinctions in a string. For example, the German lowercase letter 'ß' is equivalent to "ss". Since it is already lowercase, lower() would do nothing to 'ß'; casefold() converts it to "ss". (返回字符串的折叠大小写副本。折叠大小写的字符串可用于不区分大小写的匹配。
折叠大小写与转换为小写类似，但更为激进，因为它旨在消除字符串中的所有大小写差异。例如，德语小写字母 'ß' 等同于 "ss"。由于 'ß' 已经是小写，lower() 对其不会产生任何效果；而 casefold() 会将其转换为 "ss") -> [Arriving, Duplication]

基于已学习的Arriving, Duplication学习这个新方法，以下为预测：
playbook:
    - Duplication
        Original: 原始str对象的数据内容
        Copy: 新str对象
        Creator: 解释器

        Purpose: 消除str的数据内容大小写差异
        Time: 缺省
        Place: id()可见的虚拟堆内存
        Source: 原始str对象虚拟堆内地址引用
        Manner: 创建新str对象
        Means: unicode_casefold (更激进的映射表查表算法，多对一或一对多映射); 调用方和解释器配合调用casefold（）
        Instrument: 原str的引用定位 -> LOAD_GLOBAL/LOAD_FAST/LOAD_CONST; 调用方法定位-> LOAD_METHOD ; 控制权移交Cpyhon运行时-> CALL
        Degree: 整个原始str对象的数据内容
        Fidelity: 激进度：**打破原有的字符结构**，ß→ss、İ→i̇ 长度可增

        Goal: 新开辟的虚拟内存堆
        Characterization: PEP 393 的UCS-1/2/4紧凑表示布局
        Iterations: 缺省
        Frequency：缺省
        Co-participant：调用发-> str / 解释器

    - Arriving:
        Theme: 新str对象
        Goal: 新开辟的虚拟内存堆

        Path: id()可观测值(虚拟内存堆引用) -> 压入栈顶 -> 返回引用给调用方
        Source: 缺省
        Time: 复制并字符转换后
        Manner: 引用传递
        Means: CALL处理引用传递/引用计数
        Mode_of_transportation：和Means重叠，缺省

        Purpose: 返回新str的虚拟内存堆地址引用给调用方
        Depictive: 折叠态：字符内容全小写；可能字符膨胀
        New_situation: 引用计数=1/地址绑定->[字面量，局部变量，全局变量]
        Frequency: 1
        Period_of_iterations: 缺省
        Place: 缺省
        Cotheme: 缺省

    - Dimension
        Dimension: 长度
        Object: 新str对象
        Measurement: 变长

summary: str的casefold()实现了字符串大小写差异消除的效果。
经历两个阶段，阶段一：复制原始str并字符转换为全部小写；阶段二：返回转换后的str给调用方。
每个阶段经历多个步骤：阶段一的步骤：1.原始str的引用定位（解释器调用LAOD_FAST/LOAD_GLOBAL/LOAD_CONST）-> 2.casefold方法定位(解释器调用LOAD_METHOD(沿着str类和MRO查找)) -> 3.控制权移交Cpyton运行时(CALL携带地址引用进行移交)，执行对应c函数(此处为认知缺口，但不继续深入) -> 4.创建新str对象(内存评估与空间分配) -> 5.字符转换（全小写）；
阶段二的步骤：1. 新str对象虚拟内存堆的地址返回-> 2.地址压栈（绑定）-> 3.返回引用给调用方

推测：casefold与capitalize的主要区别在Purpose, Depictive，Means内嵌的底层细节还有最重要的Fidelity：字符膨胀以及连锁的新str对象所需的物理内存空间（Goal），可能远大于原字符串。 CPython在底层必须动态计算并扩容单块连续内存

- str.count(sub[, start[, end]])
Return the number of non-overlapping occurrences of substring sub in the range [start, end]. Optional arguments start and end are interpreted as in slice notation.
If sub is empty, returns the number of empty strings between characters which is the length of the string plus one（返回在范围【start, end】内子字符串sub的不重叠出现次数。可选参数start和end的解释方式与切片表示法相同。 如果sub为空，则返回字符之间空字符串的数量，即字符串长度加一。）-> [Arriving, Dimension, --Negation--，Scrutiny]

playbook:
    - Negation1:
        Negated_proposition: sub子串不为空
        Factual_situation: sub字串为空

    - Negation2:
        Negated_proposition: 范围内sub子串不重叠
        Factual_situation: 范围内sub子串重叠

    - Dimension:
        Dimension: 数量
        Object: str
        Measurement: <=长度+1（Negation1.Negated_proposition） / =长度+1（Negation1.Factual_situation）
        Locus: 被[start, end]范围切片的后str

    **Arraving1是幻觉认知，count不切片、不复制、零字符串分配**
    - Arraving1：
        Theme: 被[start, end]范围切片的后str -> 更正: 规范化后的绝对索引边界, 即(window_ptr, window_len)
        Goal: 原始str -> 更正: 原始str在内存字节数组（char[]）上的安全检索边界
        Path: 认知缺口，以下从两个维度推测：1.堆 -> 栈？；2.命名空间？ ->更正: 控制流转移：由CALL字节码指令将这3个参数（sub, start, end）带入CPython底层的string_count函数
        Source: 原始str的地址引用
        Manner: 认知缺口，推测：读取str对象数据并执行strip()，返回执行后的str -> 更正: 只读内存视窗
        Means：认知缺口，推测：1.定位对象地址：LOAD_FAST/LAOD_GLOBAL/LOAD_CONST -> 2.定位调用方法：LOAD_METHOD, 沿着str类、MRO链查找strip() -> 3.控制权移交Cpython运行时并执行底层c函数：CALL -> 更正: 1.解释器依次执行LOAD_FAST/LOAD_GLOBAL和LOAD_ATTR定位到count方法 -> 2.执行CALL移交控制权给CPython运行时的内置C函数 -> 3. C函数内部调用索引规范化宏，将Python风格的start/end（可能是负数或 None）转化为原字符串绝对安全的 C 数组下标
        Mode_of_transportation: 原始str的地址引用
        New_situation: 原始str不变
        Depictive: 认知缺口，新的str对象(原始str的地址引用)/临时的变量？ -> 更正: 两个纯 C语言的 Py_ssize_t（长整型）数值。它们寄生在当前虚拟机的 C 级别调用栈（C Stack）中，不是 Python 堆中的对象
        Purpose：返回被[start, end]范围切片的后str，这里为缺口，不清楚Depictive -> 更正: 划定安全的、免拷贝的只读内存扫描区间
        Time/Place/Frequency/Period_of_iterations: 缺省

    - Arraving2：
        Theme: 计数后的数量,一个全新的、代表计数值的Python整数对象PyLongObject
        Goal: 切片的后str -> 更正：虚拟机当前栈帧的求值栈（Evaluation Stack）顶
        Path: 认知缺口，以下从两个维度推测：1.堆 -> 栈？；2.命名空间？ -> 更正：1.C 栈局部变量(Source) --> 2.堆内存对象封装 -->3.压入Python虚拟机的求值栈顶（Goal）
        Source: 认知缺口，Arraving1.Depictive导致的连锁影响 -> 更正: C 语言运行栈上的纯整数变量（Py_ssize_t）
        Manner: 认知缺口，Arraving1.Depictive导致的连锁影响 -> 推测和内置的compare函数有关 -> 更正：C语言循环遍历与累加
        Means：认知缺口，Arraving1.Depictive导致的连锁影响 -> 更正： 
        1. 如果子串（sub）为空（Negation1.Factual_situation），则不启动循环，利用算术运算直接生成数值 len + 1。
        2. 如果子串非空，利用 Fastsearch 算法在 Arriving1 划定的绝对边界区间内进行不重叠（Negation2.Negated_proposition）查表扫描，C 计数器累加。
        3. 扫描结束后，调用 PyLong_FromSsize_t() 将这个 C 计数器的数值包装（Box）为一个标准的 Python 整数对象

        Mode_of_transportation: 认知缺口，Arraving1.Depictive导致的连锁影响 -> 更正：虚拟机的求值栈
        New_situation: 不受影响 -> 更正： 创建的整数对象引用计数初始化为1，压入栈顶，随时准备返回给调用方
        Depictive: 符合 Dimension.Measurement 约束的一个独立整数实体
        Purpose：返回被不重叠计数
        Time/Place/Frequency/Period_of_iterations: 缺省

summary: 
推测：“Manner是读取str数据并执行strip()或返回切片后的后 str 新对象，Means是通过类似切片手段构造临时变量”
事实：count不切片、不复制、零字符串分配、也没有创建任何新的临时字符串对象
新认知：基于原始str进行的检索类(对象获取)操作除了通过创建(复制/构造/字面量)，还有“只读内存视窗”
|类型|代表方法|行为|
|:--|:--|:--|
|创建(复制/构造/字面量)| capitalize/ center（width > len）/ casefold/ 切片 |新对象，开辟新内存空间 |
|只读视窗(扫描)|count/ find/ startswith/ endswith/ in| 零分配、索引窗口直指缓冲 |
|同一性回传|center（width <= len）/ 小整数/ 空串| 复用既有对象 |

“只读内存视窗”：1.定位左窗口：str对象的首地址 + 偏移量 （window_ptr=str_ptr + start）-> 2.确定视窗大小：window_len = end - start

另外，这个方法的描述携带了不设预期结果的校验语义（计数结果），使用Scrutiny比Negation更好：
Scrutiny:
    Cognizer: 解释器
    Groud: 原str
    Instrument: 只读内存可视窗口    
    Phenomenon: sub子串
    Medium: 缺省

- str.encode(encoding='utf-8', errors='strict')
Return the string encoded to bytes.

encoding defaults to 'utf-8'; see Standard Encodings for possible values.

errors controls how encoding errors are handled. If 'strict' (the default), a UnicodeError exception is raised. Other possible values are 'ignore', 'replace', 'xmlcharrefreplace', 'backslashreplace' and any other name registered via codecs.register_error(). See Error Handlers for details.

For performance reasons, the value of errors is not checked for validity unless an encoding error actually occurs, Python Development Mode is enabled or a debug build is used （将字符串编码为字节。 
encoding 默认值为 'utf-8'；可参见标准编码以了解可能的取值。 
errors 控制编码错误的处理方式。如果设置为'strict'（默认值），则会引发 UnicodeError 异常。其他可能的取值包括 'ignore'、'replace'、'xmlcharrefreplace'、'backslashreplace' 以及通过 codecs.register_error() 注册的任何其他名称。详情请参阅错误处理器。 
出于性能考虑，除非实际发生编码错误、启用了 Python 开发模式或使用了调试版本，否则不会检查 errors 参数的有效性。） -> [Arriving, Translating]

- str.endswith(suffix[, start[, end]])
Return True if the string ends with the specified suffix, otherwise return False. suffix can also be a tuple of suffixes to look for. With optional start, test beginning at that position. With optional end, stop comparing at that position. Using start and end is equivalent to str[start:end].endswith(suffix) （如果字符串以指定的后缀结尾，则返回 True，否则返回 False。suffix 也可以是一个需要查找的后缀元组。如果提供了可选的 start 参数，则从该位置开始测试。如果提供了可选的 end 参数，则在该位置停止比较。使用 start 和 end 的效果等同于 str[start:end].endswith(suffix)） -> [Arriving, Scrutiny]
playbook:
    Arriving描绘布尔对象地址引用的移动轨迹：布尔对象是永生单例，获取方式为同一性回传。堆内地址 -> 栈
    Scrutiny描绘解释器（Cognizer）不带预期地使用内存视窗(Instrumnet)扫描原始str(Ground)中的suffix（Phenomenon）

## fast_lean 
- str.expandtabs(tabsize=8)
[Demension, Arriving, Duplication, Replacing, Contingency]
The Method's Profiling is Arriving's Depictive. The Theme's Demension's Measurement（length）is changed and '/t' is replaced by space wich number depend on the with Outcome what is decided by Determinant(tabsize), but it remain str object. 

- str.find(sub[, start[, end]])
Return the lowest index ......, Arriving.Theme 是一个int, 盲猜不创建、复用小整数池的int地址。
...the string where substring sub is found within the slice s[start:end].Optional arguments start and end are interpreted as in slice notation, Scrutiny.Phenomenon是sub子串, 返回的是int对象，slice应该是语法说明，不是真发生创建行为，采取内存视窗的方式获取str的内容到执行栈。

- str.index(sub[, start[, end]])
Like find(), but raise ValueError when the substring is not found, 和find明显差异在Arriving.Theme是int/异常对象，

- str.format_map(mapping, /)
**Symbolic Layer（文档内容符号）**
Similar to str.format(**mapping), except that mapping is used directly and not copied to a dict. This is useful if for example mapping is a dict subclass
**Conceptual Layer（FE填充 + DNI/INI/CNI认知缺口标注）**
[Similarity, Usefulness]
Similarity: 
    Entity_1: <sense> str.format_map; <denotation> 对象复用
    Entity_2: <sense> str.format; <denotation> 创建对象
    Dimension: <sense> 输出效果; <denotation> <INI> -> <denotation> 替换域的解析行为
    Differentiating_fact: <denotation> 参数解包协议 

usefulness:
    Entity: format_map的不复制直用模式
    Purpose: <sense>保留子类重写的 getitem / missing 行为
**Indicated Layer (实现细节)**
对象复用、创建新对象、<minimal-pair>参数解包协议 vs 读取字典 -> 前者临时内存开销大

summary: 除了**参数解包协议**，format_map采取mapping[k]直取、formant把manpping当kwargs解包（dict必须真实变成kwargs字典），两者相似。不复制直用模式保留了dict对象保留子类重写的getitem / missing行为，对灵活替换域解析行为很有帮助

- str.isalnum()
**Symbolic Layer**
"Return True if all characters in the string are alphanumeric and there is at least one character, False otherwise. A character c is alphanumeric if one of the following returns True: c.isalpha(), c.isdecimal(), c.isdigit(), or c.isnumeric().
**Conceptual Layer**
"Return True Return True if all characters in the string are alphanumeric and there is at least one character, False otherwise" -> Varification<EntryFrame>
Varification:
    Inspector: 解释器
    Unconfirmed_content: "all characters in the string are alphanumeric "
    Medium: "in the string"

    Condition: "there is at least one character"
    Degree: all characters
    Manner: [INI]
    Means: [INI]
    Instrument: [INI]

Sequence<StaticScript>（静态逻辑序列，非Frame内容，用于盲演逻辑）:
1. Verification Varification.Condition ↓([ActivitingFrame@Sufficiency；ActivitingPathFrame@Interrupt_process]) -> 
2. get Varification.Medium ↓([ActivitingPathFrame@Removing]) -> 
3. Verification Varification.Unconfirmed_content ↓([ActivitingFrame@Categorization]) -> 
4. return True ↓([ActivitingFrame@Giving])

**Indicated Layer**

DataFlow<FETransmission>（数据流：实体与槽位的动态绑定，非Frame内容，用于盲演数据流向）:
*1.输入绑定*：运行时接收str对象（<INI:认知缺口>, 未说怎么获取到的对象, 不强行引入新框架解释，仅在Sequence中标记ActivitingPathFrame@Removing用于框架扩展），将内存首地址绑定到[@Varification.Meduim] -> 
*2.衍生数据*：读取[@Varification.Meduim]的对象头（PyASCIIObject/PyCompactUnicodeObject）, 直接获取其length字段, 流向[@Sufficiency.Enabled_situation] <-> [@Varification.Condition]-> 
*3.只读内存视窗*: 根据字符串的物理存储类型（4字节的 UCS4/2字节的 UCS2 /1字节的 Latin1），在内存中动态暴露出一个只读连续字符数组Py_UCS4 *data作为物理视窗，供后续校验字符归属[@Categorization] 进行低开销的指针位移（Pointer Offset）

Timeline<RunTime>（时序：关联槽位的生命周期，非Frame内容，用于盲演时间轴）:
T0（压栈与数据绑定）: 解释器[@Varification.Inspector]在CPython虚拟机的栈帧中，通过内置C函数指针之间调用（PyCFunction_Call）[@Varification.Manner]的方式，免去LOAD_FAST等通用高阶字节码开销，以直接内存地址映射[@Varification.Means] 完成输入绑定

T1（边界检查）：虚拟机通过微代码对象头反射（O(1) 复杂度字段读取）[@Varification.Manner]的方式，绕过LOAD_METHOD查找len() 的高阶开销，直接读取 [@Varification.Medium] 的内部长度字段，流向[@Sufficiency.Enabled_situation]框架进行非空验证

T2（逐字迭代过筛）：物理时钟演进。指针ptr在只读内存视窗中自增，将字符 S[ptr]泵入 [@Varification.Unconfirmed_content]。每一个字符作[@Categorization.Item] 根据 Py_UNICODE_ISALNUM（位图掩码）[@Categorization.Criteria]动态返回分类结果Alphanumeric_characters（字母数字集）[@Categorization.Category]

T3（退栈与交付）：向调用者投递布尔指针Py_True或Py_False，释放局部变量，[@Varification.Medium] 引用计数减一。

Causality<EventiveAffecting>（因果：由槽位状态触发的分支，非Frame内容，用于盲演控制流）:
1. Branch_non_empty_truncation（非空截断）: 
Cause：[@Sufficiency] 框架判定length == 0，未满足 [@Varification.Condition] -> Effect：流程在 T1 时刻强行发生逻辑阻断(<INI:认知缺口>, 不强行引入新框架解释，仅在Sequence中标记↓[ActivitingPathFrame@Interrupt_process]用于框架扩展)，拒绝为 [@Varification.Unconfirmed_content]分配任何迭代时钟，直接产出Py_False

2. Branch_illegal_melting（非法熔断）：
Cause：T2期间，某个被送入[@Categorization.Item]的字符，在底层Py_UNICODE_ISALNUM位图掩码测试（Bitmap Mask Test）中返回 0（表示该字符在 isalpha/isdecimal/isdigit/isnumeric 四个 Unicode 属性中全员落空） -> Effect：循环在当前时钟瞬间异常终止（<INI:认知缺口>, 不强行引入新框架解释，仅在Sequence中标记↓[ActivitingPathFrame@Interrupt_process]用于框架扩展），终止后续一切指针递增，交付 Py_False。

3. Branch_normal_closure（正常闭环）
Cause：T2期间，指针ptr顺利自增至length边界。期间每一个填充至 [@Varification.Unconfirmed_content] 的字符，均通过了位图掩码的 OR 链条测试（满足了 [@Varification.Degree] 的全量约束） -> Effect：时序顺利抵达T3，系统向调用者安全投递Py_True

- str.isalpha()
**Symbolic Layer**
<PythonDoc:3.14.9>
"Return True if all characters in the string are alphabetic and there is at least one character, False otherwise. Alphabetic characters are those characters defined in the Unicode character database as “Letter”, i.e., those with general category property being one of “Lm”, “Lt”, “Lu”, “Ll”, or “Lo”.
<PythonDoc:3.14.9/> -> 校验字符串内的所有字符是字母类型(“Letter”)<funtion>


**Conceptual Layer**
"Return True if all characters in the string are alphabetic and there is at least one character, False otherwise" -> [Verification]
"Alphabetic characters are those characters defined in the Unicode character database as “Letter”, i.e., those with general category property being one of “Lm”, “Lt”, “Lu”, “Ll”, or “Lo”" -> [Categorization]

<nltk_data:framenet_v17>
Varification:
    Inspector: 解释器
    Unconfirmed_content: 所有字符是字母
    Medium: str对象
    Condition: 非空字符串
    Means: 遍历字符串,根据字符的general category判断

Categorition:
    Cognizer: Cpython
    Category: Letter
    Item: characters
    Means: 
    Criteria: general category
    Circumstances: $\forall x, \, gc(x) \in \{Lu, Ll, Lt, Lm, Lo\} \implies x \in L$
<nltk_data:framenet_v17/> -> 对类型进行校验的场景 <scenario>

<Logical_Squence_Predict>
1. 获取str <对象创建><对象复用> -> 2. 非空校验<直接读取属性> -> 3. 循环判断分类
<Logical_Squence_Predict> 

<Logical_Squence_Fact>
1. 获取str <对象创建><对象复用> : <对象创建>**被<DataFlow_Fact_1>推翻,**，获取str是<对象复用>
2. 非空校验<直接读取属性>: 
3. 循环判断分类: 预测和观测一致
<Logical_Squence_Fact> 

**Indicated Layer**
<DataFlow_Predict>
1. 输入与存储: 解释器在内存创建一个静态字符串对象(pyUnicodeObject),返回内存地址到当前作用域；返回复用对象的内存地址 -> 2. 处理与流转：非空校验与循环判断字符类别 -> 3. 生成与输出：输出True/False到当前作用域，原字符串对象若无其他引用则等待垃圾回收（GC）
<DataFlow_Predict/>
---
<DataFlow_Fact>
1. 输入与存储:...解释器在内存创建一个静态字符串对象(pyUnicodeObject),返回内存地址到当前作用域"**被<DataFlow_Fact_1>推翻,** 在[同一个函数内部]的环境：
词法/语法分析：编译器扫描到源码中的字面量 "Hhǅʰxxx 333" -> 分配内存（编译期）: 在内存中创建了一个PyUnicodeObject -> 绑定常量表：创建好的字符串对象的内存地址，被塞进了这个函数对应的字节码对象（PyCodeObject）的常量元组co_consts中 -> 运行期直接读取：从已经存在的 co_consts[1] 中直接把这个指针读出来
2. 处理与流转：预测和观测一致
3. 生成与输出: 预测和观测一致
<DataFlow_Fact/>

<DataFlow_Fact_1>
```Python 新建对象
import dis
def test_func():
    return "Hhǅʰxxx 333".isalpha()
dis.dis(test_func)
print(test_func.__code__.co_consts)
# >>> dis.dis(test_func)
#   1           0 RESUME                   0
#   2           2 LOAD_CONST               1 ('Hhǅʰxxx')
#               4 LOAD_METHOD              0 (isalpha)
#              26 PRECALL                  0
#              30 CALL                     0
#              40 RETURN_VALUE
# (None, 'Hhǅʰxxx 333')

# 在【不同的作用域/全局环境】下
a = "Hhǅʰxxx 333"
b = "Hhǅʰxxx 333"
print(a is b)  
# False [环境:交互式命令行]

a = "hello_123"
b = "hello_123"
print(a is b)  
# True [环境:交互式命令行]
```
```Python 复用对象
import sys
target_str = "Hhǅʰ中"
ref_before = sys.getrefcount(target_str)
result = target_str.isalpha()
ref_after = sys.getrefcount(target_str)
print(f"调用前引用计数: {ref_before}")
print(f"调用后引用计数: {ref_after}")
print(f"计数是否改变: {ref_before != ref_after}")  

# 计数是否改变: False

```
<DataFlow_Fact_1/>

<DataFlow_Fact_2>
```Python 非空校验
import timeit
time_empty = timeit.timeit('"".isalpha()', number=10_000_000)
time_invalid = timeit.timeit('"Hhǅʰyyyyyyyyyyyyyyxxx 333".isalpha()', number=10_000_000)
print(f"空字符串耗时: {time_empty:.4f} 秒")
print(f"非空字符耗时: {time_invalid:.4f} 秒")
print(f"空字符串是否比非空字符显著更快: {time_empty < time_invalid}")
# 空字符串耗时: 0.2550 秒
# 非空字符耗时: 0.8679 秒
# 空字符串是否比非空字符显著更快: True
```

```Python 循环判断字符类别
import unicodedata
target = "Hhǅʰyyyyyyyyyyyyyyxxx "
for i, char in enumerate(target):
    category = unicodedata.category(char)
    is_char_alpha = char.isalpha()
    print(f"位置 {i} | 字符: {char} | Unicode分类: {category} | 是否属于Letter: {is_char_alpha}")

# 位置 0 | 字符: H | Unicode分类: Lu | 是否属于Letter: True
# 位置 1 | 字符: h | Unicode分类: Ll | 是否属于Letter: True
# 位置 2 | 字符: ǅ | Unicode分类: Lt | 是否属于Letter: True
# 位置 3 | 字符: ʰ | Unicode分类: Lm | 是否属于Letter: True
# 位置 4 | 字符: x | Unicode分类: Ll | 是否属于Letter: True
# 位置 5 | 字符: x | Unicode分类: Ll | 是否属于Letter: True
# 位置 6 | 字符: x | Unicode分类: Ll | 是否属于Letter: True
# 位置 7 | 字符:   | Unicode分类: Zs | 是否属于Letter: False
```
<DataFlow_Fact_2/>

<DataFlow_Fact_3>
```Python
import sys
import ctypes
target_str = "HhDžhyyyyyyyyyyyyyyxxx_unique_999"
memory_address = id(target_str)  
def get_ref_by_address(address):
    return ctypes.c_ssize_t.from_address(address).value
print("--- 开始纯物理层观测 ---")
print(f"1. 字符串物理地址: {memory_address}")
print(f"2. 初始状态（Python层引用计数）: {sys.getrefcount(target_str)}")
print(f"3. 初始状态（C底层物理计数）  : {get_ref_by_address(memory_address)}")
my_result = target_str.isalpha()
del target_str 
physical_ref_count = get_ref_by_address(memory_address)
print(f"4. del后，通过物理地址测得的底层引用计数: {physical_ref_count}")
print(f"5. 当前局部变量表是否安全持有结果: {'my_result' in locals()}")

# 1. 字符串物理地址: 2273593105488
# 2. 初始状态（Python层引用计数）: 2
# 3. 初始状态（C底层物理计数）  : 1
# 4. del后，通过物理地址测得的底层引用计数: 2273593104768
# 5. 当前局部变量表是否安全持有结果: True
```
<DataFlow_Fact_3/>
---

<TimeLine_Predict>
T0.Creating↓<Hook>:  -> T1.Using↓<Hook>: -> T2.Destructor↓<Hook>:
<TimeLine_Predict/>

<TimeLine_Fact_T0>
## 构建不同字面量的组件观测

1. 定义结构体
```python
import ctypes, struct

class State(ctypes.LittleEndianStructure):
    _pack_ = 4
    _fields_ = [
        ("interned", ctypes.c_uint, 2),
        ("kind",     ctypes.c_uint, 3),
        ("compact",  ctypes.c_uint, 1),
        ("ascii",    ctypes.c_uint, 1),
        ("ready",    ctypes.c_uint, 1),
        ("_pad",     ctypes.c_uint, 24),
    ]

class PyASCIIObject(ctypes.LittleEndianStructure):
    _pack_ = 8
    _fields_ = [
        ("ob_refcnt", ctypes.c_ssize_t),
        ("ob_type",   ctypes.c_void_p),
        ("length",    ctypes.c_ssize_t),
        ("hash",      ctypes.c_ssize_t),
        ("state",     State),
        ("_pad",      ctypes.c_uint),
        ("wstr",      ctypes.c_void_p),
    ]

class PyCompactUnicodeObject(ctypes.LittleEndianStructure):
    _pack_ = 8
    _fields_ = [
        ("_base",       PyASCIIObject),
        ("utf8_length", ctypes.c_ssize_t),
        ("utf8",        ctypes.c_void_p),
        ("wstr_length", ctypes.c_ssize_t),
    ]

class DataUnion(ctypes.Union):
    _fields_ = [
        ("any",   ctypes.c_void_p),
        ("latin1", ctypes.POINTER(ctypes.c_uint8)),
        ("ucs2",  ctypes.POINTER(ctypes.c_uint16)),
        ("ucs4",  ctypes.POINTER(ctypes.c_uint32)),
    ]

class PyUnicodeObject(ctypes.LittleEndianStructure):
    _pack_ = 8
    _fields_ = [
        ("_base", PyCompactUnicodeObject),
        ("data",  DataUnion),
    ]
```
2. 创建字符串并开辟观测窗
```python
target_L = "Hhǅʰ你"
unicode_obj = PyUnicodeObject.from_address(id(target_L))
obj = PyCompactUnicodeObject.from_address(id(target_L))
```

3. 观测
state
```python
obj._base.state.interned, obj._base.state.kind, obj._base.state.compact, obj._base.state.ascii, obj._base.state.ready
```
>>> obj._base.state.interned, obj._base.state.kind, obj._base.state.compact, obj._base.state.ascii, obj._base.state.ready
(0, 2, 1, 0, 1)

data
```python
unicode_obj.data.any, unicode_obj.data.latin1, unicode_obj.data.ucs2, unicode_obj.data.ucs4
```
>>> unicode_obj.data.any, unicode_obj.data.latin1, unicode_obj.data.ucs2, unicode_obj.data.ucs4
(193656729603932232, <__main__.LP_c_ubyte object at 0x00000298CD1CB6D0>, <__main__.LP_c_ushort object at 0x00000298CD1CB750>, <__main__.LP_c_ulong object at 0x00000298CD1CB8D0>)

4. 看所有字段
```python
obj._base.ob_refcnt, obj._base.length, obj.utf8_length, obj.utf8, obj.wstr_length
```
>>> obj._base.ob_refcnt, obj._base.length, obj.utf8_length, obj.utf8, obj.wstr_length
(1, 5, 0, None, 5)

5. 读 UCS-2 字符数据（kind=2 compact 数据在 +0x48）
```python
addr = id(target_L) + ctypes.sizeof(obj)
chars = [ctypes.c_uint16.from_address(addr + i*2).value for i in range(obj._base.length)]
chars
"".join(chr(c) for c in chars)
```
>>> chars
[72, 104, 453, 688, 20320]
>>> "".join(chr(c) for c in chars)
'Hhǅʰ你'

<TimeLine_Fact/>
---

<Causality_Predict>
<Causality_Predict/>

<Causality_Fact>
<Causality_Fact/>
---
summary:
最小对立对<minimal-pair>：
1. str的生命周期管理：自动全局驻留（Intern）机制 VS 非全局驻留 -> 全Python进程中的写这个字面量（纯ASCII字符串（包含字母、数字、下划线））都强制指向同一块内存
2. str的空间与性能： 编译器常量折叠 vs 运行时动态创建 -> 常量折叠：`"Hh" * 3`在编译期折叠成 `"HhHhHh"`到PyCodeObject的co_consts常量表，运行期只需执行一次``LOAD_CONST`指针复用；运行时动态创建：运行期分配堆内存、拼接字符、创建新对象。

互补分布<complementary-distribution>:

TIPS：
<minimal-pair>相似中的差异，是分析逻辑，把一个模糊的整体拆开，看清微观的**边界**
<complementary-distribution>差异中的相同，是构建的逻辑。抛开环境的导致的表现差异性，看清功能上一致性，建立宏观的秩序与规律
