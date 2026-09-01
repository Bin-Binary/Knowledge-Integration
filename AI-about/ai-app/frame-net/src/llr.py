# llr.py
# -*- coding: utf-8 -*-
"""P2 二元过滤：LLR + 绝对频数 + 文档频率（spec §3 P2 / 修改C）。

Dunning LLR（1993）四格表 + χ²(1) 显著性判据：
  入选需同时满足：C(w1,w2)>10, DF≥3, LLR>3.84；黄金候选 LLR>6.63。
Top-N 仅作展示排序，不作入选判据。
被淘汰对记录 rejected_reason（stopword / freq / df / llr）。
"""
import math
import os

from .io_utils import write_json


def compute_llr(c11, c_w1, c_w2, corpus_tokens):
    """Dunning LLR，Dunning 1993。返回 LLR 值。"""
    c12 = c_w1 - c11
    c21 = c_w2 - c11
    c22 = corpus_tokens - c_w1 - c_w2 + c11
    cells = [(c11, c_w1 * c_w2 / corpus_tokens),
             (c12, c_w1 * (corpus_tokens - c_w2) / corpus_tokens),
             (c21, (corpus_tokens - c_w1) * c_w2 / corpus_tokens),
             (c22, (corpus_tokens - c_w1) * (corpus_tokens - c_w2) / corpus_tokens)]
    llr = 0.0
    for a, e in cells:
        if a > 0 and e > 0:
            llr += a * math.log(a / e)
    return 2.0 * llr


def run_stage2(cfg, raw_pairs, uni, corpus_tokens):
    """返回 (filtered, rejected)。raw_pairs 为 [dict]（来自 P1 pairs 列表）。"""
    passed = []
    rejected = []
    for p in raw_pairs:
        w1, w2 = p["w1"], p["w2"]
        reason = None
        if w1 in cfg.stopwords or w2 in cfg.stopwords:
            reason = "stopword"
        elif p["c_w1w2"] <= cfg.min_freq_abs:
            reason = "freq<=%d" % cfg.min_freq_abs
        elif p["df_w1w2"] < cfg.min_doc_freq:
            reason = "df<%d" % cfg.min_doc_freq
        if reason:
            rejected.append({**p, "llr": None, "passed": False, "rejected_reason": reason})
            continue
        c_w1 = p.get("c_w1") or uni.get(w1, 0)
        c_w2 = p.get("c_w2") or uni.get(w2, 0)
        llr = compute_llr(p["c_w1w2"], c_w1, c_w2, corpus_tokens)
        if llr <= cfg.llr_significant:
            rejected.append({**p, "llr": round(llr, 4), "passed": False,
                             "rejected_reason": "llr<=%.2f" % cfg.llr_significant})
            continue
        passed.append({**p, "llr": round(llr, 4), "passed": True,
                       "top_level": "golden" if llr > cfg.llr_golden else "normal"})
    passed.sort(key=lambda x: -x["llr"])
    rejected.sort(key=lambda x: -x["c_w1w2"])
    return passed, rejected


def write_stage2(cfg, passed, rejected):
    """落盘 filtered_lexical_pairs.{json,md}"""
    write_json(os.path.join(cfg.out_dir, "filtered_lexical_pairs.json"),
               {"pairs": passed, "rejected": rejected, "params": cfg.to_dict()})
    md = ["## 二元过滤（P2·LLR）",
          "> 入选判据：C(w1,w2)>%d 且 DF≥%d 且 LLR>%.2f(p<0.05)；黄金候选 LLR>%.2f(p<0.01)。"
          % (cfg.min_freq_abs, cfg.min_doc_freq, cfg.llr_significant, cfg.llr_golden),
          "",
          "| 搭配对 | 关系 | 粗略共现频次 | DF | LLR | 级别 | 代表性例句 |",
          "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"]
    for p in passed[:300]:
        md.append("| %s-%s | %s | %d | %d | %.2f | %s | %s |" % (
            p["w1"], p["w2"], p["rel"], p["c_w1w2"], p["df_w1w2"],
            p["llr"], p["top_level"], p["example"]))
    md.append("")
    md.append("*被淘汰候选（原因）*")
    md.append("| 搭配对 | 关系 | 频次 | DF | 原因 |")
    md.append("| :--- | :--- | :--- | :--- | :--- |")
    for p in rejected[:100]:
        md.append("| %s-%s | %s | %d | %d | %s |" % (
            p["w1"], p["w2"], p["rel"], p["c_w1w2"], p["df_w1w2"], p["rejected_reason"]))
    with open(os.path.join(cfg.out_dir, "filtered_lexical_pairs.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

