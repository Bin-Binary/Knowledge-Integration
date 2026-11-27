# /schemas/internal_knowledge_base_building/__init__.py
"""域内知识库建设（Internal Knowledge Base Building）数据模型族。

按 FrameNet v17 涉及的七个框架的 Frame Element（FE）同构建立：
    运用（为什么建）  -> resolve_problem
    采集（获取数据）  -> information
    组织（分类/本体） -> labeling, set_of_interrelated_entities, relating_concepts
    存储（落地可检索）-> recording
    建设（为目标而建）-> building

每个 Schema 继承 schemas.base.ImmutableSchema（冻结 + 严格字段校验），
保持与 schemas/decision.py、schemas/api.py 一致的边界风格。
"""
from components.internal_knowledge.schemas.resolve_problem import ResolutionOutcome

__all__ = [
    "ResolutionOutcome",
]
