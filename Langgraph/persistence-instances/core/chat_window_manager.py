"""Manage chat window via sliding window
Formulas: 
• Run Time Formula: $$\text{Total\_Input\_Token} = Token_\text{Syetem\_prompt} + Token_\text{Current\_input} + Token_\text{Tool/Rag\_context} + ∑Token_\text{History\_turns}$$
• Sliding Step Size Formula: $$S_\text{Token} = Max(Total\_Input\_Token - W_\text{input\_safe}, W_\text{input\_safe} \times α)$$

Execution Pipeline：
[开始单轮对话请求]
  │
  ├──► 1. 检查 TTL 超时 ──► 交互间隔 > TTL (30min)？ ──► 是 ──► 清空所有历史 (Flush)
  │                                                      
  ├──► 2. 检查轮次死线 ──► 消息总数 > N_max (20条)？ ──► 是 ──► 强制弹出最老历史 (FIFO)
  │
  ├──► 3. 称量运行时总体积 ──► 计算 Total_Input_Token 
  │
  └──► 4. 判定边界触发 (Trigger Condition) 
            │
            ├─── (Total_Input_Token <= W_input_safe) ───► [安全放行，提交大模型 API]
            │
            └─── (Total_Input_Token > W_input_safe) 
                      │
                      ├──► 计算最优滑动步长 S_Token = Max(Δ, W_input_safe * α)
                      │
                      ├──► 判断历史容量是否足够承载步长？
                      │         │
                      │         ├─── [足够] ──► 执行 Level 1: 块级历史滑动弹出 (保护 Prompt Cache)
                      │         │
                      │         └─── [不够] ──► 执行 Level 2: 清空全部历史 + 强行剪枝 RAG/工具长文本
                      │
                      └─► [重新校验水位] ───► [绝对安全放行]
"""
import time
import logging
from typing import Optional, List, Dict, Any, Protocol, runtime_checkable
from config.config import WindowConfig

logger = logging.getLogger(__name__)

def calculate_total_input(
    static_cfg: WindowConfig,  
    current_input: str,
    rag_context: Optional[str] = None,
    history_turns: Optional[List[Dict[str, str]]] = None
) -> tuple[int, List[int]]:
    """
    • Run Time Formula: 
    Total_Input_Token = Token_System_prompt + Token_Current_input + Token_Tool/Rag_context + ∑Token_History_turns
    
    Optimization: One-time calibration returning (Total_Tokens, msg_tokens) weight lists simultaneously, completely eliminating redundant computations within strategy classes.
    """
    total_tokens = static_cfg.token_system_prompt

    if current_input:
        total_tokens += len(static_cfg.encoder.encode(current_input))
        
    if rag_context:
        total_tokens += len(static_cfg.encoder.encode(rag_context))
        
    msg_tokens: List[int] = []
    if history_turns:
        for turn in history_turns:
            token_len = len(static_cfg.encoder.encode(turn.get("content", "")))
            msg_tokens.append(token_len)
            total_tokens += token_len
            
    logger.info(f"[Runtime Metrics] Total Input Tokens calculated: {total_tokens}")
    return total_tokens, msg_tokens

def execute_window_pipeline(
    static_cfg: WindowConfig,
    strategy: Any,  
    messages: List[Dict[str, str]],
    current_input: str,
    rag_context: Optional[str] = None,
    last_interaction_time: Optional[float] = None,
    max_turns: int = 20,
    ttl_seconds: int = 1800,
    alpha: float = 0.15
) -> tuple[List[Dict[str, str]], Optional[str]]:
    """
    Dialogue Window Management Main Control Engine Execution Pipeline: 
    1. TTL Timeout -> 2. Turn Boundary -> 3. Volume Calibration -> 4. Boundary Determination and Two-Tier Degradation Scheduling.
    """

    """Specification: Detach from external references via shallow copying, 
    absolutely preventing any in-place mutations from causing side effects on external business logic.
    """
    safe_history = messages.copy()
    safe_rag_context = rag_context

    current_time = time.time()
    if last_interaction_time is not None and (current_time - last_interaction_time) > ttl_seconds:
        """Trigger the TTL circuit breaker to immediately flush the historical queue."""
        logger.warning(f"[Pipeline Step 1] session time out ({current_time - last_interaction_time:.1f}s > {ttl_seconds}s). Execute Flush to Clear History.")
        return [], safe_rag_context

    if len(safe_history) > max_turns:
        oversized = len(safe_history) - max_turns
        logger.warning(
            f"[Pipeline Step 2] Turn count ceiling reached ({len(safe_history)} > {max_turns}). "
            f"Executing forced FIFO eviction of the {oversized} oldest historical turns."
        )
        safe_history = safe_history[oversized:]

    total_input_token, msg_tokens = calculate_total_input(
        static_cfg=static_cfg,
        current_input=current_input,
        rag_context=rag_context,
        history_turns=safe_history
    )

    if total_input_token <= static_cfg.w_input_safe:
        logger.info("[Pipeline Step 4] Watermark within safe limit (<= W_input_safe). Fast-track granted for direct passage.")
        return safe_history, safe_rag_context

    overflow = total_input_token - static_cfg.w_input_safe
    total_history_capacity = sum(msg_tokens)
    
    cache_protect_tokens = int(static_cfg.w_input_safe * alpha)
    s_token = max(overflow, cache_protect_tokens)
    
    logger.warning(f"[Pipeline Step 4] Watermark overflow! Excess: {overflow}, Target token release S_Token: {s_token}, Current total historical capacity: {total_history_capacity}.")


    if total_history_capacity >= s_token:
        """Evaluate whether the historical queue capacity is sufficient to sustain the expected sliding stride:
        SUFFICIENT Execute Level 1: Block-Level History Sliding Eviction (Prompt Cache Preservation)
	    Decoupled Invocation: Dispatch the pre-calculated full dataset to the dedicated strategy class, which performs pure mathematical slicing."""

        logger.info("[Pipeline -> Level 1] Historical capacity is sufficient; triggering the block-level history sliding preservation strategy.")
        
        """Strategy-Specific Fine-Tuning: Since CacheFriendly strictly focuses on S_token, this parameter can be dynamically passed through via kwargs."""
        safe_history = strategy.slice_history(
            history_turns=safe_history,
            msg_tokens=msg_tokens,
            overflow=overflow,
            w_input_safe=static_cfg.w_input_safe
        )
        return safe_history, safe_rag_context
    else:
        """INSUFFICIENT Execute Level 2: Full History Flush + Enforced RAG/Tool Long-Text Pruning
	    1. Completely purge all historical dialogues.
	    2. Enforce pruning on long texts within RAG/Tool contexts.
        """
        logger.critical("[Pipeline -> Level 2] Extreme overflow! The system cannot return to the safety margin even after completely purging all history. Activating Level 2 forced truncation and degradation!")
        safe_history.clear()
        """Enforce pruning on long texts within RAG/Tool contexts."""
        remaining_excess = (static_cfg.token_system_prompt + static_cfg.count_tokens(current_input) + static_cfg.count_tokens(safe_rag_context)) - static_cfg.w_input_safe
        if remaining_excess > 0 and safe_rag_context:
            """Enforce physical slicing and truncation on the RAG text using the tokenizer to bring it back within the safe watermark."""
            rag_encoded = static_cfg.encoder.encode(safe_rag_context)
            allowed_rag_tokens = max(0, len(rag_encoded) - remaining_excess - 100) # 额外多留100个安全Buffer
            """Decode the truncated tokens back into a string format to complete the hard pruning process."""
            safe_rag_context = static_cfg.encoder.decode(rag_encoded[:allowed_rag_tokens])
            logger.error(f"[Level 2 Edge Defense] WARNING: Enforced a hardware truncation on Tool/Rag_context from {len(rag_encoded)} to {allowed_rag_tokens} tokens!")
        return safe_history, safe_rag_context

class CacheFriendlyBlockStrategy:
    """
    Sliding step via Cache-Friendly Dynamic Block Step Strategy.
    
    Sliding Step Size Formula: 
    S_Token = Max(Total_Input_Token - W_input_safe, W_input_safe × α)
    """
    def __init__(self, alpha: float = 0.15) -> None:
        self.alpha = alpha

    def slice_history(
        self, 
        history_turns: List[Dict[str, str]],
        msg_tokens: List[int],
        overflow: int,
        w_input_safe: int,
        **kwargs: Any
    ) -> List[Dict[str, str]]:
        """Google-grade linter defense: Explicitly declare that the parameter exists solely for protocol alignment and remains unconsumed by the current strategy."""
        _ = kwargs
        if overflow <= 0 or not history_turns:
            return history_turns

        cache_protect_tokens = int(w_input_safe * self.alpha)
        s_token = max(overflow, cache_protect_tokens)

        logger.warning(f"[CacheFriendly] Breached! Target to release S_Token: {s_token}")

        safe_history = history_turns.copy()
        released = 0
        deleted_count = 0
        """Append boundary protection conditions to eliminate IndexError caused by array asymmetry under extreme high-concurrency environments."""
        while safe_history and released < s_token and deleted_count < len(msg_tokens):
            released += msg_tokens[deleted_count]
            safe_history.pop(0) 
            deleted_count += 1
            
        return safe_history


class TurnByTurnEvictionStrategy:
    """
    Sliding step via Turn-by-Turn Strategy.
    """
    def slice_history(
        self, 
        history_turns: List[Dict[str, str]],
        msg_tokens: List[int],
        overflow: int,
        w_input_safe: int,
        **kwargs: Any
    ) -> List[Dict[str, str]]:
        """Google-grade linter defense: Explicitly declare that the parameter exists solely for protocol alignment and remains unconsumed by the current strategy."""
        _, _ = w_input_safe, kwargs
        if overflow <= 0 or not history_turns:
            return history_turns

        logger.warning(f"[TurnByTurn] Breached! Need to clear overflow: {overflow}")
        
        safe_history = history_turns.copy()
        deleted_count = 0
        
        while safe_history and overflow > 0 and deleted_count < len(msg_tokens):
            evicted_token = msg_tokens[deleted_count]
            overflow -= evicted_token
            safe_history.pop(0)
            deleted_count += 1

        return safe_history
