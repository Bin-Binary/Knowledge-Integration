"""自动扫描并加载当前包下的所有组织算子插件，触发 @OrganizationPluginRegistry.register 装饰器。"""

import importlib
import pkgutil
from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
for _mod in pkgutil.iter_modules([str(_pkg_dir)]):
    if not _mod.name.startswith("_"):
        importlib.import_module(f"{__name__}.{_mod.name}")
