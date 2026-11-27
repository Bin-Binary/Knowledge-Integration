"""自动扫描并加载当前包下的所有采集处理器模块，触发 @AcquisitionPluginRegistry.register 装饰器。"""

import importlib
import pkgutil
from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent

for _module_info in pkgutil.iter_modules([str(_pkg_dir)]):
    if not _module_info.name.startswith("_"):
        importlib.import_module(f"{__name__}.{_module_info.name}")
