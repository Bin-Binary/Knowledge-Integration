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
