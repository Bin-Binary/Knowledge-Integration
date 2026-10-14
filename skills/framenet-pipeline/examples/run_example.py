from __future__ import annotations
import json
import sys
import os
from pathlib import Path

PIPELINE_SRC = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(PIPELINE_SRC))

from framenet_retriever import retrieve
from frame_selector import build_selection_prompt, parse_llm_response
from pipeline import merge_results, format_result

MOCK_LLM_RESPONSE = r"""
[
  {
    "word": "Lists",
    "selected_frame": "Text",
    "confidence": "medium",
    "reasoning": "In programming context, a 'list' is a textual/data structure that contains items. The Text frame (a written/structured record) is closest, though it's not a perfect fit for programming lists.",
    "core_fes": ["Text"],
    "fe_binding": {
      "Text": "Lists (the data structure)"
    }
  },
  {
    "word": "sequences",
    "selected_frame": "Sequence",
    "confidence": "high",
    "reasoning": "'Sequences' directly matches the Sequence frame - entities occurring in a temporally/logically ordered arrangement. In programming, sequences are ordered collections.",
    "core_fes": ["Entity_1", "Entity_2", "Entities"],
    "fe_binding": {
      "Entities": "the items in the sequence"
    }
  },
  {
    "word": "typically",
    "selected_frame": "Typicality",
    "confidence": "high",
    "reasoning": "'Typically' directly matches the Typicality frame - describing a state of affairs as representative of its class.",
    "core_fes": ["State_of_affairs", "Feature"],
    "fe_binding": {
      "State_of_affairs": "the use of lists to store homogeneous items",
      "Feature": "typical usage pattern"
    }
  },
  {
    "word": "used",
    "selected_frame": "Emphasizing",
    "confidence": "low",
    "reasoning": "None of the candidates (Emotion_directed, Biological_urge, Being_attached etc.) match 'used' in the sense of 'utilized for a purpose'. The closest might be Emphasizing via 'focused', but this is a stretch. This word likely needs a Use/Utilization frame that doesn't exist in FrameNet v17.",
    "core_fes": ["Consideration", "Agent"],
    "fe_binding": {}
  },
  {
    "word": "store",
    "selected_frame": "Storing",
    "confidence": "high",
    "reasoning": "In 'used to store collections', 'store' is a verb meaning to put away data for safekeeping/future access. Directly matches the Storing frame (Agent places Theme in Location).",
    "core_fes": ["Agent", "Theme", "Location"],
    "fe_binding": {
      "Agent": "implied (programmer/user of lists)",
      "Theme": "collections of homogeneous items",
      "Location": "lists (the data container)"
    }
  },
  {
    "word": "collections",
    "selected_frame": "Aggregate",
    "confidence": "high",
    "reasoning": "'Collections' as a group of items matches the Aggregate frame - a collection of individuals forming a group.",
    "core_fes": ["Individuals", "Aggregate"],
    "fe_binding": {
      "Individuals": "homogeneous items",
      "Aggregate": "collections"
    }
  },
  {
    "word": "homogeneous",
    "selected_frame": "Diversity",
    "confidence": "high",
    "reasoning": "'Homogeneous' directly matches the Diversity frame (with negative polarity) - describing a group whose members are similar to each other.",
    "core_fes": ["Group", "Dimension"],
    "fe_binding": {
      "Group": "collections/items",
      "Dimension": "homogeneous (low diversity)"
    }
  },
  {
    "word": "items",
    "selected_frame": "Entity",
    "confidence": "medium",
    "reasoning": "'Items' matches the Entity frame - a highly schematic entity. In this context, items are the individual elements stored in collections.",
    "core_fes": ["Entity"],
    "fe_binding": {
      "Entity": "the individual elements in a list"
    }
  }
]

{
  "mutable": {
    "inferred_frame": "Change_of_state",
    "confidence": "low",
    "reasoning": "'Mutable' means capable of being changed after creation. The closest FrameNet frame is Change_of_state, though it describes events of change rather than the property of changeability. A better fit might be a hypothetical 'Mutability' frame.",
    "core_fes": ["Entity", "Final_state", "Initial_state"]
  }
}
"""


def run_example():
    text = "Lists are mutable sequences, typically used to store collections of homogeneous items"

    print("=" * 60)
    print("FrameNet Pipeline - End-to-End Example")
    print("=" * 60)
    print(f"\nInput: {text}\n")

    print("-" * 40)
    print("Stage 1: FrameNet LU Retrieval")
    print("-" * 40)
    retrieval = retrieve(text)
    print(f"  Total tokens: {retrieval['tokens_total']}")
    print(f"  Content tokens: {retrieval['content_tokens']}")
    print(f"  Words with candidates: {len(retrieval['frame_candidates'])}")
    print(f"  Zero-hit words: {len(retrieval['zero_hit_words'])}")
    for item in retrieval["frame_candidates"]:
        frames = [c["frame_name"] for c in item["candidates"]]
        notes = f" (via {item['candidates'][0].get('matched_via', 'direct')})" if item['candidates'][0].get('matched_via') else ""
        print(f"    {item['word']:15s} -> {', '.join(frames)}{notes}")
    for zh in retrieval["zero_hit_words"]:
        print(f"    {zh['word']:15s} -> (no match)")

    print(f"\n-" * 40)
    print("Stage 2: LLM Frame Selection")
    print("-" * 40)
    prompt = build_selection_prompt(retrieval)
    print(f"  Prompt length: {len(prompt)} chars")
    print(f"  (Prompt sent to LLM, awaiting response...)")
    print(f"\n  Using mock LLM response for demo...\n")

    selection = parse_llm_response(MOCK_LLM_RESPONSE)
    result = merge_results(retrieval, selection)

    print("-" * 40)
    print("Final Annotated Result")
    print("-" * 40)
    stats = result["statistics"]
    print(f"  Annotated words: {stats['annotated_words']}/{stats['total_content_words']}")
    print(f"  Confidence: high={stats['confidence_distribution']['high']}, "
          f"medium={stats['confidence_distribution']['medium']}, "
          f"low={stats['confidence_distribution']['low']}, "
          f"none={stats['confidence_distribution']['none']}")
    print(f"  FrameNet LU matched: {stats['framenet_lu_matched']}")
    print(f"  LLM inferred: {stats['llm_inferred']}")
    print()

    for ann in result["annotations"]:
        confidence_icon = {"high": "[H]", "medium": "[M]", "low": "[L]", "none": "[-]"}[ann["confidence"]]
        source_tag = {"framenet_lu": "FN", "llm_inference": "AI", "none": "--"}[ann["source"]]
        print(f"  {confidence_icon} {source_tag} {ann['word']:15s} -> {ann['selected_frame']}")
        if ann["fe_binding"]:
            for fe, val in ann["fe_binding"].items():
                print(f"      {fe}: {val}")

    print(f"\n-" * 40)
    print("Frame Index (Frame -> Words)")
    print("-" * 40)
    for frame, words in sorted(result["frame_index"].items()):
        print(f"  {frame:25s} <- {', '.join(words)}")

    output_path = Path(__file__).parent / "example_result.md"
    md = format_result(result)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    print("\nFull result saved to: " + str(output_path))


if __name__ == "__main__":
    run_example()
