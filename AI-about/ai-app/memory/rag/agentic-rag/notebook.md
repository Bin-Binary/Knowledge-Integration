# Agentic RAG
![工作流程图](./references/agentic-rag-workflow.png)

## FAQ
**1. load_dotenv()在三方库导入后执行导致环境变量获取失败**
Ⅰ. 某些三方库（如 langchain_community 的文档加载器 WebBaseLoader 等）导入时会进行环境变量校验

**2. 倒排索引的⌈倒排⌋如何理解**
Ⅰ. 逻辑颠倒，即正排索引由文档找词、而倒排索引是由词找文档

**3. RAG中召回的是什么？**
Ⅰ. 召回出来的核心内容是分割后的⌈文档文本块（Chunks）⌋
Ⅱ. 业务形式：召回的是⌈“半结构化/多模态知识”⌋“参考资料”
Ⅲ. 数据形式：召回的是⌈以结构化对象为载体，封装文本内容与多维元数据⌋“原始文本 + 元数据”

**4. 编码和建立向量索引的作用对象是什么**
Ⅰ. 编码和建立向量索引阶段的作用对象是Chunks（分块）

**5. 分块大小按 ⌈字符⌋ 或者 ⌈token计数⌋的区别和影响是什么**
Ⅰ. 两种计数方式的本质区别在于计量单位不同，字符按可见字符计、token按模型词表子词切分计，同一段文本的字符数≠token数（如1个汉字=1字符但可能=2-3个tokens）

Ⅱ. 分块大小直接影响上下文窗口利用率，即同样的chunk_size值，字符计数占用更多tokens，可能超出模型窗口上限导致截断或调用失败

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

text = "人工智能与大语言模型"

print(f"字符数: {len(text)}")  # 10

enc = tiktoken.get_encoding("cl100k_base")

print(f"token数: {len(enc.encode(text))}")  # 通常 > 10

splitter = RecursiveCharacterTextSplitter(chunk_size=5, chunk_overlap=0)
print(f"按字符(chunk_size=5)分块: {splitter.split_text(text)}")
# ['人工智能与大', '语言模型']

splitter_tik = RecursiveCharacterTextSplitter.from_tiktoken_encoder(chunk_size=5, chunk_overlap=0)
print(f"按token(chunk_size=5)分块: {splitter_tik.split_text(text)}")
# 实际分块数更少，因为10字符文本的token数可能仅6-8
```

**6. 文档内容编码和召回工具设计为装饰器还是参数传递**
装饰器调试困难（中间结果不可见）、嵌套地狱、不适合RAG这种需要多分支场景

**7. Embedding模型只需第一次运行时下载？网络原因导致模型下载失败怎么处理？**
Ⅰ. 模型只需首次下载、后续运行直接从缓存加载（~/.cache/huggingface/hub/（Windows: C:\Users\用户名\.cache\huggingface\hub\）

Ⅱ. 降级处理，配置HF国内镜像 > 手动离线下载模型 > 无需网络的纯本地embedding

```Python
# FakeEmbeddings生成随机向量，召回无语义相关性，仅用于验证流程，不可用于生产
from langchain_community.embeddings import FakeEmbeddings
embedding = FakeEmbeddings(size=384)  # 随机向量，仅用于调试流程
```
