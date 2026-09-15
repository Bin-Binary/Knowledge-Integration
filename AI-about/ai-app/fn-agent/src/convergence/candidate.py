"""Candidate data class.

A Candidate is a single possible value for an FE during convergence.

Responsibilities:
  - Hold one candidate value plus its origin and scoring.
  - Carry optional metadata for downstream decisions.

Not responsibilities:
  - Candidate generation (see providers/candidate_provider.py).
  - Scoring itself (done by scoring rules or LLM, results stored here).
  - Convergence decision (see convergence/decision.py).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Source constants
# ---------------------------------------------------------------------------

SOURCE_ROLE = "role"          # from R-ROLES-00 role values
SOURCE_ENTITY = "entity"      # from entity_registry by type
SOURCE_QUERY = "query"        # from system_queries
SOURCE_QUALIA = "qualia"      # from entity qualia derivation
SOURCE_FRAME = "frame"        # from another frame's FE
SOURCE_EXPLICIT = "explicit"  # from user's explicit statement
SOURCE_DEFAULT = "default"    # from schema default strategy

VALID_SOURCES = {
    SOURCE_ROLE, SOURCE_ENTITY, SOURCE_QUERY,
    SOURCE_QUALIA, SOURCE_FRAME, SOURCE_EXPLICIT, SOURCE_DEFAULT,
}


# ---------------------------------------------------------------------------
# Candidate
# ---------------------------------------------------------------------------

@dataclass
class Candidate:
    """One possible value for an FE."""

    value: Any                     # 候选值
    source: str                    # 来源，见 SOURCE_* 常量
    score: float = 0.0             # 分数，0~1，默认未打分
    reason: str = ""               # 打分依据，供审计与 LLM 解释
    metadata: dict[str, Any] = field(default_factory=dict)  # 附加信息

    def __post_init__(self) -> None:
        if self.source not in VALID_SOURCES:
            raise ValueError(
                f"Invalid candidate source: {self.source}. "
                f"Valid: {sorted(VALID_SOURCES)}"
            )

    def set_score(self, score: float, reason: str = "") -> None:
        """Set score and optional reason. score is clamped to [0, 1]."""
        if score < 0.0:
            score = 0.0
        elif score > 1.0:
            score = 1.0
        self.score = score
        if reason:
            self.reason = reason

    def is_scored(self) -> bool:
        return self.score > 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "source": self.source,
            "score": self.score,
            "reason": self.reason,
            "metadata": self.metadata,
        }