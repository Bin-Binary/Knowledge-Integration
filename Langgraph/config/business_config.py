# /config/business_config.py
import json
from pathlib import Path
from schemas.intent_and_route_catalog import (
    AgentBusinessConfig,
    IntentCatalog,
    RouteCatalog,
)


def load_business_config(
    intent_path: str | Path = "config/intent_catalog.json",
    route_path: str | Path = "config/route_catalog.json",
) -> AgentBusinessConfig:
    """加载并校验意图目录与路由目录业务配置（含跨文件一致性快速失败检查）"""
    i_file = Path(intent_path)
    r_file = Path(route_path)

    if not i_file.exists():
        raise FileNotFoundError(f"Intent catalog file not found: {i_file.resolve()}")
    if not r_file.exists():
        raise FileNotFoundError(f"Route catalog file not found: {r_file.resolve()}")

    intent_raw = json.loads(i_file.read_text(encoding="utf-8"))
    route_raw = json.loads(r_file.read_text(encoding="utf-8"))

    return AgentBusinessConfig(
        intent_catalog=IntentCatalog.model_validate(intent_raw),
        route_catalog=RouteCatalog.model_validate(route_raw),
    )
