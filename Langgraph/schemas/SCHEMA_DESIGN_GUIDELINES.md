# 数据模型设计规范 (Schema Design Guidelines)

## 1. 核心原则
* **领域驱动与最小化**：仅对具备独立生命周期的领域核心概念建立独立Schema
* **元信息自文档化**：让文档成为代码 AST 的一部分，供 IDE、OpenAPI 及大模型（LLM）直接反射读取。
* **代码校验兑现**：所有注释中声明的业务约束，建议通过Pydantic类型系统或校验器强制执行。

## 2. 元信息自文档化边界
* **建议自文档化（面向LLM与复杂领域）**：凡作为候选集注入 LLM Prompt 的枚举，或涉及复杂理论映射（如 FrameNet）的模型，建议使用 `DocumentedEnum` 并在 `Field(description=...)` 中写明语义与边界约束。
* **保持极简克制（面向确定性代码）**：如 `trace_id`、`session_id`、`latency_ms` 或通用运行状态（如 `COMPLETED`、`FAILED`），属于软件工程常识，保持标准 `Enum` 与简洁字段定义即可，避免制造视觉噪音。

## 3. 文档内聚与位置规范
* **禁用字段上方浮动注释**：Python解释器会直接丢弃属性上方的独立三引号字符串，导致外部工具无法读取。
* **类级规范收敛至 Class Docstring**：全局设计取舍、有向边方向约定、字段映射表统一写在类定义下的第一行文档字符串中。
* **字段约束收敛至 Field**：单字段的业务含义、取值范围及缺失警告统一写入 `Field(description=...)`。

```python
# 正面示例：规范内聚、无浮动注释、校验器兑现业务闭环
class ResolutionOutcome(DocumentedEnum):
    PENDING = ("pending", "运用状态", "任务已初始化，待检索与求解")
    SUCCESS = ("success", "运用结果", "问题已解决，闭环终止")
    FAILURE = ("failure", "运用结果", "未检索到有效知识，需启动采集")

class ResolveProblem(ImmutableSchema):
    """运用层契约：记录单次问题求解过程及知识缺口。
    设计规范:
        1. 任务初始化默认处于 PENDING 状态，避免前置阶段触发缺口校验。
        2. 求解失败时建议产出 remaining_gap 作为下游采集燃料。
    """
    problem: str = Field(..., min_length=1, description="待解决的具体问题")
    outcome: ResolutionOutcome = Field(default=ResolutionOutcome.PENDING, description="评估结果状态")
    remaining_gap: Optional[str] = Field(default=None, description="未解决的知识缺口（FAILURE 时必填）")

    @model_validator(mode="after")
    def validate_closed_loop(self) -> "ResolveProblem":
        if self.outcome is ResolutionOutcome.FAILURE and not self.remaining_gap:
            raise ValueError("outcome 为 failure 时建议提供 remaining_gap")
        return self
```

## 4. 多环节流水线载体规范（黑板模式）
* **统一流转载体**：当数据流经3个以上处理环节（如 `运用 -> 采集 -> 组织 -> 存储`）时，禁止各环节定义独立的输入/输出模型，统一使用累积式不可变信封（`PipelineEnvelope`）。
* **零胶水接口签名**：所有环节协议统一采用 `def process(envelope: PipelineEnvelope) -> PipelineEnvelope`，通过 `model_copy(update={...})` 追加当前环节产物，完整保留全链路血缘快照。

```python
# 正面示例：全链路唯一状态载体
class PipelineEnvelope(ImmutableSchema):
    trace_id: str = Field(..., min_length=1, description="全链路闭环追踪 ID")
    problem_resolution: Optional[ResolveProblem] = Field(default=None, description="运用层求解状态")
    raw_infos: List[Information] = Field(default_factory=list, description="采集层原子切片")
    labels: List[Labeling] = Field(default_factory=list, description="组织层概念节点")
```
