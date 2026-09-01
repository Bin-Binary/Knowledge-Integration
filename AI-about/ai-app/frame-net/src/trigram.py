# trigram.py
# -*- coding: utf-8 -*-
"""P4 三元抽取 + P5 三元过滤（spec §3 P4/P5，输出 raw_trigrams_counts / frame_skeleton_templates）。

槽位映射（D6）：
  Adv-V-N : w1=Adv, w2=V(LU), w3=N；FE 位 = w3（宾语）
  Prep-N-V: w1=Prep, w2=N,      w3=V(LU)；FE 位 = w1+w2（介宾）
以 [Active_LU]（+ [POLYSEMOUS_CHECK] 待复核）为枢纽白名单辐射抽取（spec P4）。
Trigram PMI = log2( C123*N / (C1*C2*C3) )
Partial PMI(w3;(w1,w2)) = log2( C123*N / (C(w1,w2)*C(w3)) )（spec P5 过滤伪三元）
抽取自解析边：Adv-V-N 需同句同时存在 advmod(V) 与 obj(V)；Prep-N-V 需 prep+pobj 边指向动词 V。
"""
import json
import math
import os

from .io_utils import write_json


class TripleCounter:
    def __init__(self):
        self.triples = {}
        self.sents = {}
        self.cand = {}

    def add(self, key, doc_id, sent_id, candidate):
        d = self.cand if candidate else self.triples
        bucket = d.setdefault(key, {"c": 0, "df": set(), "sents": []})
        bucket["c"] += 1
        bucket["df"].add(doc_id)
        if not candidate and len(bucket["sents"]) < 5:
            bucket["sents"].append({"doc_id": doc_id, "sent_id": sent_id})


def scan_triples(cfg, parsed_path, active_lus):
    with open(parsed_path, encoding="utf-8") as f:
        parsed = json.load(f)
    counter = TripleCounter()
    whitelist = set(active_lus)
    for doc in parsed["docs"]:
        for s in doc["sents"]:
            toks = s["tokens"]
            by_idx = {t["idx"]: t for t in toks}
            verbs = {t["idx"]: t for t in toks if t["pos"].startswith("v") and t["word"] in whitelist}
            if not verbs:
                continue
            # Adv-V-N：白名单动词后找宾语
            for vi, vt in verbs.items():
                obj = next((t for t in toks if t["idx"] > vi and (t["pos"].startswith("n") or t["pos"] == "eng")
                            and t["dep_rel"] == "obj"), None)
                adv = next((t for t in toks if abs(t["idx"] - vi) <= 2 and (t["pos"].startswith("d"))), None)
                if adv and obj:
                    key = (adv["word"], vt["word"], obj["word"], "adv_v_n")
                    counter.add(key, doc["doc_id"], s["sent_id"],
                                min([t.get("score", 0.9) for t in toks]) < cfg.parser_conf_threshold)
            # Prep-N-V：白名单动词前的介宾链
            for vi, vt in verbs.items():
                prep = next((t for t in toks if t["idx"] < vi and t["pos"].startswith("p")
                             and t["word"] not in cfg.stopwords), None)
                if prep is None:
                    continue
                pobj = next((t for t in toks if t["idx"] > prep["idx"] and t["idx"] < vi
                             and (t["pos"].startswith("n") or t["pos"] == "eng")
                             and t["word"] not in cfg.stopwords), None)
                if pobj:
                    key = (prep["word"], pobj["word"], vt["word"], "prep_n_v")
                    counter.add(key, doc["doc_id"], s["sent_id"],
                                min([t.get("score", 0.9) for t in toks]) < cfg.parser_conf_threshold)
    return parsed, counter


def write_stage4(cfg, parsed, counter, uni):
    N = sum(uni.values())
    rows = []
    for (w1, w2, w3, ttype), b in sorted(counter.triples.items(), key=lambda kv: -kv[1]["c"]):
        n1, n2, n3 = max(1, uni.get(w1, 1)), max(1, uni.get(w2, 1)), max(1, uni.get(w3, 1))
        pmi = math.log2((b["c"] * N) / (n1 * n2 * n3)) if b["c"] > 0 else 0.0
        rows.append({"w1": w1, "w2": w2, "w3": w3, "type": ttype, "c": b["c"],
                     "pmi3": round(pmi, 4), "lu": w2 if ttype == "adv_v_n" else w3,
                     "df": len(b["df"]), "sents": b["sents"]})
    obj = {"trigrams": rows, "params": cfg.to_dict()}
    write_json(os.path.join(cfg.out_dir, "raw_trigrams_counts.json"), obj)
    md = ["## 三元抽取（P4·Trigram PMI）",
          "> 以 [Active_LU] 白名单为枢纽辐射；Adv-V-N（w2=LU,FE位=w3）, Prep-N-V（w3=LU,FE位=介宾）。"
          "PMI3=log2(C123·N/(C1·C2·C3))",          "",
          "| 三元组 | type | 频次 | DF | Trigram PMI | 核心LU |",
          "| :--- | :--- | :--- | :--- | :--- | :--- |"]
    for r in rows[:300]:
        md.append("| %s | %s | %d | %d | %.2f | %s |" % (
            "%s-%s-%s" % (r["w1"], r["w2"], r["w3"]), r["type"], r["c"], r["df"], r["pmi3"], r["lu"]))
    with open(os.path.join(cfg.out_dir, "raw_trigrams_counts.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return rows


def write_stage5(cfg, rows, bigram_pairs, uni):
    """P5 过滤：Partial PMI。rows 来自 P4。pair 频数做对称索引（Adv-V 与 pred_adv 键方向相反）。"""
    N = sum(uni.values())
    bigrams = {}
    for p in bigram_pairs:
        a, b, c = p["w1"], p["w2"], p["c_w1w2"]
        bigrams[(a, b)] = bigrams.get((a, b), 0) + c
        bigrams[(b, a)] = bigrams.get((b, a), 0) + c
    templates = []
    for r in rows:
        w1, w2, w3, ttype = r["w1"], r["w2"], r["w3"], r["type"]
        if ttype == "adv_v_n":
            c_w1w2 = bigrams.get((w1, w2), 0)
            c_w3 = uni.get(w3, 1)
            fe_slot, fe_pos = "w3", "宾语"
        else:
            c_w1w2 = bigrams.get((w1, w2), 0)
            c_w3 = uni.get(w3, 1)
            fe_slot, fe_pos = "w1+w2", "介宾"
        if c_w1w2 <= 0 or c_w3 <= 0 or r["c"] <= 0:
            continue
        partial = math.log2((r["c"] * N) / (c_w1w2 * c_w3))
        if r["c"] < cfg.min_triple_freq:
            continue
        template = {"type": ttype, "lu": r["lu"], "w1": w1, "w2": w2, "w3": w3,
                    "c": r["c"], "pmi_partial": round(partial, 4),
                    "fe_slot": fe_slot, "fe_pos": fe_pos, "synthesized": False,
                    "sents": r["sents"]}
        if partial >= cfg.partial_pmi_threshold:
            template["passed"] = True
            templates.append(template)
        else:
            template["passed"] = False
            templates.append(template)
    obj = {"templates": templates, "params": cfg.to_dict()}
    write_json(os.path.join(cfg.out_dir, "frame_skeleton_templates.json"), obj)
    md = ["## 三元过滤（P5·Partial PMI）",
          "> 过滤伪三元：PMI(w3;(w1,w2))=log2(C123·N/(C(w1,w2)·C(w3)))。"
          "FE槽位仅为句法位置，不判语义角色（修改H）。",
          "",
          "| 三元模板 | type | LU | 频次 | PartialPMI | FE槽位(句法位置) | 通过 |",
          "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
    for t in sorted(templates, key=lambda x: -x["pmi_partial"]):
        md.append("| %s | %s | %s | %d | %.2f | %s(%s) | %s |" % (
            "%s-%s-%s" % (t["w1"], t["w2"], t["w3"]), t["type"], t["lu"], t["c"],
            t["pmi_partial"], t["fe_slot"], t["fe_pos"], "✓" if t["passed"] else "✗"))
    with open(os.path.join(cfg.out_dir, "frame_skeleton_templates.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    return templates
