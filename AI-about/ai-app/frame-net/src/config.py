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

