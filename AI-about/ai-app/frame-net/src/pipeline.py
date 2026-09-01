# pipeline.py
# -*- coding: utf-8 -*-
"""管线编排（spec §2/§7）：0→1→2→3→3.5→4→5，输出全部 6 组中间结果。"""
import json
import os
import time

from .config import Config
from .parser import build_parser
from . import bigram, llr, entropy, trigram


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run(cfg):
    os.makedirs(cfg.out_dir, exist_ok=True)
    report = {}

    t0 = time.time()
    parser = build_parser(cfg)

    # P0
    records = bigram.run_stage0(cfg, parser)
    report["P0_corpus_parsed"] = len(records)
    print("[P0] corpus_parsed.assert 句子数=%d (%.1fs)" % (len(records), time.time() - t0))

    # P1
    counter = bigram.extract_bigrams(cfg, records)
    pairs, cand, deverbal = bigram.write_stage1(cfg, records, counter)
    report["P1_raw_bigrams"] = len(pairs)
    report["P1_candidate_evidence"] = len(cand)
    report["P1_deverbal"] = len(deverbal)
    print("[P1] raw_bigrams 候选=%d 低置信证据=%d deverbal=%d" % (len(pairs), len(cand), len(deverbal)))

    # P2
    corpus_tokens = sum(counter.uni.values())
    passed, rejected = llr.run_stage2(cfg, pairs, counter.uni, corpus_tokens)
    llr.write_stage2(cfg, passed, rejected)
    report["P2_filtered"] = len(passed)
    report["P2_rejected"] = len(rejected)
    print("[P2] filtered=%d rejected=%d (corpus_tokens=%d)" % (len(passed), len(rejected), corpus_tokens))

    # P3 + P3.5
    lus = entropy.run_stage3(cfg, os.path.join(cfg.out_dir, "raw_bigrams_counts.json"),
                             os.path.join(cfg.out_dir, "corpus_parsed.json"))
    entropy.write_stage3(cfg, lus or [])
    active = [l["lu"] for l in (lus or []) if l["tag"] in ("Active_LU", "POLYSEMOUS_CHECK")]
    # 标定决策（修改I）：该语料谓词宾语分布中熵，单靠低熵 Active_LU 白名单为空；
    # 扩展白名单 = Active_LU ∪ P2 通过的 pred_noun 谓词头词（即“高频搭配”实际候选）。
    active += sorted({p["w1"] for p in passed if p["type"] == "pred_noun" and not p.get("rejected")})
    report["P3_lus"] = len(lus or [])
    report["P3_active_lu"] = len(active)
    print("[P3] LU 种子数=%d 三元辐射白名单=%d" % (len(lus or []), len(active)))

    # P4
    parsed, tri_counter = trigram.scan_triples(cfg, os.path.join(cfg.out_dir, "corpus_parsed.json"), active)
    trows = trigram.write_stage4(cfg, parsed, tri_counter, counter.uni)
    report["P4_raw_trigrams"] = len(trows)
    print("[P4] raw_trigrams 候选=%d" % len(trows))

    # P5
    templates = trigram.write_stage5(cfg, trows, pairs, counter.uni)
    report["P5_templates"] = len(templates)
    report["P5_passed"] = sum(1 for t in templates if t["passed"])
    print("[P5] templates=%d passed=%d" % (len(templates), report["P5_passed"]))

    report["runtime_s"] = round(time.time() - t0, 2)
    report["params"] = cfg.to_dict()
    eval_dir = os.path.join(cfg.out_dir, "eval")
    os.makedirs(eval_dir, exist_ok=True)
    with open(os.path.join(eval_dir, "run_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report

