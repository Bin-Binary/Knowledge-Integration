# /components/recovery/registry.py
import importlib
import inspect
import pkgutil
from typing import Any, ClassVar, Dict, List, Optional, Sequence, Type

from protocols.recovery import ExceptionRecoveryProtocol


class RecoveryPluginRegistry:
    """异常恢复插件注册中心（实现自发现与按配置依赖注入，严格遵循 OCP）"""

    _plugins: ClassVar[Dict[str, Type[ExceptionRecoveryProtocol]]] = {}
    _discovered_packages: ClassVar[set[str]] = set()

    @classmethod
    def register(cls, name: str):
        def wrapper(target_cls: Type[Any]) -> Type[Any]:
            if name in cls._plugins and cls._plugins[name] is not target_cls:
                raise ValueError(f"恢复插件注册冲突：已存在名为 '{name}' 的处理器")
            if not issubclass(target_cls, ExceptionRecoveryProtocol):
                raise TypeError(f"插件 '{target_cls.__name__}' 未实现 ExceptionRecoveryProtocol")
            cls._plugins[name] = target_cls
            return target_cls
        return wrapper

    @classmethod
    def discover(cls, package_paths: Sequence[str] = ("components.recovery",)) -> None:
        for pkg_path in package_paths:
            if pkg_path in cls._discovered_packages:
                continue
            pkg = importlib.import_module(pkg_path)
            for _, module_name, _ in pkgutil.walk_packages(pkg.__path__, prefix=f"{pkg_path}."):
                importlib.import_module(module_name)
            cls._discovered_packages.add(pkg_path)

    @classmethod
    def build_handlers(
        cls,
        enabled_names: Optional[Sequence[str]] = None,
        shared_deps: Optional[Dict[str, Any]] = None,
    ) -> List[ExceptionRecoveryProtocol]:
        """根据配置启用的名称列表（及顺序）实例化恢复器，并按需自动注入依赖"""
        cls.discover()
        deps = shared_deps or {}
        target_names = list(enabled_names) if enabled_names is not None else list(cls._plugins.keys())

        instances: List[ExceptionRecoveryProtocol] = []
        for name in target_names:
            if name not in cls._plugins:
                raise KeyError(f"未找到名为 '{name}' 的异常恢复插件，当前已注册: {list(cls._plugins.keys())}")
            target_cls = cls._plugins[name]
            # 智能签名匹配：子类 __init__ 声明了什么参数，就从 shared_deps 中自动喂给它，不锁死构造函数
            sig = inspect.signature(target_cls.__init__)
            init_kwargs = {
                param_name: deps[param_name]
                for param_name in sig.parameters
                if param_name != "self" and param_name in deps
            }
            instances.append(target_cls(**init_kwargs))

        return instances
