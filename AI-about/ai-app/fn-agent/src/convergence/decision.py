"""Convergence decision helpers.

Responsibilities:
  - Define source-based priority for candidates.
  - Score candidates and pick the best one.

Not responsibilities:
  - Candidate generation (see providers/candidate_provider.py).
  - Qualia / relation resolution (see graphs/nodes/*).
  - Gap detection / user interaction (see graphs/nodes/*).

Source priority (higher = more trusted):
    explicit  > frame > entity > qualia > query > default

Rationale:
  - explicit  : user explicitly stated, highest trust.
  - frame     : derived from another frame instance already resolved.
  - entity    : concrete entity from registry.
  - qualia    : derived from entity qualia, still semantic.
  - query     : from system queries, usually lists of options.
  - default   : fallback, lowest trust.
"""

from __future__ import annotations

from src.convergence.candidate import (
    Candidate,
    SOURCE_EXPLICIT,
    SOURCE_FRAME,
    SOURCE_ENTITY,
    SOURCE_QUALIA,
    SOURCE_QUERY,
    SOURCE_DEFAULT,
    SOURCE_ROLE,
)


# ---------------------------------------------------------------------------
# Source priorities
# ---------------------------------------------------------------------------

SOURCE_PRIORITY: dict[str, int] = {
    SOURCE_EXPLICIT: 100,
    SOURCE_FRAME:     80,
    SOURCE_ENTITY:    60,
    SOURCE_QUALIA:    40,
    SOURCE_QUERY:     20,
    SOURCE_ROLE:      20,
    SOURCE_DEFAULT:   10,
}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def score_candidate(c: Candidate) -> float:
    """Score a candidate based on its source.

    Return value in [0, 1]. Only source priority is used in this step.
    Later steps may combine confidence / history / cost.
    """
    priority = SOURCE_PRIORITY.get(c.source, 0)
    return priority / 100.0


def pick_best(candidates: list[Candidate]) -> Candidate | None:
    """Pick the candidate with the highest score.

    Ties are broken by original order (first wins).

    Parameters
    ----------
    candidates : list[Candidate]
        Non-empty list.

    Returns
    -------
    Candidate | None
        Best candidate, or None if the input list is empty.
    """
    if not candidates:
        return None

    scored = [(score_candidate(c), idx, c) for idx, c in enumerate(candidates)]
    # max by score, then min by idx (earlier wins on tie)
    scored.sort(key=lambda t: (-t[0], t[1]))
    return scored[0][2]