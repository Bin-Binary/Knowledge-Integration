from __future__ import annotations
import json
import sys
from pathlib import Path

PIPELINE_SRC = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(PIPELINE_SRC))

from pipeline import run_pipeline_document, format_result

PYTHON_LIST_DOC = """Lists are mutable sequences, typically used to store collections of homogeneous items (where the precise degree of similarity will vary by application).

class list(iterable=(), /)

Lists may be constructed in several ways:

Using a pair of square brackets to denote the empty list: []

Using square brackets, separating items with commas: [a], [a, b, c]

Using a list comprehension: [x for x in iterable]

Using the type constructor: list() or list(iterable)

The constructor builds a list whose items are the same and in the same order as iterable items.

This method sorts the list in place, using only < comparisons between items.

sort(*, key=None, reverse=False)

sort() accepts two arguments that can only be passed by keyword (keyword-only arguments):

key specifies a function of one argument that is used to extract a comparison key from each list element.

reverse is a boolean value. If set to True, then the list elements are sorted as if each comparison were reversed.

CPython implementation detail: While a list is being sorted, the effect of attempting to mutate, or even inspect, the list is undefined."""


def _make_mock_llm_call(mock_responses: list[str]):
    call_count = [0]

    def mock_llm_call(prompt: str) -> str:
        idx = call_count[0]
        call_count[0] += 1
        if idx < len(mock_responses):
            return mock_responses[idx]
        return "[]"

    return mock_llm_call


MOCK_LLM_RESPONSES = [
    '[\n  {"word": "Lists", "selected_frame": "Aggregate", "confidence": "medium", "reasoning": "In programming, Lists are ordered collections. Aggregate frame (Individuals forming a group).", "core_fes": ["Individuals", "Aggregate"], "fe_binding": {"Individuals": "the items in the list", "Aggregate": "list"}},\n  {"word": "sequences", "selected_frame": "Sequence", "confidence": "high", "reasoning": "Sequences directly matches Sequence frame.", "core_fes": ["Entity_1", "Entity_2", "Entities"], "fe_binding": {"Entities": "items in the sequence"}},\n  {"word": "typically", "selected_frame": "Typicality", "confidence": "high", "reasoning": "Typically matches Typicality.", "core_fes": ["State_of_affairs", "Feature"], "fe_binding": {"State_of_affairs": "use of lists to store items"}},\n  {"word": "used", "selected_frame": "Using", "confidence": "low", "reasoning": "Used means utilized for a purpose. Using frame is approximate.", "core_fes": ["Agent", "Instrument", "Purpose"], "fe_binding": {"Agent": "programmer", "Instrument": "lists", "Purpose": "to store collections"}},\n  {"word": "store", "selected_frame": "Storing", "confidence": "high", "reasoning": "Store directly matches Storing frame.", "core_fes": ["Agent", "Theme", "Location"], "fe_binding": {"Agent": "implied", "Theme": "collections", "Location": "lists"}},\n  {"word": "collections", "selected_frame": "Aggregate", "confidence": "high", "reasoning": "Collections = group of individuals. Aggregate frame.", "core_fes": ["Individuals", "Aggregate"], "fe_binding": {"Individuals": "items", "Aggregate": "collections"}},\n  {"word": "homogeneous", "selected_frame": "Diversity", "confidence": "high", "reasoning": "Homogeneous matches Diversity (negative polarity).", "core_fes": ["Group", "Dimension"], "fe_binding": {"Group": "collections/items", "Dimension": "homogeneous"}},\n  {"word": "items", "selected_frame": "Entity", "confidence": "medium", "reasoning": "Items matches Entity frame.", "core_fes": ["Entity"], "fe_binding": {"Entity": "individual elements"}}\n]\n\n{"mutable": {"inferred_frame": "Change_of_state", "confidence": "low", "reasoning": "Mutable = changeable. Closest: Change_of_state.", "core_fes": ["Entity", "Final_state", "Initial_state"]}}',

    '[\n  {"word": "denote", "selected_frame": "Signification", "confidence": "medium", "reasoning": "Denote means to signify/represent. Signification frame matches.", "core_fes": ["Sign", "Signified"], "fe_binding": {"Sign": "square brackets []", "Signified": "empty list"}},\n  {"word": "empty", "selected_frame": "Absence", "confidence": "low", "reasoning": "Empty indicates absence of content.", "core_fes": ["Absent_entity", "Context"], "fe_binding": {"Absent_entity": "items", "Context": "the list"}}\n]\n{}',

    '[\n  {"word": "separating", "selected_frame": "Separation", "confidence": "medium", "reasoning": "Separating items by commas.", "core_fes": ["Parts", "Whole"], "fe_binding": {"Parts": "items [a], [a, b, c]", "Whole": "the list content"}},\n  {"word": "commas", "selected_frame": "Entity", "confidence": "low", "reasoning": "Punctuation marks. Entity is schematic.", "core_fes": ["Entity"], "fe_binding": {"Entity": "commas as delimiters"}}\n]\n{}',

    '[\n  {"word": "constructor", "selected_frame": "Creating", "confidence": "medium", "reasoning": "A constructor creates objects. Creating frame.", "core_fes": ["Creator", "Created_entity"], "fe_binding": {"Creator": "type constructor", "Created_entity": "a new list"}},\n  {"word": "iterable", "selected_frame": "Sequence", "confidence": "medium", "reasoning": "An iterable is an ordered sequence.", "core_fes": ["Entities"], "fe_binding": {"Entities": "items of the iterable"}}\n]\n{}',

    '[\n  {"word": "constructor", "selected_frame": "Creating", "confidence": "medium", "reasoning": "Constructor builds/creates a list.", "core_fes": ["Creator", "Created_entity"], "fe_binding": {"Creator": "constructor", "Created_entity": "a list"}},\n  {"word": "builds", "selected_frame": "Creating", "confidence": "medium", "reasoning": "Builds = constructs. Creating frame.", "core_fes": ["Creator", "Created_entity"], "fe_binding": {"Creator": "constructor", "Created_entity": "a list"}},\n  {"word": "order", "selected_frame": "Sequence", "confidence": "high", "reasoning": "Order matches Sequence - items in arrangement.", "core_fes": ["Entities"], "fe_binding": {"Entities": "iterable items"}},\n  {"word": "same", "selected_frame": "Similarity", "confidence": "medium", "reasoning": "Same indicates similarity. Similarity frame.", "core_fes": ["Entities", "Dimension"], "fe_binding": {"Entities": "list items and iterable items", "Dimension": "identity"}}\n]\n{}',

    '[\n  {"word": "method", "selected_frame": "Activity", "confidence": "low", "reasoning": "A method is a procedural activity.", "core_fes": ["Actor", "Action"], "fe_binding": {"Actor": "list object", "Action": "sorting"}},\n  {"word": "sorts", "selected_frame": "Ordering", "confidence": "high", "reasoning": "Sorts directly matches Ordering frame.", "core_fes": ["Ordered_entity", "Ordering_predicate"], "fe_binding": {"Ordered_entity": "list elements", "Ordering_predicate": "< comparison"}},\n  {"word": "comparisons", "selected_frame": "Judgment", "confidence": "low", "reasoning": "Comparisons involves evaluating order.", "core_fes": ["Cognizer", "Evaluee"], "fe_binding": {"Cognizer": "sort algorithm", "Evaluee": "elements"}}\n]\n{}',

    '[\n  {"word": "accepts", "selected_frame": "Receiving", "confidence": "medium", "reasoning": "Accepts = takes/receives arguments. Receiving frame.", "core_fes": ["Recipient", "Theme"], "fe_binding": {"Recipient": "sort() method", "Theme": "keyword arguments"}},\n  {"word": "keyword", "selected_frame": "Entity", "confidence": "low", "reasoning": "Programming keyword. Entity is schematic.", "core_fes": ["Entity"], "fe_binding": {"Entity": "keyword-only parameter name"}}\n]\n{}',

    '[\n  {"word": "specifies", "selected_frame": "Statement", "confidence": "medium", "reasoning": "Specifies is a directive statement.", "core_fes": ["Speaker", "Message", "Topic"], "fe_binding": {"Speaker": "documentation", "Message": "key function desc", "Topic": "sort key param"}},\n  {"word": "function", "selected_frame": "Activity", "confidence": "low", "reasoning": "Programming function = procedural unit.", "core_fes": ["Actor", "Action"], "fe_binding": {"Actor": "key function", "Action": "extract comparison key"}},\n  {"word": "extract", "selected_frame": "Removing", "confidence": "medium", "reasoning": "Extract = pull out value. Removing frame.", "core_fes": ["Agent", "Theme", "Source"], "fe_binding": {"Agent": "key function", "Theme": "comparison key", "Source": "each list element"}},\n  {"word": "comparison", "selected_frame": "Judgment", "confidence": "low", "reasoning": "Comparison key involves evaluation.", "core_fes": ["Cognizer", "Evaluee"], "fe_binding": {"Evaluee": "list elements"}}\n]\n{}',

    '[\n  {"word": "value", "selected_frame": "Entity", "confidence": "medium", "reasoning": "Value is a data entity. Entity frame.", "core_fes": ["Entity"], "fe_binding": {"Entity": "reverse parameter value"}},\n  {"word": "elements", "selected_frame": "Entity", "confidence": "medium", "reasoning": "Elements = individual items. Entity frame.", "core_fes": ["Entity"], "fe_binding": {"Entity": "list elements"}},\n  {"word": "sorted", "selected_frame": "Ordering", "confidence": "high", "reasoning": "Sorted directly matches Ordering frame.", "core_fes": ["Ordered_entity"], "fe_binding": {"Ordered_entity": "list elements"}},\n  {"word": "reversed", "selected_frame": "Ordering", "confidence": "medium", "reasoning": "Reversed = opposite order. Ordering with reversed predicate.", "core_fes": ["Ordered_entity", "Ordering_predicate"], "fe_binding": {"Ordered_entity": "list elements", "Ordering_predicate": "reversed comparison"}}\n]\n{}',
]


def run_document_example():
    print("=" * 70)
    print("FrameNet Document Pipeline - Python List Documentation Example")
    print("=" * 70)
    print("\nDocument length: " + str(len(PYTHON_LIST_DOC)) + " chars\n")

    mock_llm = _make_mock_llm_call(MOCK_LLM_RESPONSES)
    result = run_pipeline_document(
        PYTHON_LIST_DOC,
        llm_call_fn=mock_llm,
        skip_low=True,
        min_value="medium",
        doc_name="Python List",
    )

    print("-" * 50)
    print("Document Slicing")
    print("-" * 50)
    slicing = result["slicing"]["stats"]
    print("  Total fragments: " + str(slicing["total"]))
    print("  High value (nl_description): " + str(slicing["high"]))
    print("  Medium value (nl_action): " + str(slicing["medium"]))
    print("  Low value: " + str(slicing["low"]))
    print("  Skip: " + str(slicing["skip"]))
    print("  Eligible for analysis: " + str(result["slicing"]["eligible_fragments"]))
    print("  Skipped: " + str(result["slicing"]["skipped_fragments"]))

    print("\n" + "-" * 50)
    print("Overall Statistics")
    print("-" * 50)
    stats = result["statistics"]
    print("  Processed fragments: " + str(stats["processed_fragments"]))
    print("  Total annotated words: " + str(stats["total_annotated_words"]))
    print("  Unique frames: " + str(stats["unique_frames"]))
    print("  Frame relations found: " + str(stats["frame_relations_found"]))
    cd = stats["confidence_distribution"]
    print("  Confidence: high=" + str(cd["high"]) + ", medium=" + str(cd["medium"]) + ", low=" + str(cd["low"]) + ", none=" + str(cd["none"]))
    print("  FrameNet LU matched: " + str(stats["framenet_lu_matched"]))
    print("  LLM inferred: " + str(stats["llm_inferred"]))

    print("\n" + "-" * 50)
    print("Global Frame Index (Frame -> Trigger Words @ Fragments)")
    print("-" * 50)
    for frame, info in sorted(result["global_frame_index"].items()):
        words = ", ".join(info["trigger_words"])
        frags = ", ".join(info["fragments"])
        conf = info["max_confidence"]
        src = info["source"]
        print("  [" + conf + "] " + frame + " <- " + words + "  (frag: " + frags + ") [" + src + "]")

    print("\n" + "-" * 50)
    print("Cross-Frame Relations")
    print("-" * 50)
    for rel in result["frame_relations"]:
        src_f = rel["source_frame"]
        tgt_f = rel["target_frame"]
        fn_rel = rel["framenet_relation"]
        if fn_rel == "via_common_ancestor":
            ancestor = rel.get("common_ancestor", "?")
            print("  " + src_f + " <-> " + tgt_f + "  (via common ancestor: " + ancestor + ")")
        else:
            direction = rel.get("direction", "?")
            print("  " + src_f + " --" + fn_rel + "--> " + tgt_f + "  (" + direction + ")")
        if rel.get("fe_mappings"):
            for fem in rel["fe_mappings"]:
                print("    FE: " + fem)

    print("\n" + "-" * 50)
    print("Per-Fragment Annotations")
    print("-" * 50)
    for frag_id, frag_data in sorted(result["fragment_annotations"].items()):
        ftxt = frag_data["fragment_text"]
        preview = ftxt[:80] + ("..." if len(ftxt) > 80 else "")
        print("\n  Fragment " + frag_id + ": " + preview)
        for ann in frag_data["annotations"]:
            conf_map = {"high": "[H]", "medium": "[M]", "low": "[L]", "none": "[-]"}
            c = ann.get("confidence", "none")
            print("    " + conf_map.get(c, "[-]") + " " + ann.get("word", "?") + " -> " + str(ann.get("selected_frame", "?")))

    if result.get("skipped_fragments"):
        print("\n  Skipped fragments: " + ", ".join(result["skipped_fragments"]))

    output_path = Path(__file__).parent / "document_example_result.md"
    md = format_result(result)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)
    print("\n\nFull result saved to: " + str(output_path))


if __name__ == "__main__":
    run_document_example()
