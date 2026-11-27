# /components/internal_knowledge/organization/registry.py
import importlib
import inspect
import logging
import pkgutil
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OrgStage(str, Enum):
    """知识组织四阶加工流水线阶段枚举"""

    EVALUATE = "3.1_evaluate"
    EXTRACT = "3.2_extract"
    RELATE = "3.3_relate"
    CLUSTER = "3.4_cluster"


@dataclass(frozen=True)
class _OrgPluginEntry:
    stage: OrgStage
    name: str
    cls: Type[Any]
    is_default: bool


class OrganizationPluginRegistry:
    """知识组织四阶算子插件注册中心（支持自动扫描发现 + 按构造函数签名自动依赖注入）"""

    _registry: Dict[OrgStage, Dict[str, _OrgPluginEntry]] = {
        stage: {} for stage in OrgStage
    }
    _discovered_packages: Set[str] = set()

    @classmethod
    def register(
        cls,
        stage: OrgStage,
        name: str,
        is_default: bool = False,
    ) -> Callable[[Type[T]], Type[T]]:
        """类装饰器：将算子实现注册到指定组织阶段"""

        def _decorator(plugin_cls: Type[T]) -> Type[T]:
            stage_bucket = cls._registry.setdefault(stage, {})
            stage_bucket[name] = _OrgPluginEntry(
                stage=stage,
                name=name,
                cls=plugin_cls,
                is_default=is_default,
            )
            logger.debug(
                "[OrganizationPluginRegistry] 注册插件: stage=%s, name=%s, cls=%s, is_default=%s",
                stage.value,
                name,
                plugin_cls.__name__,
                is_default,
            )
            return plugin_cls

        return _decorator

    @classmethod
    def discover(cls, package_name: str) -> None:
        """幂等扫描指定包下的所有子模块，自动触发 @register 装饰器"""
        if package_name in cls._discovered_packages:
            return
        pkg = importlib.import_module(package_name)
        pkg_paths = getattr(pkg, "__path__", None)
        if pkg_paths:
            for mod in pkgutil.iter_modules(pkg_paths):
                if not mod.name.startswith("_"):
                    importlib.import_module(f"{package_name}.{mod.name}")
        cls._discovered_packages.add(package_name)

    @classmethod
    def _instantiate(
        cls,
        entry: _OrgPluginEntry,
        shared_deps: Optional[Dict[str, Any]] = None,
        init_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """根据插件 __init__ 参数签名，从 shared_deps 与显式 init_kwargs 自动按需注入依赖"""
        deps = shared_deps or {}
        explicit = init_kwargs or {}
        sig = inspect.signature(entry.cls.__init__)

        call_kwargs: Dict[str, Any] = {}
        accepts_var_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )

        if accepts_var_kwargs:
            call_kwargs.update(deps)
            call_kwargs.update(explicit)
        else:
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                if param_name in explicit:
                    call_kwargs[param_name] = explicit[param_name]
                elif param_name in deps:
                    call_kwargs[param_name] = deps[param_name]

        return entry.cls(**call_kwargs)

    @classmethod
    def resolve_single(
        cls,
        stage: OrgStage,
        active_name: Optional[str] = None,
        shared_deps: Optional[Dict[str, Any]] = None,
        init_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """解析并实例化单选阶段算子（3.1 评估 / 3.4 聚类）"""
        stage_bucket = cls._registry.get(stage, {})
        if not stage_bucket:
            raise LookupError(f"组织阶段 [{stage.value}] 未注册任何可用插件")

        entry: Optional[_OrgPluginEntry] = None
        if active_name and active_name in stage_bucket:
            entry = stage_bucket[active_name]
        elif active_name:
            # 若传入的名称未匹配，优先回退到该阶段的默认插件（兼容历史别名如 connected_component）
            entry = next((e for e in stage_bucket.values() if e.is_default), None)
            if entry is None:
                raise LookupError(
                    f"组织阶段 [{stage.value}] 未找到插件 '{active_name}'，且无默认兜底插件"
                )
        else:
            entry = next((e for e in stage_bucket.values() if e.is_default), None) or next(
                iter(stage_bucket.values())
            )

        return cls._instantiate(entry, shared_deps=shared_deps, init_kwargs=init_kwargs)

    @classmethod
    def resolve_composite(
        cls,
        stage: OrgStage,
        enabled_names: Optional[List[str]] = None,
        shared_deps: Optional[Dict[str, Any]] = None,
        kwargs_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[Any]:
        """解析并实例化多算子合并阶段（3.2 特征提取 / 3.3 关系建模）"""
        stage_bucket = cls._registry.get(stage, {})
        if not stage_bucket:
            raise LookupError(f"组织阶段 [{stage.value}] 未注册任何可用插件")

        kw = kwargs_map or {}
        if enabled_names is not None:
            entries = []
            for name in enabled_names:
                if name not in stage_bucket:
                    raise LookupError(f"组织阶段 [{stage.value}] 未找到指定插件 '{name}'")
                entries.append(stage_bucket[name])
        else:
            entries = [e for e in stage_bucket.values() if e.is_default] or list(
                stage_bucket.values()
            )

        return [
            cls._instantiate(e, shared_deps=shared_deps, init_kwargs=kw.get(e.name))
            for e in entries
        ]
