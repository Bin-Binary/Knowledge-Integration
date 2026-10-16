- 文本序列类型 - str 在 Python 中，文本数据通过 str 对象（即字符串）进行处理 -> [Sequence, Type, Text]

- 字符串是不可变的Unicode码点序列 -> [Sequence, Type, Text]

- 字符串字面量有多种书写方式：单引号：'允许嵌入"双引号"' 双引号："允许嵌入'单引号'" 三引号：'''三个单引号'''，"""三个双引号""" -> [Diversity, Prohibiting_or_licensing]

- 作为单个表达式的一部分且仅在它们之间有空白字符的字符串字面量，将被隐式转换为一个单一的字符串字面量 -> [Part_whole, Cause_change]

- 字符串也可以通过 str 构造函数从其他对象创建 -> [Entity, Creating]

- 由于没有单独的字符类型，对字符串进行索引会产生长度为1的字符串 -> [Type, Creating, Dimension]

- 也没有可变字符串类型，但可以使用 `str.join()` 或 `io.StringIO` 来高效地从多个片段构建字符串 -> [Type, Cause_to_amalgamate, Building]

- 这(Debug specifier)通常对调试很有帮助 -> [Usefulness]

- 转换说明符 默认情况下，替换字段表达式的值会使用 str() 转换为字符串 -> -> [Undergo_transformation]
