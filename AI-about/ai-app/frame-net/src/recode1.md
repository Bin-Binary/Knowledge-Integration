```python
# io_utils.py
# -*- coding: utf-8 -*-
"""JSON + MD 双格式输出（spec §4：每个中间结果必须落盘为 .json 与 .md）。"""
import json
import os
from pathlib import Path


def ensure_dir(path):
    p = Path(path)
    if not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path, obj, indent=2):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent)


def render_table(columns, rows, col_sep=" | "):
    """渲染对齐的 Markdown 表。columns: list[str]; rows: list[list[str]]。"""
    cols = list(columns)
    data = [[str(c).replace("\n", " ").replace("|", "\\|") for c in cols]]
    for r in rows:
        data.append([str(x).replace("\n", " ").replace("|", "\\|").strip() if x is not None else "" for x in r])
    widths = [max(len(r[i]) for r in data) for i in range(len(cols))]
    head = col_sep.join(c.ljust(widths[i]) for i, c in enumerate(data[0]))
    sep = "-+-".join("-" * w for w in widths)
    body = []
    for r in data[1:]:
        body.append(col_sep.join(r[i].ljust(widths[i]) for i in range(len(cols))))
    return (head + "\n" + "|" + sep + "|" + "\n" + "\n".join(body))


def write_md(path, title, quote, section_header, columns, rows):
    lines = ["## " + title, "", "> " + quote, "", "*" + section_header + "*", "",
             "| " + " | ".join(columns) + " |",
             "| " + " | ".join([":---"] * len(columns)) + " |"]
    for r in rows:
        lines.append("| " + " | ".join(str(x).replace("|", "\\|") if x is not None else "" for x in r) + " |")
    lines.append("")
    write_md_raw(path, "\n".join(lines))


def write_md_raw(path, text):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def path_stem(out_dir, name):
    return os.path.join(out_dir, name)

```

```python
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

```
```python
# parser.py
# -*- coding: utf-8 -*-
"""P0 解析器（spec D1/D1a/D1b）。

后端抽象：`ParserBackend.parse_sentence(text) -> ParseResult`。
- rule: 内置规则浅层依存（jieba posseg）。输出 SD 风格 rel：nsubj/obj/advmod/prep(+pobj)/amod/cop。
- hanlp: 可选后端（COARSE_ELECTRA_SMALL_ZH + CTB9_DEP），模型不存在/离线时自动回退 rule。

修改A·解析噪声控制：每条边带置信度 score；score < parser_conf_threshold 的边以
`candidate=true` 形式保留在 ParseResult 中（写盘），但**不计入共现频数**。
"""
import os
import jieba.posseg as pseg

from .config import Config
from . import domain_dict

LIGHT = None
COP_WORDS = {"是", "为", "叫", "等于"}
ASPECT = {"的", "了", "过", "着"}          # 助词（跳读）
BA_WORDS = {"把", "将"}                   # 处置式
BEI_WORDS = {"被"}                        # 被动式
# 方式/频率副词强制覆盖：即使 jieba 标为 v，也按副词处理（修正“自动触发”等伪主谓）
ADV_OVERRIDE = frozenset(
    "自动 批量 依次 单独 定时 手动 异步 重新 直接 另 再由 只 仅 均 随时 立刻 一直 仅支持 "
    "联合 集中 统一 同时 分别 一并 循环 定期 动态 静态".split())
NOUN_PREFIX = ("n",)                      # jieba: n/nz/nr/an/vn
EN_POS = ("eng", "x")                     # 英文/未知词视为可填充名词位


class Token:
    __slots__ = ("idx", "word", "pos", "dep_head", "dep_rel", "score")

    def __init__(self, idx, word, pos, dep_head=-1, dep_rel="", score=0.9):
        self.idx = idx
        self.word = word
        self.pos = pos
        self.dep_head = dep_head
        self.dep_rel = dep_rel
        self.score = score

    def to_dict(self):
        return {"idx": self.idx, "word": self.word, "pos": self.pos,
                "dep_head": self.dep_head, "dep_rel": self.dep_rel, "score": self.score}


class Edge:
    __slots__ = ("head", "dep", "rel", "score", "candidate")

    def __init__(self, head, dep, rel, score=0.8, candidate=False):
        self.head = head
        self.dep = dep
        self.rel = rel
        self.score = score
        self.candidate = candidate  # 低置信度证据：保留但不计频（修改A）

    def to_dict(self):
        return {"head": self.head, "rel": self.rel, "score": self.score, "candidate": self.candidate}


class ParseResult:
    def __init__(self, text, tokens, edges):
        self.text = text
        self.tokens = tokens
        self.edges = edges

    def to_dict(self):
        return {"text": self.text,
                "tokens": [t.to_dict() for t in self.tokens],
                "edges": [e.to_dict() for e in self.edges]}


class RuleParser:
    """规则浅层依存解析器（离线可复现），产出 nsubj/obj/advmod/prep+pobj/amod。"""

    def __init__(self, cfg):
        self.cfg = cfg
        global LIGHT
        LIGHT = cfg.light_verbs

    # ---------- 基础 ----------
    def _pos(self, t):
        return t.pos

    def _is_noun(self, t):
        if t.pos.startswith(NOUN_PREFIX) and t.pos != "ng":
            return True
        if t.pos == "eng":
            return True
        if t.pos == "x" and any(c.isalnum() for c in t.word):
            return True
        return False

    def _is_verb(self, t):
        if t.word in ADV_OVERRIDE:
            return False
        return t.pos.startswith("v") and t.word not in LIGHT and t.pos != "vyou"

    def _is_adv(self, t):
        if t.word in ADV_OVERRIDE:
            return True
        return t.pos.startswith("d") or t.word in {"非常", "很", "也", "已", "就", "才"}

    def parse_sentence(self, text):
        raw = [(w, f) for w, f in pseg.cut(text) if w.strip()]
        if len(raw) < 2:
            return None
        toks = []
        for i, (w, f) in enumerate(raw):
            toks.append(Token(i, w, f))
        edges = []
        self._parse_edges(toks, edges)
        return ParseResult(text, toks, edges)

    def _nearest(self, toks, start, step, pred, skip_pred=None):
        """从 start 向 step(+1右/-1左) 找最近的满足 pred 的 token。"""
        i = start + step
        while 0 <= i < len(toks):
            t = toks[i]
            if skip_pred and skip_pred(t):
                i += step
                continue
            if pred(t):
                return i, t
            if t.pos in ("w",) or t.pos.startswith("u"):
                i += step
                continue
            # 越界：遇到另一实义动词（obj 不回跨动词、nsubj 不跨动词/处置介词）
            if step == 1 and self._is_verb(t):
                break
            if step == -1 and (self._is_verb(t) or t.word in BA_WORDS or t.word in BEI_WORDS):
                break
            i += step
        return None

    def _next_verb(self, toks, start):
        """从 start 右起找第一个实义动词（跳过 light verb，如“进行初始化”）。"""
        for i in range(start + 1, len(toks)):
            if self._is_verb(toks[i]):
                return i, toks[i]
        return None

    def _parse_edges(self, toks, edges):
        n = len(toks)
        verb_ids = [i for i, t in enumerate(toks) if self._is_verb(t)]
        cop_ids = [i for i, t in enumerate(toks) if t.word in COP_WORDS]

        # 1. 副词邻接动词 advmod
        for i, t in enumerate(toks):
            if not self._is_adv(t):
                continue
            for step in (1, -1):
                hit = self._nearest(toks, i, step, self._is_verb,
                                    skip_pred=lambda x: self._is_adv(x))
                if hit:
                    j, v = hit
                    score = 0.8 if abs(j - i) == 1 else 0.65
                    edges.append(Edge(v.idx, t.idx, "advmod", score, score < self.cfg.parser_conf_threshold))
                    break

        # 2. 介词 + 介宾 prep+pobj
        for i, t in enumerate(toks):
            if not t.pos.startswith("p"):
                continue
            pobj = self._nearest(toks, i, 1, lambda x: self._is_noun(x) or self._is_verb(x))
            if not pobj:
                continue
            j, objtok = pobj
            # 介词后的动词（如"用于设置密码"）pobj 可后移到其宾语
            if self._is_verb(objtok):
                objtok2 = self._nearest(toks, j, 1, self._is_noun)
                if objtok2 and objtok2[1].word not in ASPECT:
                    k, objtok = objtok2
                    j = k
            score = 0.7 if abs(j - i) <= 2 else 0.55
            edges.append(Edge(t.idx, j, "pobj", score, score < self.cfg.parser_conf_threshold))
            # prep 依附其后最近的实义动词（跳过 light verb，如“按...进行初始化”）
            vj = self._next_verb(toks, max(i, j))
            if vj:
                edges.append(Edge(vj[1].idx, t.idx, "prep", score, score < self.cfg.parser_conf_threshold))

        # 3. 处置/被动 把/将/被 宾语 -> obj
        for i, t in enumerate(toks):
            if t.word not in BA_WORDS and t.word not in BEI_WORDS:
                continue
            nxt = self._nearest(toks, i, 1, self._is_noun)
            vj = self._nearest(toks, max(i, nxt[0] if nxt else i), 1, self._is_verb)
            if nxt and vj:
                score = 0.65
                edges.append(Edge(vj[1].idx, nxt[1].idx, "obj", score,
                                  score < self.cfg.parser_conf_threshold))

        # 4. 主宾语：每个动词取最近 nsubj / obj
        for i in verb_ids + cop_ids:
            v = toks[i]
            subj = self._nearest(toks, i, -1,
                                 lambda x: self._is_noun(x) or x.pos.startswith("r"),
                                 skip_pred=lambda x: x.word in BA_WORDS or x.word in BEI_WORDS
                                 or x.pos.startswith("p") or self._is_adv(x))
            if subj and subj[1].idx not in {e.dep for e in edges if e.rel == "pobj"}:
                s = 0.8 if abs(subj[0] - i) == 1 else 0.65
                edges.append(Edge(v.idx, subj[1].idx, "nsubj", s, s < self.cfg.parser_conf_threshold))
            obj = self._nearest(toks, i, 1, self._is_noun,
                                skip_pred=lambda x: x.pos.startswith("p") or x.word in BA_WORDS or x.word in BEI_WORDS)
            if obj:
                o = 0.8 if abs(obj[0] - i) == 1 else 0.65
                edges.append(Edge(v.idx, obj[1].idx,
                                  "obj" if v.pos != "cop" else "cop_obj", o,
                                  o < self.cfg.parser_conf_threshold))

        # 5. 定中 amod（N 的 N / 形容词 N）——二元抽取不取 amod，仅作句法上下文（修改B：含 vn 事件名词中心语）
        for i, t in enumerate(toks):
            if not (self._is_noun(t) or t.pos == "vn"):
                continue
            prev = self._nearest(toks, i, -1, lambda x: self._is_noun(x) or x.pos.startswith("a"))
            if prev and toks[prev[0] + 1].word == "的":
                edges.append(Edge(t.idx, prev[1].idx, "amod", 0.8, False))

        self._finalize(toks, edges, verb_ids, cop_ids)

    def _finalize(self, toks, edges, verb_ids, cop_ids):
        """分配 root、回填 dep_head 到 token。"""
        heads = {}
        rels = {}
        for e in edges:
            heads.setdefault(e.dep, e.head)
            rels.setdefault(e.dep, e.rel)
        roots = verb_ids + cop_ids
        if roots:
            root = roots[0]
        else:
            root = -1
        conf = 0.9
        for t in toks:
            if t.idx in heads:
                t.dep_head = heads[t.idx]
                t.dep_rel = rels[t.idx]
            elif t.idx == root:
                t.dep_head = -1
                t.dep_rel = "root"
            else:
                t.dep_head = root if root != -1 else -1
                t.dep_rel = "discourse"
        # 句子级最低边置信度（用于 P1 频数过滤）
        if edges:
            conf = min(e.score for e in edges)
        self._sent_conf = conf


class HanlpParser:
    """hanlp 后端（可选）。模型缺失/离线时构造失败，由工厂回退 RuleParser。"""

    def __init__(self, cfg):
        try:
            import hanlp
        except Exception:
            raise RuntimeError("hanlp 不可用")
        pipeline = (hanlp.pipeline()
                    .append(hanlp.utils.rules.split_sentence, output_key="sentences")
                    .append(hanlp.load("COARSE_ELECTRA_SMALL_ZH"), output_key="tok")
                    .append(hanlp.load("CTB9_DEP_ELECTRA_SMALL"), input_key="tok", output_key="dep"))
        self.nlp = pipeline
        self.cfg = cfg

    def parse_sentence(self, text):
        try:
            doc = self.nlp(text)
            toks, deps = doc["tok"][0], doc["dep"][0]
            out = []
            for i, (w, d) in enumerate(zip(toks, deps)):
                h, rel = d
                h = h - 1  # CTB9 1-based -> 0-based
                out.append(Token(i, w, "x", h if h >= 0 else -1, rel, 0.9))
            self._sent_conf = 0.9
            return ParseResult(text, out, [])
        except Exception:
            return None


def build_parser(cfg):
    """解析器工厂（spec D1a：经接口抽象可替换）。"""
    domain_dict.install(cfg.domain_dict_path)
    if cfg.parser_backend == "hanlp":
        try:
            return HanlpParser(cfg)
        except Exception:
            pass
    return RuleParser(cfg)
```
```python
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

```
```python
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
```
