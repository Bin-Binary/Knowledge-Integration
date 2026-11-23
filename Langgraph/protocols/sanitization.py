# /protocols/sanitization.py
from typing import Protocol, runtime_checkable


@runtime_checkable
class InputSanitizerProtocol(Protocol):
    """前置输入数据清洗器协议"""

    def sanitize(self, text: str) -> str:
        """同步清洗用户原始输入"""
        ...

    async def asanitize(self, text: str) -> str:
        """异步清洗用户原始输入"""
        ...


@runtime_checkable
class RawPayloadRepairerProtocol(Protocol):
    """网关原始字节流容错修复协议（供接入层中间件调用）"""

    def repair_bytes(self, raw_bytes: bytes) -> bytes:
        """修复原始请求体字节流中的非法转义字符"""
        ...
