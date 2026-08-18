# 笔记
记录Python相关笔记


---
## 一些未验证的想法

---
## FAQ
**1.LangChain的TextLoader加载win环境的文件报错**
```Python
# 原写法
local_docs = [TextLoader(_local_paths).load() for _local_paths in _LOCAL_PATHS]

# 修复写法
local_docs = [TextLoader(_local_paths, encoding="utf-8").load() for _local_paths in _LOCAL_PATHS]
```
文件编码和加载器的解码格式不匹配导致。Windows下TextLoader默认用GBK编码，而文件编码是UTF-8。WIN环境下的编码是GBK编码无法读取UTF-8文件
---
