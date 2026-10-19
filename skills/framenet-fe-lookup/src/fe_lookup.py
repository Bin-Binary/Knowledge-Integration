from __future__ import annotations
import json
import sys
from typing import Optional

try:
    import nltk
    from nltk.corpus import framenet as fn
except ImportError:
    nltk = None
    fn = None


def _ensure_framenet():
    if fn is None:
        raise ImportError("nltk and nltk.corpus.framenet are required. pip install nltk; python -m nltk.downloader framenet_v17")
    return fn


def lookup_frame(frame_name: str) -> Optional[dict]:
    fn_corpus = _ensure_framenet()
    try:
        frame = fn_corpus.frame(frame_name)
    except Exception:
        candidates = fn_corpus.frames(name=r".*" + frame_name.lower() + ".*")
        if not candidates:
            return None
        frame = fn_corpus.frame(candidates[0].name)

    core = []
    peripheral = []
    extra_thematic = []
    for fe in frame.FE.values():
        entry = {
            "name": fe.name,
            "abbreviation": fe.abbrev if hasattr(fe, "abbrev") else "",
            "definition": (fe.definition or "").strip(),
            "core_type": fe.coreType,
            "required": fe.coreType == "Core",
        }
        ct = fe.coreType
        if ct == "Core":
            core.append(entry)
        elif ct == "Peripheral":
            peripheral.append(entry)
        elif ct in ("Extra-Thematic", "Core-Unexpressed"):
            extra_thematic.append(entry)
        else:
            extra_thematic.append(entry)

    fe_relations = []
    try:
        for fer in frame.FE.values():
            if hasattr(fer, "requiresFE") and fer.requiresFE:
                fe_relations.append({"type": "Requires", "source": fer.name, "target": fer.requiresFE.name if hasattr(fer.requiresFE, "name") else str(fer.requiresFE)})
            if hasattr(fer, "excludesFE") and fer.excludesFE:
                fe_relations.append({"type": "Excludes", "source": fer.name, "target": fer.excludesFE.name if hasattr(fer.excludesFE, "name") else str(fer.excludesFE)})
    except Exception:
        pass

    lus = []
    for lu in frame.lexUnit.values():
        lus.append({
            "name": lu.name,
            "pos": lu.POS if hasattr(lu, "POS") else "",
        })

    frame_relations = []
    try:
        for rel in fn_corpus.frame_relations(frame=frame):
            frame_relations.append({
                "type": rel.type.name if hasattr(rel.type, "name") else str(rel.type),
                "source_frame": rel.subFrameName if hasattr(rel, "subFrameName") else "",
                "target_frame": rel.superFrameName if hasattr(rel, "superFrameName") else "",
            })
    except Exception:
        pass

    return {
        "frame_name": frame.name,
        "frame_id": frame.ID,
        "definition": frame.definition[:500].strip(),
        "core_fes": core,
        "peripheral_fes": peripheral,
        "extra_thematic_fes": extra_thematic,
        "fe_relations": fe_relations,
        "lexical_units": lus[:20],
        "frame_relations": frame_relations[:15],
    }


def _stem_variants(word: str) -> list[str]:
    w = word.lower()
    variants = {w}
    suffixes_to_strip = [
        ("ing", 3), ("tion", 4), ("sion", 4), ("ment", 4),
        ("ness", 4), ("ence", 4), ("ance", 4), ("able", 4),
        ("ible", 4), ("ful", 3), ("less", 4), ("ous", 3),
        ("ive", 3), ("al", 2), ("ed", 2), ("es", 2), ("er", 2), ("s", 1),
        ("y", 1),
    ]
    for suffix, min_stem in suffixes_to_strip:
        if w.endswith(suffix) and len(w) - len(suffix) >= min_stem:
            base = w[:-len(suffix)]
            variants.add(base)
            variants.add(base + suffix)
            for s2, _ in suffixes_to_strip:
                if len(base + s2) > 3:
                    variants.add(base + s2)
            break
    if w.endswith("ies"):
        base = w[:-3] + "y"
        variants.add(base)
        variants.add(w[:-3])
    if w.endswith("ied"):
        base = w[:-3] + "y"
        variants.add(base)
    return [v for v in variants if len(v) > 2]


def search_frames(query: str, limit: int = 10) -> list[dict]:
    fn_corpus = _ensure_framenet()
    patterns = _stem_variants(query)
    scored = []
    for f in fn_corpus.frames():
        name_lower = f.name.lower()
        best_score = 0
        for p in patterns:
            if name_lower == p:
                best_score = max(best_score, 100)
            elif name_lower.startswith(p) or p.startswith(name_lower):
                best_score = max(best_score, 80)
            elif p in name_lower or name_lower in p:
                best_score = max(best_score, 60)
        if best_score > 0:
            core_count = sum(1 for fe in f.FE.values() if fe.coreType == "Core")
            scored.append({
                "name": f.name,
                "id": f.ID,
                "core_fe_count": core_count,
                "definition": f.definition[:200].strip(),
                "_score": best_score,
            })
    scored.sort(key=lambda x: -x["_score"])
    if len(scored) < limit:
        lu_variants = _stem_variants(query)
        for suffix in [".n", ".v", ".a", ".adv"]:
            for lv in lu_variants:
                try:
                    for lu in fn_corpus.lus(lv + suffix):
                        fname = lu.frame.name
                        if not any(s["name"] == fname for s in scored):
                            core_count = sum(1 for fe in lu.frame.FE.values() if fe.coreType == "Core")
                            scored.append({
                                "name": fname,
                                "id": lu.frame.ID,
                                "core_fe_count": core_count,
                                "definition": lu.frame.definition[:200].strip(),
                                "_score": 40,
                            })
                except Exception:
                    continue
        scored.sort(key=lambda x: -x["_score"])
    for item in scored:
        item.pop("_score", None)
    return scored[:limit]


def format_result(result: dict) -> str:
    if result is None:
        return "Frame not found."
    lines = []
    lines.append(f"# {result['frame_name']} (ID: {result['frame_id']})")
    lines.append("")
    lines.append(result["definition"])
    lines.append("")
    lines.append("## Core FEs")
    lines.append("")
    if result["core_fes"]:
        for fe in result["core_fes"]:
            abbrev = f" ({fe['abbreviation']})" if fe.get("abbreviation") else ""
            lines.append(f"- **{fe['name']}**{abbrev}: {fe['definition'][:300]}")
    else:
        lines.append("(none)")
    lines.append("")
    lines.append("## Peripheral FEs")
    lines.append("")
    if result["peripheral_fes"]:
        for fe in result["peripheral_fes"]:
            abbrev = f" ({fe['abbreviation']})" if fe.get("abbreviation") else ""
            lines.append(f"- **{fe['name']}**{abbrev}: {fe['definition'][:300]}")
    else:
        lines.append("(none)")
    if result.get("extra_thematic_fes"):
        lines.append("")
        lines.append("## Extra-Thematic FEs")
        lines.append("")
        for fe in result["extra_thematic_fes"]:
            abbrev = f" ({fe['abbreviation']})" if fe.get("abbreviation") else ""
            lines.append(f"- **{fe['name']}**{abbrev}: {fe['definition'][:300]}")
    if result.get("fe_relations"):
        lines.append("")
        lines.append("## FE Relations")
        lines.append("")
        for rel in result["fe_relations"]:
            lines.append(f"- {rel['type']}: {rel['source']} → {rel['target']}")
    if result.get("lexical_units"):
        lines.append("")
        lines.append("## Lexical Units (top 20)")
        lines.append("")
        lu_strs = [f"`{lu['name']}`" for lu in result["lexical_units"]]
        lines.append(", ".join(lu_strs))
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python fe_lookup.py <frame_name> [--search] [--json]")
        print("  frame_name   Exact or partial FrameNet frame name")
        print("  --search     Search mode: fuzzy match frame names")
        print("  --json       Output as JSON instead of Markdown")
        sys.exit(1)

    frame_name = sys.argv[1]
    do_search = "--search" in sys.argv
    do_json = "--json" in sys.argv

    if do_search:
        results = search_frames(frame_name)
        if do_json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for r in results:
                print(f"- {r['name']} (ID:{r['id']}, core FEs: {r['core_fe_count']}) — {r['definition'][:120]}")
            if not results:
                print("No matching frames found.")
    else:
        result = lookup_frame(frame_name)
        if result is None:
            print(f"Frame '{frame_name}' not found. Try --search for fuzzy matching.")
            sys.exit(1)
        if do_json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_result(result))


if __name__ == "__main__":
    main()
