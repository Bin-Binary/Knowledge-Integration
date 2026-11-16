# infra/observability.py（纯通用日志与观测基础设施，零业务耦合）
import contextvars
import functools
import inspect
import logging
import re
import time
import uuid
from typing import Any, Callable, Optional

# ==========================================
# 1. 全局默认配置与协程安全上下文
# ==========================================
_GLOBAL_VERBOSE_DEFAULT: bool = False

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="tr_none")
_session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("session_id", default="sess_none")
_verbose_var: contextvars.ContextVar[Optional[bool]] = contextvars.ContextVar("is_verbose", default=None)

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
) -> tuple[contextvars.Token, contextvars.Token, contextvars.Token]:
    """在请求或任务入口绑定上下文"""
    tid = trace_id or f"tr_{uuid.uuid4().hex[:12]}"
    sid = session_id or "sess_unknown"
    return (
        _trace_id_var.set(tid),
        _session_id_var.set(sid),
        _verbose_var.set(is_verbose),
    )


def reset_observability_context(tokens: tuple) -> None:
    """请求或任务结束时重置上下文"""
    t1, t2, t3 = tokens
    _trace_id_var.reset(t1)
    _session_id_var.reset(t2)
    _verbose_var.reset(t3)

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
    """
    通用执行日志装饰器（支持任意同步/异步函数）：
    - 记录开始、结束与执行耗时
    - 捕获异常记录日志后原样 raise，绝不干涉业务返回值或异常恢复流
    """
    def decorator(func: Callable) -> Callable:
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
