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
