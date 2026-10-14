from __future__ import annotations
import json
import os
from pathlib import Path

PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def _load_prompt(name: str) -> str:
    path = PROMPT_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def build_selection_prompt(retrieval_result: dict, fragment_context: dict | None = None) -> str:
    template = _load_prompt("frame_selection.md")
    if not template:
        template = DEFAULT_SELECTION_PROMPT

    text = retrieval_result["text"]
    candidates_json = json.dumps(
        retrieval_result["frame_candidates"], indent=2, ensure_ascii=False
    )
    zero_hit_json = json.dumps(
        retrieval_result["zero_hit_words"], indent=2, ensure_ascii=False
    )

    prompt = template.replace("{{TEXT}}", text)
    prompt = prompt.replace("{{CANDIDATES}}", candidates_json)
    prompt = prompt.replace("{{ZERO_HIT_WORDS}}", zero_hit_json)

    if fragment_context:
        loc = fragment_context.get("source_location", {})
        loc_str = f"Paragraph {loc.get('paragraph', '?')}"
        if loc.get("sentence"):
            loc_str += f", Sentence {loc['sentence']}"
        prompt = prompt.replace("{{FRAGMENT_ID}}", fragment_context.get("id", "N/A"))
        prompt = prompt.replace("{{FRAGMENT_LOCATION}}", loc_str)
        prompt = prompt.replace("{{DOCUMENT_TOPIC}}", fragment_context.get("doc_topic", "N/A"))
        prompt = prompt.replace("{{PREV_FRAGMENT}}", str(fragment_context.get("prev_text", "none")) if fragment_context.get("prev_text") else "(none - first fragment)")
        prompt = prompt.replace("{{NEXT_FRAGMENT}}", str(fragment_context.get("next_text", "none")) if fragment_context.get("next_text") else "(none - last fragment)")
    else:
        for placeholder in ["{{FRAGMENT_ID}}", "{{FRAGMENT_LOCATION}}", "{{DOCUMENT_TOPIC}}", "{{PREV_FRAGMENT}}", "{{NEXT_FRAGMENT}}"]:
            prompt = prompt.replace(placeholder, "N/A")

    return prompt


def _extract_json_blocks(text: str) -> list[str]:
    blocks = []
    i = 0
    while i < len(text):
        if text[i] in ("[", "{"):
            depth = 0
            start = i
            in_string = False
            escape = False
            while i < len(text):
                ch = text[i]
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"' and not escape:
                    in_string = not in_string
                elif not in_string:
                    if ch in ("[", "{"):
                        depth += 1
                    elif ch in ("]", "}"):
                        depth -= 1
                        if depth == 0:
                            blocks.append(text[start : i + 1])
                            break
                i += 1
        i += 1
    return blocks


def parse_llm_response(response_text: str) -> dict:
    selections = []
    supplement = {}

    blocks = _extract_json_blocks(response_text)
    for block in blocks:
        try:
            obj = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, list):
            selections = obj
        elif isinstance(obj, dict):
            if any(isinstance(v, dict) and "inferred_frame" in v for v in obj.values()):
                supplement = obj
            elif "selections" in obj and isinstance(obj["selections"], list):
                selections = obj["selections"]
                supplement = obj.get("supplement", supplement)

    return {
        "selections": selections,
        "supplement": supplement,
    }


DEFAULT_SELECTION_PROMPT = """You are a FrameNet semantic analyst. Your task is to select the most appropriate FrameNet frame for each content word in the given text, based on the candidate frames retrieved from FrameNet.

## Input Text
{{TEXT}}

## Candidate Frames (from FrameNet retrieval)
{{CANDIDATES}}

## Zero-hit Words (no FrameNet LU found)
{{ZERO_HIT_WORDS}}

## Instructions

### Step 1: Frame Selection (for words with candidates)
For each word with candidate frames, select the ONE best frame that matches the word's meaning **in this specific context**. Apply word sense disambiguation:
- Consider the surrounding context to determine the correct sense
- If no candidate fits the contextual meaning, mark confidence as "low"

### Step 2: Zero-hit Word Annotation
For words with no FrameNet LU match, try to assign a reasonable frame by semantic reasoning:
- Map to the closest existing FrameNet frame by meaning
- Set `source` to "llm_inference" instead of "framenet_lu"
- Set confidence to "low" or "medium" (never "high" for inferred frames)

## Output Format

Return a JSON array for frame selections:
```json
[
  {
    "word": "store",
    "selected_frame": "Storing",
    "confidence": "high",
    "reasoning": "In context 'used to store collections', store is a verb meaning to put away for safekeeping, matching the Storing frame with Agent/Theme/Location FEs.",
    "core_fes": ["Agent", "Theme", "Location"],
    "fe_binding": {
      "Agent": "implied (programmer/user)",
      "Theme": "collections of homogeneous items",
      "Location": "lists (container)"
    }
  }
]
```

Then return a JSON object for zero-hit word supplements:
```json
{
  "mutable": {
    "inferred_frame": "Change_of_state",
    "confidence": "low",
    "reasoning": "'mutable' means capable of change; the closest frame is Change_of_state, though it typically describes events rather than properties.",
    "core_fes": ["Entity", "Final_state", "Initial_state"]
  }
}
```

## Confidence Levels
- **high**: FrameNet LU directly matches the word in this context, core FEs align well
- **medium**: FrameNet LU exists but the match is approximate; FE binding is partial
- **low**: No direct LU match; frame assigned by LLM inference alone

## Important Rules
1. Only select from the provided candidates (don't invent frame names for Step 1)
2. Explain your reasoning for each selection
3. Attempt FE binding: map sentence constituents to core frame elements
4. Consider cross-word frame relations (e.g., if "store" triggers Storing and "collections" triggers Aggregate, note the container-content relation)
"""


if __name__ == "__main__":
    import sys
    retrieval_path = sys.argv[1] if len(sys.argv) > 1 else None
    if retrieval_path:
        with open(retrieval_path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        from framenet_retriever import retrieve
        data = retrieve("Lists are mutable sequences, typically used to store collections of homogeneous items")

    prompt = build_selection_prompt(data)
    print(prompt)
