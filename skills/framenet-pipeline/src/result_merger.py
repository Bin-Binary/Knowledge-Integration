from __future__ import annotations
import json
from typing import Optional

try:
    import nltk
    from nltk.corpus import framenet as fn
except ImportError:
    fn = None

RELATION_TYPE_MAP = {
    "Inheritance": "hierarchical",
    "Using": "hierarchical",
    "Subframe": "compositional",
    "Causative_of": "causal",
    "Precedes": "temporal",
    "Perspective_on": "associative",
    "See_also": "associative",
    "ReFraming_Mapping": "associative",
    "Metaphor": "associative",
}


def _ensure_framenet():
    if fn is None:
        raise ImportError("nltk and nltk.corpus.framenet required")
    return fn


def _get_frame_id(frame_name: str) -> Optional[int]:
    fn_corpus = _ensure_framenet()
    try:
        f = fn_corpus.frame(frame_name)
        return f.ID
    except Exception:
        return None


def _get_ancestors(frame_name: str, max_depth: int = 5) -> list[str]:
    fn_corpus = _ensure_framenet()
    ancestors = []
    current = frame_name
    visited = set()
    for _ in range(max_depth):
        if current in visited:
            break
        visited.add(current)
        try:
            f = fn_corpus.frame(current)
        except Exception:
            break
        parents = []
        for rel in f.frameRelations:
            rel_type = rel.get("type")
            if rel_type and rel_type.name in ("Inheritance", "Using", "Inchoative_of", "Causative_of", "Subframe", "Perspective_on"):
                if rel.get("subFrameName") == current:
                    parent_name = rel.get("superFrameName")
                    if parent_name and parent_name != current:
                        parents.append(parent_name)
        if not parents:
            break
        ancestors.extend(parents)
        current = parents[0]
    return ancestors


def query_frame_relations(frame_names: list[str]) -> list[dict]:
    fn_corpus = _ensure_framenet()
    frame_ids = {}
    for name in frame_names:
        fid = _get_frame_id(name)
        if fid is not None:
            frame_ids[name] = fid

    if len(frame_ids) < 2:
        return []

    results = []
    checked_pairs = set()
    valid_names = list(frame_ids.keys())

    for i, name_a in enumerate(valid_names):
        fid_a = frame_ids[name_a]
        try:
            all_rels = list(fn_corpus.frame_relations(frame=fid_a))
        except Exception:
            continue

        for rel in all_rels:
            sub_name = rel.get("subFrameName")
            sup_name = rel.get("superFrameName")
            partner = None
            direction = None

            if name_a == sup_name and sub_name in frame_ids:
                partner = sub_name
                direction = "parent_to_child"
            elif name_a == sub_name and sup_name in frame_ids:
                partner = sup_name
                direction = "child_to_parent"
            else:
                for other_name in valid_names:
                    if other_name == name_a:
                        continue
                    if other_name in (sub_name, sup_name):
                        partner = other_name
                        direction = "sibling" if name_a not in (sup_name, sub_name) else direction
                        break

            if partner is None:
                continue

            pair_key = tuple(sorted([name_a, partner]))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            rel_type_name = rel.get("type", None)
            rel_type_str = rel_type_name.name if rel_type_name else "Unknown"
            semantic_type = RELATION_TYPE_MAP.get(rel_type_str, "associative")

            fe_mappings = []
            for fer in rel.get("feRelations", []):
                fe_mappings.append(str(fer))

            results.append({
                "source_frame": name_a,
                "target_frame": partner,
                "relation_type": semantic_type,
                "framenet_relation": rel_type_str,
                "direction": direction,
                "fe_mappings": fe_mappings,
            })

    for i in range(len(valid_names)):
        for j in range(i + 1, len(valid_names)):
            pair_key = tuple(sorted([valid_names[i], valid_names[j]]))
            if pair_key in checked_pairs:
                continue

            ancestors_a = _get_ancestors(valid_names[i])
            ancestors_b = _get_ancestors(valid_names[j])

            common = None
            path_a = []
            path_b = []
            for idx_a, anc_a in enumerate(ancestors_a):
                if anc_a in ancestors_b:
                    idx_b = ancestors_b.index(anc_a)
                    common = anc_a
                    path_a = ancestors_a[: idx_a + 1]
                    path_b = ancestors_b[: idx_b + 1]
                    break

            if common:
                checked_pairs.add(pair_key)
                results.append({
                    "source_frame": valid_names[i],
                    "target_frame": valid_names[j],
                    "relation_type": "hierarchical",
                    "framenet_relation": "via_common_ancestor",
                    "direction": "sibling",
                    "common_ancestor": common,
                    "fe_mappings": [],
                    "path_source": [valid_names[i]] + path_a,
                    "path_target": [valid_names[j]] + path_b,
                })

    return results


def merge_fragment_results(fragment_results: list[dict], doc_source: str = "") -> dict:
    frame_index: dict[str, dict] = {}
    all_annotations: dict[str, dict] = {}
    skipped_fragments = []

    for frag_result in fragment_results:
        frag_id = frag_result.get("fragment_id", "?")
        frag_text = frag_result.get("fragment_text", "")
        annotations = frag_result.get("annotations", [])
        skipped = frag_result.get("skipped", False)

        if skipped:
            skipped_fragments.append(frag_id)
            continue

        all_annotations[frag_id] = {
            "fragment_text": frag_text,
            "annotations": annotations,
        }

        for ann in annotations:
            frame_name = ann.get("selected_frame")
            if not frame_name:
                continue

            if frame_name not in frame_index:
                frame_index[frame_name] = {
                    "trigger_words": [],
                    "fragments": [],
                    "max_confidence": "none",
                    "core_fes": ann.get("core_fes", []),
                    "source": ann.get("source", "unknown"),
                }

            entry = frame_index[frame_name]
            word = ann.get("word", "")
            if word and word not in entry["trigger_words"]:
                entry["trigger_words"].append(word)

            if frag_id not in entry["fragments"]:
                entry["fragments"].append(frag_id)

            conf_order = {"high": 3, "medium": 2, "low": 1, "none": 0}
            if conf_order.get(ann.get("confidence", "none"), 0) > conf_order.get(entry["max_confidence"], 0):
                entry["max_confidence"] = ann["confidence"]

    frame_names = list(frame_index.keys())
    frame_relations = query_frame_relations(frame_names) if frame_names and fn else []

    total_words = sum(len(a.get("annotations", [])) for a in all_annotations.values())
    conf_dist = {"high": 0, "medium": 0, "low": 0, "none": 0}
    fn_matched = 0
    llm_inferred = 0
    for ann_list in all_annotations.values():
        for ann in ann_list.get("annotations", []):
            c = ann.get("confidence", "none")
            if c in conf_dist:
                conf_dist[c] += 1
            if ann.get("source") == "framenet_lu":
                fn_matched += 1
            elif ann.get("source") == "llm_inference":
                llm_inferred += 1

    return {
        "document": doc_source,
        "global_frame_index": frame_index,
        "frame_relations": frame_relations,
        "fragment_annotations": all_annotations,
        "skipped_fragments": skipped_fragments,
        "statistics": {
            "total_fragments": len(fragment_results),
            "processed_fragments": len(all_annotations),
            "skipped_fragments": len(skipped_fragments),
            "total_annotated_words": total_words,
            "unique_frames": len(frame_index),
            "frame_relations_found": len(frame_relations),
            "confidence_distribution": conf_dist,
            "framenet_lu_matched": fn_matched,
            "llm_inferred": llm_inferred,
        },
    }


if __name__ == "__main__":
    if fn is None:
        print("nltk/framenet not available")
    else:
        test_frames = ["Storing", "Containing", "Aggregate", "Diversity", "Typicality", "Sequence"]
        rels = query_frame_relations(test_frames)
        print(json.dumps(rels, indent=2, ensure_ascii=False))
