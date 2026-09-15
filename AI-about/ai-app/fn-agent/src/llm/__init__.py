"""LLM package.

Exposes:
  - get_llm:    create a ChatOpenAI instance
  - selectors:  open-choice selection calls
"""

from .client import get_llm
from .selectors import SelectionResult, select_one

__all__ = ["get_llm", "SelectionResult", "select_one"]