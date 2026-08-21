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

**8. init_chat_model()在langchain的什么版本引入？**
langchain >= 0.2.8、升级命令：

```Python
pip install -U langchain langchain-core langchain-openai

```

**9. .env怎么配置结构化数据格式(例如json)？**
不建议使用 .env适配该场景

**10. oepncode的opencode.josn文件是否适用于langchain的init_chat_model()**
Ⅰ. 两者⌈Schema结构⌋完全不同，即init_chat_model()接收的是标准的独立关键字参数，或者接收由对应大模型厂商官方包（如langchain-openai、langchain-anthropic）定义的特定参数格式
```Python
@overload
def init_chat_model(  # type: ignore[overload-overlap]
    model: str,
    *,
    model_provider: Optional[str] = None,
    configurable_fields: Literal[None] = None,
    config_prefix: Optional[str] = None,
    **kwargs: Any,
) -> BaseChatModel: ...
```

**11. 怎么提取异构⌈Schema结构⌋的交集**
Ⅰ. Pydantic有⌈忽略未知字段⌋策略、即从 .json/...等数据源提取Pydantic模型定义的数据
```Python
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from langchain.chat_models import init_chat_model

# 定义Pydantic模型，只提取OpenCode中LangChain关心的字段
class OpenCodeModelConfig(BaseModel):
    # 核心：使用extra="ignore" 自动忽略 opencode.json 里的快捷键、UI 等杂七杂八的配置
    model_config = ConfigDict(extra="ignore")
    
    # 提取默认模型名称 (例如 "anthropic/claude-sonnet-4-5")
    model_name: str = Field(..., alias="model")

```

**12. Path读取Win环境路径：unicode error**
Ⅰ. 反斜杠 \ 是转义字符, 即代表一个8位的Unicode字符转义序列
Ⅱ. r是原始字符串（Raw String）的缩写，即r后的字符串会被当作普通文本处理
```Python

# 原
config_path = config_path or Path("C:\Users\xxx\config\opencode\opencode.json")

# 改
config_path = config_path or Path(r"C:\Users\xxx\config\opencode\opencode.json")

```

**13. 对于LiteLLM为什么OpenCode支持，而LangChain却不纳入核心**
Ⅰ. LiteLLM的定位是⌈模型网关⌋、属于**模型调用的提供者**，即**作为代理来路由多模型**、对外提供请求路由、成本统计、负载均衡等能力。

Ⅱ. OpenCode定位是一个⌈终端AI编程工具/客户端⌋、属于**模型调用的消费者**。自身只维护一套provider接入层（OpenAI 兼容协议为主），接入LiteLLM网关几乎零成本。

Ⅲ. LangChain定位是⌈企业级的底层开发框架⌋、同在模型调用的消费侧。但对provider的接入处理策略不同：LangChain选择原生直连各供应商。

从接入模型成本来看，OpenCode自身没有模型抽象层，逐家自建100+集成成本过高，委托网关是最优解；
而LangChain的BaseChatModel抽象 + partner packages（langchain-openai、langchain-anthropic…）降低集成成本。它虽也能消费LiteLLM网关（如ChatLiteLLM/ OpenAI兼容端点指向网关），但为避免额外一跳的延迟、故障点以及功能被网关截断（流式、工具调用、结构化输出保真），所以不纳入核心。

**14. Agent的记忆与业务落地：修改OpenCode还是基于LangChain自研？**
Ⅰ. 记忆是⌈生物/机器编码、存储、检索信息的能力

Ⅱ. 记忆的一个重要功能是帮助确保Agent的**行为符合当前情景（上下文）、并根据经验(短期、长期记忆)进行调整**。[引用](https://www.psychologytoday.com/us/basics/memory/how-memory-works)

Ⅲ. 记忆是Agent**理解业务**的基础设施

将opencode作为langchain的一个工具节点负责执行，litellm进行模型路由

**15. 如何验证RAG效果**
Ⅰ.POC
从最简架构和默认参数开始，先跑通流程拿到**基线数据**，再开始有针对性的优化。

**评估embedding的指标是什么**
[参考](https://zilliz.com.cn/blog/Vector-Database-POC-Guide-Embedding-Model-Selection)

**16. LangChain的向量存储是什么？**
Ⅰ. 指集成层？集成了什么？

**17.向量模型输出的是什么？存在哪里？**
**18.向量模型有哪些？怎么选?**
**19.模型不可用时，降级机制怎么实现**
**20.LangChain的embedding源怎么配置**
**21.RAG的效果受文档质量影响，那怎么反向通过AI生成好的文档**
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

**22.好的文档的评估指标是什么**
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

**23. pytest的测试命令**
1. 基础运行命令：
- 运行所有测试：直接在项目根目录下输入 pytest
- 指定文件运行：pytest test_login.py
- 指定目录运行：pytest tests/
- 指定函数运行：pytest test_login.py::test_user_login
- 指定类与方法：pytest test_login.py::TestClass::test_method

2. 常用控制台输出参数
- 详细输出模式：pytest -v（显示每个测试用例的详细结果）
- 简略输出模式：pytest -q（只显示关键结果，减少干扰）
- 打印捕获的标准输出：pytest -s（允许在测试时看到代码中的 print() 信息）
- 显示最慢的N个用例：pytest --durations=N（排查测试性能瓶颈）

3. 执行控制与筛选
- 按关键字筛选：pytest -k "login or logout"（运行名字包含相关词的用例）
- 按标签/标记筛选：pytest -m smoke（只运行被 @pytest.mark.smoke 标记的用例）遇
- 错即停：pytest -x（只要有一个用例失败，立即停止整个测试任务）
- 限制失败次数：pytest --maxfail=2（失败 2 次后停止测试）
- 失败重跑：pytest --lf（last failed，只运行上一次失败的用例）
- 从失败处开始：pytest --ff（failed first，先运行上次失败的，再运行其他的）

4. 调试与排查
- 失败时进入PDB调试：pytest --pdb（用例失败时自动断点，进入 Python 调试器）
- 查看已注册的 Markers：pytest --markers
- 查看已可用的 Fixtures：pytest --fixtures

**24. embedding模型的作用是什么？**
**25. 用户的原始问题会被embedding模型执行什么操作？处理后的内容是什么？**
**26. 原始文档会被embedding模型执行什么操作？处理后的内容是什么？**
**27. Pytest中的方法的名称有什么要求？**
Ⅰ.  Pytest会在指定的目录（未指定则默认为当前目录）下，按照「文件 -> 类 -> 函数/方法」 的层级，根据特定的命名规则自动寻找并执行测试
Ⅱ.  识别test_开头和_test结尾的**py文件**
Ⅲ. **类名**必须以 Test 开头，且不能有 __init__ 方法
Ⅳ. **函数名**必须以 test_ 开头
Ⅴ. **路径搜索优先级**, 显式指定（命令行写了路径（如 pytest tests/）） > 根目录配置文件（从当前目录开始，寻找pytest.ini、pyproject.toml或setup.cfg 等配置文件，并读取其中定义的 testpaths 路径） > 默认当前目录

**28. TypedDict和Pydantic区别是什么**
~~Ⅰ. TypedDict是Python**类型提示（Type Hints）字典**的一种结构，会被静态类型检查工具拦截检查~~
~~Ⅱ. TypedDict在代码运行时仍然是一个普通的Python普通字典~~

**29. LangChain中的消息合并机制有哪些？convert_to_messages()采取的是什么方式？**

**30. langchain_core只接受PromptValue/str/BaseMessage列表**
Ⅰ.`BaseChatModel.invoke()`及`_convert_input()`定义在langchain_core的抽象基类中，所有`BaseChatModel`子类(ChatOpenAI/ChatAnthropic/ChatGoogleGenerativeAI等)共用同一入参校验路径

Ⅱ.顶层入参契约是`LanguageModelInput = Union[PromptValue, str, Sequence[MessageLikeRepresentation]]`,裸dict不在其列，但列表内部的dict会被`convert_to_messages()`逐元素转成BaseMessage

Ⅲ.各厂商(partner包)只负责消息下游序列化为自家API格式，不参与该层入参类型校验

langchain_core在抽象基类层统一约束"PromptValue/str/BaseMessage列表"的入参契约，各厂商子类只做下游消息序列化而不改变该校验，因此该结论可跨模型厂商泛化使用

**31. Annotated是什么？**
Ⅰ.是Python类型提示(Type Hints)系统中的一个**通用元数据装饰器**——更准确说是**特殊形式(special form)类型构造器**，语句`Annotated[T, meta1, meta2, ...]`在类型T上附着任意元数据形成新类型，但**不改变T本身的类型语义**

Ⅱ."通用"指不依赖任何特定框架，各库均可自定义并读取元数据（如pydantic的`Field`/`AfterValidator`、FastAPI的`Query`/`Path`）；同时运行时`isinstance(x, T)`仍按原类型T判断

Ⅲ.元数据是任意对象的附加信息（字符串/枚举/函数/方法均可），可传多个，存于类型对象的`__metadata__`属性；它不参与类型约束，仅在消费方运行时按需读取

Ⅳ.装饰器——"装饰"体现为对类型做"包装+附加"，而非函数/类的`@装饰器`语法；读取时`get_type_hints()`默认剥离元数据，需`include_extras=True`，或直接访问`Annotated[T, meta].__metadata__`

Annotated的核心应用场景：数据校验(pydantic)、依赖注入(FastAPI)、运行时读取元数据(自省)、类型化文档；**本质是"类型T+附着信息"的单一声明点**，让类型系统与业务约束在同一处表达

**LangGraph示例**：`messages: Annotated[list[AnyMessage], add_messages]`中`T=list[AnyMessage]`、元数据为reducer函数`add_messages`——LangGraph通过`include_extras`读取`__metadata__`拿到合并策略(按消息id去重后追加)，即"类型声明+状态更新策略"绑定于同一声明点，属核心点Ⅲ的直接体现
