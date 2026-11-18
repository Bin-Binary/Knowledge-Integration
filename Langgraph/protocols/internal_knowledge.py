# /protocols/internal_knowledge.py
"""域内知识库构建

核心架构思想：依赖倒置（DIP）
    本协议层仅约束全链路业务接口与数据流转契约，与具体采集工具、推理算子及持久化引擎完全隔离。
    全链路四大环节均以 `PipelineEnvelope` 作为唯一通用传输载体（黑板模式），各实现以适配器
    （Adapter）形态插件化挂载，实现零胶水代码与正交演进。

全链路四大环节与状态流转：
    1. 【运用 (Application / Usage)】
       - 职能：记忆检索与问题求解，驱动全链路闭环。
       - 读取：`problem_resolution`（包含初始问题 `problem` 及检索得到的 `resolutions`）。
       - 写入：更新 `problem_resolution`（产出 `outcome`、`resultant_situation` 或 `remaining_gap`）。
         * 若 `outcome == SUCCESS`：闭环终止。
         * 若 `outcome != SUCCESS`：携带 `remaining_gap` 流向【采集】环节。

    2. 【采集 (Acquisition)】
       - 职能：按源路由（AST代码切片 / 结构化文档树 / 对话窗口 / 网页滑窗）截取原子符号。
       - 读取：`source_locator`（静态全量源）或 `problem_resolution.remaining_gap`（缺口定向采集）。
       - 写入：向信封追加 `raw_infos: List[Information]`（最细粒度的不可变原始符号载体）。

    3. 【组织 (Organization)】
       - 职能：四阶信息密度递增加工，将零散原始符号转化为高内聚知识图谱形态。
       - 读取：`raw_infos: List[Information]`。
       - 内部加工流水线：
         * 3.1 评估过滤：`Information` ➔ `float`（质量标量 [0.0, 1.0]，过滤低质噪声）。
         * 3.2 提取特征：`Information` ➔ `List[Labeling]`（可检索概念节点）。
         * 3.3 关系建模：`List[Labeling]`（条数 >= 2） ➔ `List[RelatingConcepts]`（有向语义边）。
         * 3.4 本体聚拢：`List[Labeling] + List[RelatingConcepts]` ➔ `List[Ontology]`（知识闭环体）。
       - 写入：向信封填充 `labels`、`relations` 与 `complexes`。

    4. 【存储 (Storage)】
       - 职能：屏蔽底层物理介质差异，完成多形态知识结构的持久化落盘与记忆召回。
       - 写入落盘 (`save`)：读取 `raw_infos`、`labels`、`relations`、`complexes` 持久化，追加 `storage_receipts: List[StorageReceipt]`。
       - 记忆检索 (`retrieve`)：读取 `problem_resolution.problem` 检索已有知识，填充 `problem_resolution.resolutions`。

核心数据模型与职能：
    - `PipelineEnvelope`          : 全链路唯一状态容器与传输载体（聚合所有阶段上下文与 `StorageReceipt`）。
    - `ResolveProblem`            : 定义"为什么建"（问题 -> 方案 -> 结果/缺口），驱动整个闭环的引擎。
    - `Information`               : 知识的原始符号载体（最细粒度、不可变、带源定位符）。
    - `Labeling`                  : 概念节点，对信息片段进行特征分类与语义判断（粒度适中，维护成本低）。
    - `RelatingConcepts`          : 语义边，连接离散标签形成可推理的有向网络（支持领域隔离关系枚举）。
    - `Ontology` : 成型的知识形态（Complex），聚拢相关节点与边的高内聚知识闭环体。

按问题驱动的闭合回路（Closed-Loop）：
    [初始化 PipelineEnvelope(problem)]
        ➔ 【存储.retrieve: 检索已有知识填充 resolutions】
        ➔ 【运用.resolve: 评估求解】
            ├── (命中且解决: outcome=SUCCESS) ➔ 输出 `resultant_situation`（闭环结束）
            └── (存在知识缺口: remaining_gap)
                    ➔ 【采集.acquire: 补充切片至 raw_infos】
                    ➔ 【组织.organize: 加工并填充 labels / relations / complexes】
                    ➔ 【存储.save: 持久化落盘并记录 storage_receipts】
                    ➔ 重新触发 【存储.retrieve ➔ 运用.resolve】 直至问题闭合。
"""

from typing import Protocol
from schemas.internal_knowledge.pipeline_envelope import PipelineEnvelope

class KnowledgeApplicationProtocol(Protocol):
    """1. 【运用】环节：读取 problem 与 resolutions，更新 problem_resolution（含 remaining_gap）"""

    def resolve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """执行问题求解与缺口诊断。"""
        ...

class KnowledgeAcquisitionProtocol(Protocol):
    """2. 【采集】环节：根据 source_locator 或 remaining_gap 截取切片，追加 raw_infos"""

    def acquire(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """按数据源协议路由切片策略，产出原子信息片段并写入信封。"""
        ...

class KnowledgeOrganizationProtocol(Protocol):
    """3. 【组织】环节：读取 raw_infos，完成评估、特征抽取、建边与本体聚拢，填充 labels/relations/complexes"""

    def organize(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """端到端知识加工流水线：过滤噪声并构建结构化知识网络写入信封。"""
        ...

class KnowledgeStorageProtocol(Protocol):
    """4. 【存储】环节：负责多后端知识持久化（save）与记忆召回（retrieve）"""

    def save(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """将信封中的多形态知识结构持久化至底层存储引擎，并追加 StorageReceipt。"""
        ...

    def retrieve(self, envelope: PipelineEnvelope) -> PipelineEnvelope:
        """根据信封中的问题意图检索已有知识，填充至 problem_resolution.resolutions 供运用环节使用。"""
        ...
