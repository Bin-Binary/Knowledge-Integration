# Agentic RAG
RAG是构建有⌈记忆⌋的Agent的一种解决方案。
从**结构**上解决*LLM上下文窗口有限*的问题（选择裁剪与当前上下文相似度最高的片段进行相似度召回）、从**时序**上解决*LLM知识时效性不足*的问题(接入最新数据源)、
从**依赖关系**上解决*LLM领域/私有知识缺失* 及 降低*LLM事实性幻觉*、从**合规/安全**上解决*LLM的生成不可追溯&不可解释*的问题

弥补了"上下文窗口管理"、"Scracthpad"两种记忆方案在构建可溯源的长期显式⌈记忆⌋的短板

## 目标
1. 获取并预处理将用于检索的文档。
2. 为这些文档建立索引以支持语义搜索，并为代理创建一个检索工具。
3. 构建一个代理式RAG系统，能够决定何时使用该检索工具。

[流程视图]{}

## 工程落地
代码实现落地, 参考链接：https://github.com/langchain-ai/langgraph/blob/23961cff61a42b52525f3b20b4094d8d2fba1744/docs/docs/tutorials/rag/langgraph_agentic_rag.md

### 设置
下载必要的依赖
```
pip install -U --quiet langgraph "langchain[openai]" langchain-community langchain-text-splitters
```

### 预处理文档
```Python
from langchain_community.document_loaders import WebBaseLoader
# 获取文档
urls = [
    "https://lilianweng.github.io/posts/2024-11-28-reward-hacking/",
    "https://lilianweng.github.io/posts/2024-07-07-hallucination/",
    "https://lilianweng.github.io/posts/2024-04-12-diffusion-video/",
]

docs = [WebBaseLoader(url).load() for url in urls]

docs[0][0].page_content.strip()[:1000] 

# 文档切片、用于索引到向量数据库
from langchain_text_splitters import RecursiveCharacterTextSplitter

docs_list = [item for sublist in docs for item in sublist]

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=100, chunk_overlap=50
)
doc_splits = text_splitter.split_documents(docs_list)
```
