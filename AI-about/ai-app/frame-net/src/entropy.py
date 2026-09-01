# entropy.py
# -*- coding: utf-8 -*-
"""P3 语义熵提纯 + P3.5 义项检查（spec §3 P3/P3.5 / 修改D、修改E）。

H(V) = -Σ P(N|V) log2 P(N|V)，P(N|V)=C(V,N)/C(V)，名词分布做加一平滑（alpha）。
H_norm = H / log2(|N_V|)。判读（修改D 弱化版）：
  H_norm ≥ high  且 C(V) 高 → [Drop_Light_Verb]（降权保留，待义项检查复核）
  H_norm ≤ low   且 C(V) 高 → [Active_LU]（黄金 LU 种子候选）
  其余 → [Keep_Watch]
熵为打分特征之一，非一票否决。

P3.5 义项检查：对每个 [Active_LU]，收集句子上下文（句中名词 bag），
单链接 Jaccard 聚类 → 簇≥2 且簇间名词集差异显著 → [POLYSEMOUS_CHECK] + polysemy_flag。
"""
import json
import math
import os
import re

from .io_utils import write_json


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compute_entropy(counts, alpha):
    """counts: dict N->int。返回 (H, |N_V|)。"""
    total = float(sum(counts.values()) + alpha * len(counts))
    h = 0.0
    for c in counts.values():
        p = (c + alpha) / total
        h -= p * math.log2(p)
    return h, len(counts)


BOOL_LIKE = {"true", "false", "yes", "no", "none", "null", "null值", "undefined"}


def _is_placeholder(obj):
    """布尔/纯数字/占位符对象不计入熵分布（避免“重复率→true”这类伪低熵）。"""
    w = obj.lower()
    if w in BOOL_LIKE:
        return True
    if obj.isdigit() or re.fullmatch(r"[\d./:%+\-]+", obj):
        return True
    return False


def build_object_sets(pairs):
    """V -> Counter(N)，只取 pred_noun/obj。pairs 为 P1 全部词对。"""
    objs = {}
    for p in pairs:
        if p["type"] == "pred_noun" and p["rel"] == "obj":
            if _is_placeholder(p["w2"]):
                continue
            d = objs.setdefault(p["w1"], {})
            d[p["w2"]] = d.get(p["w2"], 0) + p["c_w1w2"]
    return objs


def assign_tag(cfg, c_v, h_norm, n_nouns):
    if c_v < cfg.min_c_for_seed:
        return "Keep_Watch", "sample_limited(c<%d)" % cfg.min_c_for_seed
    if n_nouns < cfg.min_objects_for_active:
        return "Keep_Watch", "objects<%d" % cfg.min_objects_for_active
    if h_norm >= cfg.entropy_high:
        return "Drop_Light_Verb", "high_entropy>=%.2f" % cfg.entropy_high
    if h_norm <= cfg.entropy_low:
        return "Active_LU", "low_entropy<=%.2f" % cfg.entropy_low
    return "Keep_Watch", "0.35<h_norm<0.85"


# ---------- P3.5 上下文聚类（搭配签名聚类，修改E） ----------
def _jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def single_link_clusters(bags, threshold, max_clusters):
    """bags: list[set]。单链接 Jaccard 聚类，返回簇列表。"""
    clusters = []
    for b in bags:
        merged = [i for i, cl in enumerate(clusters)
                  if any(_jaccard(b, x) > threshold for x in cl)]
        if not merged:
            clusters.append([b])
        else:
            base = clusters[merged[0]]
            base.append(b)
            for i in reversed(merged[1:]):
                base.extend(clusters[i])
                del clusters[i]
        if len(clusters) >= max_clusters:
            break
    return clusters


def run_stage3(cfg, raw_path, parsed_path):
    raw = _load(raw_path)
    pairs = raw["pairs"]
    objs = build_object_sets(pairs)
    lus = []
    for v, cnt in sorted(objs.items(), key=lambda kv: -sum(kv[1].values())):
        h, n_nouns = compute_entropy(cnt, cfg.entropy_smooth)
        c_v = sum(cnt.values())
        h_norm = h / math.log2(max(2, n_nouns))
        tag, note = assign_tag(cfg, c_v, h_norm, n_nouns)
        top_nouns = [n for n, _ in sorted(cnt.items(), key=lambda kv: -kv[1])[:5]]
        lus.append({"lu": v, "c": c_v, "h": round(h, 4), "h_norm": round(h_norm, 4),
                    "n_nouns": n_nouns, "tag": tag, "note": note, "top_nouns": top_nouns,
                    "senses": [], "polysemy_flag": False, "deverbal": []})
    return do_sense_check(cfg, lus, parsed_path, raw)


def do_sense_check(cfg, lus, parsed_path, raw):
    """P3.5：上下文聚类。仅对 Active_LU 执行；簇≥2 且簇间名词集差异显著→POLYSEMOUS_CHECK。"""
    parsed = _load(parsed_path)
    active = {l["lu"] for l in lus if l["tag"] == "Active_LU"}
    if not active:
        return finish_stage3(cfg, lus, raw)
    # 每句 (text, 名词bag) 索引：只索引含目标动词的句子
    sent_bags = {}  # word -> list[set]
    for doc in parsed["docs"]:
        for s in doc["sents"]:
            words = [t["word"] for t in s["tokens"]]
            hit = active & set(words)
            if not hit:
                continue
            nouns = {t["word"] for t in s["tokens"]
                     if (t["pos"].startswith("n") or t["pos"] in ("eng",)) and t["word"] not in cfg.stopwords
                     and any(c.isalnum() for c in t["word"])}
            for w in hit:
                sent_bags.setdefault(w, []).append(frozenset(nouns - {w}) | {w})
    for l in lus:
        if l["lu"] not in active:
            continue
        bags = sent_bags.get(l["lu"], [])[:500]
        bags = [b for b in bags if len(b) >= 2]
        if len(bags) < 4:
            continue
        clusters = single_link_clusters(list(bags), cfg.sense_jaccard_threshold,
                                        cfg.sense_max_clusters)
        clusters = [c for c in clusters if len(c) >= 2]
        if len(clusters) >= cfg.sense_min_clusters:
            l["polysemy_flag"] = True
            l["senses"] = []
            for cl in clusters:
                union = set()
                for b in cl:
                    union |= set(b)
                union.discard(l["lu"])
                l["senses"].append({"n_ctx": len(cl),
                                    "signature": sorted(union, key=lambda x: -sum(1 for b in cl if x in b))[:8]})
            l["tag"] = "POLYSEMOUS_CHECK"
            l["note"] = "上下文聚类≥%d簇，簇间名词集差异显著，待义项复核" % cfg.sense_min_clusters
    return finish_stage3(cfg, lus, raw)


def finish_stage3(cfg, lus, raw):
    if not lus:
        return None
    # 并入修改B 的 deverbal
    for d in raw.get("deverbal", []):
        match = next((l for l in lus if l["lu"] == d["head"]), None)
        if match:
            match["deverbal"].append(d["phr"])
        else:
            lus.append({"lu": d["head"], "c": 0, "h": None, "h_norm": None, "n_nouns": 0,
                        "tag": "Deverbal_Noun", "note": "名词化谓词(修改B)：%s" % d["phr"],
                        "top_nouns": [], "senses": [], "polysemy_flag": False,
                        "deverbal": [d["phr"]]})
    return lus


def write_stage3(cfg, lus):
    if lus is None:
        lus = []
    obj = {"lus": lus,
           "drop_table": str(cfg._builtin_light_verbs),
           "params": cfg.to_dict()}
    write_json(os.path.join(cfg.out_dir, "lu_seeds_qualified.json"), obj)
    md = ["## 语义熵提纯（P3）与义项检查（P3.5）",
          "> H_norm=H/log2(|N_V|)；tag 判定：高熵高配(轻动词)标记 Drop_Light_Verb、低频高配标记 Active_LU、"
          "上下文聚区分多义标记 POLYSEMOUS_CHECK；均为候选标签，非最终 LU 判定",
          "",
          "| LU | 频数 | H | H_norm | N名词 | tag | note | 主要搭配名词Top5 |",
          "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
    for l in lus:
        md.append("| %s | %s | %s | %s | %d | %s | %s | %s |" % (
            l["lu"], l["c"], l.get("h", ""), l.get("h_norm", ""), l["n_nouns"],
            l["tag"], l["note"], "，".join(l["top_nouns"])))
    md.append("")
    md.append("*义项检查（仅 Active_LU 上下文聚类）*")
    md.append("| LU | polysemy_flag | 义项簇 | 簇签名名词 |")
    md.append("| :--- | :--- | :--- | :--- |")
    for l in lus:
        if l["senses"]:
            for si, s in enumerate(l["senses"]):
                md.append("| %s | %s | sense%d(上下文%d) | %s |" % (
                    l["lu"], "true" if l["polysemy_flag"] else "false",
                    si + 1, s["n_ctx"], "，".join(s["signature"][:6])))
    md.append("")
    with open(os.path.join(cfg.out_dir, "lu_seeds_qualified.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

