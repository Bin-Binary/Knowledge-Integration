# 推理基础原理 (Inference Fundamentals)

> 大模型推理的核心机制：Token 计量、Prefill/Decode 生命周期、自注意力与 KV Cache。

---

## 推理

> Ⅰ  推理 = 前向传播（FP），不涉及反向传播（BP）
> Ⅱ  同一输入 + 同一权重 + 同一解码参数 → 输出完全一致
> Ⅲ  解码策略（Top-p/Temperature）是唯一的随机来源

---

## 词元 (Token)

> Ⅰ  模型无法理解原始文本，输入输出全部映射为整数 Token ID
> Ⅱ  一个中文汉字 ≈ 1~2 个 Token，一个英文单词 ≈ 1~3 个 Token
> Ⅲ  Token 数量决定计算量（Prefill $\mathcal{O}(L^2)$）和显存（KV Cache $\propto L$），是推理成本的核心计量单位

---

## 推理请求的完整生命周期（Decoder-only 架构）

> 一次请求 = 1 次 Prefill 阶段 + N 次 Decode 阶段

> 注：本文档以 Decoder-only 架构（如 GPT、LLaMA）为基准。对于 Encoder-Decoder 架构（如 T5），Prefill 包含 Encoder 处理输入 + Decoder 处理已生成部分

### Prefill 阶段（初始化）

> 一次性处理完整提示词，填充 KV Cache，为后续自回归生成做准备

### Decode 阶段（自回归生成循环）

> Ⅰ  每个词元都需要经过模型的一次完整前向传播
> Ⅱ  新生成的词元会被追加到输入序列末尾，作为下一步的输入，循环往复
> Ⅲ  生成 N 个词元的回复 = N 次 Decode 前向传播（投机解码场景除外）

---

### 模型内部的一次前向传播

> 输出候选词的概率分布、根据策略选取新词并将其添加到新的上下文序列

> Ⅰ  上一层的隐藏状态（Hidden State）作为本层输入
> Ⅱ  经过自注意力和 FFN 两层线性变换后输出新的隐藏状态
> Ⅲ  最后一层隐藏状态经 LM Head 映射为词表概率分布，由解码策略选取最终输出词元

### 单个 Transformer 层内部

> 主要通过自注意力机制、前馈神经网络两个线性层，生成新的隐藏状态

> Ⅰ  自注意力机制（SA）跨词元交换信息，输出每个词元"看到"全文上下文后的表示
> Ⅱ  前馈神经网络（FFN）单词元独立做非线性变换（升维→激活→降维），提取深层语义
> Ⅲ  每层的输入和输出都是形状相同的隐藏状态矩阵，层与层之间形成残差连接

### 自注意力机制 (Self-Attention)

> Ⅰ  三步流程：Q × K^T 得分数矩阵 → Softmax 归一化为权重 → 权重 × V 得加权输出
> Ⅱ  核心作用：让每个词元"看到"序列中所有其他词元，捕获长距离依赖关系
> Ⅲ  计算复杂度 $\mathcal{O}(L^2)$：序列长度翻倍计算量翻 4 倍，是长文本 Prefill 耗时的根本原因

| 步骤 | 操作 | 产出 |
| :--- | :--- | :--- |
| 1 | Q × K^T（点积） | 注意力分数矩阵 |
| 2 | Softmax（归一化） | 注意力权重（0~1） |
| 3 | 权重 × V（加权和） | 更新后隐藏状态 |

---

## KV Cache

> 缓存 Decode 阶段已计算过的 K、V 矩阵，避免重复计算

> Ⅰ  每步 Decode 只需计算新 Token 的 Q，K 和 V 从缓存直接读取

> Ⅱ  128k 序列可达数十 GB（显存大头）

> Ⅲ  GQA/MQA 通过减少 KV 头数（$H_{kv} < H_q$）等比压缩 KV Cache，是长上下文部署的标配

单次请求 KV Cache 大小 = $2 \times L \times L_{\text{layers}} \times H_{kv} \times d_{\text{head}} \times B \times \text{dtype\_size}$

---

## 相关概念

| 术语 | 详见 |
|------|------|
| Compute-Bound vs Memory-Bound | [GPU-Memory-Hierarchy.md](../../hardware/docs/GPU-Memory-Hierarchy.md) |
| GPU 显存层次 (SRAM→HBM→DRAM→SSD) | [GPU-Memory-Hierarchy.md](../../hardware/docs/GPU-Memory-Hierarchy.md) |
| W8A8 量化、PD 分离、投机采样 | [../../terminology-quick-reference.md](../../terminology-quick-reference.md) |

---

## 🔬 实际环境观测

> 以下为理论概念在真实生产环境中的可观测方法与快照参考。操作过程详见 [LLM-Platform-Practice.md](../../platform/docs/LLM-Platform-Practice.md)

### 观测 1：Token 计量与推理延迟（对应"词元"节）

**观测方法**：通过 LiteLLM API 请求返回的 `usage` 字段直接观测 Token 计量

**环境快照**：
```json
{
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 50,
    "total_tokens": 65
  }
}
```
> 观测点：每次 API 响应的 `usage.total_tokens` 即为本次请求消耗的 Token 总量，对应推理成本计量

### 观测 2：KV Cache 占用率（对应"KV cache"节）

**观测方法**：查询 vLLM metrics 端点的 `vllm:kv_cache_usage_ratio` 指标

**环境快照**（上海绿区 A3，空闲态）：
```
vllm:kv_cache_usage_ratio 0.0
vllm:num_requests_running 0
vllm:gauge_num_tokens_in_kv_cache 0
```
> 观测点：KV Cache ratio 从 0 开始增长，随并发请求增加而上升；接近 1.0 时面临 OOM 风险

**环境快照**（苏州黄区 A2-112 GLM-V5.2，PD 分离场景异常时）：
```
External prefix cache hit rate: 100.0%    ← KV 全部"命中"（实为 PD 传输过来的 KV）
```
> 异常观测：当 KV Cache 传输失败时，D 节点可能使用错误/空 KV 继续推理，导致乱码（详见 [GLM-5.2-W8A8-Output-Garbled.md](../faq/GLM-5.2-W8A8-Output-Garbled.md)）

---

*快照更新时间：2026-08-06*
