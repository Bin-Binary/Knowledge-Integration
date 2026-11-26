# /infra/sanitization_pipeline.py
import re
import json
from typing import List, Callable, Optional
from langchain_core.runnables import RunnableLambda, RunnableSerializable

from protocols import InputSanitizerProtocol, RawPayloadRepairerProtocol

_WIN_PATH_RE = re.compile(r'(?:[a-zA-Z]:|\.\.?)(?:\\[^\s"\'<>|?*]+)+')
_CTRL_CHARS_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\u200b-\u200d\ufeff]')
# 匹配非合法 JSON 转义序列的单个反斜杠（以及非 4 位十六进制的 \u，如 C:\Users）
_INVALID_JSON_ESCAPE_RE = re.compile(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})')


def _remove_control_chars(text: str) -> str:
    return _CTRL_CHARS_RE.sub("", text)


def _normalize_windows_paths(text: str) -> str:
    return _WIN_PATH_RE.sub(lambda m: m.group(0).replace("\\", "/"), text)


def _trim_whitespace(text: str) -> str:
    return text.strip()


def repair_raw_json_bytes(raw_body: bytes) -> bytes:
    """网关前置容错：仅在标准 JSON 解码失败时，自动转义非法单反斜杠（如 Windows 路径）"""
    if not raw_body:
        return raw_body
    try:
        json.loads(raw_body)
        return raw_body
    except json.JSONDecodeError:
        text = raw_body.decode("utf-8", errors="replace")
        return _INVALID_JSON_ESCAPE_RE.sub(r"\\\\", text).encode("utf-8")


class InputSanitizationPipeline(InputSanitizerProtocol):
    """基于 LangChain Runnable 管道的前置文本清洗器"""

    def __init__(self, extra_steps: Optional[List[Callable[[str], str]]] = None) -> None:
        chain: RunnableSerializable[str, str] = (
            RunnableLambda(_remove_control_chars)
            | RunnableLambda(_normalize_windows_paths)
            | RunnableLambda(_trim_whitespace)
        )
        if extra_steps:
            for step in extra_steps:
                chain = chain | RunnableLambda(step)
        self._chain = chain

    def sanitize(self, text: str) -> str:
        return self._chain.invoke(text) if text else ""

    async def asanitize(self, text: str) -> str:
        return await self._chain.ainvoke(text) if text else ""


class LenientJsonPayloadRepairer(RawPayloadRepairerProtocol):
    """网关原始字节流容错修复器（显式实现 RawPayloadRepairerProtocol）"""

    def repair_bytes(self, raw_bytes: bytes) -> bytes:
        return repair_raw_json_bytes(raw_bytes)
