from __future__ import annotations
import re
import json
from typing import Optional

CODE_SIGNATURE_PAT = re.compile(
    r'\w+\s*\([^)]*[/,][^)]*\)'  
    r'|\w+\([^)]*=\s*None[^)]*\)'
    r'|\w+\([^)]*\*\s*[^)]*\)'
    r'|\w+\([^)]*\*\*[^)]*\)'
)

BACKTICK_PAT = re.compile(r'`[^`]+`')

RETURNS_EXAMPLE_PAT = re.compile(r'\[.*\]\s+returns\s+\[|returns\s+\[|returns\s+\{')

IMPL_DETAIL_PAT = re.compile(
    r'implementation\s+detail|CPython|thread.safety|thread-safe|implementation\s+note',
    re.IGNORECASE,
)

ACTION_DESC_PAT = re.compile(
    r'(?:This|The|A|An)\s+(?:method|function|class|constructor|operation|process|action|approach)\s+'
    r'(?:sorts?|modifies?|changes?|creates?|builds?|returns?|produces?|accepts?|takes?|'
    r'specifies?|guarantees?|operates?|means?|allows?|provides?|'
    r'extracts?|converts?|calculates?|compares?|attempts?|reminds?|inspects?)\b',
    re.IGNORECASE,
)


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r'\n\s*\n', text)
    return [p.strip() for p in parts if p.strip()]


def _split_sentences(paragraph: str) -> list[str]:
    sents = re.split(r'(?<=[.!?])\s+(?=[A-Z])', paragraph)
    return [s.strip() for s in sents if s.strip()]


def _classify_fragment(text: str) -> dict:
    code_sig_score = len(CODE_SIGNATURE_PAT.findall(text))
    backtick_score = len(BACKTICK_PAT.findall(text))
    returns_score = 1 if RETURNS_EXAMPLE_PAT.search(text) else 0
    impl_score = 1 if IMPL_DETAIL_PAT.search(text) else 0
    action_score = 1 if ACTION_DESC_PAT.search(text) else 0

    has_natural_lang = bool(re.search(r'[A-Za-z]{3,}(?:\s+[A-Za-z]{3,}){2,}', text))
    code_ratio = (code_sig_score + backtick_score + returns_score) / max(len(text.split()), 1)
    is_class_def = bool(re.match(r'^\s*class\s+\w+', text))

    if is_class_def:
        return {"category": "code_syntax", "value": "low", "score": 2}

    if impl_score:
        return {"category": "impl_detail", "value": "skip", "score": impl_score}

    if code_sig_score >= 1 and code_ratio > 0.1:
        return {"category": "code_syntax", "value": "low", "score": code_sig_score}

    if (backtick_score >= 2 or returns_score) and code_ratio > 0.05:
        return {"category": "code_example", "value": "low", "score": backtick_score + returns_score}

    if action_score and has_natural_lang:
        return {"category": "nl_action", "value": "medium", "score": action_score}

    if has_natural_lang:
        return {"category": "nl_description", "value": "high", "score": 0}

    return {"category": "code_syntax", "value": "low", "score": 1}


def slice_document(text: str, doc_name: str = "") -> dict:
    fragments = []
    frag_id = 0
    para_idx = 0

    for para in _split_paragraphs(text):
        para_idx += 1
        sentences = _split_sentences(para)

        if len(sentences) <= 1:
            frag_id += 1
            classification = _classify_fragment(para)
            fragments.append({
                "id": f"F{frag_id:02d}",
                "text": para,
                "category": classification["category"],
                "value": classification["value"],
                "source_location": {"paragraph": para_idx, "sentence": None},
            })
        else:
            sent_idx = 0
            for sent in sentences:
                sent_idx += 1
                frag_id += 1
                classification = _classify_fragment(sent)
                fragments.append({
                    "id": f"F{frag_id:02d}",
                    "text": sent,
                    "category": classification["category"],
                    "value": classification["value"],
                    "source_location": {"paragraph": para_idx, "sentence": sent_idx},
                })

    for i, frag in enumerate(fragments):
        frag["prev_fragment_id"] = fragments[i - 1]["id"] if i > 0 else None
        frag["next_fragment_id"] = fragments[i + 1]["id"] if i < len(fragments) - 1 else None

    stats = {"total": len(fragments), "high": 0, "medium": 0, "low": 0, "skip": 0}
    for f in fragments:
        v = f["value"]
        if v in stats:
            stats[v] += 1

    return {
        "source": doc_name,
        "fragments": fragments,
        "stats": stats,
    }


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if path:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    else:
        text = """Lists are mutable sequences, typically used to store collections of homogeneous items (where the precise degree of similarity will vary by application).

class list(iterable=(), /)

Lists may be constructed in several ways:

Using a pair of square brackets to denote the empty list: []

Using square brackets, separating items with commas: [a], [a, b, c]

Using a list comprehension: [x for x in iterable]

Using the type constructor: list() or list(iterable)

The constructor builds a list whose items are the same and in the same order as iterable's items. iterable may be either a sequence, a container that supports iteration, or an iterator object. If iterable is already a list, a copy is made and returned, similar to iterable[:].

This method sorts the list in place, using only < comparisons between items. Exceptions are not suppressed - if any comparison operations fail, the entire sort operation will fail (and the list will likely be left in a partially modified state).

sort(*, key=None, reverse=False)

sort() accepts two arguments that can only be passed by keyword (keyword-only arguments):

key specifies a function of one argument that is used to extract a comparison key from each list element (for example, key=str.lower). The key corresponding to each item in the list is calculated once and then used for the entire sorting process. The default value of None means that list items are sorted directly without calculating a separate key value.

CPython implementation detail: While a list is being sorted, the effect of attempting to mutate, or even inspect, the list is undefined."""

    result = slice_document(text, doc_name="Python List")
    print(json.dumps(result, indent=2, ensure_ascii=False))
