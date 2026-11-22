# /components/internal_knowledge/organization/registry.py
import asyncio
import importlib
import pkgutil
from enum import Enum
from typing import Any, Callable, ClassVar, Dict, List, Optional, Type

from schemas.internal_knowledge.information import Information
from schemas.internal_knowledge.labeling import Labeling
from schemas.internal_knowledge.relating_concepts import RelatingConcepts
from schemas.internal_knowledge.ontology import Ontology
from protocols.evaluation import QualityEvaluatorProtocol
from protocols.internal_knowledge import (
    LabelExtractorProtocol,
    RelationBuilderProtocol,
    OntologyClustererProtocol,
)


class OrgStage(str, Enum):
    """组织阶段四阶算子归属标识"""
    EVALUATE = "3.1_evaluate"    # 质量评估（单选模式：同一时间只激活一个）
    EXTRACT = "3.2_extract"      # 特征提取（支持多算子累加合并）
    RELATE = "3.3_relate"        # 关系建模（支持多算子累加合并）
    CLUSTER = "3.4_cluster"      # 本体聚拢（单选模式：同一时间只激活一个）


class OrganizationPluginRegistry:
    """【组织】环节统一插件注册中心：
    1. 自动扫描并归类 3.1 ~ 3.4 四个阶段的所有算子实现。
    2. 解决同阶段多实现冲突：
       - 单选阶段 (EVALUATE / CLUSTER)：通过 active_profiles 配置指定启用哪一个（未指定则取默认或第一个）。
       - 累加阶段 (EXTRACT / RELATE)：自动组合所有已启用的算子并发执行并去重合并结果。
    """

    # 结构: { OrgStage: { plugin_name: {"cls": Type, "is_default": bool} } }
    _plugins: ClassVar[Dict[OrgStage, Dict[str, Dict[str, Any]]]] = {
        stage: {} for stage in OrgStage
    }

    @classmethod
    def register(cls, stage: OrgStage, name: str, *, is_default: bool = False):
        """统一装饰器：声明算子归属阶段、唯一名称及是否为该阶段默认实现"""
        def wrapper(target_cls: Type[Any]) -> Type[Any]:
            if name in cls._plugins[stage]:
                raise ValueError(f"组织插件注册冲突：阶段 [{stage.value}] 已存在名为 '{name}' 的实现")
            cls._plugins[stage][name] = {
                "cls": target_cls,
                "is_default": is_default,
            }
            return target_cls
        return wrapper

    @classmethod
    def discover(cls, package_path: str) -> None:
        """递归自动扫描指定包下的所有子模块，触发装饰器注册"""
        pkg = importlib.import_module(package_path)
        for _, module_name, is_pkg in pkgutil.walk_packages(pkg.__path__, prefix=f"{package_path}."):
            importlib.import_module(module_name)

    @classmethod
    def resolve_single(
        cls,
        stage: OrgStage,
        active_name: Optional[str] = None,
        init_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """【单选仲裁器】（用于 3.1 评估 / 3.4 聚类）：
        优先级：显式传入 active_name > 标记为 is_default=True 的插件 > 注册表中的第一个插件。
        """
        candidates = cls._plugins[stage]
        if not candidates:
            raise RuntimeError(f"阶段 [{stage.value}] 尚未注册任何可用算子")

        chosen_name = active_name
        if not chosen_name:
            defaults = [k for k, v in candidates.items() if v["is_default"]]
            chosen_name = defaults[0] if defaults else next(iter(candidates))

        if chosen_name not in candidates:
            raise KeyError(f"阶段 [{stage.value}] 未找到名为 '{chosen_name}' 的算子，可选: {list(candidates.keys())}")

        target_cls = candidates[chosen_name]["cls"]
        return target_cls(**(init_kwargs or {}))

    @classmethod
    def resolve_composite(
        cls,
        stage: OrgStage,
        enabled_names: Optional[List[str]] = None,
        kwargs_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[Any]:
        """【多算子装配器】（用于 3.2 提特征 / 3.3 建边）：
        若 enabled_names 为 None，则默认激活该阶段下所有已注册算子；否则仅实例化指定列表。
        """
        candidates = cls._plugins[stage]
        if not candidates:
            return []

        target_names = enabled_names if enabled_names is not None else list(candidates.keys())
        kwargs_map = kwargs_map or {}

        instances = []
        for name in target_names:
            if name not in candidates:
                raise KeyError(f"阶段 [{stage.value}] 未找到名为 '{name}' 的算子")
            instances.append(candidates[name]["cls"](**kwargs_map.get(name, {})))
        return instances
