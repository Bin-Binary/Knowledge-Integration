# infra/observability.py（纯通用日志与观测基础设施，零业务耦合）
import contextlib
import contextvars
import functools
import inspect
import logging
import re
import time
import uuid
from typing import Any, Callable, Iterator, Optional

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


@contextlib.contextmanager
def observability_scope(
    trace_id: Optional[str] = None,
    session_id: Optional[str] = None,
    is_verbose: Optional[bool] = None,
) -> Iterator[str]:
    """上下文管理器语法糖：自动绑定并在退出时安全重置，返回当前生效的 trace_id"""
    tokens = bind_observability_context(trace_id, session_id, is_verbose)
    try:
        yield get_current_trace_id()
    finally:
        reset_observability_context(tokens)


# ==========================================
# 2. 全局日志注入与脱敏过滤器
# ==========================================
class ContextAndSanitizeFilter(logging.Filter):
    """对密钥、内网 IP 及非 verbose 载荷进行脱敏"""

    SENSITIVE_PATTERNS = [
        (re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE), r"\1***"),
        (re.compile(r"(sk-[a-zA-Z0-9]{10,})"), r"sk-***"),
        (
            re.compile(
                r"\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b"
            ),
            r"[INTERNAL_IP]",
        ),
    ]
    PAYLOAD_PATTERN = re.compile(r"(<raw_payload>.*?</raw_payload>)", re.DOTALL)

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        for pattern, replacement in cls.SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        if not is_verbose_enabled():
            text = cls.PAYLOAD_PATTERN.sub("[REDACTED_PAYLOAD]", text)
        return text

    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = _trace_id_var.get()
        record.session_id = _session_id_var.get()

        # 1. 脱敏主消息
        msg = self.sanitize_text(record.getMessage())
        record.msg = msg
        record.args = ()

        # 2. 保留异常堆栈（方便生产排错），但对格式化后的堆栈文本同样执行脱敏（防止密钥泄露在异常信息中）
        if record.exc_info and not record.exc_text:
            formatter = logging.Formatter()
            raw_exc_text = formatter.formatException(record.exc_info)
            record.exc_text = self.sanitize_text(raw_exc_text)

        return True


def setup_global_observability_logging(log_level: str = "info", enable_verbose: bool = False) -> None:
    """对接 ServerConfig 初始化全局日志格式与脱敏过滤器"""
    global _GLOBAL_VERBOSE_DEFAULT
    _GLOBAL_VERBOSE_DEFAULT = enable_verbose

    # 从底层 LogRecord 工厂注入默认字段，彻底杜绝任何动态 Handler 报 KeyError: 'trace_id'
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        if not hasattr(record, "trace_id"):
            record.trace_id = _trace_id_var.get()
        if not hasattr(record, "session_id"):
            record.session_id = _session_id_var.get()
        return record

    logging.setLogRecordFactory(record_factory)

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
