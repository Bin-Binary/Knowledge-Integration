# components/internal_knowledge/organization/heuristics/general_rules.py
import re
from typing import Optional
from components.internal_knowledge.schemas.information import Information


def heuristic_chat(info: Information) -> Optional[float]:
    """对话记录快筛：过滤纯表情、纯标点符号或无实质字符的水贴消息"""
    text = info.information or ""
    valid_chars = len(re.findall(r"[\w\u4e00-\u9fa5]", text))
    if valid_chars / max(len(text), 1) < 0.30:
        return 0.1
    return None


def heuristic_web(info: Information) -> Optional[float]:
    """网页抓取快筛：拦截纯页脚版权声明、隐私协议等导航噪音"""
    text = (info.information or "").lower()
    markers = ("all rights reserved", "copyright ©", "隐私政策", "用户协议", "备案号", "icp备")
    if sum(1 for m in markers if m in text) >= 2 and len(text) < 250:
        return 0.1
    return None
