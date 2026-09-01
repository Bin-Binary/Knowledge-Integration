# 高频搭配管线（LU/FE 候选生成）软件规格说明书 .spec

- 状态：Draft（评审后转 Approved）
- 依据：`poc.md` §「### 高频搭配」（含全部【修改 A~I】块，以修改后内容为准，原文冲突处按修改块/更正优先）
- 范围：原始语料 ➔ 6+ 组中间结果文件，供下游 LU/FE 候选并最终生成 `.spec`。**本管线仅产出候选集合，不做 FE 划分/框架匹配/框架命名（先共现后划分；过早 FE 划分会因词元句法位置变化引发 FE 漂移）。**
- 输出要求：**每个中间结果都必须落盘**，JSON 与 Markdown 双格式。

## 0. 术语与常量

| 项 | 定义 |
|---|---|
| LU | 词汇单元（"词-义项"绑定，FrameNet 定义） |
| FE | 框架元素候选（本管线中仅为**句法位置**，不判语义角色） |
| V / N / Adv / Prep | 谓词 / 名词 / 副词 / 介词 |
| 二元搭配 | V-N（动宾/主谓）、V-Adv（advmod）、V-Prep（介宾骨架） |
| 三元搭配 | Adv-V-N、Prep-N-V（槽位映射见 §3.5） |
| 语义熵 | 谓词搭配选择限制熵 H(V)（归一化 H_norm） |
| Partial PMI | 偏互信息，三元相对二元基础的关联度 |

## 1. 实现决策（默认值，覆盖 poc 未明确定义处）

| ID | 决策项 | 默认值 |
|---|---|---|
| D1 | 中文分词/POS | `jieba`（posseg）；词表通过领域词表 warm-start（见 D3b） |
| D1a | 依存句法 | 优先 `LTP`（哈工大）或 `hanlp`；输出 SD 风格依存边；解析器经接口抽象可替换 |
| D1b | 依存标签集 | `nsubj/obj/advmod/prep`(→pobj)/`ccomp` 等 SD 简化集；`V-obj-N` 取 `obj` 或 `dobj`，`V-Adv` 取 `advmod`，`V-Prep` 取 `prep+pobj` |
| D2 | 输入格式 | 语料根目录（递归），读取 UTF-8；扩展名 `.txt`/无后缀/`.0` 均纳入；按句切分（`。！？!?；;` 及换行）；每句产出 `sent_id` |
| D3 | 词形归一化 | 小写；下划线/连字 ID 保留为专名 token 并标记 `[NAME]`；不丢原始 offset（用于回写例句） |
| D3b | 领域词表 | 固化 `cloudedragon/` 与产品词汇（pipeline/MR/PBI/Release/YAML/Build/Versionset/codehub/pclint 等），先于分词加载，防止未登录词切错 |
| D3c | 名词化谓词平行线 | 对 `N+的+V`（如"流水线的创建"）另抽 deverbal 二元，落盘到 `lu_seeds_qualified.json` 附加段 `deverbal_units`（修改 B），防止漏框架 |
| D4 | 停用词/轻动词表 | 内置默认表（的/了/在/对/是/有/一个/可以/进行/具有 等），支持外部覆盖文件；表内容在输出中登记 |
| D5 | 代表性例句选取 | 每搭配对：优先取频数最高；并列取依存结构最规整（完整三元/无额外补语）的一句；截取 ≤ 80 字符 |
| D6 | 三元槽位映射 | `Adv-V-N`：w1=Adv(w3?)见 §3.5；`Prep-N-V`：w1=Prep,w2=N,w3=V；FE 位规则见 §3.5 |

置信度控制（修改 A）：
- 每条句法边记录 `score`（解析器置信度）；`score < 0.7` 的证据保留字段 `candidate=true` 但**不计入共现频数**。
- 低质量语料预过滤：纯表头行、纯数字行、控制字符行跳过。

## 2. 管线数据流

```
[原始语料目录]
  0. 语料解析──────────────────────────────────► corpus_parsed.json/.md
  1. 二元抽取────────────────────────────────────► raw_bigrams_counts.json/.md
  2. 二元过滤(LLR+DF+Freq)──────────────────────► filtered_lexical_pairs.json/.md
  3. 语义熵提纯 H(V)/H_norm─────────────────────► lu_seeds_qualified.json/.md   (+deverbal_units)
  3.5 义项检查(上下文聚类)───────────────────────► (并入 lu_seeds_qualified: lu_senses/polysemy_flag)
  4. 三元抽取(以[Active_LU]白名单为枢纽)─────────► raw_trigrams_counts.json/.md
  5. 三元过滤(Partial PMI)──────────────────────► frame_skeleton_templates.json/.md
```

数据依赖：`raw_bigrams_counts` 提供一元/二元频数（LLR、H(V)、Trigram PMI、Partial PMI 的分母）；`lu_seeds_qualified` 的 `[Active_LU]` 作为三元抽取白名单。

## 3. 阶段规格

### P0 语料解析
- 输入：原始语料目录（见 D2）
- 动作：加载领域词表 ➔ 分句 ➔ 分词+POS+依存 ➔ 过滤低质句 ➔ 输出带特征行
- 去噪（标定环，P0 内完成，见 §9）：
  1. 无中文字符片段（纯 URL / 版本号 / 枚举 / 英文列表）直接丢弃；
  2. 长度 < 4 或中文 < 2 字的片段丢弃；
  3. 剥离列表/序号前缀（`1、`、`①`、`Step1:`、`-` 等），避免"标题类名词短语"被解析为伪主谓式（如 `1、仓库授权`）。
- 字段：`doc_id, sent_id, text, tokens[], token{index,word,pos,dep_head,dep_rel}, score, valid`

### P1 二元抽取
- 输入：`corpus_parsed.json`
- 动作：遍历句法树，按 D1b 标签捞出二元候选对，统计一元频数 `C(w_i)`、二元共现频数 `C(w_i,w_j)`，并记录共现文档数 `DF(w_i,w_j)`
- 分类（默认标签 → 搭配型）：
  - V-obj-N / V-nsubj-N → `pred_noun`
  - V-advmod-Adv → `pred_adv`
  - V-prep→pobj-N → `pred_prep`
  - Prep-pobj（介词+介宾，Prep-N-V 三元 Partial PMI 分母 `C(w1,w2)` 的来源）→ `prep_pobj`（标定新增，§9-D）
- 输出：`raw_bigrams_counts.json/.md`（schema §4.1）

### P2 二元过滤（LLR + 频率 + 文档频率）
- 输入：`raw_bigrams_counts.json`
- 公式（Dunning 1993，修改 C 为准）：
  - 四格表：`a11=C(w1,w2)`, `a12=C(w1)-a11`, `a21=C(w2)-a11`, `a22=N-a11-a12-a21`
  - 独立假设期望：`e11=C(w1)C(w2)/N`（余类推）
  - `LLR(w1,w2) = 2 * Σ_{i,j} a_ij * ln(a_ij / e_ij)  ~  χ²(1)`
- 入选判据（并列，全部满足）：
  1. `C(w1,w2) > 3`（绝对频数；二级过滤非唯一门槛；**标定值**，由 spec 初值 >10 下调，理由见 §9-B）
  2. `DF(w1,w2) ≥ 3`（文档频率/离散度，防单文档拉高）
  3. `LLR > 3.84`（p<0.05）；黄金候选 `LLR > 6.63`（p<0.01）
  4. 剔除身份：高频虚词/停用词（D4）、`[Drop_Light_Verb]` 后验（见 P3）
- Top-N 仅用于排序展示（N 无统计意义、随语料规模漂移，不作为入选判据）
- 输出：`filtered_lexical_pairs.json/.md` + 记录被淘汰对及原因（`rejected_reason`）

### P3 语义熵提纯 H(V)/H_norm
- 输入：`filtered_lexical_pairs.json`（干净数据）
- 公式：
  - `H(V) = -Σ_{N∈N_V} P(N|V) * log2(P(N|V))`，`P(N|V)=C(V,N)/C(V)`
  - 归一化（修改 D）：`H_norm(V) = H(V) / log2(|N_V|)` ∈ [0,1]
  - 平滑：名词分布做加一平滑（count+1）后再算概率
- 判读（修改 D 弱化版，非一票否决）：
  - `H_norm(V)` 高（≥0.85）且 `C(V)` 高 → 标 `[Drop_Light_Verb]`（降权保留，待义项检查复核；不删除）
  - `H_norm(V)` 低（≤0.35）且 `C(V)` 高、且不同宾语数 `|N_V| ≥ 3` → 标 `[Active_LU]`（黄金 LU 种子候选）
  - 其余 → `[Keep_Watch]`
  - **熵只是打分特征之一**；义项检查（P3.5）可推翻标记
- 防"表格/布尔值占位"污染（标定，§9-C）：宾语为布尔/纯数字/占位符（true/false/None/数字）不计入对象分布；`|N_V|<3` 的谓词不标 `[Active_LU]`（避免"重复率→true"伪低熵）
- 输出：`lu_seeds_qualified.json/.md`（schema §4.3）

### P3.5 义项检查（多义词/LU 义项，修改 E）
- 动作：对每个 `[Active_LU]` 收集其全部二元/三元共现上下文，做上下文聚类（搭配签名/词向量）
- 规则：聚类簇 ≥ 2 且簇间名词集差异显著 → 不宣判单一 LU，标 `[POLYSEMOUS_CHECK]`；挂外部价目表（HowNet/同义词词林/对齐 FrameNet）或人工复核后切分义项
- 输出字段：`lu_senses[]`、`polysemy_flag`（并入 `lu_seeds_qualified`）
- 后续管道按**义项**而非词形进行

### P4 三元抽取（Trigram PMI）
- 输入：`lu_seeds_qualified.json`（`[Active_LU]` 白名单，核心枢纽）+ `corpus_parsed.json` + `raw_bigrams_counts.json`
- 白名单（标定，§9-F）：`[Active_LU]` ∪ `[POLYSEMOUS_CHECK]` ∪ P2 通过的 `pred_noun` 谓词头词。理由：cloudedragon 语料谓词宾语分布居中，单靠低熵 `[Active_LU]` 白名单为空，三元链断裂；P2 通过的谓词即"高频搭配"实际候选。
- 动作：以该白名单为枢纽，向两侧辐射抽取含副词/介词的三元组 `(w1,w2,w3)`，统计 `C(w1,w2,w3)`
- 槽位映射（D6）与 PMI 公式：
  - `PMI(w1,w2,w3) = log2( P(w1,w2,w3) / (P(w1)P(w2)P(w3)) )`
  - `Adv-V-N`：w1=Adv, w2=V(LU), w3=N；FE 位 = w3
  - `Prep-N-V`：w1=Prep, w2=N, w3=V(LU)；FE 位 = w1+w2（介宾）
- 输出：`raw_trigrams_counts.json/.md`

### P5 三元过滤（Partial PMI）
- 输入：`raw_trigrams_counts.json`（分子 `C(w1,w2,w3)`）+ `raw_bigrams_counts.json`（分母 `C(w1,w2)`、`C(w3)`）
- 公式：
  - `PMI(w3;(w1,w2)) = log2( C(w1,w2,w3)·N / (C(w1,w2)·C(w3)) )`
- 分母口径（标定，§9-D）：`C(w1,w2)` 用**原始共现频数**（未经 P2 过滤），pair 索引按无序对称查找（`pred_adv` 记 `(V,Adv)`、三元记 `(Adv,V)`，查任一方）；Prep-N-V 的 `C(介宾)` 来自 P1 新增 `prep_pobj` 统计
- 判据：Partial PMI > 阈值（默认 1.5，可标定）才认定 w3（FE 位）与 `[副词-谓词]`/`[介宾骨架]` 强绑定；过滤"非常+喜欢+[任意名词]"类伪三元
- 警示（修改 H）：已知槽位仅是**句法位置**；语义角色（Agent/Theme 等）需下游语义泛化聚类后命名，本管线不判
- 输出：`frame_skeleton_templates.json/.md`

### 跨句"虚拟三元拼凑"（修改 F 约束）
- 若按 LU 枢纽合并两个共元二元 → 拼凑三元必须标 `[SYNTHESIZED]` 且置信度降权，待真实三元或人工标注验证后才升级为正式模板；禁止静默当真实三元使用。
- 本版本默认仅输出真实三元；`[SYNTHESIZED]` 作为可选开关（默认 off）。

## 4. 输出 schema

通用要求：JSON 必然包含对应 MD 表的一行；MD 表头与示例见各节；所有候选字段**不得空造**，均可回溯到 `corpus_parsed.json` 的 `doc_id/sent_id`。

### 4.1 corpus_parsed.json
```json
{"docs": [{"doc_id": "d001", "source": "相对路径", "sents": [
  {"sent_id": "s0001", "text": "原句", "valid": true,
   "score": 0.92,
   "tokens": [{"idx": 0, "word": "创建", "pos": "v", "dep_head": 1, "dep_rel": "root"}]}]}]}
```
corpus_parsed.md：句级列表（doc_id | sent_id | text | 依存边摘要）。

### 4.2 raw_bigrams_counts.json
```json
{"pairs": [
  {"w1": "创建", "w2": "流水线", "type": "pred_noun",
   "rel": "obj", "c_w1": 120, "c_w2": 45, "c_w1w2": 24, "df_w1w2": 9,
   "sents": [{"doc_id": "d001", "sent_id": "s0001"}]}]}
```
md 表：| w1 | w2 | type | c_w1w2 | DF | 代表性例句 |

### 4.3 filtered_lexical_pairs.json
```json
{"pairs": [
  {"w1": "创建", "w2": "流水线", "type": "pred_noun", "c_w1w2": 24,
   "llr": 42.1, "passed": true,
   "rejected_reason": null,
   "top_level": "top_ttl"}]}
```
md 表：| 搭配对 | type | 粗略共现频次 | LLR | 代表性例句 |

### 4.4 lu_seeds_qualified.json
```json
{"lus": [
  {"lu": "执行", "c": 90, "h_norm": 0.21, "h": 1.9, "n_nouns": 14,
   "tag": "Active_LU",
   "senses": [{"cluster": 0, "signature": ["方案","流水线","计划"]}],
   "polysemy_flag": false,
   "deverbal": [{"phr": "流水线的创建", "head": "创建", "obj": "流水线"}]},
  {"lu": "进行", "tag": "Drop_Light_Verb", "recheck": true}],
 "drop_table": "停用/轻动词表名",
 "params": {"entropy_norm_base": 2}}
```
md 表：| LU | 频数 | H_norm | tag | 主要搭配名词 Top5 |

### 4.5 raw_trigrams_counts.json
```json
{"trigrams": [
  {"w1": "自动", "w2": "触发", "w3": "流水线", "type": "adv_v_n",
   "c": 10, "pmi3": 5.2, "lu": "触发",
   "sents": [{"doc_id": "d001", "sent_id": "s0030"}]}]}
```
md 表：| 三元组 | type | 频次 | Trigram PMI | 核心LU |

### 4.6 frame_skeleton_templates.json
```json
{"templates": [
  {"type": "adv_v_n", "lu": "触发",
   "w1": "自动", "w2": "触发", "w3": "流水线",
   "c": 10, "partial_pmi": 4.0,
   "fe_slot": "w3",
   "fe_pos": "宾语", "synthesized": false,
   "sents": [{"doc_id": "d001", "sent_id": "s0030"}]}]}
```
md 表：| 三元模板 | type | LU | FE槽位(句法位置) | Partial PMI | 代表性例句 |

## 5. 参数与默认值汇总

| 参数 | 默认值 | 依据/备注 |
|---|---|---|
| 分句切分符 | `。！？!?；;\n` | D2 |
| 绝对频数阈值 `C(w1,w2)` | > 3 | 标定值（§9-B），spec 初值 >10 |
| 文档频率阈值 `DF` | ≥ 3 | 修改 C（P0-1） |
| LLR 显著性 | > 3.84（p<0.05）；黄金 > 6.63（p<0.01） | 修改 C |
| 解析置信度门槛 | ≥ 0.7 才计频 | 修改 A |
| 归一化熵 | `H/log2(|N_V|)` | 修改 D |
| 熵高低界 | High ≥ 0.85 / Low ≤ 0.35 | 修改 D 弱化版，可标定 |
| `[Active_LU]` 对象数下限 | ≥ 3 | 标定值（§9-C） |
| P0 去噪 | 无中文丢弃 / 剥列表前缀 | 标定值（§9-A） |
| P4 三元白名单 | `[Active_LU]` ∪ P2 通过谓词头词 | 标定值（§9-F） |
| Partial PMI 阈值 | > 1.5 | 可标定 |
| 代表性例句长度 | ≤ 80 字符 | D5 |
| `[SYNTHESIZED]` 开关 | off | 修改 F |

## 6. 质量与评估环

- 修改 A：raw/filtered 各随机抽 100 条人工复核，解析错误率收敛后方进入下一步。
- 修改 I：任何阈值（Freq/DF/LLR/熵界/Partial PMI）落地前先标定：人工标注小样本（保留/剔除各约 300 条）分别计算 precision/recall；True Positive 抽样计入下游回归锚定测试，形成闭环。标定结果记录到 `references/corpus_processing/eval/`。
- 命名笔误统一 `.json`（修改 G）；FE 仅限句法位置（修改 H）；禁止静默覆盖冲突。

## 7. 验收标准

1. 覆盖 0~5 全管线，一次执行产出 §4 全部 6 组 `.json` + `.md` 文件；
2. `lu_seeds_qualified` 中每个 `[Active_LU]` 均有 `C`、`H_norm`、`tag`，且能从 `corpus_parsed` 回溯原文；
3. 所有候选值可溯源（doc_id/sent_id 非空，不存在无来源字段）；
4. 阈值全部参数化、可经 CLI/配置覆盖；
5. 标定报告（§6）随结果输出。

## 8. 后续阶段接口（本 spec 之外，仅约定数据交接）

- 谓词提取 / 邻接论元 / 对比构式 / Frame 派生等以 `frame_skeleton_templates` 为输入继续（见 `poc.md` 后续章节）；本 spec 不定义其行为。

## 9. 标定评估环记录（修改 I，cloudedragon 语料，2026-09-01）

| 编号 | 决策 | 证据 | 影响 |
|---|---|---|---|
| A | P0 去噪：无中文片段丢弃、剥列表/序号前缀 | 标定初跑产生 `所示-图`（"如下图所示"）、`授权-仓库`（"1、仓库授权"）、`会-则` 等结构性噪声 | P0 句子 2548→2125；P2 噪声对显著下降 |
| B | `C(w1,w2)` 阈值 >10 → >3 | 语料仅 2548 句 / 1.8 万 tokens，>10 使 P2 仅剩 9 对、且顶部全是噪声；>3 时 P2=29~46 对，包含 `修改-流水线(DF8)`、`运行-流水线(DF7)`、`提交-代码` 等真实高频搭配 | P2 候选从 9→29（标定后），下游(pred 头词)可开展 |
| C | 布尔/数字宾语不计熵对象；`[Active_LU]` 需 `|N_V|≥3` | 表格行"重复率 true / 未处理 true"产出 `率→true`、`未处理→true` 伪低熵 | `[Active_LU]` 不再出现垃圾种子 |
| D | P1 新增 `prep_pobj` 类型作为 Prep-N-V 的 `C(介宾)` 分母；P5 分母用原始 pair 频数+对称索引 | 原仅记谓-介共现，`C(往,分支)` 恒 0 → 全部 Prep-N-V 被 P5 丢弃 | P5 产出含真实模板：`往-分支-提交`、`针对-MR-变更`、`按-版本号-选择` |
| E | 修改 B 修正：中心名词（head）词性为 vn 才算名词化谓词；amod 允许 vn 中心语 | 原判据写在修饰语（dep）上，日志显示 deverbal=0 且方向与 spec 相反 | deverbal 机制可用（本语料 vn-amod 罕见，实测仍少） |
| F | P4 三元白名单 = `[Active_LU]` ∪ P2 通过 `pred_noun` 头词 | 该语料谓词宾语分布中熵，低熵 `[Active_LU]` 空 → 三元链断裂、P4/P5 恒空 | P4=148 条、P5=14 条模板，端到端贯通 |
| G | 副词强制覆盖（自动/批量/手动/异步 等按 ADV_OVERRIDE 处理）+ 介宾名词不再重复计入 obj/nsubj + light verb 不阻断 prep 动词搜索 | 修复伪主谓（`自动→MR`）、介宾重复计数（`分享→流水线`）、"按…进行初始化"介词链丢失 | 22 条解析冒烟样本主谓宾/介宾质量显著提升 |

**复现命令**（等价于配置默认值）：
```
python -X utf8 -m corpus_processing.cli --corpus-dir <cloudedragon> --out-dir <out> --min-freq-abs 4
```
标定数据归档：`<out>/eval/run_report.json`（params 记录全部阈值）。
