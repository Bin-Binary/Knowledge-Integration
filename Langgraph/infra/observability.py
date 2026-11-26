# infra/observability.py（纯通用日志、实时遥测与观测基础设施，零业务耦合）
import asyncio
import contextvars
import functools
import inspect
import logging
import re
import time
import uuid
from typing import Any, Callable, Dict, Optional

# ==========================================
# 1. 全局默认配置与协程安全上下文
# ==========================================
_GLOBAL_VERBOSE_DEFAULT: bool = False

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="tr_none")
_session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("session_id", default="sess_none")
_verbose_var: contextvars.ContextVar[Optional[bool]] = contextvars.ContextVar("is_verbose", default=None)
_stream_queue_var: contextvars.ContextVar[Optional[asyncio.Queue[Dict[str, Any]]]] = contextvars.ContextVar(
    "agent_stream_queue", default=None
)


def is_verbose_enabled() -> bool:
    """优先取当前请求的动态覆盖值，否则回退到全局 ServerConfig 设置"""
    req_override = _verbose_var.get()
    return req_override if req_override is not None else _GLOBAL_VERBOSE_DEFAULT


def get_current_trace_id() -> str:
    return _trace_id_var.get()


def get_current_session_id() -> str:
    return _session_id_var.get()


def bind_observability_context(
    trace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    is_verbose: Optional[bool] = None,
    stream_queue: Optional[asyncio.Queue[Dict[str, Any]]] = None,
) -> tuple[contextvars.Token, contextvars.Token, contextvars.Token, contextvars.Token]:
    """在请求或任务入口统一绑定全链路可观测上下文（追踪 ID、日志级别与可选流式遥测队列）"""
    tid = trace_id or f"tr_{uuid.uuid4().hex[:12]}"
    sid = session_id or "sess_unknown"
    return (
        _trace_id_var.set(tid),
        _session_id_var.set(sid),
        _verbose_var.set(is_verbose),
        _stream_queue_var.set(stream_queue),
    )


def reset_observability_context(tokens: tuple) -> None:
    """请求或任务结束时统一无损重置全部上下文"""
    t1, t2, t3, t4 = tokens
    _trace_id_var.reset(t1)
    _session_id_var.reset(t2)
    _verbose_var.reset(t3)
    _stream_queue_var.reset(t4)


def emit_component_status(
    message: str,
    *,
    phase: str = "running",
) -> None:
    """
    实时遥测状态发射器（供 components/ 自主声明暴露执行进度）：
    - 在 ainvoke_turn 非流式模式下（stream_queue=None）：自动静默跳过（No-op）
    - 在 astream_turn 流式模式下：即时投递至当前协程的遥测队列
    """
    queue = _stream_queue_var.get()
    if queue is not None and message:
        queue.put_nowait(
            {
                "type": "component_status",
                "phase": phase,
                "message": message,
            }
        )

# ==========================================
# 2. 全局日志注入与脱敏过滤器
# ==========================================
class ContextAndSanitizeFilter(logging.Filter):
    """自动注入 trace_id/session_id，并对密钥、内网 IP 及非 verbose 载荷脱敏"""

    SENSITIVE_PATTERNS = [
        (re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE), r"\1***"),
        (re.compile(r"(sk-[a-zA-Z0-9]{10,})"), r"sk-***"),
        (re.compile(r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b"), r"[INTERNAL_IP]"),
    ]
    PAYLOAD_PATTERN = re.compile(r"(<raw_payload>.*?</raw_payload>)", re.DOTALL)

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = _trace_id_var.get()
        record.session_id = _session_id_var.get()

        msg = record.getMessage()
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = pattern.sub(replacement, msg)

        if not is_verbose_enabled():
            msg = self.PAYLOAD_PATTERN.sub("[REDACTED_PAYLOAD]", msg)
            record.exc_info = None
            record.exc_text = None

        record.msg = msg
        record.args = ()
        return True


def setup_global_observability_logging(log_level: str = "info", enable_verbose: bool = False) -> None:
    """对接 ServerConfig 初始化全局日志格式与脱敏过滤器"""
    global _GLOBAL_VERBOSE_DEFAULT
    _GLOBAL_VERBOSE_DEFAULT = enable_verbose

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | [%(trace_id)s] | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if not root_logger.handlers:
        root_logger.addHandler(logging.StreamHandler())

    for handler in root_logger.handlers:
        handler.setFormatter(formatter)
        if not any(isinstance(f, ContextAndSanitizeFilter) for f in handler.filters):
            handler.addFilter(ContextAndSanitizeFilter())


# ==========================================
# 3. 纯通用执行日志装饰器（只记录耗时与错误，原样抛出异常）
# ==========================================
def log_execution(operation_name: Optional[str] = None, level: int = logging.INFO):
    def decorator(func: Callable) -> Callable:
        if inspect.isasyncgenfunction(func):
            return func

        logger = logging.getLogger(func.__module__)
        op = operation_name or func.__qualname__

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            logger.log(level, f"[{op}] started.")
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.log(level, f"[{op}] succeeded in {elapsed_ms:.1f}ms.")
                return result
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(f"[{op}] failed after {elapsed_ms:.1f}ms | error={exc}", exc_info=True)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            logger.log(level, f"[{op}] started.")
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.log(level, f"[{op}] succeeded in {elapsed_ms:.1f}ms.")
                return result
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(f"[{op}] failed after {elapsed_ms:.1f}ms | error={exc}", exc_info=True)
                raise

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
