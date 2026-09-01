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
