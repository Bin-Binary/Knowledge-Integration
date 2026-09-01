# cli.py
# -*- coding: utf-8 -*-
"""命令行入口：python -m corpus_processing.cli [--corpus-dir ...] [--out-dir ...] [--parser rule|hanlp] ..."""
import argparse
import sys

from .config import Config
from .pipeline import run


def main(argv=None):
    ap = argparse.ArgumentParser(prog="corpus_processing", description="高频搭配管线（LU/FE 候选生成，spec corpus_processing.spec.md）")
    ap.add_argument("--corpus-dir", help="原始语料根目录（递归）")
    ap.add_argument("--out-dir", help="中间结果输出目录（默认 references/corpus_processing）")
    ap.add_argument("--parser", choices=["rule", "hanlp"], default=None, help="解析后端，默认 rule（hanlp 无模型时自动回退）")
    ap.add_argument("--min-freq-abs", type=int, help="P2 绝对频数阈值 C(w1,w2)>N（默认11）")
    ap.add_argument("--min-doc-freq", type=int, help="P2 文档频率阈值 DF>=N（默认3）")
    ap.add_argument("--llr-significant", type=float, help="P2 LLR 显著阈值（默认3.84）")
    ap.add_argument("--entropy-high", type=float, help="P3 高熵界（默认0.85）")
    ap.add_argument("--entropy-low", type=float, help="P3 低熵界（默认0.35）")
    ap.add_argument("--partial-pmi", type=float, help="P5 Partial PMI 阈值（默认1.5）")
    args = ap.parse_args(argv)

    overrides = {}
    if args.corpus_dir:
        overrides["corpus_dir"] = args.corpus_dir
    if args.out_dir:
        overrides["out_dir"] = args.out_dir
    if args.parser:
        overrides["parser_backend"] = args.parser
    if args.min_freq_abs is not None:
        overrides["min_freq_abs"] = args.min_freq_abs
    if args.min_doc_freq is not None:
        overrides["min_doc_freq"] = args.min_doc_freq
    if args.llr_significant is not None:
        overrides["llr_significant"] = args.llr_significant
    if args.entropy_high is not None:
        overrides["entropy_high"] = args.entropy_high
    if args.entropy_low is not None:
        overrides["entropy_low"] = args.entropy_low
    if args.partial_pmi is not None:
        overrides["partial_pmi_threshold"] = args.partial_pmi

    cfg = Config(**overrides)
    report = run(cfg)
    print("\n[v] 运行完成，输出目录: %s" % cfg.out_dir)
    for k, v in report.items():
        if not k.startswith("params"):
            print("   %s = %s" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())
