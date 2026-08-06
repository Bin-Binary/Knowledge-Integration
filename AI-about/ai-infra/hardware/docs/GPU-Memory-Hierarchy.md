# GPU 显存层次 (GPU Memory Hierarchy)

> 推理硬件的四级存储架构：SRAM → HBM → DRAM → SSD，理解显存层次是推理部署与性能优化的物理基础。

---

## 四级存储层次

GPU 拥有四级存储层次，从上到下容量递增、带宽递减：

| 层级 | 典型容量 | 典型带宽 | 用途 |
| :--- | :--- | :--- | :--- |
| **SRAM**（片上缓存） | ~20-50 MB | ~数十 TB/s | 计算核心直接读写，执行矩阵乘法 |
| **HBM**（高带宽显存） | 40-80 GB | ~1-2 TB/s | 存放模型权重、KV Cache、激活值 |
| **CPU DRAM**（主机内存） | 数百 GB ~ TB | ~100 GB/s | 存放不常用的 KV Cache（UCM 温/冷层） |
| **SSD**（固态硬盘） | 数 TB | ~几 GB/s | 持久化 KV Cache 冷数据 |

> Ⅰ  所有数据必须从 HBM 搬运到 SRAM 才能被计算核心执行矩阵乘——这是推理延迟的核心瓶颈

> Ⅱ  Decode 是 Memory-Bound（每次搬全量权重，算一点点）；Prefill 是 Compute-Bound（算整个长序列注意力，搬运时间被掩盖）

> Ⅲ  三级异构存储（HBM ↔ DRAM ↔ SSD）让 KV Cache 突破单卡显存物理上限，是长上下文高并发推理的关键支撑

---

## NPU 算力参数（A2 推理卡）

| 指标 | 数值 | 说明 |
|:---|:---|:---|
| INT8 算力 | 560 TOPS | 8 位整数下每秒 560 万亿次运算 |
| FP16 算力 | 280 TFLOPS | 16 位半精度浮点下每秒 280 万亿次浮点运算 |
| HBM 容量 | 64 GB | 高带宽显存，模型权重 + KV Cache 常驻 |

---

## 相关概念

| 术语 | 详见 |
|------|------|
| KV Cache 计算与生命周期 | [../../inference/docs/Inference-Fundamentals.md](../../inference/docs/Inference-Fundamentals.md) |
| Prefill / Decode 阶段 | [../../inference/docs/Inference-Fundamentals.md](../../inference/docs/Inference-Fundamentals.md) |
| UCM 三层异构内存分级 | [../../terminology-quick-reference.md](../../terminology-quick-reference.md) |
| PagedAttention 分页管理 | [../../terminology-quick-reference.md](../../terminology-quick-reference.md) |

---

## 🔬 实际环境观测

> 以下为理论概念在真实生产环境中的可观测方法与快照参考。操作过程详见 [LLM-Platform-Practice.md](../../platform/docs/LLM-Platform-Practice.md)

### 观测 1：GPU 内存层次映射（对应"四级存储层次"节）

**观测方法**：在 vLLM 服务器上执行 `nvidia-smi`（NVIDIA GPU）或 `npu-smi info`（华为 NPU）

**环境快照**（NPU A2 64G，宿主机 `npu-smi info`）：

| 层级 | 理论值 | 生产环境实际映射 |
|:---|:---|:---|
| **SRAM** | ~20-50 MB | npu-smi 不直接暴露，通过算子执行时间间接观测 |
| **HBM** | 64 GB | npu-smi `HBM Capacity: 65536 MB`，模型权重+KV Cache 常驻 |
| **CPU DRAM** | 数百 GB | `free -h` 可查，UCM 温层 KV Cache 换出目标 |
| **SSD** | 数 TB | `df -h /data0` 可查，UCM 冷层持久化目标 |

---

### 观测 2：Memory-Bound vs Compute-Bound 实证

**观测方法**：对比 vLLM 的 `time_to_first_token_seconds`（Prefill/Compute-Bound）与 `generation_time_seconds`（Decode/Memory-Bound）

**环境快照**（vLLM metrics，上海绿区 A3）：
```
vllm:time_to_first_token_seconds_count 150
vllm:time_to_first_token_seconds_sum 45.2
→ 平均 TTFT ≈ 0.30s（Prefill 阶段，计算密集）

vllm:generation_time_seconds_count 150
vllm:generation_time_seconds_sum 120.5
→ 平均生成时间 ≈ 0.80s（Decode 阶段，访存瓶颈占主导）
```
> 观测点：Decode 阶段单 Token 耗时远高于 Prefill 阶段均摊的每 Token 耗时，验证了"Decode 是 Memory-Bound"的结论

---

*快照更新时间：2026-08-06*
