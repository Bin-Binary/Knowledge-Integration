- str.format(*args, **kwargs)
"The string on which this method is called can contain literal text or replacement fields delimited by braces {}" -> [Inclusion, Filling]
Inclusion:
    Total: 被格式化的str
    Part: literal/replacement field
    Time: CNI
    Place: CNI
    Manner: str的literal(' ' " " """ """)
    Purpose: CNI
    Frequency: CNI
    Contrast_set: 无
    Subregion: litteral 可以在{}中
    Explanation: 无

Filling:
    Agent: 解释器
    Goal: {}
    Theme: [INI], 但推测为str对象
    Cause: [INI]
    Source: [INI], 但推测为：str/int/float/complex/tuple/list/dict/set/bool/bytes/bytearray
    Path: [INI], 但推测为: 1.[logic] Source -> str; 2.[physic] 堆->栈->堆/堆->堆(视窗) -> 应该只需要Source经过处理的值，所以似乎不需要str对象，直接在视窗扫描即可。
    Degree: [CNI]
    Manner: [INI], 但推测为: str的literal/lambda/推导式/闭包/....
    Means: [INI], 但推测为: Manner的具体实现
    Instrument: [CNI]
    Result: [INI], 但推测为: 生成str对象
    Purpose: [DNI]

"Each replacement field contains either the numeric index of a positional argument, or the name of a keyword argument" -> [Inclusion, Filling]
Inclusion:
    Total: {}
    Part: index/keyword

Replacing:
    Old: Inclusion.Part
    New: [INI], 但被Filling.Theme替换
这里发现{}应该是mutable的，因为可以被替换, 结合Inclusion.Part，大概其是容器类型中的一种：list/tuple/dict/set

Filling:
只保留相关FE
    Agent: 这里具体的填充者[INI]
    Goal: [INI]，但推测是容器实例：list/tuple/dict/set
    Theme: [INI]，但推测为str对象
    Source: [INI], 之前推测为：str/int/float/complex/tuple/list/dict/set/bool/bytes/bytearray， 但根据对Goal的推测，Source应该是可以？[INI]
    Path: [INI]
    Manner: [INI], 依旧推测为: str的literal/lambda/推导式/闭包/....
    Means: [INI], 依旧推测为: Manner的具体实现
    Result: [INI], 之前推测为: 生成str对象， 但现在根据替换场景，Result应该是容器实例经过str()后的结果

"Returns a copy of the string where each replacement field is replaced with the string value of the corresponding argument"
Duplication:
    Creator: 解释器
    Original: str
    Copy: str
    Source: [Physic]堆地址引用
    Goal: [Physic]新开辟的堆
    Co-participant: Cpython运行时
    Manner: 创建新对象
    Means: LAOD_FAST/LOAD_CLOBAL/LOAD_CONST -> LOAD_METHOD -> CALL, 再细节的[INI],但当前不深入
    Characterization: 地址引用(和上面有重叠，但起提示作用) 

Arriving:
    Theme: str的对象引用
    Goal: [Logic]str -> str; [Physic] 栈指向新开辟的堆

playbook:
    [INI]
