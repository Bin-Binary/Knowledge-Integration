"""Open-choice selectors.

Wraps LLM calls for the "open-choice" pattern:
  - LLM must choose from a provided candidate list.
  - LLM may refuse (chosen=null) and report what is missing.
  - Output is parsed into SelectionResult.

Parsing rules:
  - The chosen value is stripped of any trailing "[frame=...]" or "(note)"
    suffix that may have been copied from the formatted candidate list.
  - If after stripping the value is empty, chosen becomes None.

Currently single-turn: no tool calls, no multi-step retrieval.
Tool calls are deferred to a later step.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from src.convergence.candidate import Candidate
from src.llm.client import get_llm
from src.llm.prompts import OPEN_CHOICE_SYSTEM_PROMPT, build_open_choice_prompt


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------

@dataclass
class SelectionResult:
    """Result of an open-choice selection."""

    chosen: str | None = None
    basis: list[str] = field(default_factory=list)
    confidence: float = 0.0
    missing: list[str] = field(default_factory=list)
    reasoning_steps: list[str] = field(default_factory=list)
    raw: str = ""                  # raw LLM output, for debugging

    def is_chosen(self) -> bool:
        return self.chosen is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "chosen": self.chosen,
            "basis": self.basis,
            "confidence": self.confidence,
            "missing": self.missing,
            "reasoning_steps": self.reasoning_steps,
        }


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)

# Strip suffixes like "[frame=...]" or "(note)" that may be appended to chosen.
_SUFFIX_RE = re.compile(r"\s*(\[[^\]]*\]|\([^)]*\))")


def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from LLM output.

    Handles:
      - pure JSON
      - ```json ... ``` blocks
      - JSON embedded with surrounding prose
    Raises ValueError if no JSON found.
    """
    text = text.strip()

    # 1. Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Try fenced block
    m = _JSON_BLOCK_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Try first {...} substring
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No JSON found in LLM output: {text[:200]}")


def _strip_suffix(value: str) -> str:
    """Remove trailing [..] or (..) segments from a chosen value.

    Examples:
      "build [frame=Processing_materials]" -> "build"
      "build (构建新版本)"                -> "build"
      "build"                             -> "build"
    """
    return _SUFFIX_RE.sub("", value).strip()


def _parse_selection(raw: str) -> SelectionResult:
    """Parse LLM output into SelectionResult."""
    try:
        data = _extract_json(raw)
    except ValueError:
        return SelectionResult(raw=raw)

    chosen_raw = data.get("chosen")
    chosen: str | None
    if chosen_raw is None:
        chosen = None
    else:
        text = chosen_raw if isinstance(chosen_raw, str) else str(chosen_raw)
        text = _strip_suffix(text)
        chosen = text if text else None

    confidence = data.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    return SelectionResult(
        chosen=chosen,
        basis=list(data.get("basis", []) or []),
        confidence=confidence,
        missing=list(data.get("missing", []) or []),
        reasoning_steps=list(data.get("reasoning_steps", []) or []),
        raw=raw,
    )


# ---------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------

def select_one(
    fe_name: str,
    fe_type_ref: dict[str, Any],
    candidates: list[Candidate],
    known: dict[str, Any],
) -> SelectionResult:
    """Ask the LLM to choose one candidate.

    Parameters
    ----------
    fe_name : str
        FE name, e.g. "act".
    fe_type_ref : dict
        FE type ref, e.g. {"kind": "role", "ref": "ActionType"}.
    candidates : list[Candidate]
        Candidates to choose from.
    known : dict
        Known facts.

    Returns
    -------
    SelectionResult
        Parsed result. If LLM refuses, chosen is None and missing is filled.
    """
    if not candidates:
        return SelectionResult(
            chosen=None,
            missing=[f"no candidates available for FE '{fe_name}'"],
        )

    llm = get_llm(temperature=0.0)
    prompt = build_open_choice_prompt(
        fe_name=fe_name,
        fe_type_ref=fe_type_ref,
        candidates=candidates,
        known=known,
    )

    from langchain_core.messages import SystemMessage, HumanMessage

    messages = [
        SystemMessage(content=OPEN_CHOICE_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    response = llm.invoke(messages)
    raw = response.content if isinstance(response.content, str) else str(response.content)

    return _parse_selection(raw)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    from src.loader.loader import load_all
    from src.loader.index import build_index
    from src.registry.entity_registry import build_entity_registry
    from src.providers.candidate_provider import CandidateProvider

    bundle = load_all()
    index = build_index(bundle)
    registry = build_entity_registry(bundle)
    provider = CandidateProvider(index=index, entity_registry=registry)

    candidates = provider.from_role("ActionType")

    known = {
        "user_request": "帮我搭建新版本",
        "patient": {
            "id": "entity:Version:V2.3.0",
            "type": "Version",
            "name": "v2.3.0",
            "qualia": {
                "formal": "版本标识",
                "telic": ["发布", "回滚", "追溯"],
                "agentive": ["由构建过程产生"],
            },
        },
        "agent": "human:user123",
        "domain": "ci",
    }

    print(f"Calling LLM with {len(candidates)} candidates for FE 'act'...")
    print()

    result = select_one(
        fe_name="act",
        fe_type_ref={"kind": "role", "ref": "ActionType"},
        candidates=candidates,
        known=known,
    )

    print("=== SelectionResult ===")
    print(f"chosen          = {result.chosen!r}")
    print(f"confidence      = {result.confidence}")
    print(f"basis           = {result.basis}")
    print(f"missing         = {result.missing}")
    print(f"reasoning_steps = {result.reasoning_steps}")
    print()
    print("=== Raw ===")
    print(result.raw)


if __name__ == "__main__":
    _main()