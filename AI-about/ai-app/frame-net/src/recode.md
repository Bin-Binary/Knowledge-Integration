```python
# __init__.py
# -*- coding: utf-8 -*-
"""corpus_processing - 高频搭配管线（LU/FE 候选生成）

依据: corpus_processing.spec.md（以 poc.md §高频搭配 + 修改块 A~I 为权威）。
本包实现 spec 0-5 阶段，输出 6 组 .json + .md 中间结果。
"""
__version__ = "0.1.0"
```
```python
# bigram.py
# -*- coding: utf-8 -*-
"""P0 语料解析 + P1 二元抽取（spec §3 P0/P1，输出 corpus_parsed / raw_bigrams_counts）。

语料加载（D2）：递归读取 UTF-8；ext 在 include_exts；跳过 in.txt 等；按 split_re 分句。
二元抽取（D1b）：从解析边
  V-obj-N / V-nsubj-N → pred_noun
  V-advmod-Adv       → pred_adv
  V-prep→pobj-N      → pred_prep
只对置信度达标的边计频（修改A），低置信证据保留在 candidate_evidence。
修改B：amod 结构中词性为 vn 的事件名词 → deverbal 名词化谓词（N 的 V）。
"""
import os
import re

from .io_utils import write_json, write_md

SPLIT_PAT_CACHE = {}
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
# 列表/序号/项目符号/标题前缀（P0 去噪，标定环修改I）
LEADER_RE = re.compile(
    r"^\s*(?:[①-⑳\d一二三四五六七八九十百千]+[\.、．:：\)）]|"
    r"\(\d+\)|\[\d+\]|[-\*•·>►▶]|[a-zA-Z]\d{0,2}\)|"
    r"(?:Case|步骤|Step|Note|注意|说明|场景|方案)[一二三四五六七八九十\d]*[\.、:：])\s*")


def _split_pat(cfg):
    if cfg.split_re not in SPLIT_PAT_CACHE:
        SPLIT_PAT_CACHE[cfg.split_re] = re.compile("[" + re.escape(cfg.split_re) + "]")
    return SPLIT_PAT_CACHE[cfg.split_re]


class ParseRecord:
    __slots__ = ("doc_id", "source", "text", "sent_id", "pr", "score")

    def __init__(self, doc_id, source, text, sent_id, pr, score):
        self.doc_id = doc_id
        self.source = source
        self.text = text
        self.sent_id = sent_id
        self.pr = pr
        self.score = score


def load_documents(cfg):
    files = []
    for root, _dirs, names in os.walk(cfg.corpus_dir):
        for name in names:
            if name in cfg.skip_files:
                continue
            if os.path.splitext(name)[1] not in cfg.include_exts:
                continue
            files.append(os.path.join(root, name))
    return sorted(files)


def split_sentences(cfg, text):
    pat = _split_pat(cfg)
    out = []
    for seg in pat.split(text):
        seg = seg.strip()
        if not seg:
            continue
        if re.fullmatch(r"[\d\t|、，,。/\\ \-\+%=]+", seg):
            continue
        # P0 去噪（标定环修改I）：无中文片段（纯 URL/版本/枚举）直接丢弃
        if not CJK_RE.search(seg):
            continue
        if len(seg) < 4:
            continue
        # 剥离列表/标题前缀，使“1、仓库授权”变为名词短语而非伪主谓
        stripped = LEADER_RE.sub("", seg).strip()
        if stripped and CJK_RE.search(stripped):
            seg = stripped
        if len(CJK_RE.findall(seg)) < 2:
            continue
        out.append(seg[: cfg.max_sent_len])
    return out


def run_stage0(cfg, parser):
    """P0 解析并落盘 corpus_parsed.{json,md}，返回 records。"""
    records = []
    docs = []
    for doc_id, path in enumerate(load_documents(cfg), 1):
        with open(path, encoding=cfg.encoding, errors="replace") as f:
            text = f.read()
        doc_recs = {"doc_id": f"d{doc_id:03d}",
                    "source": os.path.relpath(path, cfg.corpus_dir), "sents": []}
        sent_no = 0
        for seg in split_sentences(cfg, text):
            pr = parser.parse_sentence(seg)
            if pr is None:
                continue
            sent_no += 1
            score = min((e.score for e in pr.edges), default=0.9)
            records.append(ParseRecord(doc_recs["doc_id"], doc_recs["source"], seg,
                                       f"s{sent_no:04d}", pr, score))
            doc_recs["sents"].append({
                "sent_id": records[-1].sent_id, "text": seg, "valid": True,
                "score": score, "tokens": [t.to_dict() for t in pr.tokens]})
        docs.append(doc_recs)

    write_json(os.path.join(cfg.out_dir, "corpus_parsed.json"),
               {"docs": docs, "params": cfg.to_dict()})
    rows = [[r.doc_id, r.sent_id, r.source, r.text[: cfg.example_max_chars], f"{r.score:.2f}"]
            for r in records]
    write_md(os.path.join(cfg.out_dir, "corpus_parsed.md"),
             "语料解析（P0）",
             "分词+POS+依存解析结果；score=句子最低边置信度（修改A），低于阈值边的二元不计频",
             "corpus_parsed", ["doc_id", "sent_id", "source", "text", "score"], rows)
    return records


class BigramCounter:
    def __init__(self):
        self.uni = {}
        self.pairs = {}
        self.candidate = {}
        self.deverbal = {}

    def uni_add(self, toks, cfg):
        seen = set()
        for t in toks:
            w = t.word
            if not w or w in cfg.stopwords or not any(c.isalnum() for c in w):
                continue
            if w in seen:
                continue
            seen.add(w)
            self.uni[w] = self.uni.get(w, 0) + 1


def extract_bigrams(cfg, records):
    counter = BigramCounter()
    for rec in records:
        pr = rec.pr
        counter.uni_add(pr.tokens, cfg)
        by_idx = {t.idx: t for t in pr.tokens}
        # 介宾名词不再重复计入 obj/nsubj（如“返回给流水线”中“流水线”只算介宾）
        pobj_deps = {e.dep for e in pr.edges if e.rel == "pobj"}
        for e in pr.edges:
            head = by_idx.get(e.head)
            dep = by_idx.get(e.dep)
            if head is None or dep is None:
                continue
            if e.rel == "obj" or e.rel == "nsubj":
                if e.dep in pobj_deps:
                    continue
                ptype, prel = "pred_noun", e.rel
            elif e.rel == "advmod":
                ptype, prel = "pred_adv", "advmod"
            elif e.rel == "prep":
                ptype, prel = "pred_prep", "prep"
            elif e.rel == "pobj":
                # 介-宾 共现（Prep-N-V 三元 Partial PMI 的分母 C(w1,w2)）
                ptype, prel = "prep_pobj", "pobj"
            else:
                # 修改B：名词化谓词（中心名词词性为 vn 的事件名词 → “N的V” 短语）
                if e.rel == "amod" and head.pos in ("vn",):
                    phrase = f"{dep.word}的{head.word}"
                    d = counter.deverbal.setdefault(phrase, {"head": head.word, "mod": dep.word, "n": 0})
                    if rec.score >= cfg.parser_conf_threshold:
                        d["n"] += 1
                continue
            w1, w2 = head.word, dep.word
            if not w1 or not w2 or w1 in cfg.stopwords or w2 in cfg.stopwords:
                continue
            key = (w1, w2, ptype, prel)
            if e.candidate:
                counter.candidate[key] = counter.candidate.get(key, 0) + 1
                continue
            bucket = counter.pairs.setdefault(key, {"c": 0, "df": set(), "sents": []})
            bucket["c"] += 1
            bucket["df"].add(rec.doc_id)
            if len(bucket["sents"]) < 5:
                bucket["sents"].append({"doc_id": rec.doc_id, "sent_id": rec.sent_id})
    return counter


def write_stage1(cfg, records, counter):
    """P1 落盘 raw_bigrams_counts.{json,md}。"""
    rec_by = {(r.doc_id, r.sent_id): r for r in records}

    def sent_text(m):
        r = rec_by.get((m["doc_id"], m["sent_id"]))
        return r.text[: cfg.example_max_chars] if r else ""

    pairs = []
    for (w1, w2, ptype, rel), b in sorted(counter.pairs.items(), key=lambda kv: -kv[1]["c"]):
        pairs.append({
            "w1": w1, "w2": w2, "type": ptype, "rel": rel,
            "c_w1": counter.uni.get(w1, 0), "c_w2": counter.uni.get(w2, 0),
            "c_w1w2": b["c"], "df_w1w2": len(b["df"]),
            "example": sent_text(b["sents"][0]) if b["sents"] else "",
            "sents": b["sents"]})
    cand = [{"w1": k[0], "w2": k[1], "type": k[2], "rel": k[3], "count": v,
             "note": "低置信度证据，不计入共现频数（修改A）"}
            for k, v in counter.candidate.items()]
    deverbal = [{"phr": k, "head": v["head"], "mod": v["mod"], "n": v["n"]}
                for k, v in counter.deverbal.items() if v["n"] > 0]

    write_json(os.path.join(cfg.out_dir, "raw_bigrams_counts.json"),
               {"pairs": pairs, "candidate_evidence": cand, "deverbal": deverbal,
                "params": cfg.to_dict()})

    sections = [("pred_noun", "谓词‑名词"), ("pred_adv", "谓词‑副词"), ("pred_prep", "谓词‑介词"),
                ("prep_pobj", "介词‑介宾")]
    md = ["## 高频搭配提取（P1 二元抽取·原始共现）",
          "> 二元候选原始频数；DF=文档频率（≥%d）；低置信候选在 json candidate_evidence 中保留但不计频" % cfg.min_doc_freq,
          ""]
    for ptype, title in sections:
        md.append("*%s*" % title)
        md.append("| 搭配对 | 关系 | 粗略共现频次 | DF | 代表性例句 |")
        md.append("| :--- | :--- | :--- | :--- | :--- |")
        for p in [x for x in pairs if x["type"] == ptype][:200]:
            md.append("| %s-%s | %s | %d | %d | %s |" % (
                p["w1"], p["w2"], p["rel"], p["c_w1w2"], p["df_w1w2"], p["example"]))
        md.append("")
    write_md_raw(os.path.join(cfg.out_dir, "raw_bigrams_counts.md"), "\n".join(md))
    return pairs, cand, deverbal


def write_md_raw(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
```
```python
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
```

```python
# config.py
# -*- coding: utf-8 -*-
"""配置：spec §1 实现决策 + §5 参数表，全部可经 CLI/环境变量覆盖。
"""
import os
import json


class Config:
    def __init__(self, **overrides):
        # ---- 路径与输入 (D2) ----
        self.corpus_dir = r"D:\code-repo\Knowledge-Integration\AI-about\ai-app\memory\schemas\frame_net\cloudedragon"
        self.out_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),  # frame_net
            "references", "corpus_processing",
        )
        self.domain_dict_path = None          # 可选：外部领域词表文件（每行一个词）
        self.stopwords_path = None            # 可选：外部停用/轻动词表（每行一个词）
        self.include_exts = [".txt", ".0", ""]  # 空串=无扩展名文件
        self.skip_files = {"in.txt"}
        self.encoding = "utf-8"
        self.split_re = "。！？!?；;\n"

        # ---- 解析 (D1/D1a/D1b, 修改A) ----
        self.parser_backend = "rule"          # "rule" | "hanlp"，自动探测
        self.parser_conf_threshold = 0.7      # 低于此置信度的边不计入共现频数(修改A)
        self.max_sent_len = 200               # 超长句丢弃（表格/无标点噪声）

        # ---- 三元槽位映射 (D6) ----
        #   Adv-V-N : w1=Adv, w2=V(LU), w3=N (FE位=w3)
        #   Prep-N-V: w1=Prep, w2=N,      w3=V(LU) (FE位=w1+w2)

        # ---- P2 二元过滤 (修改C / §5) ----
        self.min_freq_abs = 4                # C(w1,w2) > 3；标定值（修改I，§9-B），初值11
        self.min_doc_freq = 3                # DF >= 3
        self.llr_significant = 3.84          # p<0.05
        self.llr_golden = 6.63               # p<0.01

        # ---- P3 语义熵 (修改D / §5) ----
        self.entropy_high = 0.85             # >= => [Drop_Light_Verb]
        self.entropy_low = 0.35              # <= => [Active_LU]
        self.min_c_for_seed = 5              # 极低频谓词不参与标记
        self.min_objects_for_active = 3      # Active_LU 需 ≥3 个不同宾语（排除 bool/数字等占位）
        self.entropy_smooth = 1.0            # 加一平滑(修改D)

        # ---- P3.5 义项检查 (修改E) ----
        self.sense_min_clusters = 2
        self.sense_max_clusters = 3
        self.sense_jaccard_threshold = 0.30  # 簇间名词集差异判定

        # ---- P4/P5 三元 (§5) ----
        self.min_triple_freq = 2
        self.partial_pmi_threshold = 1.5
        self.synthesized_switch = False      # 修改F：默认 off

        # ---- 输出 (D5) ----
        self.example_max_chars = 80

        # ---- 评估环 (修改I) ----
        self.eval_dir = os.path.join(os.path.dirname(self.out_dir), "corpus_processing", "eval")
        self.calibration_sample = 300        # 人工标定样本量(预留)

        # 停用/轻动词表内置默认(修改D4)
        self._builtin_stopwords = set(
            "的 了 在 对 是 有 一个 进行 具有 通过 可以 以及 和 与 或 并 也 就 都 被 把 将 这 那 该 一些 "
            "每个 所有 自己 其他 其它 之间 其中 是否 就是 需要 用于 包括 或者 然后 如果 因为 所以 "
            "这个 那个 我们 用户 系统 相关 对应 例如 以上 以下 一般 主要 非常 很 也 还 已 到 从 向 等 "
            "为 上 中 下 前 后 则 无 另 时 场景 方式 可 会 能 所示 如上 如下 以下 综上".split())
        self._builtin_light_verbs = set(
            "进行 具有 得到 给予 做出 实施 开展 完成 存在 起 予以 加以".split())

        for k, v in overrides.items():
            setattr(self, k, v)
        self.stopwords_path = os.environ.get("STOPWORDS_FILE") or self.stopwords_path
        if self.stopwords_path and os.path.isfile(self.stopwords_path):
            with open(self.stopwords_path, encoding="utf-8") as f:
                self._builtin_stopwords.update(x.strip() for x in f if x.strip())

    @property
    def stopwords(self):
        return frozenset(self._builtin_stopwords)

    @property
    def light_verbs(self):
        return frozenset(self._builtin_light_verbs)

    def to_dict(self):
        d = {k: v for k, v in self.__dict__.items() if k in (
            "min_freq_abs", "min_doc_freq", "llr_significant", "llr_golden",
            "entropy_high", "entropy_low", "min_c_for_seed", "sense_min_clusters",
            "sense_jaccard_threshold", "min_triple_freq", "partial_pmi_threshold",
            "parser_conf_threshold", "parser_backend", "synthesized_switch")}
        return d

```

```python
# domain_dict.py
# -*- coding: utf-8 -*-
"""领域词表（D3b）：固化 cloudedragon 产品域词汇，先于分词加载，
防止 pipeline_id / MR / YAML 等未登录词切错，并提升候选质量。

来源：对 cloudedragon/ 语料人工观察固化（spec 修改A·第2条）。
"""
import os
import jieba
import jieba.posseg as pseg

BUILTIN_TERMS = [
    # 英/中混排专名与单元
    "流水线", "代码库", "微服务", "门禁", "插件", "方案", "版本", "群组", "仓库", "模板",
    "构建", "部署", "发布", "触发", "启动", "停止", "执行", "创建", "配置", "测试",
    "stage", "job", "task", "pipeline", "pipeline_id", "job_id", "group_id", "service_id",
    "scheme_id", "parameter", "parameter_id", "branch", "tag", "snapshot", "release",
    "MR", "mr", "PBI", "pbi", "YAML", "yaml", "YML", "Bash", "SDK", "API", "URL", "URI",
    "Build", "Source", "Beta", "Alpha", "Gamma", "Iota", "Kappa", "Lambda", "Versionset",
    "codehub", "pclint", "codedex", "DEVOPS", "DevOps", "deploy", "CheckConfig", "toORM",
    "ReleaseToORM", "CloudInit", "clouddragon", "CloudDragon", "Atlas", "git-mm",
    "评审人", "合并人", "工作项", "子流水线", "质量门禁", "门禁指标", "检查任务",
    "可信构建", "可追溯", "可重复", "自动化发布", "串行", "并行", "超时时间", "部署任务",
    # 阶段链
    "微服务型", "组合服务型",
    # 去噪复合词（标定评估环，修改I）：降低列表/标题行切分噪声
    "版本包", "运行时", "代码检查", "静态检查", "编译构建", "定时任务", "执行计划",
    "版本号", "任务编排", "仓库授权", "流水线模板", "插件配置", "参数引用",
]
EXTRA_POS_HINTS = {
    "pipeline": "nz", "pipeline_id": "nz", "job_id": "nz", "group_id": "nz",
    "service_id": "nz", "scheme_id": "nz", "MR": "nz", "mr": "nz", "PBI": "nz",
    "pbi": "nz", "YAML": "nz", "yaml": "nz", "YML": "nz", "URL": "nz", "URI": "nz",
    "codehub": "nz", "pclint": "nz", "Versionset": "nz", "Build": "vn", "Source": "nz",
}


def _load_external(path=None):
    words = []
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    words.append(line.split()[0] if line.startswith(("词|", "term|")) else line)
    return words


def load_terms(path=None):
    return list(dict.fromkeys(BUILTIN_TERMS + _load_external(path)))


def install(path=None):
    """向 jieba 注入领域词表（D3b）。多次调用幂等。"""
    if getattr(install, "_done", False):
        return
    for w in load_terms(path):
        jieba.add_word(w, freq=9999, tag=EXTRA_POS_HINTS.get(w, "nz" if any(
            c.isalpha() for c in w) else "n"))
    # 防止错误切分（强制定长优先）
    install._done = True


def annotate_pos(seg_list):
    """jieba 分词 -> (word, pos) 序列（pseg.cut 保证与 add_word tag 一致）。"""
    out = []
    for tk in seg_list:
        out.append((tk.word, tk.flag))
    return out
```

```pyhton
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

```
