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
