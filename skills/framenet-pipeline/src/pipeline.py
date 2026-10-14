from __future__ import annotations
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional

SRC_DIR = Path(__file__).parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from framenet_retriever import retrieve
from frame_selector import build_selection_prompt, parse_llm_response
from document_slicer import slice_document
from result_merger import merge_fragment_results, query_frame_relations
from md_formatter import format_result


def stage1_retrieve(text: str, pos_tags: dict | None = None) -> dict:
    return retrieve(text, pos_tags=pos_tags)


def stage2_build_prompt(retrieval_result: dict, fragment_context: dict | None = None) -> str:
    return build_selection_prompt(retrieval_result, fragment_context=fragment_context)


def stage2_parse_response(response_text: str) -> dict:
    return parse_llm_response(response_text)


def merge_results(retrieval_result: dict, selection_result: dict) -> dict:
    word_selections = {s["word"]: s for s in selection_result.get("selections", [])}
    supplement = selection_result.get("supplement", {})

    annotated = []
    for item in retrieval_result["frame_candidates"]:
        word = item["word"]
        sel = word_selections.get(word)
        if sel:
            annotated.append({
                "word": word,
                "position": item["position"],
                "selected_frame": sel.get("selected_frame"),
                "confidence": sel.get("confidence"),
                "reasoning": sel.get("reasoning"),
                "core_fes": sel.get("core_fes", []),
                "fe_binding": sel.get("fe_binding", {}),
                "all_candidates": [c["frame_name"] for c in item["candidates"]],
                "source": "framenet_lu",
            })

    for zh in retrieval_result["zero_hit_words"]:
        word = zh["word"]
        sup = supplement.get(word)
        if sup:
            annotated.append({
                "word": word,
                "position": zh["position"],
                "selected_frame": sup.get("inferred_frame"),
                "confidence": sup.get("confidence"),
                "reasoning": sup.get("reasoning"),
                "core_fes": sup.get("core_fes", []),
                "fe_binding": {},
                "all_candidates": [],
                "source": "llm_inference",
            })
        else:
            annotated.append({
                "word": word,
                "position": zh["position"],
                "selected_frame": None,
                "confidence": "none",
                "reasoning": "No FrameNet match and LLM did not infer a frame",
                "core_fes": [],
                "fe_binding": {},
                "all_candidates": [],
                "source": "none",
            })

    high = sum(1 for a in annotated if a["confidence"] == "high")
    medium = sum(1 for a in annotated if a["confidence"] == "medium")
    low = sum(1 for a in annotated if a["confidence"] == "low")
    none_c = sum(1 for a in annotated if a["confidence"] == "none")

    return {
        "text": retrieval_result["text"],
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "total_content_words": retrieval_result["content_tokens"],
            "annotated_words": len(annotated),
            "confidence_distribution": {"high": high, "medium": medium, "low": low, "none": none_c},
            "framenet_lu_matched": sum(1 for a in annotated if a["source"] == "framenet_lu"),
            "llm_inferred": sum(1 for a in annotated if a["source"] == "llm_inference"),
            "unmatched": sum(1 for a in annotated if a["source"] == "none"),
        },
        "annotations": annotated,
        "frame_index": _build_frame_index(annotated),
    }


def _build_frame_index(annotations: list[dict]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for a in annotations:
        frame = a.get("selected_frame")
        if frame:
            index.setdefault(frame, []).append(a["word"])
    return index


def run_pipeline(text: str, llm_response: str | None = None, output_path: str | None = None, output_format: str = "md") -> dict:
    retrieval = stage1_retrieve(text)
    prompt = stage2_build_prompt(retrieval)

    if llm_response:
        selection = stage2_parse_response(llm_response)
        result = merge_results(retrieval, selection)
    else:
        result = {
            "text": text,
            "timestamp": datetime.now().isoformat(),
            "stage1_retrieval": retrieval,
            "stage2_prompt": prompt,
            "stage2_status": "pending",
            "message": "Pass the prompt to an LLM and feed its response back via llm_response parameter",
        }

    if output_path:
        _write_output(result, output_path, output_format)

    return result


VALUE_ORDER = {"high": 3, "medium": 2, "low": 1, "skip": 0}


def _build_fragment_context(frag: dict, fragments: list[dict], doc_topic: str) -> dict:
    prev_text = ""
    next_text = ""
    prev_id = frag.get("prev_fragment_id")
    next_id = frag.get("next_fragment_id")
    for f in fragments:
        if f["id"] == prev_id:
            prev_text = f["text"]
        if f["id"] == next_id:
            next_text = f["text"]

    return {
        "id": frag["id"],
        "source_location": frag.get("source_location", {}),
        "doc_topic": doc_topic,
        "prev_text": prev_text,
        "next_text": next_text,
    }


def run_pipeline_document(
    text: str,
    llm_call_fn: Callable[[str], str] | None = None,
    skip_low: bool = True,
    min_value: str = "medium",
    doc_name: str = "",
    output_path: str | None = None,
    output_format: str = "md",
) -> dict:
    min_val_score = VALUE_ORDER.get(min_value, 2)

    sliced = slice_document(text, doc_name=doc_name)
    fragments = sliced["fragments"]

    eligible = []
    skipped_ids = []
    for frag in fragments:
        val_score = VALUE_ORDER.get(frag["value"], 0)
        if skip_low and frag["value"] in ("low", "skip"):
            skipped_ids.append(frag["id"])
            continue
        if val_score < min_val_score:
            skipped_ids.append(frag["id"])
            continue
        eligible.append(frag)

    doc_topic = doc_name or sliced.get("source", "")
    fragment_results = []

    for frag in eligible:
        frag_ctx = _build_fragment_context(frag, fragments, doc_topic)

        retrieval = stage1_retrieve(frag["text"])
        prompt = stage2_build_prompt(retrieval, fragment_context=frag_ctx)

        if llm_call_fn is not None:
            llm_resp = llm_call_fn(prompt)
            selection = stage2_parse_response(llm_resp)
            merged = merge_results(retrieval, selection)
            fragment_results.append({
                "fragment_id": frag["id"],
                "fragment_text": frag["text"],
                "category": frag["category"],
                "value": frag["value"],
                "annotations": merged["annotations"],
                "skipped": False,
            })
        else:
            fragment_results.append({
                "fragment_id": frag["id"],
                "fragment_text": frag["text"],
                "category": frag["category"],
                "value": frag["value"],
                "stage1_retrieval": retrieval,
                "stage2_prompt": prompt,
                "stage2_status": "pending",
                "annotations": [],
                "skipped": False,
            })

    for sid in skipped_ids:
        fragment_results.append({
            "fragment_id": sid,
            "fragment_text": "",
            "category": "skipped",
            "value": "skip",
            "annotations": [],
            "skipped": True,
        })

    document_result = merge_fragment_results(fragment_results, doc_source=doc_name or sliced.get("source", ""))
    document_result["slicing"] = {
        "stats": sliced["stats"],
        "eligible_fragments": len(eligible),
        "skipped_fragments": len(skipped_ids),
        "min_value_filter": min_value,
    }

    if llm_call_fn is None:
        document_result["stage2_status"] = "pending"
        document_result["message"] = "No LLM call function provided. Prompts are generated per fragment. Provide llm_call_fn to complete pipeline."
        document_result["fragment_prompts"] = {
            fr["fragment_id"]: fr.get("stage2_prompt", "")
            for fr in fragment_results if not fr["skipped"]
        }

    if output_path:
        _write_output(document_result, output_path, output_format)

    return document_result


def _write_output(result: dict, output_path: str, output_format: str = "md"):
    if output_format == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    else:
        p = Path(output_path)
        if p.suffix not in (".md", ".markdown"):
            p = p.with_suffix(".md")
        md_content = format_result(result)
        with open(str(p), "w", encoding="utf-8") as f:
            f.write(md_content)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FrameNet Pipeline: Retrieval + LLM Selection")
    parser.add_argument("text", nargs="?", default="Lists are mutable sequences, typically used to store collections of homogeneous items")
    parser.add_argument("--llm-response", type=str, help="Path to file containing LLM response for Stage 2")
    parser.add_argument("--output", "-o", type=str, help="Output file path (.md or .json)")
    parser.add_argument("--format", "-f", type=str, default="md", choices=["md", "json"], help="Output format (default: md)")
    parser.add_argument("--prompt-only", action="store_true", help="Only output the Stage 2 prompt (for manual LLM call)")
    args = parser.parse_args()

    if args.prompt_only:
        retrieval = stage1_retrieve(args.text)
        prompt = stage2_build_prompt(retrieval)
        print(prompt)
    elif args.llm_response:
        with open(args.llm_response, encoding="utf-8") as f:
            llm_resp = f.read()
        result = run_pipeline(args.text, llm_response=llm_resp, output_path=args.output, output_format=args.format)
        if not args.output:
            if args.format == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(format_result(result))
    else:
        result = run_pipeline(args.text, output_path=args.output, output_format=args.format)
        if args.output:
            out_name = args.output
            if args.format != "json" and not Path(args.output).suffix in (".md", ".markdown"):
                out_name = Path(args.output).with_suffix(".md").name
            print("Output saved to " + out_name)
            if not result.get("stage2_prompt"):
                pass
            else:
                print("Stage 2 prompt is included. Pass it to an LLM and re-run with --llm-response")
        else:
            if args.format == "json":
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                if result.get("stage2_status") == "pending":
                    print("Stage 1 complete. Stage 2 prompt generated but needs LLM. Use --llm-response to complete.")
                else:
                    print(format_result(result))
