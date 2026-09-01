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

