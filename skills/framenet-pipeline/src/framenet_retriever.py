from __future__ import annotations
import re
import json
from typing import Optional

try:
    import nltk
    from nltk.corpus import framenet as fn
except ImportError:
    nltk = None
    fn = None

FUNCTION_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "shall",
    "should", "may", "might", "must", "can", "could", "to", "of", "in",
    "for", "on", "with", "at", "by", "from", "as", "into", "through",
    "during", "before", "after", "above", "below", "between", "out", "off",
    "over", "under", "again", "further", "then", "once", "here", "there",
    "when", "where", "why", "how", "all", "each", "few", "more", "most",
    "other", "some", "such", "no", "nor", "not", "only", "own", "same",
    "so", "than", "too", "very", "just", "because", "but", "and", "or",
    "if", "while", "although", "it", "its", "this", "that", "these",
    "those", "i", "me", "my", "we", "us", "our", "you", "your", "he",
    "him", "his", "she", "her", "they", "them", "their", "what", "which",
    "who", "whom",
})

POS_MAP = {
    "n": ".n", "v": ".v", "a": ".a", "adv": ".adv",
    "noun": ".n", "verb": ".v", "adj": ".a", "adverb": ".adv",
}


def _ensure_framenet():
    if fn is None:
        raise ImportError("nltk and nltk.corpus.framenet are required. Install via: pip install nltk")
    return fn


def _tokenize(text: str) -> list[dict]:
    tokens = []
    for m in re.finditer(r"[A-Za-z']+", text):
        word = m.group()
        start, end = m.start(), m.end()
        tokens.append({"word": word, "lower": word.lower(), "start": start, "end": end})
    return tokens


def _is_content_word(word_lower: str) -> bool:
    return word_lower not in FUNCTION_WORDS and len(word_lower) > 1


def _lookup_lus(word_lower: str, pos: Optional[str] = None) -> list[dict]:
    fn_corpus = _ensure_framenet()
    suffixes = [POS_MAP[pos]] if pos and pos in POS_MAP else [".n", ".v", ".a", ".adv"]
    results = []
    seen_frames = set()
    for suffix in suffixes:
        try:
            lus = fn_corpus.lus(word_lower + suffix)
        except Exception:
            continue
        for lu in lus:
            frame_name = lu.frame.name
            if frame_name in seen_frames:
                continue
            seen_frames.add(frame_name)
            frame = fn_corpus.frame(frame_name)
            core_fes = [fe.name for fe in frame.FE.values() if fe.coreType == "Core"]
            peripheral_fes = [fe.name for fe in frame.FE.values() if fe.coreType == "Peripheral"][:5]
            results.append({
                "lu_name": lu.name,
                "lu_pos": suffix.lstrip("."),
                "frame_name": frame_name,
                "frame_id": frame.ID,
                "definition": frame.definition[:300],
                "core_fes": core_fes,
                "peripheral_fes": peripheral_fes,
            })
    return results


def retrieve(text: str, pos_tags: Optional[dict[str, str]] = None, max_candidates_per_word: int = 8) -> dict:
    fn_corpus = _ensure_framenet()
    tokens = _tokenize(text)
    content_tokens = [t for t in tokens if _is_content_word(t["lower"])]

    results = []
    zero_hit_words = []

    for tok in content_tokens:
        word_lower = tok["lower"]
        pos = pos_tags.get(word_lower) if pos_tags else None
        candidates = _lookup_lus(word_lower, pos)

        if not candidates and pos is None:
            for suffix in [".n", ".v", ".a"]:
                stem_variants = [word_lower.rstrip("s"), word_lower.rstrip("es"),
                                 word_lower.rstrip("ed"), word_lower.rstrip("ing")]
                seen = set()
                for stem in stem_variants:
                    if stem and stem != word_lower and stem not in seen and len(stem) > 2:
                        seen.add(stem)
                        candidates = _lookup_lus(stem)
                        if candidates:
                            for c in candidates:
                                c["matched_via"] = f"stem:{stem}"
                            break
                if candidates:
                    break

        candidates = candidates[:max_candidates_per_word]

        if candidates:
            results.append({
                "word": tok["word"],
                "position": [tok["start"], tok["end"]],
                "candidates": candidates,
            })
        else:
            zero_hit_words.append({
                "word": tok["word"],
                "position": [tok["start"], tok["end"]],
            })

    return {
        "text": text,
        "tokens_total": len(tokens),
        "content_tokens": len(content_tokens),
        "frame_candidates": results,
        "zero_hit_words": zero_hit_words,
        "framenet_version": "v17",
        "frame_count": len(fn_corpus.frames()),
    }


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "Lists are mutable sequences, typically used to store collections of homogeneous items"
    output = retrieve(text)
    print(json.dumps(output, indent=2, ensure_ascii=False))
