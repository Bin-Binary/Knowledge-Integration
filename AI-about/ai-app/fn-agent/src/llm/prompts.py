"""Prompt templates for open-choice selection.

An open-choice prompt presents:
  1. What is known (fe_name, type_ref, candidates, context).
  2. What the LLM may do (choose, or report missing).
  3. What output format is expected (strict JSON).

The LLM is NOT allowed to freely generate candidate values.
It must choose from the provided candidate list.

Important:
  - The "chosen" field must contain the candidate VALUE only.
  - Any suffix such as "[frame=...]" or "(note)" displayed in the formatted
    candidate list is for human/LLM context, not part of the value.
"""

from __future__ import annotations

import json
from typing import Any

from src.convergence.candidate import Candidate


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

OPEN_CHOICE_SYSTEM_PROMPT = """\
You are a semantic frame-filling assistant.

Task:
  Given a frame element (FE) with a fixed candidate list, choose exactly ONE
  candidate that best matches the known context.

Rules:
  1. You MUST choose from the given candidate list. Do not invent new values.
  2. The "chosen" field must be the candidate's VALUE ONLY. Do not include
     any suffix such as "[frame=...]" or "(note text)" that may appear in
     the formatted list.
  3. If no candidate fits, return chosen=null and list what information is
     missing under "missing".
  4. Provide "basis": short references to which known facts led to your choice.
  5. Provide "confidence": a float between 0 and 1.
  6. Optionally provide "reasoning_steps": a short list of intermediate steps.

Output format (strict JSON, no extra prose):
{
  "chosen": "<candidate value only, or null>",
  "basis": ["<fact 1>", "<fact 2>"],
  "confidence": <0.0-1.0>,
  "missing": ["<what is missing if chosen is null>"],
  "reasoning_steps": ["<optional step 1>", "<optional step 2>"]
}
"""


# ---------------------------------------------------------------------------
# User prompt builder
# ---------------------------------------------------------------------------

def _format_candidates(candidates: list[Candidate]) -> str:
    """Format candidates as a compact numbered list.

    Format:
      <idx>. <value> [frame=<frame_name>] (<note>)

    The bracket / paren parts are context hints for the LLM.
    The LLM is instructed to return only the value in "chosen".
    """
    lines = []
    for i, c in enumerate(candidates, 1):
        frame = c.metadata.get("frame")
        note = c.metadata.get("note", "")
        suffix = ""
        if frame:
            suffix += f" [frame={frame}]"
        if note:
            suffix += f" ({note})"
        lines.append(f"  {i}. {c.value}{suffix}")
    return "\n".join(lines)


def build_open_choice_prompt(
    fe_name: str,
    fe_type_ref: dict[str, Any],
    candidates: list[Candidate],
    known: dict[str, Any],
) -> str:
    """Build the user prompt for an open-choice selection.

    Parameters
    ----------
    fe_name : str
        The frame element name, e.g. "act".
    fe_type_ref : dict
        The FE's type reference, e.g. {"kind": "role", "ref": "ActionType"}.
    candidates : list[Candidate]
        Candidates to choose from.
    known : dict
        Known facts to inform the choice. Free-form.

    Returns
    -------
    str
        The user prompt string.
    """
    candidates_text = _format_candidates(candidates) if candidates else "  (none)"

    known_text = json.dumps(known, ensure_ascii=False, indent=2)

    prompt = f"""\
Known:
{known_text}

Frame element (FE):
  name     = {fe_name}
  type_ref = {json.dumps(fe_type_ref, ensure_ascii=False)}

Candidates:
{candidates_text}

Instruction:
  Choose exactly one candidate from the list above.
  The "chosen" field must be the candidate VALUE ONLY — do not include any
  suffix like [frame=...] or (note).
  If none fits, return chosen=null and list what is missing.
  Respond with JSON only.
"""
    return prompt


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> None:
    from src.convergence.candidate import Candidate

    cands = [
        Candidate(value="build", source="role",
                  metadata={"frame": "Processing_materials", "note": "构建新版本"}),
        Candidate(value="release", source="role",
                  metadata={"frame": "Change", "note": "发布版本"}),
        Candidate(value="rollback", source="role",
                  metadata={"frame": "Change", "note": "回滚版本"}),
    ]

    prompt = build_open_choice_prompt(
        fe_name="act",
        fe_type_ref={"kind": "role", "ref": "ActionType"},
        candidates=cands,
        known={
            "user_request": "帮我搭建新版本",
            "patient": "entity:Version:V2.3.0",
        },
    )
    print(prompt)


if __name__ == "__main__":
    _main()