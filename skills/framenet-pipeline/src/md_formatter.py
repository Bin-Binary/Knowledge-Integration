from __future__ import annotations
from datetime import datetime

CONF_ICON = {"high": "[+++]", "medium": "[++]", "low": "[+]", "none": "[-]"}
CONF_TAG = {"high": "H", "medium": "M", "low": "L", "none": "-"}


def _conf_icon(c: str) -> str:
    return CONF_ICON.get(c, "⬜")


def _conf_tag(c: str) -> str:
    return CONF_TAG.get(c, "-")


def format_single_sentence(result: dict) -> str:
    lines = []
    lines.append("# FrameNet Semantic Annotation")
    lines.append("")

    lines.append("## Input")
    lines.append("")
    lines.append("> " + result.get("text", ""))
    lines.append("")

    stats = result.get("statistics", {})
    lines.append("## Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append("| Total content words | " + str(stats.get("total_content_words", 0)) + " |")
    lines.append("| Annotated words | " + str(stats.get("annotated_words", 0)) + " |")
    cd = stats.get("confidence_distribution", {})
    lines.append("| High confidence | " + str(cd.get("high", 0)) + " |")
    lines.append("| Medium confidence | " + str(cd.get("medium", 0)) + " |")
    lines.append("| Low confidence | " + str(cd.get("low", 0)) + " |")
    lines.append("| No match | " + str(cd.get("none", 0)) + " |")
    lines.append("| FrameNet LU matched | " + str(stats.get("framenet_lu_matched", 0)) + " |")
    lines.append("| LLM inferred | " + str(stats.get("llm_inferred", 0)) + " |")
    lines.append("| Unmatched | " + str(stats.get("unmatched", 0)) + " |")
    lines.append("")

    lines.append("## Annotations")
    lines.append("")
    lines.append("| Word | Frame | Conf | Source | Core FEs | FE Binding |")
    lines.append("|------|-------|------|--------|----------|------------|")
    for ann in result.get("annotations", []):
        word = ann.get("word", "")
        frame = ann.get("selected_frame") or "—"
        conf = ann.get("confidence", "none")
        conf_str = _conf_icon(conf) + " " + conf
        source = ann.get("source", "")
        source_str = {"framenet_lu": "FN", "llm_inference": "LLM", "none": "—"}.get(source, source)
        core_fes = ", ".join(ann.get("core_fes", [])) or "—"
        fe_bind = ann.get("fe_binding", {})
        fe_bind_str = "; ".join(k + "→" + v for k, v in fe_bind.items()) if fe_bind else "—"
        lines.append("| " + word + " | " + frame + " | " + conf_str + " | " + source_str + " | " + core_fes + " | " + fe_bind_str + " |")
    lines.append("")

    fi = result.get("frame_index", {})
    if fi:
        lines.append("## Frame Index")
        lines.append("")
        lines.append("| Frame | Trigger Words |")
        lines.append("|-------|--------------|")
        for frame, words in sorted(fi.items()):
            lines.append("| " + frame + " | " + ", ".join(words) + " |")
        lines.append("")

    lines.append("<!-- generated: " + result.get("timestamp", datetime.now().isoformat()) + " -->")
    lines.append("")
    return "\n".join(lines)


def format_document(result: dict) -> str:
    lines = []
    doc_name = result.get("document", "Document")
    lines.append("# FrameNet Document Annotation: " + doc_name)
    lines.append("")

    slicing = result.get("slicing", {})
    s_stats = slicing.get("stats", {})
    lines.append("## Document Slicing")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append("| Total fragments | " + str(s_stats.get("total", 0)) + " |")
    lines.append("| High value (nl_description) | " + str(s_stats.get("high", 0)) + " |")
    lines.append("| Medium value (nl_action) | " + str(s_stats.get("medium", 0)) + " |")
    lines.append("| Low value | " + str(s_stats.get("low", 0)) + " |")
    lines.append("| Skip | " + str(s_stats.get("skip", 0)) + " |")
    lines.append("| Eligible for analysis | " + str(slicing.get("eligible_fragments", 0)) + " |")
    lines.append("| Skipped | " + str(slicing.get("skipped_fragments", 0)) + " |")
    lines.append("")

    stats = result.get("statistics", {})
    lines.append("## Overall Statistics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    cd = stats.get("confidence_distribution", {})
    lines.append("| Processed fragments | " + str(stats.get("processed_fragments", 0)) + " |")
    lines.append("| Total annotated words | " + str(stats.get("total_annotated_words", 0)) + " |")
    lines.append("| Unique frames | " + str(stats.get("unique_frames", 0)) + " |")
    lines.append("| Frame relations found | " + str(stats.get("frame_relations_found", 0)) + " |")
    lines.append("| High confidence | " + str(cd.get("high", 0)) + " |")
    lines.append("| Medium confidence | " + str(cd.get("medium", 0)) + " |")
    lines.append("| Low confidence | " + str(cd.get("low", 0)) + " |")
    lines.append("| No match | " + str(cd.get("none", 0)) + " |")
    lines.append("| FrameNet LU matched | " + str(stats.get("framenet_lu_matched", 0)) + " |")
    lines.append("| LLM inferred | " + str(stats.get("llm_inferred", 0)) + " |")
    lines.append("")

    gfi = result.get("global_frame_index", {})
    if gfi:
        lines.append("## Global Frame Index")
        lines.append("")
        lines.append("| Frame | Triggers | Fragments | Conf | Source | Core FEs |")
        lines.append("|-------|----------|-----------|------|--------|----------|")
        for frame, info in sorted(gfi.items()):
            triggers = ", ".join(info.get("trigger_words", []))
            frags = ", ".join(info.get("fragments", []))
            conf = info.get("max_confidence", "none")
            conf_str = _conf_icon(conf) + " " + conf
            source = info.get("source", "")
            source_str = {"framenet_lu": "FN", "llm_inference": "LLM"}.get(source, source)
            core_fes = ", ".join(info.get("core_fes", [])) or "—"
            lines.append("| " + frame + " | " + triggers + " | " + frags + " | " + conf_str + " | " + source_str + " | " + core_fes + " |")
        lines.append("")

    frame_rels = result.get("frame_relations", [])
    if frame_rels:
        lines.append("## Cross-Frame Relations")
        lines.append("")
        lines.append("| Source | Target | Relation | Direction | Detail |")
        lines.append("|--------|--------|----------|-----------|--------|")
        for rel in frame_rels:
            sf = rel.get("source_frame", "")
            tf = rel.get("target_frame", "")
            fn_rel = rel.get("framenet_relation", "")
            direction = rel.get("direction", "")
            if fn_rel == "via_common_ancestor":
                detail = "common ancestor: " + str(rel.get("common_ancestor", "?"))
            else:
                detail = fn_rel
                fe_maps = rel.get("fe_mappings", [])
                if fe_maps:
                    detail += "; FE: " + ", ".join(str(m) for m in fe_maps[:3])
            lines.append("| " + sf + " | " + tf + " | " + rel.get("relation_type", "") + " | " + direction + " | " + detail + " |")
        lines.append("")

    frag_anns = result.get("fragment_annotations", {})
    if frag_anns:
        lines.append("## Fragment Annotations")
        lines.append("")
        for frag_id in sorted(frag_anns.keys()):
            fdata = frag_anns[frag_id]
            ftxt = fdata.get("fragment_text", "")
            anns = fdata.get("annotations", [])
            lines.append("### " + frag_id)
            lines.append("")
            lines.append("> " + ftxt)
            lines.append("")
            if not anns:
                lines.append("*No annotations*")
                lines.append("")
                continue
            lines.append("| Word | Frame | Conf | Source | Core FEs | FE Binding |")
            lines.append("|------|-------|------|--------|----------|------------|")
            for ann in anns:
                word = ann.get("word", "")
                frame = ann.get("selected_frame") or "—"
                conf = ann.get("confidence", "none")
                conf_str = _conf_icon(conf) + " " + conf
                source = ann.get("source", "")
                source_str = {"framenet_lu": "FN", "llm_inference": "LLM", "none": "—"}.get(source, source)
                core_fes = ", ".join(ann.get("core_fes", [])) or "—"
                fe_bind = ann.get("fe_binding", {})
                fe_bind_str = "; ".join(k + "→" + v for k, v in fe_bind.items()) if fe_bind else "—"
                lines.append("| " + word + " | " + frame + " | " + conf_str + " | " + source_str + " | " + core_fes + " | " + fe_bind_str + " |")
            lines.append("")

    skipped = result.get("skipped_fragments", [])
    if skipped:
        lines.append("## Skipped Fragments")
        lines.append("")
        lines.append(", ".join(skipped))
        lines.append("")

    lines.append("<!-- generated: " + datetime.now().isoformat() + " -->")
    lines.append("")
    return "\n".join(lines)


def format_result(result: dict, mode: str = "auto") -> str:
    if mode == "auto":
        if "global_frame_index" in result:
            return format_document(result)
        return format_single_sentence(result)
    if mode == "document":
        return format_document(result)
    return format_single_sentence(result)
