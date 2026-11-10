"""Manage chat window via sliding window
Formulas: 
• Run Time Formula: $$\text{Total\_Input\_Token} = Token_\text{Syetem\_prompt} + Token_\text{Current\_input} + Token_\text{Tool/Rag\_context} + ∑Token_\text{History\_turns}$$
• Sliding Step Size Formula: $$S_\text{Token} = Max(Total\_Input\_Token - W_\text{input\_safe}, W_\text{input\_safe} \times α)$$
"""
import logging
from typing import Optional, List, Dict, Any, Protocol, runtime_checkable
from config.config import WindowConfig

logger = logging.getLogger(__name__)

def calculate_total_input(
    static_cfg: WindowConfig,  
    current_input: str,
    rag_context: Optional[str] = None,
    history_turns: Optional[List[Dict[str, str]]] = None
) -> int:
    """
    • Run Time Formula: 
    Total_Input_Token = Token_System_prompt + Token_Current_input + Token_Tool/Rag_context + ∑Token_History_turns
    """
    total_tokens = static_cfg.token_system_prompt

    if current_input:
        total_tokens += len(static_cfg.encoder.encode(current_input))
        
    if rag_context:
        total_tokens += len(static_cfg.encoder.encode(rag_context))
        
    if history_turns:
        for turn in history_turns:
            total_tokens += len(static_cfg.encoder.encode(turn.get("content", "")))
            
    logger.info(f"[Runtime Metrics] Total Input Tokens calculated: {total_tokens}")
    return total_tokens

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
        
        if overflow <= 0 or not history_turns:
            return history_turns

        cache_protect_tokens = int(w_input_safe * self.alpha)
        s_token = max(overflow, cache_protect_tokens)

        logger.warning(f"[CacheFriendly] Breached! Target to release S_Token: {s_token}")

        safe_history = history_turns.copy()
        released = 0
        deleted_count = 0
        
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
