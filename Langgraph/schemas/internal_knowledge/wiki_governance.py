# /schemas/internal_knowledge/wiki_governance.py
from schemas.base import DocumentedEnum

class WikiMaturityStage(DocumentedEnum):
    """LLM-WIKI 知识成熟度三层生命周期"""
    DEBUG = ("debug", "缓冲区", "AI 自动生成的初始知识产物，待人工审核")
    RELEASE = ("release", "准生产区", "人工审核通过的 AI 产物或人工直接编写的知识")
    GOLD = ("gold", "黄金标准区", "经过真实问题求解闭环验证有效（outcome=SUCCESS）的高可信度知识")

class WikiArtifactLayer(DocumentedEnum):
    """LLM-WIKI 四层抽象粒度（信息密度由低到高）"""
    INFORMATION = ("information", "L1 原始符号", "知识采集环节产出的最细粒度原始切片")
    LABELING = ("labeling", "L2 概念节点", "信息片段的特征分类与语义标签")
    RELATING = ("relating", "L3 语义边", "连接离散标签的有向语义网络边")
    ONTOLOGY = ("ontology", "L4 知识本体", "多轮信息积累聚拢的高内聚子图闭环体")
