---
name: framenet-fe-lookup
description: Query FrameNet by frame name to retrieve Core/Peripheral/Extra-Thematic FE definitions, FE relations, lexical units, and frame relations. Trigger when the user asks about a specific FrameNet frame's frame elements,FE types, core vs peripheral FEs, or wants to look up a frame by name.
---

# framenet-fe-lookup

Look up a FrameNet frame by name and return its full FE (Frame Element) breakdown:
Core FEs, Peripheral FEs, Extra-Thematic FEs, FE relations (Requires/Excludes),
lexical units, and frame inheritance/using relations.

## Quick Reference

| Mode | Command | Purpose |
|------|---------|---------|
| Exact lookup | `python src/fe_lookup.py "Frame_name"` | Get full FE breakdown for a known frame |
| Fuzzy search | `python src/fe_lookup.py "keyword" --search` | Find frames by name keyword or LU stem |
| JSON output | Add `--json` flag | Machine-readable output |

## Dependencies

- Python 3.9+
- `nltk` with `framenet_v17` corpus at `D:\nltk_data\corpora\framenet_v17`

## Script Location

```
skills/framenet-fe-lookup/src/fe_lookup.py
```

## Usage Patterns

### 1. Exact Frame Lookup

When the user names a specific FrameNet frame (e.g., "Commerce_buy", "Motion", "Cause_change"):

```bash
python src/fe_lookup.py "Commerce_buy"
```

Output (Markdown):
- Frame name, ID, definition
- **Core FEs** — required participants (e.g., Buyer, Goods)
- **Peripheral FEs** — optional modifiers (e.g., Money, Seller, Time)
- **Extra-Thematic FEs** — background/secondary (e.g., Explanation, Recipient)
- **FE Relations** — Requires/Excludes constraints
- **Lexical Units** — top 20 LUs (e.g., `buy.v`, `purchase.v`)

If an exact match fails, the tool auto-falls back to partial name matching.

### 2. Fuzzy Search

When the user provides a keyword that may not be an exact frame name:

```bash
python src/fe_lookup.py "buy" --search
python src/fe_lookup.py "storage" --search
```

Returns ranked list of matching frames with core FE counts.

### 3. JSON Output

For programmatic use, add `--json`:

```bash
python src/fe_lookup.py "Motion" --json
```

## Workflow

```
User says: "What are the core FEs of the Commerce_buy frame?"
  → Run: python src/fe_lookup.py "Commerce_buy"
  → Return the Core FEs section to the user

User says: "Find frames related to storing things"
  → Run: python src/fe_lookup.py "storing" --search
  → Present the matching frame list
  → If user picks one: python src/fe_lookup.py "Storing"
```

## Relationship to Other Skills

- **framenet-pipeline**: End-to-end text → LU → frame analysis. This skill is a **focused lookup tool** used when the frame name is already known or suspected.
- **generate-frame**: Topic-level frame structure modeling. This skill provides **ground-truth FE data** from FrameNet for validation or enrichment.

## API Summary (fe_lookup.py)

| Function | Parameters | Returns |
|----------|-----------|---------|
| `lookup_frame(frame_name)` | Exact or partial frame name | `dict` with core/peripheral/extra FEs, relations, LUs |
| `search_frames(query, limit)` | Keyword, max results | `list[dict]` with name, id, core_fe_count |
| `format_result(result)` | Output from `lookup_frame` | Markdown string |

## High-quality output

Sequence (ID: 2135) 的 Frame Elements 如下：
Core FEs
FE	Abbrev	说明
Entity_1	Ent1	与 Entity_2 按顺序出现的实体
Entity_2	Ent2	相对于 Entity_1 按顺序出现的实体
Entities	Ents	按时间顺序出现的实体集合
Peripheral FEs
FE	说明
Descriptor	序列的特征或描述
Extra-Thematic FEs
FE	说明
Relation_type	实体出现顺序的特征化描述，如 "chronologically varied"
FE Relations
- Entity_1 Excludes Entities（二者互斥，不能同时出现）
- Entity_2 Excludes Entities
