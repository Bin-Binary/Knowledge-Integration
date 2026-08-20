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
-----------------分割线-----------------
**如何验证RAG效果**
Ⅰ.POC
从最简架构和默认参数开始，先跑通流程拿到**基线数据**，再开始有针对性的优化。

**评估embedding的指标是什么**
[参考](https://zilliz.com.cn/blog/Vector-Database-POC-Guide-Embedding-Model-Selection)

**LangChain的向量存储是什么？**
Ⅰ. 指集成层？集成了什么？
**向量模型输出的是什么？存在哪里？**
**向量模型有哪些？怎么选?**
**模型不可用时，降级机制怎么实现**
**LangChain的embedding源怎么配置**
**RAG的效果受文档质量影响，那怎么反向通过AI生成好的文档**
以下为AI参考回答
```
不是"AI 凭空造文档"，而是用 AI 做清洗、结构化、增强：
1. 清洗：去噪、去 HTML、合并断行、纠正 OCR/格式错误
2. 结构化：加标题层级、表格化、提取元数据（来源/日期/主题）
3. 语义补全：把"这里/前文"等指代替换为明确实体
4. chunk 友好：按语义边界切分，保证每个 chunk 自包含、可独立理解
5. 生成 Q&A 对：为每段生成"问题-答案"对，做 query 侧增强
6. 摘要/关键词标注：为 chunk 加摘要字段，辅助检索排序
```

**好的文档的评估指标是什么**
Ⅰ.
Ⅱ.

以下为AI参考回答
```
- 检索侧（找得准不准）：Recall、Precision、Hit Rate、MRR、nDCG
- 生成侧（答得好不好）：Faithfulness（忠实度）、Answer Relevancy（答案相关性）、Context Relevancy（上下文相关性）— 常用 RAGAS 框架统一评测
- 文档本身：结构完整性、chunk 语义自包含度、指代消解率、信息密度（无冗余/无歧义）、可追溯性
```

以下为AI评估一段内容是否为好的文档
```
客观辩证评估：这段属于"有价值的草稿"，但还不是合格的文档段落，直接作为 RAG chunk 会降低检索与生成质量。
优点（保留价值）
- 有分类意识：明确用"语义记忆"这个抽象层次，并给出"是什么""信息量→博学"的洞察，认知框架是对的
- 有通俗类比（"信息量越大 AI 越博学"），降低了理解门槛
- 列表式结构，比纯散文更利于机器切分与检索
问题（阻碍成为"好文档"）
1. 结构断裂/未闭合：标题是"记忆分类"，但只写了语义记忆就戛然而止，缺情节记忆、程序记忆等并列项 → chunk 不完整、不满足"自包含"
2. 占位符残留：语义记忆描述xxx"是什么" 中的 xxx 未替换，属于未完成内容，会直接污染检索结果
3. 符号错配：⌈知识⌋ 括号不配对（应为「知识」或"知识"），全/半角标点混用（⌈知识⌋、空格"事实、概念"）
4. 序号层级混乱：1. 与 Ⅰ. Ⅱ. Ⅲ. 混用，Ⅱ、Ⅲ 本质是"知识"的展开，却挂在"信息量"（Ⅰ）的平级下，逻辑层级错乱
5. 指代与冗余：Ⅱ 定义"知识"，Ⅲ 又回到"语义记忆"，中间缺过渡，信息密度被稀释；⌈泛化表现⌋ 一词突兀未解释
结论
- 作为草稿/素材：合格，有可提炼的观点
- 作为RAG 文档段落：不合格，违反"结构完整、chunk 自包含、无指代/占位符、格式规范"四条核心标准
修改方向（示例）
## 记忆分类：语义记忆
语义记忆是长期积累的知识，用于解释 Agent 输入"是什么"。
- 核心指标：信息量（信息量越大，AI 越博学）
- 知识：事实、概念的含义及其关联，是构成其他记忆的基本单位
- 语义记忆可描述无直接关联的事实与意义（如俚语含义）
补全其余记忆类型后，方可作为合格段落。
```