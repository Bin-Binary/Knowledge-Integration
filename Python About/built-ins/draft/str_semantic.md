- [Textual data in Python is handled with str objects, or strings.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 文本、载体

- [Strings are immutable sequences of Unicode code points.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 不可变、序列、Unicode 码位

- [String literals are written in a variety of ways: Single quotes: 'allows embedding "double" quotes'; Double quotes: "allows embedding 'single' quotes".](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 字面量、多写法、引号互嵌

- [Triple quoted: '''Three single quotes''', """Three double quotes""" ](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 三引号

- [Triple quoted strings may span multiple lines - all associated whitespace will be included in the string literal.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 跨行、保留空白

- [Strings implement all of the common sequence operations, along with the additional methods described below.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 全序列操作

- [Return a string version of object. If object is not provided, returns the empty string.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 字符串化、默认空串

- [If neither encoding nor errors is given, str(object) returns type(object).str(object), which is the 'informal' or nicely printable string representation of object.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 优雅打印、str

- [For string objects, this is the string itself.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 幂等、自返回

- [If object does not have a str() method, then str() falls back to returning repr(object).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 回退、repr

- [If at least one of encoding or errors is given, object should be a bytes-like object (e.g. bytes or bytearray).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 解码入口、bytes-like

- [Return a copy of the string with its first character capitalized and the rest lowercased.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 副本、首字母大写        

- [Return a casefolded copy of the string. Casefolded strings may be used for caseless matching.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 大小写折叠、无大小写匹配

- [Return centered in a string of length width. Padding is done using the specified fillchar (default is an ASCII space).](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 居中、填充

- [Return the number of non-overlapping occurrences of substring sub in the range [start, end].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 计数、非重叠

- [Encode the string using the specified encoding, which defaults to 'utf-8'.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 编码、默认 utf-8

- [Return True if the string ends with the specified suffix, otherwise return False. suffix can also be a tuple of suffixes to look for.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 后缀判定、元组选项

- [Return True if the string starts with the prefix, otherwise return False.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 前缀判定

- [Return a copy of the string where all tab characters are replaced by whitespace.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 制表符展开

- [Return the lowest index in the string where substring sub is found within the slice s[start:end]. Return -1 if sub is not found.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 查找、最低索引、-1 哨兵  

- [Like str.find(), but raise ValueError when the substring is not found.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 异常版查找

- [Perform a string formatting operation. The string on which this method is called can contain literal text or replacement fields delimited by braces {}.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 格式化、替换域

- [Similar to str.format(**mapping), except that mapping is used directly and not copied to a dict.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 直用映射、免复制

- [Return True if all characters in the string are alphabetic and there is at least one character, False otherwise.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 谓词、非空、全称量词

- [Return True if the string is a valid identifier according to the language definition.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 标识符判定

- [Return a string which is the concatenation of the strings in iterable. A TypeError will be raised if there are any non-string values in iterable, including bytes objects.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 拼接、分隔符、类型严格

- [Return the string left justified in a string of length width. If width is less than or equal to len(s), the original string is returned.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 左对齐、不足原样

- [Return a copy of the string with all the cased characters converted to lowercase.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 小写化、Unicode 规则

- [Return a copy of the string with the leading and trailing characters removed.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 去两端

- [static str.maketrans(x[, y[, z]]): Return a translation table usable for str.translate().](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 转换表、静态方法

- [Split the string at the first occurrence of sep, and return a 3-tuple containing the part before the separator, the separator itself, and the part after the separator.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 三分、首次分割

- [If the string starts with the prefix string and that prefix is not empty, return string[len(prefix):]. Otherwise, return a copy of the original string.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 去前缀、条件拷贝

- [Return a copy of the string with all occurrences of substring old replaced by new.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 替换、全次数

- [Return the highest index in the string where substring sub is found within the slice s[start:end].](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 反向查找、最高索引

- [Return a list of the words in the string, using sep as the delimiter string.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 分词、返回列表

- [If sep is not specified or is None, runs of consecutive whitespace are regarded as a single separator, and the result will contain no empty strings at the start or end.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 默认空白、聚合分隔

- [Return a list of the lines in the string, breaking at line boundaries. Line breaks are not included in the resulting list unless keepends is given and true.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 拆行、通用换行

- [Return a copy of the string in which each character has been mapped through the given translation table.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 逐字符映射

- [Return a copy of the string left filled with ASCII '0' digits to make a string of length width. A leading sign prefix ('+'/'-') is handled by inserting the padding after the sign character rather than before.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 补零、符号后置

- [The formatting operations described here exhibit a variety of quirks that lead to a number of common errors. Using the newer formatted string literals, the str.format() interface, or template strings may help avoid these errors.](https://docs.python.org/zh-cn/3.14/builtins/stdtypes.html#str) -> 旧式、易错、替代方案

str语义总集： 文本、不可变、序列、Unicode 码位、字面量、三引号、跨行、保留空白、全序列操作、字符串化、优雅打印、幂等、回退、解码、副本、大小写折叠、填充、计数、编码、前缀判定、后缀判定、谓词、查找、哨兵、异常版、格式化、替换域、拼接、类型严格、对齐、去两端、转换表、三分、去前缀、替换、反向查找、分词、默认空白、拆行、映射、补零、旧式、易错