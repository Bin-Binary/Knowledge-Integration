# 实体粗筛: 文件I/O

> Step 2 产出 | 来源: 提取清单 C100-C103

---

╔═══════════════════════════════════════════════════════════╗
║  【I/O操作】文件操作 open()                                ║
║  编号: E028 | 来源: 提取清单C100+C101                     ║
╚═══════════════════════════════════════════════════════════╝

【定义】 open()打开文件返回文件对象(file object), 支持文本/二进制模式, 是Python与OS文件系统的桥梁, 支持上下文管理器协议。

【结构】"它长什么样？"
- 文件对象层次: FileIO(原始字节) → BufferedReader/BufferedWriter(缓冲) → TextIOWrapper(文本解码)
- open(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True)
- 文件模式(mode):
  - 'r': 只读(默认, 文件必须存在)
  - 'w': 只写(创建或截断)
  - 'a': 追加(创建或追加到末尾)
  - 'x': 排他创建(文件已存在则失败)
  - '+': 同时读写
  - 'b': 二进制模式(不存在编解码层, 返回bytes)
  - 't': 文本模式(默认, 自动编解码, 返回str)
- 缓冲(buffering): -1(系统默认), 0(无缓冲, 仅二进制), 1(行缓冲, 仅文本), >1(指定字节)

【时序】"它按什么顺序动？"
- 打开文件:
  1. open() → 调用os.open()(系统调用)
  2. 创建BufferedReader/BufferedWriter → 包装syscall fd
  3. 若文本模式: 再包装一层TextIOWrapper
  4. 返回文件对象
- 读操作:
  - f.read(n): 读取n个字符/字节, 无参数读全部
  - f.readline(): 读取一行(含\n)
  - f.readlines(): 读取所有行返回list
  - 迭代: for line in f — 逐行迭代(惰性, 内存友好)
- 写操作:
  - f.write(s): 写入s(字符串或bytes)
  - f.writelines(lines): 写入多个字符串(逐个write, 不自带换行)
- 关闭:
  - f.close(): 刷新缓冲区→关闭fd(系统调用close)
  - 上下文管理器: with open(...) as f: → 自动close

【实体】"它的最小数据单元？"
- 文件描述符(fd): int, 操作系统文件句柄
- 文件位置(f.tell()): 当前读写偏移
- 缓冲区: 内存中的bytearray(缓冲写入的数据)
- 编码器(codec): 文本模式的编码/解码器

【边界】"它在哪里交出控制权？"
- open()系统调用: 穿越用户态→内核态→文件系统(可能触发磁盘I/O, 阻塞)
- 权限: 文件访问受OS权限控制(PermissionError)
- 路径: 分隔符依赖平台(Windows:\, Posix:/)
- 文件描述符泄漏: 未关闭的文件在GC时自动关闭, 但CPython不保证时机
- 行尾: 文本模式下, 读取时\n自动转换, 写入时\n转换为平台行尾
- encoding默认: locale.getpreferredencoding() (Windows:cp1252, Linux:UTF-8), 可能导致跨平台混乱

【内部关联】
- open() --[触发(文件操作→OS)]--> os.open (系统调用)
- f.read() --[触发(读→偏移前进)]--> f.tell()位置更新
- f --[配对(文件→资源)]--> with语句 (上下文管理器)

【薄概念合并】 C100+C101

【示例】
```python
# 文本模式写入
with open("hello.txt", "w", encoding="utf-8") as f:
    f.write("Hello 世界\n")
    f.writelines(["line1\n", "line2\n"])

# 文本模式读取
with open("hello.txt", "r", encoding="utf-8") as f:
    for line in f:              # 逐行迭代(惰性)
        print(line, end="")

# 二进制模式
with open("data.bin", "wb") as f:
    f.write(b'\x00\x01\x02\xFF')
with open("data.bin", "rb") as f:
    print(f.read())    # b'\x00\x01\x02\xff'

# 文件位置操作
with open("hello.txt", "r") as f:
    f.seek(3)          # 移动到第3个字节
    print(f.read(2))   # 读2个字符
    print(f.tell())    # 当前位置
```

---
╔═══════════════════════════════════════════════════════════╗
║  【I/O操作】标准流 stdout/stdin/stderr                     ║
║  编号: E029 | 来源: 提取清单C102+C103                     ║
╚═══════════════════════════════════════════════════════════╝

【定义】 sys.stdin/stdout/stderr是预打开的TextIOWrapper对象, 分别对应操作系统标准输入(fd 0)、标准输出(fd 1)、标准错误(fd 2)。

【结构】"它长什么样？"
- sys.stdin: TextIOWrapper包装fd 0, 可读
- sys.stdout: TextIOWrapper包装fd 1, 可写(有缓冲)
- sys.stderr: TextIOWrapper包装fd 2, 可写(无缓冲/行缓冲)
- print()默认写入sys.stdout, 可通过file参数改变
- input()从sys.stdin读取一行(移除行尾), 可显示提示文字(写入sys.stdout)
- 文本I/O vs 二进制I/O: 文本模式自动编解码(Unicode↔bytes), 二进制模式直接操作字节

【时序】"它按什么顺序动？"
- print("hello"): 调用sys.stdout.write("hello\n") → 写入内部缓冲区 → 满时/换行时/flush()时 → 系统调用write(2)
- input("> "): 提示文字→写入sys.stdout → 调用sys.stdin.readline() → 系统调用read(2) → 阻塞等待用户输入 → 返回字符串(无尾\n)
- stderr: 通常无缓冲(每write立即flush), 确保错误信息即时可见

【实体】"它的最小数据单元？"
- 文件描述符: 0(stdin), 1(stdout), 2(stderr)
- 缓冲区(buffer): TextIOWrapper内部的bytearray
- line_buffering: stdout连接到终端时行缓冲(每行flush)

【边界】"它在哪里交出控制权？"
- 重定向: sys.stdout可以被替换(如写入文件或StringIO)
- 管道: stdout → 管道 → 另一个进程的stdin (子进程通信)
- stderr与stdout分离: stderr通常是行缓冲或无缓冲, stdout在管道中变成全缓冲
- UnicodeEncodeError: 终端不支持Unicode时stdout.write可能失败

【内部关联】
- print() --[触发(输出→stdout)]--> sys.stdout.write
- input() --[触发(输入→stdin)]--> sys.stdin.readline
- sys.stdout --[配对(流→fd)]--> fd 1

【示例】
```python
import sys

# 重定向stdout
from io import StringIO
buf = StringIO()
sys.stdout = buf
print("captured")
sys.stdout = sys.__stdout__
print(buf.getvalue())  # "captured\n"

# 写入stderr (错误信息)
sys.stderr.write("Error occurred!\n")

# 读取stdin
name = input("Your name: ")
print(f"Hello, {name}")

# 二进制stdout
import sys
sys.stdout.buffer.write(b'raw bytes')
```
