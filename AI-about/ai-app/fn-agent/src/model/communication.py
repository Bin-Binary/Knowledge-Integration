"""F-COMM-01 入口路由框架的Python数据模型。

对应schema: schema/design/fram/f-communication/F-COMM-01.json (v1.2-draft)

框架职责:
- 对话入口的意图分流器, 将话轮分类为 phatic/ood/in_domain
- in_domain 时激活目标框架并前景化
- 不承载域事件内容, 不执行业务逻辑
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union


class EntityRef(str, Enum):
    """实体引用候选集(core_fe/peripheral_fe 的 enum 约束)。"""
    ENT_HUMAN = "ENT-HUMAN"
    ENT_SYSTEM = "ENT-SYSTEM"
    ENT_GROUP = "ENT-GROUP"
    ENT_GUEST = "ENT-GUEST"  # INI(上游无信息)缺省填充值

class RoutingOutcome(str, Enum):
    """instance_template.routing_outcome: 路由判定结果, 入口框架唯一产出。"""

    PHATIC = "phatic"
    OOD = "ood"
    IN_DOMAIN = "in_domain"


class Force(str, Enum):
    """instance_template.force / foreground_operator.force: 前景化类型。

    决定目标框架走哪条执行路径:
    - request:    执行子图(写)
    - question:   只读子图(读)
    - statement:  记录确认
    - commitment: 待办追踪
    - unclear:    激活澄清框架
    """

    REQUEST = "request"
    QUESTION = "question"
    STATEMENT = "statement"
    COMMITMENT = "commitment"
    UNCLEAR = "unclear"


@dataclass
class CoreFeature:
    """core_fe 槽位。"""

    communicator: Optional[EntityRef] = None
    addressee: Optional[EntityRef] = None
    utterance: Optional[str] = None


@dataclass
class PeripheralFeature:
    """peripheral_fe 槽位。"""

    medium: Optional[EntityRef] = None
    topic: Optional[str] = None
    language: Optional[str] = None
    source: Optional[EntityRef] = None


@dataclass
class RoutingRule:
    """frame_rules.routing 单分支: 话轮去向对应的动作。"""

    action: str
    note: Optional[str] = None


@dataclass
class RoutingRules:
    """frame_rules.routing: 路由表。"""

    phatic: RoutingRule = field(
        default_factory=lambda: RoutingRule(action="respond", note="礼貌回应,不激活框架,不调工具")
    )
    ood: RoutingRule = field(
        default_factory=lambda: RoutingRule(action="guide", note="礼貌引导回域内,不激活框架,不调域工具")
    )
    in_domain: RoutingRule = field(
        default_factory=lambda: RoutingRule(action="activate", note="激活目标框架,按force选择执行路径")
    )


@dataclass
class ForegroundOperator:
    """frame_rules.foreground_operator: 前景化操作, in_domain 分支的附加信息。"""

    force: Optional[Force] = None
    target_frame_schema_id: Optional[str] = None


@dataclass
class FrameRules:
    """frame_rules 集合。"""

    routing: RoutingRules = field(default_factory=RoutingRules)
    foreground_operator: ForegroundOperator = field(default_factory=ForegroundOperator)


@dataclass
class CommunicationFrame:
    """F-COMM-01 框架 schema 的模型化表示。"""

    metadata: Dict[str, object] = field(default_factory=dict)
    core: CoreFeature = field(default_factory=CoreFeature)
    peripheral: PeripheralFeature = field(default_factory=PeripheralFeature)
    rules: FrameRules = field(default_factory=FrameRules)


@dataclass
class CommunicationFrameInstance:
    """instance_template 的实例模型。

    每轮对话实例化一次, uuid 只在这一层生成。

    条件约束(schema if/then):
    - routing_outcome == in_domain 时, force 与 target_frame_schema_id 必填
    """

    frame_instance_id: str
    frame_schema_id: str
    communicator: EntityRef
    utterance: str
    routing_outcome: RoutingOutcome
    addressee: Optional[EntityRef] = None
    in_response_to: Optional[str] = None
    force: Optional[Force] = None
    target_frame_schema_id: Optional[str] = None
    created_at: Optional[str] = None
    peripheral: PeripheralFeature = field(default_factory=PeripheralFeature)

    def validate(self) -> None:
        """校验实例满足 schema 的 required + if/then 约束。

        Raises:
            ValueError: 缺少必填字段或 in_domain 时缺少 force/target_frame_schema_id
        """
        if not self.frame_instance_id:
            raise ValueError("frame_instance_id is required")
        if self.frame_schema_id != "F-COMM-01":
            raise ValueError(f"frame_schema_id must be 'F-COMM-01', got {self.frame_schema_id!r}")
        if self.communicator is None:
            raise ValueError("communicator is required")
        if not self.utterance:
            raise ValueError("utterance is required")
        if self.routing_outcome is None:
            raise ValueError("routing_outcome is required")
        if self.routing_outcome == RoutingOutcome.IN_DOMAIN:
            if self.force is None or self.target_frame_schema_id is None:
                raise ValueError(
                    "force and target_frame_schema_id are required when routing_outcome == in_domain"
                )

    def to_dict(self) -> dict:
        """导出为实例字典(供快照链序列化)。"""
        return {
            "frame_instance_id": self.frame_instance_id,
            "frame_schema_id": self.frame_schema_id,
            "in_response_to": self.in_response_to,
            "communicator": self.communicator.value if self.communicator else None,
            "addressee": self.addressee.value if self.addressee else None,
            "utterance": self.utterance,
            "routing_outcome": self.routing_outcome.value if self.routing_outcome else None,
            "force": self.force.value if self.force else None,
            "target_frame_schema_id": self.target_frame_schema_id,
            "peripheral": {
                "medium": self.peripheral.medium.value if self.peripheral.medium else None,
                "topic": self.peripheral.topic,
                "language": self.peripheral.language,
                "source": self.peripheral.source.value if self.peripheral.source else None,
            },
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CommunicationFrameInstance":
        """从实例字典(快照链反序列化)重建实例。"""
        peripheral_data = data.get("peripheral") or {}
        return cls(
            frame_instance_id=data.get("frame_instance_id", ""),
            frame_schema_id=data.get("frame_schema_id", ""),
            in_response_to=data.get("in_response_to"),
            communicator=EntityRef(data["communicator"]) if data.get("communicator") else None,
            addressee=EntityRef(data["addressee"]) if data.get("addressee") else None,
            utterance=data.get("utterance", ""),
            routing_outcome=RoutingOutcome(data["routing_outcome"]) if data.get("routing_outcome") else None,
            force=Force(data["force"]) if data.get("force") else None,
            target_frame_schema_id=data.get("target_frame_schema_id"),
            created_at=data.get("created_at"),
            peripheral=PeripheralFeature(
                medium=EntityRef(peripheral_data["medium"]) if peripheral_data.get("medium") else None,
                topic=peripheral_data.get("topic"),
                language=peripheral_data.get("language"),
                source=EntityRef(peripheral_data["source"]) if peripheral_data.get("source") else None,
            ),
        )
