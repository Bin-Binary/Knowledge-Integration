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
**文档预处理阶段观察到的现象**
Ⅰ. 内容结构被破坏、即文档切片后文档内部的语义关系被破坏：
- 因果/时序关系（causes/before-after）断裂：原文以 ➔ 串联的完整因果链（每个箭头 = 一条causes边），切片后被拆成 11 个片段；每个箭头两侧的"前件→后件"对被拆到不同chunk，推理链条断裂。
  
Ⅱ. chunk_overlap的重叠修复方案的局限性：重叠区（如MoE模型 ➔ 因为太庞大 ➔ 工程师用TP+PP+EP+DP）仍是残缺的因果半句——前件的后件可能留在上一块，后件的前件可能被切到下一块，重叠只保留了字符，未保留完整的 causes 边。

```原文
## 总结
为了实现极高的智商 ➔ 科学家设计了万亿参数的 MoE 模型 ➔ 因为太庞大 ➔ 工程师用 TP+PP+EP+DP 把它拆分并克隆到全球的数据中心进行训练与部署 ➔ 为了在线上迎接高并发（QPS） ➔ 推理引擎开启 异步调度 与 连续批处理，用 PagedAttention 将显存切成固定页并消灭碎片 ➔ 为了应对企业级 RAG 和长提示词 ➔ 框架利用 Automatic Prefix Cache 跨用户共享显存块，配合 解耦部署 和 Chunked Prefill 彻底消灭长文本带来的卡顿 ➔ 最后，在芯片微观层面 ➔ 通过 Fullgraph 静态图 抹平 CPU 驱动开销，利用 MLP 权重预取 隐藏硬件搬运延迟，再套上 投机采样 让小模型盲猜，最终将大模型的蹦字速度拉到了物理极限
```
*切分后：*
```
## 总结' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='为了实现极高的智商 ➔ 科学家设计了万亿参数的 MoE 模型 ➔ 因为太庞大 ➔ 工程师用 TP+PP+EP+DP' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='MoE 模型 ➔ 因为太庞大 ➔ 工程师用 TP+PP+EP+DP 把它拆分并克隆到全球的数据中心进行训练与部署 ➔' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='➔ 为了在线上迎接高并发（QPS） ➔ 推理引擎开启 异步调度 与 连续批处理，用 PagedAttention' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='推理引擎开启 异步调度 与 连续批处理，用 PagedAttention 将显存切成固定页并消灭碎片 ➔ 为了应对企业级 RAG' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='将显存切成固定页并消灭碎片 ➔ 为了应对企业级 RAG 和长提示词 ➔ 框架利用 Automatic Prefix Cache' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='为了应对企业级 RAG 和长提示词 ➔ 框架利用 Automatic Prefix Cache 跨用户共享显存块，配合 解耦部署 和 Chunked Prefill' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='Automatic Prefix Cache 跨用户共享显存块，配合 解耦部署 和 Chunked Prefill 彻底消灭长文本带来的卡顿 ➔' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='解耦部署 和 Chunked Prefill 彻底消灭长文本带来的卡顿 ➔ 最后，在芯片微观层面 ➔ 通过 Fullgraph 静态图 抹平 CPU' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='最后，在芯片微观层面 ➔ 通过 Fullgraph 静态图 抹平 CPU 驱动开销，利用 MLP 权重预取' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='通过 Fullgraph 静态图 抹平 CPU 驱动开销，利用 MLP 权重预取 隐藏硬件搬运延迟，再套上 投机采样' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}

this item: page_content='隐藏硬件搬运延迟，再套上 投机采样 让小模型盲猜，最终将大模型的蹦字速度拉到了物理极限' metadata={'source': 'C:\\lbyier\\code_repo\\Knowledge-Integration\\AI-about\\terminology-quick-reference.md'}
```