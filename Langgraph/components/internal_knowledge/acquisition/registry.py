# /components/internal_knowledge/acquisition/registry.py# /components/internal_knowledge/acquisition/registry.py
import importlib
import inspect
import logging
import pkgutil
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Set, Tuple, Type

from components.internal_knowledge.schemas.source_uri import SourceScheme
from components.internal_knowledge.protocols import GapRoutingProtocol
from components.internal_knowledge.acquisition.composite_acquirer import (
    CompositeKnowledgeAcquirer,
    SourceHandlerProtocol,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AcquisitionHandlerSpec:
    """采集处理器注册元数据规格"""

    name: str
    handler_cls: Type[SourceHandlerProtocol]
    routes: Tuple[Tuple[SourceScheme, str], ...]


class AcquisitionPluginRegistry:
    """
    知识采集处理器自发现注册中心（严格遵循 OCP）：
    - 支持通过装饰器 @register(name, routes=[(SourceScheme.FILE, ".sh"), ...]) 声明式注册；
    - 启动期自动扫描包模块，基于 inspect.signature 从 shared_deps 自动匹配构造函数依赖；
    - 彻底消除工厂硬编码实例化与手写 import 触发注册的痛点。
    """

    _specs: ClassVar[Dict[str, AcquisitionHandlerSpec]] = {}
    _discovered_packages: ClassVar[Set[str]] = set()

    @classmethod
    def register(
        cls,
        name: str,
        *,
        routes: Sequence[Tuple[SourceScheme, str]],
    ):
        """
        装饰器：声明采集处理器的唯一标识名与支持的 (SourceScheme, suffix) 复合路由列表。
        示例：
            @AcquisitionPluginRegistry.register(
                "shell_script",
                routes=[(SourceScheme.FILE, ".sh"), (SourceScheme.REPO, ".sh")],
            )
        """
        if not routes:
            raise ValueError(f"采集插件 '{name}' 注册失败：routes 不能为空")

        normalized_routes: List[Tuple[SourceScheme, str]] = []
        for scheme, suffix in routes:
            norm_suffix = (
                suffix.lower()
                if suffix == "*" or suffix.startswith(".")
                else f".{suffix.lower()}"
            )
            normalized_routes.append((scheme, norm_suffix))

        def wrapper(target_cls: Type[Any]) -> Type[Any]:
            if name in cls._specs and cls._specs[name].handler_cls is not target_cls:
                raise ValueError(f"采集插件注册冲突：已存在名为 '{name}' 的处理器")
            if not issubclass(target_cls, SourceHandlerProtocol):
                raise TypeError(
                    f"采集插件 '{target_cls.__name__}' 未实现 SourceHandlerProtocol"
                )
            cls._specs[name] = AcquisitionHandlerSpec(
                name=name,
                handler_cls=target_cls,
                routes=tuple(normalized_routes),
            )
            return target_cls

        return wrapper

    @classmethod
    def discover(
        cls,
        package_paths: Sequence[str] = ("components.internal_knowledge.acquisition",),
    ) -> None:
        """幂等扫描指定包下的所有子模块，自动触发 @register 装饰器注册"""
        for pkg_path in package_paths:
            if pkg_path in cls._discovered_packages:
                continue
            pkg = importlib.import_module(pkg_path)
            if hasattr(pkg, "__path__"):
                for _, module_name, _ in pkgutil.walk_packages(
                    pkg.__path__, prefix=f"{pkg_path}."
                ):
                    importlib.import_module(module_name)
            cls._discovered_packages.add(pkg_path)

    @classmethod
    def build_acquirer(
        cls,
        *,
        gap_router: Optional[GapRoutingProtocol] = None,
        enabled_names: Optional[Sequence[str]] = None,
        shared_deps: Optional[Dict[str, Any]] = None,
        max_concurrency: int = 5,
        handler_timeout_seconds: Optional[float] = None,
    ) -> CompositeKnowledgeAcquirer:
        """
        自动发现、按签名依赖注入实例化处理器，并组装返回 CompositeKnowledgeAcquirer。
        """
        cls.discover()
        deps = shared_deps or {}
        target_names = (
            list(enabled_names)
            if enabled_names is not None
            else list(cls._specs.keys())
        )

        acquirer = CompositeKnowledgeAcquirer(
            gap_router=gap_router,
            max_concurrency=max_concurrency,
            handler_timeout_seconds=handler_timeout_seconds,
        )

        for name in target_names:
            if name not in cls._specs:
                raise KeyError(
                    f"未找到名为 '{name}' 的采集插件，当前已注册: {list(cls._specs.keys())}"
                )
            spec = cls._specs[name]
            sig = inspect.signature(spec.handler_cls.__init__)
            init_kwargs = {
                param_name: deps[param_name]
                for param_name in sig.parameters
                if param_name != "self" and param_name in deps
            }
            handler_instance = spec.handler_cls(**init_kwargs)

            for scheme, suffix in spec.routes:
                acquirer.register(scheme=scheme, handler=handler_instance, suffix=suffix)

        logger.info(
            "[AcquisitionRegistry] Built CompositeKnowledgeAcquirer with plugins=%s (max_concurrency=%d)",
            target_names,
            max_concurrency,
        )
        return acquirer
