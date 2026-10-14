---
name: framenet-pipeline
description: 当用户要求对文本进行FrameNet框架激活、语义框架标注、框架语义角色标注时使用本技能。支持单句和文档级分析。关键词：框架分析、FrameNet 标注、语义框架、frame annotation、semantic role labeling via FrameNet、文档级框架分析
---

## 依赖

- Python 3.9+
- nltk + framenet_v17 语料库（`D:\nltk_data\corpora\framenet_v17`）

## 架构

```
输入（单句 or 文档）
  │
  ├── 单句模式
  │     │
  │     ▼
  │   Stage 1 - framenet_retriever.py（确定性召回）
  │     ├── 分词 + 功能词过滤
  │     ├── FrameNet LU 查询
  │     ├── 词干回退
  │     └── 输出: {word, candidates: [{frame, definition, core_FE}]}
  │     │
  │     ▼
  │   Stage 2 - frame_selector.py（LLM 语义消歧）
  │     ├── 构建 prompt（候选框架 + 上下文）
  │     ├── LLM 上下文消歧
  │     ├── 零命中词推理
  │     ├── FE 绑定
  │     └── 输出: {word, selected_frame, confidence, fe_binding}
  │     │
  │     ▼
  │   合并输出 - pipeline.py (merge_results)
  │     ├── 框架索引（frame → [words]）
  │     ├── 置信度分布统计
  │     └── JSON 结构化结果
  │
  └── 文档模式
        │
        ▼
      document_slicer.py（文档切片 + 启发式分类）
        ├── 按句切分
        ├── 分类: nl_description(high) / nl_action(medium) / code_syntax(low) / impl_detail(skip)
        ├── 过滤低价值片段
        └── 输出: [{id, text, category, value, source_location}]
        │
        ▼
      逐片段执行 Stage 1 + Stage 2
        ├── 每片段独立 framenet_retriever → frame_selector
        ├── 片段上下文注入（前/后片段、文档主题、位置信息）
        └── 每片段输出: {fragment_id, annotations}
        │
        ▼
      result_merger.py（跨片段合并 + 框架关系发现）
        ├── 全局框架索引（frame → {trigger_words, fragments, max_confidence}）
        ├── FrameNet frame_relations 查询（直接关系）
        ├── 继承链追溯（Inheritance/Using/Inchoative_of/Subframe → 共同祖先）
        ├── FE 映射提取
        └── 输出: {global_frame_index, frame_relations, fragment_annotations, statistics}
```

## 使用方式

### 方式一：单句分析（两步执行）

```bash
# Step 1: 召回 + 生成 prompt
python pipeline.py "Your text here" --prompt-only

# 将输出 prompt 传给 LLM，获取响应后保存为 llm_response.txt

# Step 2: 合并 LLM 选择结果 → 输出 markdown（默认）
python pipeline.py "Your text here" --llm-response llm_response.txt -o result.md

# 或输出 JSON
python pipeline.py "Your text here" --llm-response llm_response.txt -o result.json -f json
```

### 方式二：单句分析（编程调用）

```python
from pipeline import run_pipeline, stage1_retrieve, stage2_build_prompt, stage2_parse_response, merge_results, format_result

retrieval = stage1_retrieve("Lists are mutable sequences, typically used to store collections of homogeneous items")
prompt = stage2_build_prompt(retrieval)
# ... send prompt to LLM, get response_text ...
selection = stage2_parse_response(response_text)
result = merge_results(retrieval, selection)

# 输出 markdown
print(format_result(result))
```

### 方式三：文档级分析

```python
from pipeline import run_pipeline_document, format_result

# 带 LLM 调用函数
def my_llm_call(prompt: str) -> str:
    # 调用你的 LLM API
    return llm_api.generate(prompt)

result = run_pipeline_document(
    text=document_text,
    llm_call_fn=my_llm_call,
    skip_low=True,          # 跳过低价值片段
    min_value="medium",     # 最低分析价值
    doc_name="Python List", # 文档主题
    output_path="result.md" # 输出 markdown（也支持 .json + output_format="json"）
)

# 不带 LLM（仅生成 prompts，稍后手动发送）
result = run_pipeline_document(text=document_text, doc_name="Python List")
prompts = result["fragment_prompts"]  # dict[fragment_id -> prompt]

# 手动格式化为 markdown
print(format_result(result))
```

### 方式四：独立使用切片器 / 合并器

```python
from document_slicer import slice_document
from result_merger import merge_fragment_results, query_frame_relations

# 切片
sliced = slice_document(text, doc_name="My Doc")
print(sliced["stats"])  # {total, high, medium, low, skip}

# 框架关系查询
rels = query_frame_relations(["Storing", "Containing", "Sequence"])
# 返回: [{source, target, relation_type, framenet_relation, direction, fe_mappings}]
```

## 输出格式

**默认输出为 Markdown**（`output_format="md"`）。也可选 JSON（`output_format="json"`）。

### 单句 Markdown 输出

```markdown
# FrameNet Semantic Annotation

## Input

> Lists are mutable sequences, typically used to store collections of homogeneous items

## Statistics

| Metric | Value |
|--------|-------|
| Total content words | 9 |
| Annotated words | 9 |
| High confidence | 5 |
| Medium confidence | 2 |
| Low confidence | 2 |
| No match | 0 |
| FrameNet LU matched | 8 |
| LLM inferred | 1 |
| Unmatched | 0 |

## Annotations

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| store | Storing | [+++] high | FN | Agent, Theme, Location | Agent→implied; Theme→collections; Location→lists |
| collections | Aggregate | [+++] high | FN | Individuals, Aggregate | Individuals→items; Aggregate→collections |
| ... | ... | ... | ... | ... | ... |

## Frame Index

| Frame | Trigger Words |
|-------|--------------|
| Storing | store |
| Aggregate | collections |
| ... | ... |

<!-- generated: 2026-10-14T... -->
```

### 文档级 Markdown 输出

```markdown
# FrameNet Document Annotation: Python List

## Document Slicing

| Metric | Value |
|--------|-------|
| Total fragments | 15 |
| Eligible for analysis | 9 |
| Skipped | 6 |

## Overall Statistics

| Metric | Value |
|--------|-------|
| Processed fragments | 9 |
| Unique frames | 15 |
| Frame relations found | 16 |
| ... | ... |

## Global Frame Index

| Frame | Triggers | Fragments | Conf | Source | Core FEs |
|-------|----------|-----------|------|--------|----------|
| Storing | store | F01 | [+++] high | FN | Agent, Theme, Location |
| Ordering | sorts, sorted | F09, F14 | [+++] high | FN | Ordered_entity, Ordering_predicate |
| ... | ... | ... | ... | ... | ... |

## Cross-Frame Relations

| Source | Target | Relation | Direction | Detail |
|--------|--------|----------|-----------|--------|
| Aggregate | Using | hierarchical | sibling | common ancestor: Event |
| Storing | Creating | hierarchical | sibling | common ancestor: Transitive_action |
| ... | ... | ... | ... | ... |

## Fragment Annotations

### F01

> Lists are mutable sequences, typically used to store collections of homogeneous items

| Word | Frame | Conf | Source | Core FEs | FE Binding |
|------|-------|------|--------|----------|------------|
| ... | ... | ... | ... | ... | ... |

<!-- generated: 2026-10-14T... -->
```

### 置信度图标

| 置信度 | 图标 | 含义 |
|--------|------|------|
| high | [+++] | FrameNet LU 匹配 + LLM 确认 |
| medium | [++] | FrameNet LU 匹配但 LLM 不确定 |
| low | [+] | 候选框架弱匹配或 LLM 推断 |
| none | [-] | 未找到任何框架 |

## 关键设计决策

| 决策 | 理由 |
|------|------|
| 功能词预过滤 | "of"/"to" 在 FrameNet 中命中数百个框架，噪声远大于信号 |
| 词干回退 | FrameNet v17 收录不完整，"sequences"→"sequence" 可命中 |
| LLM 只在候选集内选择 | 防止幻觉，保证框架名称来自 FrameNet 官方 |
| 零命中词单独处理 | LLM 推理框架标记 `source: llm_inference`，置信度不超过 medium |
| FE 绑定要求 | 促使 LLM 做深度语义分析而非浅层标签匹配 |
| 文档切片启发式分类 | 代码签名/实现细节低价值，NL 描述高价值；节省 LLM 调用 |
| 片段上下文注入 | 让 LLM 知道文档主题和前后片段，提升消歧质量 |
| FrameNet frame_relations 查询 | 利用 FrameNet 内置关系（非 LLM 推断），确保关系可溯源 |
| 继承链追溯共祖 | 无直接关系的框架通过 Inheritance/Using/Subframe 链找共同祖先 |

## 片段分类规则

| 类别 | 价值 | 匹配条件 | 示例 |
|------|------|---------|------|
| nl_description | high | 自然语言描述句，无代码特征 | "Lists are mutable sequences..." |
| nl_action | medium | 含动作动词，描述操作 | "This method sorts the list in place" |
| code_syntax | low | 代码签名、函数声明 | "sort(*, key=None, reverse=False)" |
| impl_detail | skip | 实现细节标记 | "CPython implementation detail:..." |

## 框架关系类型

| FrameNet 关系 | 语义类型 | 描述 |
|--------------|---------|------|
| Inheritance | hierarchical | 子框架继承父框架的 FE 语义 |
| Using | hierarchical | 子框架使用父框架的分析框架 |
| Subframe | compositional | 子框架是复合框架的事件阶段 |
| Causative_of | causal | 因果关系 |
| Precedes | temporal | 时序关系 |
| Perspective_on | associative | 视角关系 |
| Inchoative_of | hierarchical | 状态变化关系 |
| via_common_ancestor | hierarchical | 本管道发现的共同祖先关系 |

## 文件结构

```
framenet-pipeline/
├── src/
│   ├── framenet_retriever.py    # Stage 1: FrameNet LU 检索
│   ├── frame_selector.py        # Stage 2: prompt 构建 + 响应解析
│   ├── pipeline.py              # 编排器: 单句 + 文档级流水线 + md/json 输出
│   ├── document_slicer.py       # 文档切片 + 启发式分类
│   ├── result_merger.py         # 跨片段合并 + FrameNet 关系发现
│   └── md_formatter.py          # 内部 dict → Markdown 格式化
├── prompts/
│   └── frame_selection.md       # LLM 框架选择 prompt 模板（含片段上下文）
├── examples/
│   ├── run_example.py           # 单句端到端示例
│   └── run_document_example.py  # 文档级端到端示例
└── SKILL.md                     # 本文件
```

## NLTK FrameNet 数据路径

```
D:\nltk_data\corpora\framenet_v17
├── 1221 frames
├── 2070 frame relations (6+ types)
└── FE relations per frame_relation
```
