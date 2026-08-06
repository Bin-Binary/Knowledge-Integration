# GLM5.2 工具调用JSON解析问题分析

## 一、现象

GLM模型从5.1升级到5.2后，工具调用功能全部失败。核心表现为模型输出的工具调用JSON参数中字符串值缺少闭合双引号，导致下游JSON解析器报错：

`
JSON parsing failed: Text: {"pipeline_id": "e3e0**", "group_id": g4c3f**"}
Error message: JSON Parse error: Unexpected identifier "g4c3f**"
`

特征：
- 非流式场景下3次调用均失败，错误一致，非偶现
- `"pipeline_id"`有引号，`group_id`缺少引号 -- 同一次输出中部分字段正确、部分异常
- GLM5.1同样场景正常

## 二、分析

### 2.1 问题指向（发散可能的模块）

针对"JSON参数字符串缺少引号"这一表象，逐层发散可能的责任模块：

| 序号 | 可能模块 | 判断依据 | 排查结论 |
|------|---------|---------|---------|
| 1 | **模型本身输出异常** | 模型升级后行为变化，可能直接生成了不带引号的非法JSON | 不完全排除，但同次输出中pipeline_id有引号而group_id没有，说明模型大概率输出了合法XML格式，问题出在XML->JSON转换环节 |
| 2 | **推理框架vllm的tool parser** | vllm负责将模型原始输出(XML格式)转换为OpenAI兼容的JSON格式，引号丢失最可能发生在此转换过程中 | **高度指向** -- XML到JSON的转换是引号增减的关键环节 |
| 3 | **推理框架vllm的reasoning parser** | reasoning parser先剥离think标签，再交给tool parser；若剥离异常可能截断后续内容 | 可能关联，但日志中group_id值本身存在只是缺引号，不像是被截断 |
| 4 | **调用方/MCP客户端的JSON反序列化** | 日志中报错发生在客户端JSON.parse | 不是根因 -- 客户端收到的JSON本身就不合法，问题在上游 |
| 5 | **GLM5.2输出格式较5.1有差异** | GLM系列使用XML-like工具调用格式(start_invoke/end_invoke + arg_key/arg_value标签)，5.2可能微调了格式细节 | **高度指向** -- 格式微调导致旧解析器匹配失败，是问题的直接触发因素 |

### 2.2 问题收敛

**聚焦模块**：vllm tool parser（GLM XML格式 -> JSON转换层）

**排查路径**：对比PR-45915的3个commit，定位旧解析器的具体缺陷。

---

**旧版解析器链路**：`Glm4MoeModelToolParser`（glm4_moe_tool_parser.py, 495行） -> 子类`Glm47MoeModelToolParser`（glm47_moe_tool_parser.py）

**关键缺陷 #1：函数名正则强制要求换行符**

``python
# 旧版 glm4_moe_tool_parser.py
self.func_detail_regex = re.compile(
    r"start_invoke([^\n]*)\n(.*)end_invoke", re.DOTALL  # 要求func_name后必须有 \n
)
``

GLM5.2输出中函数名后可能直接跟arg_key标签（无换行），正则匹配失败 -> 捕获组错位 -> 函数名或参数解析异常。

PR中的修正 -- 旧Glm47Moe子类已尝试修复此问题：
``python
# 旧版 glm47_moe_tool_parser.py (PR前)
self.func_detail_regex = re.compile(
    r"start_invoke\s*(\S+?)\s*(arg_section.*)?end_invoke", re.DOTALL  # 去掉了\n要求
)
``

但这只是修补了表面症状，核心问题在缺陷#2。

**关键缺陷 #2：_build_args_json_so_far 手动拼接JSON时对partial值只加开引号不加闭引号**

旧版在流式场景下对尚未闭合的参数值，采用"开引号无闭引号"策略：
``python
# 旧版 glm4_moe_tool_parser.py _build_args_json_so_far()
elif self._is_string_type(tool_name, partial_key):
    escaped = self._json_escape_string_content(partial_content)
    parts.append(f'{key_json}: "{escaped}')  # 只有开引号，没有闭引号！
``

当GLM5.2的输出格式差异导致正则未能正确闭合参数值（**本应complete的值被误判为partial**），手动拼接只加了`"`没有加`"`，直接产生了日志中`g4c3fae999c1c4f7785f45352869bb61a6`缺少引号的现象。

**关键缺陷 #3：func_arg_regex 非贪婪匹配在跨token边界时截断值**

``python
self.func_arg_regex = re.compile(
    r"arg_key(.*?)arg_key_end\s*arg_val(.*?)arg_val_end", re.DOTALL
)
``

`.*?`非贪婪匹配在流式场景下，当值内容尚未完整到达时可能提前截断，导致值不完整或标签错位。

---

**根因归纳**：旧版GLM tool parser采用**正则匹配 + 手动JSON字符串拼接**的架构，该架构对模型输出格式有隐式假设（如函数名后必须换行、arg_val_end标签一定在值末尾等）。GLM5.2输出格式微调后，这些假设被打破，正则匹配失败导致值被误判为partial，手动拼接时只加开引号不加闭引号，产生不合法JSON。

### 2.3 PR-45915的修复方案

PR的核心不是新增解析引擎（ParserEngine框架已存在于代码库），而是让GLM系列**从正则解析器迁移到已有的声明式状态机框架**：

| PR变更 | 文件 | 具体内容 |
|--------|------|---------|
| 新增GLM解析器配置 | `vllm/parser/glm47_moe.py`（+226行） | 定义GLM4.7/5.1/5.2的terminals、transitions、arg_converter，声明式接入ParserEngine |
| 重写tool parser | `vllm/tool_parsers/glm47_moe_tool_parser.py` | 从继承`Glm4MoeModelToolParser`（正则+手动拼接）改为继承`Glm47MoeParserToolAdapter`（适配到ParserEngine） |
| 删除旧解析器 | commit da10b7删除`glm4_moe_tool_parser.py` | 整个495行`Glm4MoeModelToolParser`删除，GLM-4.5也复用新parser |
| 更新reasoning注册 | `vllm/reasoning/__init__.py` | glm45从`DeepSeekV3ReasoningWithThinkingParser` -> `Glm47MoeParserReasoningAdapter`；新增glm47注册 |
| 更新tool parser注册 | `vllm/tool_parsers/__init__.py` | glm45指向`Glm47MoeModelToolParser`（基于新引擎） |

**新旧架构对比**：

| 维度 | 旧版（Glm4Moe + Glm47Moe） | 新版（Glm47MoeParserEngine） |
|------|---------------------------|----------------------------|
| 函数名提取 | 正则`r"start_invoke([^\n]*)\n"`，硬编码换行 | 状态机：TOOL_NAME状态 -> ARG_KEY_START转移，无格式假设 |
| 参数名值解析 | 正则`r"arg_key(.*?)arg_key_end"`非贪婪匹配 | 增量词法器 + 状态机：terminal驱动，逐字符处理 |
| XML->JSON转换 | 手动字符串拼接，partial值只加开引号 | `_glm47_arg_converter`：正则提取完整kv对 -> dict -> `json.dumps()`，始终产出合法JSON |
| 流式输出 | 重解析current_text + diff，partial值可能导致不合法JSON | ParserEngine的`_feed_args_char`状态机：追踪字符串/嵌套/转义状态，安全水位线发送 |
| 容错性 | 低 -- 正则失败则整个tool call丢失 | 高 -- 状态机逐步推进，部分匹配也能产出已确认内容 |

**新版arg_converter为何不会产生缺引号问题**：
``python
# 新版 vllm/parser/glm47_moe.py
def _glm47_arg_converter(raw_args: str, partial: bool) -> str:
    params = {}
    for match in _ARG_RE.finditer(raw_args):
        params[match.group("key").strip()] = match.group("value")
    if partial:
        remaining = _ARG_RE.sub("", raw_args)
        match = _PARTIAL_ARG_RE.search(remaining)
        if match:
            key = match.group("key").strip()
            if key:
                params[key] = match.group("value")
    return json.dumps(params, ensure_ascii=False)  # 由json.dumps保证引号闭合
``

关键：最终由`json.dumps()`统一序列化，**永远产出合法JSON**，不存在手动拼接导致的缺引号问题。

## 三、验证

### 3.1 问题复现

- **环境**：GLM5.1 -> GLM5.2升级后
- **操作**：通过MCP客户端发起流水线启动工具调用
- **现象**：3次`start_pipeline`调用均失败，group_id值缺双引号，JSON解析失败

### 3.2 修复部署

应用vllm PR-45915（commit d371488 + da10b7），重新构建并部署推理容器。

### 3.3 验证结果

- 工具调用成功，JSON参数正确解析
- group_id参数值包含正确的双引号
- PR作者测试覆盖enable_thinking x stream的4种组合，均解析正确

## 四、复盘

### 4.1 问题归类

| 维度 | 归类 |
|------|------|
| 问题类型 | 兼容性问题 -- 模型输出格式微调触发解析器隐式假设失效 |
| 影响范围 | GLM5.2及后续版本的全部工具调用功能 |
| 严重程度 | 高（核心功能不可用） |

### 4.2 经验教训

1. **正则解析脆弱性**：正则匹配对手动格式假设非常敏感（如换行符、标签间距），模型微调易导致静默解析失败。对结构化格式应优先使用声明式解析器或状态机。
2. **手动拼接JSON的危险**：手工拼接JSON字符串（特别是partial场景只加开引号）极易产出不合法JSON。应始终通过json.dumps等标准库序列化，杜绝手动拼引号。
3. **模型升级回归盲区**：模型版本升级时通常关注推理质量，对输出格式（特别是工具调用这类结构化输出）的兼容性验证容易被忽略。

### 4.3 改进措施

| 措施 | 类型 | 责任方 | 时机 |
|------|------|--------|------|
| 建立GLM模型升级回归用例（覆盖工具调用、流式、thinking模式） | 短期 | 测试 | 模型升级前 |
| 监控生产环境工具调用成功率，低于阈值触发告警 | 短期 | 运维 | 部署后 |
| 订阅vllm仓库PR，关注GLM相关变更 | 中期 | 技术负责人 | 持续 |
| 记录GLM各版本输出格式差异，形成知识库 | 长期 | 全体 | 持续 |

---

**分析方法**：问题指向（发散） -> 问题收敛 -> 根因定位  
**验证状态**：已闭环
