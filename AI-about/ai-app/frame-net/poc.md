---
name: 基于框架语义学和生成词汇学的垂直领域Agent工程实践POC
description: 从官方文档/生产日志抽取先建立基线Frame、持续使用真实语料迭代FrameNet
---
# ༄ 基于框架语义学和生成词汇学的垂直领域Agent工程实践POC

<!-- 极简细蓝线（适合技术文档/CI 领域提示） -->
<hr style="border:0; height:1px; background-color:#007bff;">

## ༄༅ 基于生产语料分布观察

<!-- 极简细蓝线（适合技术文档/CI 领域提示） -->
<hr style="border:0; height:1px; background-color:#007bff;">

框架从使用中归纳出来，不要内省出来！！！(一段很长的痛苦经历)
*实践建议：先共现后划分，先提取高频搭配、扁平化词汇，先做FE划分会因词元位置变化导致FE漂移*

### ༄༅༅ 高频搭配
<!-- 极简细蓝线（适合技术文档/CI 领域提示） -->
<hr style="border:0; height:1px; background-color:#007bff;">

从原始语料统计，提取高频二元/三元搭配，过滤噪声，"建立槽位边界与句法骨架",用来做后续LU、FE候选的种子。因此从原始语料解析到三元过滤(P_0 -> P_5), 只处理"句法"、不引入"语义"。


**语料处理流程**：
```
[原始语料] ➔ P_0. 原始语料解析 ➔ P_1. 二元抽取 ➔ P_2. 二元过滤(LLR)
➔ P_3. 语义熵提纯(H(V)) ➔ P_4. 三元抽取 ➔ P_5. 三元过滤(Partial PMI)
```

#### ༄༅༅༅ P_0 原始语料解析
<!-- 极简细蓝线（适合技术文档/CI 领域提示） -->
<hr style="border:0; height:1px; background-color:#007bff;">

对原始语料解析, 输出包含分词、词性标注、依存句法分析的[语料形态: corpus_parsed.json/corpus_parsed.md](./references/corpus_processing/corpus_parsed.json)
༅
*分词: 确定“槽位（Slot）”的物理边界*
自然语言字与字之间没有空格。分词能把连续的字串切分为独立的语义单元（词）

*词性标注: 初步筛选“句法位置”的候选资格*
识别每个词的语法属性

*依存句法分析: 拉近“跨度距离”，建立槽位间的骨架关系*
句子在现实中可能非常冗长, 依存句法可以跨越中间的修饰词，清洗出核心业务逻辑线

!!! note 这里为什么不做SRL、SDP
    句法分析是语义分析的基础

!!! note POS、DPE、SRL、SDP的关系
    关系：层层递进、由表及里
    关系纽带：句法分析是语义分析的基础
    

!!! note 说明：句法分析是语义分析的基础
    1. 句法结构决定了语义的“归属”
    人类语言存在大量的结构歧义，同样的词汇，只要句法结构（骨架）一变，语义就会彻底反转。
    经典例子：“张三看见李四正在砍他的树。”
    句法可能性 A：如果句法分析断定“他的树”的修饰对象（依存 Head）是张三 → 语义：张三是受害者。
    句法可能性 B：如果句法分析断定“他的树”的修饰对象（依存 Head）是李四 → 语义：李四在砍自己的树。
    语义分析（谁是受害者、谁是资产所有人）必须依赖句法分析先理清这些词到底在修饰谁。

    2. 句法分析帮语义分析“缩短距离”
    在真实的原始语料（如IT运维文档、法律条文）中，充斥着大量的超长难句。核心动词（谓词）和它的承受者（论元）可能隔了十万八千里。
    例子：“CloudPipeline 是一套可帮助您……（中间省略50字描述）……的流水线服务。
    ”没有句法：语义分析（SRL）如果只在字面上挨个看，由于“CloudPipeline”和“流水线服务”离得太远，它很难把两者建立起【A是B】的语义关系。
    有了句法：句法分析（DP）会直接砍掉中间所有的修饰性从句，在句法树上把 CloudPipeline (主语) 和 流水线服务 (宾语) 直接连在一起。语义分析顺着这条句法线，就能瞬间秒杀这个长难句。

    3. 句法标签是语义映射的“黄金线索”
    在语言学中，句法位置（主宾语）和语义角色（施受事）之间存在着极强的映射规律。
    比如在绝大多数主动句中：句法上的【主语 (nsubj)】 → 极大概率映射为 语义上的【施事者 (A0 / Agent)】
    句法上的【宾语 (obj)】 → 极大概率映射为 语义上的【受事者 (A1 / Patient)】
    结论：句法分析的结果，直接为语义角色标注（SRL）和框架元素（FE）的提取提供了最精准的候选范围。
    语义分析不需要大海捞针，只需要在句法树的特定分支上“对号入座”即可。

    4. 句法分析是低成本的“噪声过滤器”
    语料中有很多像*“未”、“随意”、“除了”*这样的词。
    如果不进行句法分析，语义分析就要把所有词都纳入语义图谱的计算中，算力消耗极大，且噪声极多。
    句法分析通过advmod（副词修饰）、prep（介词）等标签，在底层就把这些词的“物理属性”定性了。
    语义分析阶段可以据此直接开启过滤机制，只对真正有语义分量的名词、动词进行深度推理。

!!! note 扩展：NER、CON、AMR
    NER：命名实体识别（Named Entity Recognition）是一种识别文本中**实体的位置以及类别**的任务
    CON：成分句法分析（Constituency Parsing、CON）是一种分析一个**句子在语法上的递归构成**，并将其表示为树形结构的任务
    AMR：抽象意义表示（Abstract Meaning Representation，AMR）是一种将**句子的意义**（时间地点谁对谁怎样地做了什么）表示为以概念为节点的单源有向无环图的语言学框架

**解析噪声控制**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

1. 对每条句法边（V-obj-N、Adv-advmod-V等）记录解析器置信度；低置信度证据保留但不计入共现频数，防止分词/依存错误污染统计
2. 中文分词对未登录词/专名（pipeline_id、YAML、MR）易出错，预处理先固化领域词表再执行分词
3. 定期人工抽检：raw/filtered 各随机抽 100 条复核，解析错误率收敛后再进入下一步

**【diff: 理论 vs 实践（P0）】**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

1. 理论仅要求"固化领域词表再分词"，实践发现中文分词仍把**方式副词**（自动/批量/手动/定时/异步/另/只/仅/均…）误标为动词（v），进而被句法规则捞成伪主谓（"自动(MR,nsubj)"）或跳过；落地须维护强制副词覆盖词表（ADV_OVERRIDE），且nsubj搜索允许跨副词。

2. 文档类语料大量"1、仓库授权"式列表/序号前缀会被解析成伪主谓短语；落地在分句后剥离列表/序号前缀、丢弃无中文字符片段（URL/版本号/英文枚举）。实测孤立句子 2548→2125，`所示-图` 类结构噪声显著下降。

3. 领域复合词（版本包/运行时/代码检查/编译构建/定时任务/执行计划/版本号…）必须预先进入领域词表，否则被拆碎后污染一元/二元频数。

**【修改 B（P1-6）＝新增·非动词 LU 缺失预警】**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

框架唤起词不限于谓词FrameNet中大量名词（事件名词如"冲突/谈判"）、形容词亦可作LU。本管线以V/N动宾为主，须另补一条**名词化谓词（deverbal noun）**平行抽取（如"流水线的创建"），避免系统性漏框架

**【diff: 理论 vs 实践（P1-6）、deverbal判据方向与触发规模】**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

1. 理论未指明判据作用点，实践发现方向易落反：amod边中**中心名词（head，被修饰语）**才可能是名词化谓词，判据须检查 head 词性 == vn，而非修饰语（dep）。
--
2. 实测该语料deverbal=0：jieba对事件名词多标v而非vn（"依赖/变更"），且vn作amod中心语的句法场景本就少见；机制保留有效，但对依赖POS标签vn的词典语料近似失效，需以"V 标签 + 语义后缀（明细/清单/变更）"补充召回。

#### ༄༅༅༅ 二元搭配的抽取与过滤噪声
<!-- 极简细蓝线（适合技术文档/CI 领域提示） -->
<hr style="border:0; height:1px; background-color:#007bff;">
*二元搭配*: [谓词‑名词、谓词‑副词、谓词‑介词]

三元搭配结构更完整，但在真实语料中: 

1. 三元搭配的共现概率呈指数级下降（数据稀疏问题（Data Sparsity）与泛化能力），
如果只抽三元，会因为数据太稀疏而漏掉大量极具框架唤起能力的低频、中频核心谓词（LU）。二元结构作为保证召回率（Recall）的兜底
--
2. 框架语义的“核心唤起者”通常是单字或二元绑定，根据FrameNet的定义，框架唤起词（LU）本身通常只是一个单独的词（多数为谓词 V，或名词 N）。
二元结构负责“定性”（确定 LU）、三元结构负责“定量”（扩充 FE）。没有二元结构先对LU进行定位和沉淀，直接处理三元组会引入巨大的语义组合噪声
--
3. “隐性省略”与“非连续性”（人类说话时，很少会把所有的框架元素（FE）在一个句子里完整、连续地表达出来）。
例如：句型A（缺副词）：“警方[FE] 正在调查[LU] 这一案件[FE]。” ➔ 触发 [谓词-名词] 二元、
句型B（缺宾语）：“针对这起事件，警方正在深入调查[LU]。” ➔ 触发[谓词-副词]二元。
如果只设置三元抽取，上面这两句极具价值的语料都会被误过滤掉。通过抽取不同的二元结构，再在后台进行求交集或并集，才能拼凑出一个完整的虚拟三元/多元框架

**【修改 F（P1-5）＝警告·"虚拟三元拼凑"仅思路陈述】**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">
跨句"求交集/并集拼凑虚拟三元"目前只是思路陈述，尚无跨句槽位合并算法。落地时必须：① 定义以【核心 LU 为枢纽】的槽位合并规则（两个二元共享同一 LU 则槽位合并）；② 对拼凑出的虚拟三元标记 [SYNTHESIZED] 并降低置信度，待真实三元模板或人工标注验证后再升级为正式模板；禁止静默当作真实三元使用。

--
4. 降低噪声过滤的基准线（Baseline），在统计学过滤中，三元组的关联度（如 Partial PMI）必须依赖二元组的概率作为分母和参照物。
要计算“强烈 + 谴责 + 行为”是不是一个真正的语义搭配，算法必须先知道“强烈 + 谴责”和“谴责 + 行为”各自的黏合度有多高。

*流水线与数据流设计*：[原始语料] ➔ 1. 二元抽取 ➔ 2. 二元过滤(LLR) ➔ 3. 语义熵提纯(H(V))

**二元抽取（基础共现计数）**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

输入：corpus_parsed.json
动作：遍历句法树，直接捞出所有的二元候选对，并统计最基础的原子频数：一元频数 \(C(w_i)\) 和二元共现频数 \(C(w_i, w_j)\)
输出：包含所有的原始 (w₁, w₂) 关系及其频数计数（如 V-obj-N、Adv-advmod-V 等）的[语料形态：raw_bigrams_counts.json/raw_bigrams_counts.md](./references/corpus_processing/raw_bigrams_counts.json)

**【diff: 理论 vs 实践（P1）＝新增·介宾去重与轻动词边界】**
1. 介宾（pobj）名词同时会被 obj/nsubj 规则捞到（"把流水线分享给团队"中"分享→流水线"），导致一个论元被双计；落地须维护每句 pobj 集合，从 obj/nsubj 计数中剔除。
--
2. 轻动词"进行/予以/做了"不应阻断介词链："按方案进行初始化"中"初始化"才是真实谓词；介词挂载须跳过 light verb 再找下一个真实动词。
--
3. Prep-N-V 三元的 Partial PMI 分母 C(介词,介宾) 不在理论给出的"谓-名词/谓-副词/谓-介词"二元范畴内（谓-介词记的是 谓-介 共现），必须新增**介词-介宾（prep_pobj）**共现统计，否则该分母恒为 0、该类三元全军覆没。

**过滤噪声策略: 对数似然比（Log-Likelihood Ratio, LLR）**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

检验“谓词 \(V\) 和名词 \(N\) 相互独立”的假设是否成立。LLR值越大，说明两者越不是随机凑在一起的

*工程策略*：
1. 设定绝对频数阈值: \(Freq(w_1, w_2) > 10\)，直接剔除长尾低频噪声
--
2. 计算 \(LLR(V, N)\) 并重排，截取 Top-\(N\)作为候选集。此时得到的二元组既有高频稳定性，又具备强语义黏性
--
**【修改 C（P0-1）＝新增/更正·LLR 计算与显著性判据】（非原文）**
> 对本文"过滤噪声策略: LLR"一节的补充与更正：
> LLR 计算公式（Dunning 1993）：四格表 \(a_{11}=C(w_1,w_2)\)、\(a_{12}=C(w_1)-a_{11}\)、\(a_{21}=C(w_2)-a_{11}\)、\(a_{22}=N-a_{11}-a_{12}-a_{21}\)，独立假设期望 \(e_{11}=\frac{C(w_1)C(w_2)}{N}\)（余类推），
> \(\text{LLR}(w_1,w_2)=2\sum_{i,j} a_{ij}\ln\frac{a_{ij}}{e_{ij}}\ \sim\ \chi^2(1)\)
> **显著性判据**：\(\text{LLR} > 3.84\)（p<0.05）或 \(> 6.63\)（p<0.01）视为显著非随机。**用显著性阈值替代上述"Top-N 截断"作为入选判据**，Top-N 仅用于展示排序（N 无统计意义且随语料规模漂移）。
> **工程策略更正**：上文第 1 条"\(Freq>10\)"是二级过滤而非唯一准入门槛；并新增**文档频率/离散度过滤**：统计 \(DF(w_1,w_2)\)（同时含二者的文档数），过滤 \(DF<3\) 的搭配，防止聚合频数被单文档/单主题拉高。

**【diff: 理论 vs 实践（P2）＝更正·绝对频数阈值须随语料规模标定】（非原文）**
> 1. \(Freq>10\) 是跨语料无意义的绝对数：在微语料（63 文档 / 2125 句 / 约 1.8 万 tokens）上实测过严，P2 仅剩约 7 对且顶部（Active_LU）全是"率→true"类伪候选；标定 >3 后约 29 对，才保住 `修改-流水线(DF8)`、`运行-流水线(DF7)`、`提交-代码` 等真实高频搭配。
> 2. LLR 高分为**必要不充分**条件：高 LLR 仍会夹杂结构噪声（`所示`、`会-则`），且"P2 十强"感性上不如词表去噪（P0 diff）后再过滤可靠；调阈值不如先做语料级去噪。DF≥3 判据在微语料稳健、防单文档拉高有效。

输入：raw_bigrams_counts.json
动作：通过LLR结合绝对频数阈值： \(C > 10\)，彻底清洗掉由高频虚词、停用词（如“的、了、在”）或句法解析错误导致的偶然共现噪声
输出：包含高纯度的优质二元搭配集合的[语料形态：filtered_lexical_pairs.json/filtered_lexical_pairs.md](./references/corpus_processing/filtered_lexical_pairs.json)

**抽取：语义信息熵过滤（Entropy）**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

> 如果一个谓词（如“进行”、“具有”）可以搭配成百上千个名词，说明其语义空泛（轻动词/虚词），它自身的框架唤起能力极弱


方法：计算谓词 \(V\) 的搭配选择限制熵。熵值越高，说明搭配越杂乱，唤起特定框架的能力越弱；熵值越低且频数高，说明其语义指向性极强，是极佳的LU种子

计算公式：
对于任意一个谓词 \(V\)，假设与其存在动宾关系的所有名词集合为 \(\mathcal{N}_{V}\)，则该谓词的语义熵 \(H(V)\) 为：
\(H(V)=-\sum _{N\in \mathcal{N}_{V}}P(N|{}V)\log _{2}P(N|{}V)\)
其中，条件概率 \(P(N\vert{}V) = \frac{C(V, N)}{C(V)}\)。

*工程策略*：
高频高熵（Noise ❌）：\(C(V)\) 很高，但 \(H(V)\) 极大（趋近于均匀分布）。说明该动词是泛化词、虚词，直接剥夺其独立作为LU的资格。
高频低熵（Seed ⭐）：\(C(V)\) 很高，但 \(H(V)\) 很低。说明该动词只与少数特定领域的名词搭配（例如“罹患”主要搭配“疾病、癌症”），框架唤起能力极强，属于黄金 LU 种子。

输入：filtered_lexical_pairs.json
动作：此时利用干净的数据计算谓词的搭配选择限制熵 \(H(V)\)。
\(H(V)=-\sum _{N\in \mathcal{N}_{V,\text{filtered}}}P(N|{}V)\log _{2}P(N|{}V)\)。
高熵的被标记为 [Drop_Light_Verb]，低熵高频的被标记为 [Active_LU]
输出：包含计算完H(V) 后的优质谓词（LU 种子）的[语料形态：lu_seeds_qualified.json/lu_seeds_qualified.md](./references/corpus_processing/lu_seeds_qualified.json)

**【修改 D（P1-7）＝新增/更正·熵判读局限与归一化熵】（非原文）**
> 1. 低熵 ≠ 强框架唤起能力：低熵可能是领域受限或语料量太小（样本不足会人为压低熵）
> 2. 高熵 ≠ 轻动词：高熵可能是多义词多个义项摊薄了名词分布（与下述修改 E 的义项检查强耦合）
> 3. H(V) 应作为**打分特征之一**，而非一票否决的开关：原文"高频高熵→直接剥夺其独立作为LU的资格"建议弱化为"降权标记 [Drop_Light_Verb]，不删除，待义项检查复核"；"高频低熵→黄金 LU 种子"亦仅作为 [Active_LU] 候选，仍需义项检查。
> 4. 建议计数时对名词分布做**平滑**（加一/插值），并用**归一化熵**消除名词集规模差异：\(H_{\text{norm}}(V)=\frac{H(V)}{\log_{2}\lvert\mathcal{N}_{V}\rvert}\)（取值 0~1）

**【diff: 理论 vs 实践（P3）＝更正·占位宾语与中熵语料下的熵失效】（非原文）**
> 1. 表格/布尔值占位污染：宾语为 true/false/纯数字时产出"重复率→true""未处理→true"伪低熵；计算对象分布前须过滤布尔/数字占位宾语。
> 2. 低对象数谓词（\(|\mathcal{N}_V| < 3\)）熵噪声大，不宣判 Active_LU。
> 3. **该垂直语料谓词宾语分布普遍为中熵，低熵 Active_LU 天然缺失（实测 0 个）**——"低熵高频 = 黄金 LU 种子"的涌现假设在此类文档语料上几近失效；熵判据弱化为打分特征后，直接动摇 P4"以 Active_LU 为枢纽"的输入源，见下条三元抽取 diff。

**【修改 E（P0-2）＝新增·多义词/LU 义项检查阶段】（非原文，插在"二元过滤"与"三元抽取"之间）**
> FrameNet 的 LU 是"词-义项"绑定：一个多义词（如"调查""打击"）的不同义项唤起不同框架；统计共现会把所有义项揉成一个伪 LU，必须在进入三元抽取前拦截。
> 1. 对每个 [Active_LU] 收集其全部二元/三元共现上下文，做**上下文聚类**（词向量或搭配签名聚类）
> 2. 聚类簇 ≥ 2 且簇间名词集差异显著时，暂不宣判单一 LU，标记 [POLYSEMOUS_CHECK]；挂靠外部价目表（HowNet/同义词词林/对齐 FrameNet）或人工复核后再切分义项
> 3. 输出增加字段：lu_senses / polysemy_flag；后续框架匹配按**义项**而非词形进行

#### 三元搭配的抽取与过滤噪声
<!-- 极简细蓝线（适合技术文档/CI 领域提示） -->
<hr style="border:0; height:1px; background-color:#007bff;">

**三元搭配**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

[副词-谓词-名词、介词-名词-谓词]

副词-谓词-名词 (Adv + V + N) -> LU修饰 + LU核心 + FE候选

介词-名词-谓词 (Prep + N + V) -> 【锁定：框架的句法外壳】; 这种三元搭配直接固化了框架的句法边界

**为什么三元搭配**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

在框架语义学（Frame Semantics）中，三元搭配是锁定框架唤起能力（LU）和“框架元素（FE）的利器。

因为二元搭配常常语义不完整，而三元搭配能直接勾勒出一个微型的句法外壳（Argument Structure）

**流水线与数据流设计**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

[二元处理结果] ➔ 三元抽取 ➔ 三元过滤(Partial PMI)

**抽取：三元抽取（句法外壳初筛：Trigram PMI）**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

> 以[二元处理结果]筛选出的“优质LU种子”为核心枢纽，向外辐射抽取包含副词或介词的三元组。

*计算公式*：
\(\text{PMI}(w_{1},w_{2},w_{3})=\log _{2}\frac{P(w_{1},w_{2},w_{3})}{P(w_{1})P(w_{2})P(w_{3})}\)

*输入*：
lu_seeds_qualified.json（核心枢纽谓词白名单）+ corpus_parsed.json（从中提取三元结构并统计频数） + raw_bigrams_counts.json（用于计算分母 \(P(w_1)P(w_2)P(w_3)\) 所需的单字频数）

*动作*：
统计三元频数 \(C(w_1, w_2, w_3)\)，并计算Trigram PMI，确保这三个词在整语料中具有宏观上的共现显著性

*输出*：
包含以lu_seeds_qualified.josn中的[Active_LU]为核心，关联出的原始三元组及频数的[raw_trigrams_counts.json/raw_trigrams_counts.md](./references/corpus_processing/raw_trigrams_counts.json)

**【diff: 理论 vs 实践（P4）＝更正·三元枢纽白名单必须扩展】（非原文）**
> 1. "以 [Active_LU] 为枢纽"实测落空：该语料 Active_LU=0（见 P3 diff），三元链直接断裂，P4 恒空；白名单落地为 \([Active\_LU] \cup [POLYSEMOUS\_CHECK] \cup \text{P2 通过的} pred\_noun\) 谓词头词（即"高频搭配"实际候选），P4 才产出 148 条三元。
> 2. 微语料三元频数极低（实测 C≤6、多数 2~3），Trigram PMI / Partial PMI 漂移大，模板须按频数截取 + 人工/义项抽检，不能只看分数。
> 3. 扩展白名单后的 top 三元仍夹句法噪声（如"同意-点击-success""将-服务-微服务"），强制副词覆盖（P0 diff）与义项复核仍是必要后处理。

**过滤噪声：偏互信息 (Partial PMI)**
<hr style="border:0; height:1px; background-color:#ddd; margin-top:-10px;">

> 在提取LU和FE的候选时，要防范一种噪声：
\((w_1, w_2)\) 组合本来就很黏，\(w_{3}\) 只是碰巧凑过来的。例如：
“非常 [Adv] + 喜欢 [V]” 已经是一个极强二元组，
后面加任何名词（苹果、看书、打球）都能跑出高频。
这会导致“非常-喜欢-苹果”的三元频数很高，但“苹果”并不是“喜欢”的专属高唤起能力搭配

*计算三元概率相对于二元基础的条件互信息*：
\(\text{PMI}(w_{3};(w_{1},w_{2}))=\log _{2}\frac{P(w_{1},w_{2},w_{3})}{P(w_{1},w_{2})P(w_{3})}=\log _{2}\frac{C(w_{1},w_{2},w_{3})\cdot N}{C(w_{1},w_{2})\cdot C(w_{3})}\)

*说明*: 
只有当这个值也很高时，才说明\(w_{3}\)（比如名词FE）和这个[副词-谓词]组合有强烈的语义绑定

*输入*：
raw_trigrams_counts.json（提供分子 \(C(w_1, w_2, w_3)\)）+ raw_bigrams_counts.json（提供分母 \(C(w_1, w_2)\)）

*动作*：
使用偏互信息（Partial PMI）公式：
\(\text{PMI}(w_{3};(w_{1},w_{2}))=\log _{2}\frac{C(w_{1},w_{2},w_{3})\cdot N}{C(w_{1},w_{2})\cdot C(w_{3})}\)

> 通过代入LLR计算好的 \(C(w_1, w_2)\) 作为分母，过滤“非常+喜欢+[任何名词]”这类由于局部二元极强而导致的伪三元

*最终输出*：
包含兼具LU唤起能力与FE句法外壳填充边界的黄金三元种子模板的[语料形态：frame_skeleton_templates.josn/frame_skeleton_templates.md](./references/corpus_processing/frame_skeleton_templates.json)

**【diff: 理论 vs 实践（P5）＝更正·Partial PMI 分母口径】**
> 1. 理论"通过 LLR 计算好的 C(w1,w2) 作为分母"不可按**过滤后的候选集**理解：分母应为**原始共现频数**（仅去停用词）。实测用过滤集 → P5 恒 0（低配副词对全被计 0），改原始频数 → 14 条通过。
> 2. Adv-V-N 的 pair 轴方向与三元相反（二元记 (V,Adv)、三元记 (Adv,V)），pair 索引须按无序对称查找。
> 3. Prep-N-V 的分母 C(介词,介宾) 需 P1 新增的 prep_pobj 统计（见 P1 diff）；修正后 P5 产出真实模板：`往-分支-提交`、`针对-MR-变更`、`按-版本号-选择`、`随意-修改-阶段`。

**【修改 G＝更正·笔误标注】**
> 原文 "lu_seeds_qualified.josn"（三元抽取输入处）与 "frame_skeleton_templates.josn"（本行）中的 `.josn` 均为笔误，应为 `.json`；落地实现统一按 `.json` 处理，本文原文保持原样不动。

**【修改 H（P0-3）＝警告·FE 仍是句法位置非语义角色】**
> 三元模板目前只给出 Adv/N 的**句法位置**，不等于语义角色（Agent/Theme 等）。从"填充边界"到"角色归纳"必须对槽位内名词做**语义泛化聚类**（上位概念/语义类）后才能命名角色，否则产出的是句法外壳模板，而非框架元素定义。

**【修改 I（P0-4）＝新增·统计过滤评估环】（非原文）**
> 任何阈值（C>10、DF<3、LLR 显著性、熵界限）落地前先做标定——人工标注小样本（保留/剔除各约 300 条），对 LLR、H(V)、Partial PMI 的筛出结果分别计算 precision/recall；筛出的 True Positive 抽样计入下游"回归锚定测试"，形成闭环。

### ༄༅༅ 谓词提取
<!-- 极简细蓝线（适合技术文档/CI 领域提示） -->
<hr style="border:0; height:1px; background-color:#007bff;">

识别高频搭配结果中承担事件/动作核心的谓词（动词、状态形容词）；针对每个谓词，提取句法邻接、参与该动作事件的短语，作为Action FE（动作框架元素）候选集合；仅输出候选，不做最终框架判定

交给AI处理，以下为提示词：
```markdown
你是谓词与框架元素候选提取专家，精通框架语义学、句法分析。
擅长从高频搭配结果中提取核心谓词并生成Action FE候选集合。
你的任务是基于高频搭配中间结果，从搭配对、代表性例句中识别核心谓词；围绕识别出的谓词，提取参与动作事件的短语作为Action FE候选；并追加输出结构化表格到输出路径
以下需要的输入：
    高频搭配中间结果：./references/corpus_processing/corpus_{时间戳}_{hash}.md(默认)/{高频搭配中间结果}
    输出路径：./references/corpus_processing/corpus_{时间戳}_{hash}.md(默认)/{输出路径}
    原始语料路径 {原始语料路径} (如用户未指定高频搭配中间结果和输出路径则不可缺省)

约束：
1. 谓词、Action FE候选、原句片段必须全部取自高频搭配中间结果内部的搭配与例句，不得引入外部文本，不得编造，不得照搬样例。
2. 输入槽位 {}、必须被真实内容替换。
3. 不要输出说明、不要添加解释或前言、思考过程。
4. 过滤修饰性定语、无关插入语、语气词；优先动作参与者、对象、目标、源点、终点类短语。
5. 只输出有实际语义的谓词与FE候选，过滤无意义成分。
6. 说明中内容仅为格式示范，不得照搬样例
7. 高频搭配中间结果和输出路径不可缺省并支持用户指定输入覆盖
8. {时间戳}_{hash}的计算如下：
```python
python -c "import hashlib; from datetime import datetime; hash_use=r'{始语料路径}'; hour_str=datetime.now().strftime('%Y%m%d%H'); hash_str=hashlib.md5(hash_use.encode('utf-8')).hexdigest(); filename_suffix=f'{hour_str}_{hash_str}'; print(filename_suffix)"
```

输出格式:
```markdown
## 谓词提取
> 识别高频搭配结果中承担事件/动作核心的谓词（动词、状态形容词）；针对每个谓词，提取句法邻接、参与该动作事件的短语，作为Action FE（动作框架元素）候选集合；仅输出候选，不做最终框架判定

*谓词‑Action FE候选映射表*
| 原句片段 | 核心谓词 | Action FE候选清单 |
| :--- | :--- | :--- |
| {sent1} | {pred1} | {fe_candidate_1} |

说明: 
    **关于谓词‑Action FE候选映射表占位符说明**：
        sent1: 取自高频搭配中间结果内的代表性例句片段
        pred1: 识别得到的核心谓词
        fe_candidate_1: 多个FE候选使用分号;分隔
```


!!! 在实践操作中犯了错误
    混淆了语法主语和语义角色，例如"流水线成功"中，流水线是语法主语，但语义角色是Entity（处于某状态的实体），不是Agent（有意行动的施事）

### 邻接论元候选清单
基于高频搭配结果，找出与目标谓词/LU直接关联的论元短语（主语、宾语、介宾成分等）；剔除修饰成分；输出句法层面论元候选集合，不做语义角色最终判定

交给AI处理，以下为提示词：
```markdown
你是句法论元抽取专家，精通依存句法、论元结构分析。
擅长基于高频搭配结果内的谓词/LU提取句法邻接的论元候选。
你的任务是基于高频搭配中间结果，针对搭配中出现的谓词/LU，找出句法直接关联的论元短语，产出邻接论元候选清单；并追加输出结构化表格到并追加输出结构化表格到输出路径
以下需要的输入：
    高频搭配中间结果：./references/corpus_processing/corpus_{时间戳}_{hash}.md(默认)/{高频搭配中间结果}
    输出路径：./references/corpus_processing/corpus_{时间戳}_{hash}.md(默认)/{输出路径}
    原始语料路径 {原始语料路径} (如用户未指定高频搭配中间结果和输出路径则不可缺省)

约束：
1. 论元候选、原句片段必须全部取自{高频搭配中间结果}内部的搭配与例句，不得引入外部文本，不得编造，不得照搬样例。
2. 输入槽位 {}、必须被真实内容替换。
3. 不要输出说明、不要添加解释或前言、思考过程。
4. 剔除单纯定语、语气词、插入语；只保留主语、宾语、介宾等论元成分。
5. 每条候选附带简要句法位置标记；只输出有实际语义的论元候选。
7. 高频搭配中间结果和输出路径不可缺省并支持用户指定输入覆盖
8. {时间戳}_{hash}的计算如下：
```python
python -c "import hashlib; from datetime import datetime; hash_use=r'{始语料路径}'; hour_str=datetime.now().strftime('%Y%m%d%H'); hash_str=hashlib.md5(hash_use.encode('utf-8')).hexdigest(); filename_suffix=f'{hour_str}_{hash_str}'; print(filename_suffix)"
```

输出格式:
```markdown
## 邻接论元候选清单
> 基于高频搭配结果，找出与目标谓词/LU直接关联的论元短语（主语、宾语、介宾成分等）；剔除修饰成分；输出句法层面论元候选集合，不做语义角色最终判定。

*邻接论元候选表*
| 目标单元(谓词/LU) | 原句片段 | 邻接论元候选[句法位置] |
| :--- | :--- | :--- |
| {unit1} | {sent1} | {arg_candidate_1} |

说明: 
    **关于邻接论元候选表占位符说明**：
        unit1: 来自高频搭配的目标谓词或者LU词汇单元
        sent1: 取自高频搭配中间结果内的代表性例句片段
        arg_candidate_1: 候选短语[句法位置]，多个候选使用分号;分隔；句法位置：主语/宾语/介宾

```

[分支、pipeline_id、版本、group_id、job_id、执行方案、service_id、scheme_id]
*论元结构是连接核心事件（语义面）与句子外壳（句法面）的桥梁*
*必须是该事件发生不可或缺的参与者（Core Arguments），不出现则意义彻底改变*

### 对比构式中的对照词
价值是实体词表扩充和语义轴（qualia 维度）
FrameNet的LU特指能唤起框架的目标词元（“创建”“执行”这类），而“流水线 vs 部署”里的两个词是被填充的语义内容
扫描高频搭配结果内的例句，识别X vs Y类对比构式（A比B、A相较于B、A而不是B、A胜过B等）；定位构式对照位置X、Y上的对照词/短语，作为对比轴上的实体/填充词候选集合；无对比构式则标记无

交给AI处理，以下为提示词：
```markdown
你是构式语义分析专家，精通对比构式识别、FrameNet词汇单元对比轴上的实体/填充词候选挖掘。
擅长从高频搭配结果的例句中识别X vs Y类对比句式，提取对照位置词汇生成对比轴上的实体/填充词候选。
你的任务是基于上一步产出的【高频搭配中间结果】，扫描其内部代表性例句，识别对比构式，定位X、Y对照位置短语，生成邻接对比轴上的实体/填充词候选集合；并追加输出结构化表格到输出路径
以下需要的输入：
    高频搭配中间结果：./references/corpus_processing/corpus_{时间戳}_{hash}.md(默认)/{高频搭配中间结果}
    输出路径：./references/corpus_processing/corpus_{时间戳}_{hash}.md(默认)/{输出路径}
    原始语料路径 {原始语料路径} (如用户未指定高频搭配中间结果和输出路径则不可缺省)

约束：
【重要生产实践约束】
框架必须从真实语料使用中归纳，禁止内省式空想定义框架、FE、LU。
遵循：先共现后划分；本阶段只产出各类候选集合，**禁止执行正式FE划分、禁止框架匹配、禁止分配框架名称**；过早进行FE划分会因为词元句法位置变化引发FE漂移。所有输出仅作为后续归纳框架的原始候选素材。

1. 构式判定、对照词、原句片段必须全部取自高频搭配中间结果内部的搭配与例句，不得引入外部文本，不得编造，不得照搬样例
2. 输入槽位 {}、必须被真实内容替换。
3. 仅输出规定Markdown内容，不要添加解释、前言、思考过程。
4. 在高频搭配例句中无对比构式时，对照位置与对比轴上的实体/填充词候选字段填写“无”。
5. 对比轴上的实体/填充词候选为可能唤起框架的词汇单元候选，不做最终LU判定。
6. 行动前先让用户确认
7. {时间戳}_{hash}的计算如下：
```python
python -c "import hashlib; from datetime import datetime; hash_use=r'{始语料路径}'; hour_str=datetime.now().strftime('%Y%m%d%H'); hash_str=hashlib.md5(hash_use.encode('utf-8')).hexdigest(); filename_suffix=f'{hour_str}_{hash_str}'; print(filename_suffix)"
```

输出格式:
```markdown
## 对比构式(X vs Y句式)中的对照词
> 扫描高频搭配结果内的例句，识别X vs Y类对比构式（A比B、A相较于B、A而不是B、A胜过B等）；定位构式对照位置X、Y上的对照词/短语，作为邻接LU（词汇单元）候选集合；无对比构式则标记无。

*对比构式‑对比轴上的实体/填充词候选表*
| 原句片段 | 构式类型 | 对照位置X | 对照位置Y | 邻对比轴上的实体/填充词候选 |
| :--- | :--- | :--- | :--- | :--- |
| {sent1} | {constr_type1} | {x1} | {y1} | {lu_candidate_1} |

说明: 
    **关于对比构式‑对比轴上的实体/填充词候选表占位符说明**：
        sent1: 取自高频搭配中间结果内的代表性例句片段
        constr_type1: 构式类型，如“A比B”；无对比构式填“无”
        x1: 对照位置X短语；无填“无”
        y1: 对照位置Y短语；无填“无”
        lu_candidate_1: 多个对比轴上的实体/填充词候选使用分号;分隔；无填“无”
```

*X vs Y句式可以拉出一条对立或互补的语义轴*
*将共现的X和Y记录为强相关对偶节点 -> 自动联想或预测Y的存在*
*先共现后划分后，X vs Y加速FE的泛化和扩充*
*有些词汇在单独出现时含义模糊，但在X vs Y中语义会瞬间精确*
*对比构式拉出的语义轴（归属、自动化、粒度……），归入对应qualia维度*
*语义轴价值——它们可以作为实体的属性维度（用Pustejovsky的qualia的属性组织来归类），也可以作为外围FE附加到具体子框架上*

### 发现

## 框架定义与FE清单
*先基于生产语料分布观察候选出一般框架作为父类框架、再进一步根据候选FE派生出具体领域内框架*
*核心FE随层级递增：每往下一层，框架就多出若干核心FE——因为更具体的框架需要更多角色才能定义*
*这是框架语义学的核心设计原则：框架越具体，核心FE越多；框架越一般，核心FE越少（退化为框架本身 + 外围环境信息）*
例如：Event只需要一个核心FE（事件本身）；Intentionally_act需要四个（施事 + 行动 + 目的 + 手段）
---
## 难点
1. 选取品文档还是生产日志作为语料抽取基线？
建议：**文档做冷启动基线，日志做迭代与验证**。
理由：基线需要概念空间的完备性（Stage/Job/Task 层级、触发类型枚举这些只存在于文档，日志里是沉默证据）；
而FE的真实填充模式、频率分布、长尾变体只能来自日志。两者角色不同，不是二选一。

2. 基线和迭代语料冲突怎么办？
先分类冲突类型再处理：
(a) 同一LU唤起不同框架——语境歧义，正常，多框架共存即可；
(b) FE核心性漂移——需要版本化FrameNet + 变更类型标记（新增/重分类/拆分合并）+ 证据权重（文档与日志不同置信度）；
(c) 框架边界冲突——设冲突计数阈值，超阈值升级人工仲裁。
关键是冲突不能静默地被最后一次LLM调用覆盖。

3. 怎么进行迭代？
最小可行协议：
迭代触发器（新语料量阈值/分布漂移检测，如PSI或KL散度）→ 只对新语料段重放全管线 → 增量合并 → **回归锚定测试**：
固定一组已判定样本（如“流水线成功”必须仍归State框架、“创建流水线”的Agent必须能填 Human_operator），每次迭代后重跑，锚定失败即框架发生了非预期漂移。

### 候选父类清单
Event
 ├── Process        （加 Duration 维度）
 ├── Change         （加 Entity + Initial/Final_state）
 └── Activity       （加 Agent + Activity）
      └── Intentionally_act  （加 Purpose + Means，意向性约束）

| 框架ID | 框架名(EN/ZH) | 类型 | 父框架 | 关系 | Core FE 数 |
|---|---|---|---|---|---|
| F0 | Intentionally_act/意图性行动框架| 抽象父框架 | — | — | 2 |
| F1 | Change/变化框架 | 抽象父框架 | — | — | 3 |
| F3 | Activity/活动框架| 抽象父框架 | — | — | 2 |
| F4 | State/状态框架| 抽象父框架 | — | — | 2 |

### 派生框架
*重要的实操建议：非必要不派生框架、除非候选FE*
从每个子框架继承Fn的全部FE，必须新增子框架专属FE（如F1增加基于模板Template FE；F2增加执行方案 Scheme FE为核心），
#### F0的派生框架
```
语义不能是无意向的习惯性行为，例如、启动流水线
```
##### F0_create: Create_pipeline（创建流水线）
**定义**: 施事(Operator)意图性地创建一条新的流水线(Pipeline)。'创建'隐含从无到有(genesis)——Pipeline作为Patient从不存在到存在的意图
**落地难点**:
1. 无法确定加哪些FE
2. 无法确认哪些FE必须继承、哪些可以新增
3. 无法确定Patient的Qualia驱动领域发现
**理论/方法**
[框架派生](./frame_derive.md)

**落地难点的理论/方法实操**
1. 决定FE签名
例如：当Act取'create'后进行特征分析后确定事件类型为'Accomplishment'，明确了当前框架有[Agent、Patient、Result、Material/Source]FE签名

2. 继承父框架 FE:
| 父 FE | 类型 | 子 FE 处理 |
|---|---|---|
| Agent | Core | 继承为核心；填充约束细化 → Human_operator |
| Act | Core | 继承为核心；取定值 = create |
| Purpose | Core | 继承为核心 |
| Means | Core | 继承为核心；填充约束细化 → Template/Scheme/Copy |
| Condition | Peripheral | 待定（step 6 重新分类） |
| Goal | Peripheral | 继承为外围 |
| Manner | Peripheral | 继承为外围 |

3. 按事件类型签名补FE
diff已继承的FE和事件类型签名FE:
| 签名要求的 FE | 是否已继承 | 处理 |
|---|---|---|
| Agent | ✓ 已继承 | — |
| Patient | ✗ 父框架没有 Patient | **新增为核心** |
| Result | ✗ 父框架没有 Result | **新增为核心** |
| Material/Source | ✗ 父框架没有 | **新增为核心**（领域映射为 Template） |

4. 用Qualia发现领域FE
对Patient做qualia分析，找出与Act相关的维度

*v2 基于示例实体Entry（其生命周期的主事件为 Act）*
```markdown
你是语言学专家，你精通Pustejovsky的理论。
擅长事件的子事件分解和Qualia。
你的任务是基于文档内容/URL、对实体进行Qualia分析，并输出结构化表格到: ./references/qualia/qualia_{实体}.md
约束：
1. 说明中内容仅为格式示范，属性和候选FE必须从{文档内容}中提取，不得照搬样例，除非文档确证相同语义
2. 输入槽位 {}、必须被真实内容替换
3. 仅输出下述两张Markdown表格，不要添加解释或前言

以下为输出格式:
## Qualia分析
| Quale | 属性 | 与{主事件}相关？ | → 候选 FE |
| :--- | :--- | :--- | :--- |
| Formal | {fill_Formal_1} | {fill_Formal_2} | {fill_Formal_3} |
| Constitutive | {fill_Constitutive_1} | {fill_Constitutive_2} | {fill_Constitutive_3} |
| Telic | {fill_Telic_1} | {fill_Telic_2} | {fill_Telic_3} |
| Agentive | {fill_Agentive_1} | {fill_Agentive_2} | {fill_Agentive_3} |

说明: 
    **关于Qualia表占位符说明**：
        fill_Formal_1: Entry 是可寻址的工作单元，具有唯一标识与状态机（待触发/运行/完成/失败）
        fill_Formal_2: 同类别成员：Act 调度的对象
        fill_Formal_3: EntryIdentity, EntryState ; {约束1}
        fill_Constitutive_1: 由任务定义、入参、触发条件、执行上下文（凭证/环境）组成
        fill_Constitutive_2: 构成决定 Act 可执行性
        fill_Constitutive_3: TaskDef, Parameters, TriggerCondition; {约束1}
        fill_Telic_1: 承载请求上下文、驱动 Act 执行并记录结果以支持调度与回溯
        fill_Telic_2: 直接服务 Act
        fill_Telic_3: Context, Outcome, Retrieval; {约束1}
        fill_Agentive_1: 由触发事件（用户操作/定时/上游信号）实例化产生
        fill_Agentive_2: 事件源决定 Act 何时启动
        fill_Agentive_3: TriggerSource, Creator; {约束1}

## 子事件分解
| 子事件阶段 | 协同的Qualia维度 | 语义融合逻辑 (Why) | 最终确定的领域 FE |
| :--- | :--- | :--- | :--- |
| **$e_1$ (过程阶段)** | **Agentive (施成)** | 探究事件"始发原因"：Entry由谁/什么触发而生成 | {fill_e_1_Agentive} |
| **$e_1$ (过程阶段)** | **Constitutive (构成)** | 探究动作发生时的"装配物料"：是哪些任务定义与参数被组装进Entry | {fill_e_1_Constitutive} |
| **$e_2$ (状态阶段)** | **Formal (形式)** | 探究Entry如何被识别：系统必须赋予它区别于其他实体的特征（唯一ID+状态） | {fill_e_2_Formal} |
| **$e_2$ (状态阶段)** | **Telic (目的)** | 探究Entry诞生后的"生存意义"：处于等待被Act触发、在何环境运行的状态 | {fill_e_2_Telic} |
说明: 
    **关于子事件表结构**：
        子事件表固定为4行（e1-Agentive/Constitutive、e2-Formal/Telic）属于预设结构，
        若目标实体生命周期都符合"过程+状态"二元切分则保留，否则"先判定事件类型 → 再选择对应模板"
    **关于子事件表占位符说明**：
        fill_e_1_Agentive: TriggerSource, BY_ACT——FE: 触发源; {约束1}
        fill_e_1_Constitutive: TaskDef, Parameters——FE: 装配物; {约束1}
        fill_e_2_Formal: EntryIdentity, EntryState——FE: 识别特征; {约束1}
        fill_e_2_Telic: Pending, RunEnvironment, Trigger——FE: 待运行环境; {约束1}

以下是实体 {实体}
以下是文档内容 {文档内容}

```

例如对"创建流水线":
*Qualia分析*
| Quale | 属性 | 与执行(Act)相关？ | → 候选 FE |
| :--- | :--- | :--- | :--- |
| Formal | 流水线是可寻址的自动化发布单元（人造物），具有唯一标识（pipeline_id/URL）并按类型固定阶段链形态（如微服务型 Source→Build→Alpha→Beta→Gamma→Production；组合服务型 Assemble→Package→Iota→Kappa→Lambda→Production），归属于云龙服务，一个服务下可有多条流水线 | 同类别成员：作为流水线操作/执行框架的受事(Patient)，被启动/停止/查询/创建/配置 | Pipeline, PipelineType, LifecycleStage, Service |
| Constitutive | 由阶段(Stage)→Job→任务(Task)递归构成；阶段配置含阶段名称、阶段类型、是否默认运行/总是运行、超时时间、触发类型（手动/成功/失败/总是）、工作项串/并行；支持参数化定义、通知(notify)与子流水线引用 | 构成决定流水线可执行性与执行路径（触发条件、串/并行、超时中止整条流水线） | Stage, Job, Task, Trigger, ConfigItem, SubPipeline, Parameter |
| Telic | 服务于自动化发布链路：自动出包（编译构建+静态检查+测试）、通过平台接口任务发布、配置云龙部署任务自动部署；通过质量门禁（110+检查项）管控各阶段出口质量，满足可信构建（可视化/可追溯/可重复）要求 | 直接服务执行——执行是流水线发挥"出包→部署"功效的载体 | Artifact, Gate, Metric, EvaluationResult, Outcome |
| Agentive | 由创建行为实例化产生：单独创建/使用模板创建/代码化(Yaml)创建/复制流水线；也可由配置推送事件或MR触发自动创建，服务初始化(CloudInit)可初始化创建 | 创建者与推送事件源决定流水线何时进入可执行状态 | Operator, Template, ConfigRepo, TriggerSource, PipelineType |

*子事件分解*
| 子事件阶段 | 协同的Qualia维度 | 语义融合逻辑 (Why) | 最终确定的领域 FE |
| :--- | :--- | :--- | :--- |
| **$e_1$ (过程阶段)** | **Agentive (施成)** | 探究流水线"始发原因"：由谁/什么创建而生成（操作者手工创建 / 模板 / 代码化YAML / 配置推送事件自动创建 / 基于流水线复制） | Operator, Template, ConfigRepo, TriggerSource——FE: 创建者/创建方式 |
| **$e_1$ (过程阶段)** | **Constitutive (构成)** | 探究装配物料：哪些阶段/Job/任务、参数与触发规则被组装进流水线定义 | Stage, Job, Task, Parameter, TriggerType——FE: 装配物料 |
| **$e_2$ (状态阶段)** | **Formal (形式)** | 探究流水线如何被识别：系统必须赋予唯一流水线ID与类型并挂载阶段链，以区别于其他实体 | PipelineID, PipelineType, LifecycleStage——FE: 识别特征 |
| **$e_2$ (状态阶段)** | **Telic (目的)** | 探究流水线诞生后的"生存意义"：处于任务默认勾选就绪待触发、被启动运行、向下游产出并被质量门禁判定的状态 | DefaultRun, RunStatus, Trigger, GateResult, Artifact——FE: 待运行与产出状态 |

*新增候选FE*
Formal：[Pipeline、PipelineType、LifecycleStage、Service]
Constitutive：[Stage、Job、Task、Trigger、ConfigItem、SubPipeline、Parameter]
Telic：[Artifact、Gate、Metric、EvaluationResult、Outcome]
Agentive：[Operator、Template、ConfigRepo、TriggerSource、PipelineType]

5. 候选FE验证

*语料验证*：回到语料，检查"创建流水线"的共现词是否覆盖了上述FE
*问题*：尚未做新的语料抽取、此处先人工确认
交给AI处理、以下为提示词：
```markdown
你是数据分析专家。
你的任务是对语料进行验证，要求为：回到语料集，检查激活词的共现词是否覆盖了上述FE。将结果结构化输出表格到: ./frame_net/frame/sub_frame_{name}/debug/candidate_fe_verification.md
约束：
1. 说明中内容仅为格式示范，属性和候选FE必须从{文档内容}中提取，不得照搬样例，除非文档确证相同语义
2. 输入槽位 {}、必须被真实内容替换
3. 仅输出下述一张Markdown表格，不要添加解释或前言

以下为输出格式:
| 候选 FE | 语料中的共现词 | 验证 |
| :--- | :--- | :--- |
例如：
| 候选 FE | 语料中的共现词 | 验证 |
| :--- | :--- | :--- |
| Pipeline | 人工确认 | ✓ |
| PipelineType | 人工确认 | ✓ |
| LifecycleStage | 人工确认 | ✓ |
....

```

*子框架对比*：把{sub_frame_{name}}与兄弟子框架并列，找出独有FE
交给AI处理、以下为提示词：
```markdown
你是边界定义专家。
你的任务是：把{sub_frame_{name}}与兄弟子框架并列，找出独有FE。将结果结构化追加输出表格到: ./frame_net/frame/{sub_frame_name}/debug/candidate_fe_verification.md的末尾
约束：
1. 例子中内容仅为格式示范，属性和候选FE必须从{文档内容}中提取，不得照搬样例，除非文档确证相同语义
2. 输入槽位 {}、必须被真实内容替换
3. 仅输出下述一张Markdown表格 + 发现，不要添加解释或前言

以下为输出格式:
*子框架对比*
| FE | {sub_frame_name} | {sub_frame_name_contrast} |
| :--- | :--- | :--- |
*发现*
[{FE_0}、{FE_1}、...、{FE_N}]是"{sub_frame_name}"独有的核心FE——因为没有[{FE_0}、{FE_1}、...、{FE_N}]，"{fe_name}"行为无法完成

例如：
*子框架对比*
| FE | create_frame | execute_frame | 
| :--- | :--- | :--- |
| Template | ✓ 核心 | ✗ |
| Pipeline_name | ✓ 核心 | ✗（用已有 ID）|
| Result（新实体）| ✓ 核心（新建的 pipeline） | △（执行结果）|
| Scheme | △ 外围 | ✓ 核心 |
...

*发现*
Template和Pipeline_name是Create独有的核心FE——因为没有模板和名称，"创建"行为无法完成。

....

```

6. 核心性重新分类
*问题*: 无检验标准、更倾向使用实际的生产语料 + anget自执行判断；如选后者、提示词也需要修改
对全部FE（继承 + 新增）做三项检验
交给AI处理、以下为提示词：
```markdown
你是分类专家。
你的任务是对{./frame_net/frame/{sub_frame_name}/debug/candidate_fe_verification.md}中的候选FE进行检验后分类，要求为：对全部FE（继承 + 新增）做三项检验。将结果结构化追加输出到: ./frame_net/frame/sub_frame_{name}/debug/candidate_fe_verification.md
约束：
1. 说明中内容仅为格式示范，属性和候选FE必须从{文档内容}中提取，不得照搬样例，除非文档确证相同语义
2. 输入槽位 {}、必须被真实内容替换
3. 仅输出下述一张Markdown表格，不要添加解释或前言

以下为输出格式:
| FE | 来源 | 必要性 | 句法必选 | 框架特有 | 判定 |
| :--- | :--- | :--- | :--- | :--- | :--- |
例如：
| FE | 来源 | 必要性 | 句法必选 | 框架特有 | 判定 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Agent | 继承 | ✓无施事则无创建 | ✓ | ✓ | Core |
| Patient | 新增（事件类型）| ✓ 无流水线则无创建 | ✓ | ✓ | Core |
| Template | 新增（qualia）| △ 模板可选 | △ | ✓ Create 独有 | Peripheral |
....

```
**Core FE**:
| FE | 语义角色 | 填充物示例 |
| operator | Agent/施事 |---| 
| crate | Act/行动 | "创建流水线" |
| {fill} | Purpose/行动目的 |---|
| {fill} | Means/手段 |---|
| Pipeline | Patient |---|
| Pipeline | Result |---|
<!-- ### F0: Intentionally_act（流水线操作）

**定义**: 一个意图性行动框架：施事 Agent（Operator）对受事 Patient（Pipeline）执行某种自主性动作 Action，通过工具 Means（Scheme）在条件 Condition（Branch/Trigger/Version）下达成目标，并产生结果 Result（Outcome）。本框架为所有流水线操作子框架的抽象父框架，Action 不取定值。

**框架关系**: 顶层框架

**Core FE**:

| FE | 语义角色 | 填充物示例 |
|---|---|---| 
F0: Intentionally_act（流水线操作·父框架）
  Act 不取定值
  
  ├── F1: Create_pipeline（创建流水线）  Act = 创建
  ├── F2: Execute_pipeline（执行流水线）  Act = 执行
  ├── F3: Query_pipeline（查询流水线）    Act = 查询
  ├── F4: Configure_pipeline（配置流水线） Act = 配置
  ├── F5: Stop_pipeline（停止流水线）     Act = 停止
  └── F6: Deploy_pipeline（部署流水线）   Act = 部署


-->
## 评估体系
LLM多次采样的自一致性、FE对语料的覆盖率、下游任务（意图识别→工具调用）准确率的对照实验

## 激活词筛选的**选择偏差**
---
## 附录
---
### 核心“通用”语义角色（FE） -> 所有框架共用的非核心FE
在“先共现后划分”阶段，最容易被高频介词洗出来的非核心元素：
[Purpose（主观目的/意图）、Means（手段）、Patient（受事）、Time（时间）、Place（地点）、result(结果)、Condition（条件）]

!!! Purpose（主观目的/意图）不是Goal（空间、数据或状态终点）
    Purpose: 意图（Intentionality）。施事者心智中想要达成的宏观愿望
    Goal:    终点（Boundedness）。动作在空间、数据流或状态转移上的落脚点
---
### 常用语义框架总览
**Using（使用工具）**
*定义*: 刻画施事通过工具作用于某对象以实现目的。
*Core FE*: [Agent/施事、Instrument/工具、Patient/受作用对象]
*Peripheral FE*: [Purpose/目的、Manner/方式、Means/手段]
*高频词元(LUs)*: [use、utilize、employ、wield、leverage、apply、operate]

**Choosing（选择）**
*定义*: 刻画认知者从备选项中选出一个。
*Core FE*: [Cognizer/认知者、Chosen/被选中的、Alternatives/备选集]
*Peripheral FE*: [Basis/选择依据、Manner/方式、Purpose/选择目的]
*高频词元(LUs)*: [choose、select、pick、decide、opt、elect、prefer]

**Processing_materials（材料加工）**
*定义*: 刻画原材料被加工转化为产品的过程。
*Core FE*: [Material/原材料、Product/产品]
*Peripheral FE*: [Agent/加工者、Means/加工手段、Time/时间、Place/地点]
*高频词元(LUs)*: [process、refine、manufacture、produce、fabricate、convert、treat]

**Communication（交流）**
*定义*: 刻画发送方向接收方传递信息。
*Core FE*: [Communicator/发送方、Addressee/接收方、Message/信息内容]
*Peripheral FE*: [Topic/主题、Medium/媒介、Manner/方式、Language/语言]
*高频词元(LUs)*: [say、tell、speak、communicate、inform、notify、convey、state]

**State（状态）**
*定义*: 刻画一个实体处于某种持续的状态。
*Core FE*: [Entity/实体、State/状态]
*Peripheral FE*: [Duration/持续时间、Time/时间、Place/地点]
*高频词元(LUs)*: [be、exist、remain、stay、stand、lie、rest]

**Event（事件）**
*定义*: 刻画某事在特定时间和地点发生。这是最一般的"发生"框架，不预设意向性、持续性或状态变化性。
*Core FE*: [Event/事件]
*Peripheral FE*：[Time/时间、Place/地点、Duration/持续时间、Frequency/频率、Manner/方式、Particular_iteration/特定实例]
*高频词元(LUs)*: [event、happen、occur、take place、come about、transpire、come off、befall]

**Process（过程）**
*定义*: 刻画一个过程在一段时间内展开。描述持续进行的事件，不预设特定施事或状态变化。
*Core FE*: [Process/过程]
*Peripheral FE*: [Duration/持续时间、Time/时间、Place/地点、Manner/方式、Rate/速率]
*高频词元(LUs)*: [process、proceed、unfold、develop、evolve、play out、go on、pan out]

**Change（变化）**
*定义*: 刻画一个实体从初始状态转变为终状态。
*Core FE*: [Entity/实体、Initial_state/初始状态、Final_state/终状态]
*Peripheral FE*: [Time/时间、Place/地点、Manner/方式、Cause/原因、Rate/速率]
*高频词元(LUs)*: [change、turn、become、transform、shift、convert、alter、modify、switch]

**Activity（活动）**
*定义*: 刻画施事参与一项活动。引入施事，但不预设意向性（可是有意的，也可以是无意的习惯性行为）。
*Core FE*: [Agent/施事、Activity/活动]
*Peripheral FE*: [Time/时间、Place/地点、Duration/持续时间、Manner/方式、Purpose/目的、Means/手段]
*高频词汇*: [do、engage in、perform、practice、work (at)、carry out、conduct、undertake]

**Intentionally_act（意图性行动）**
*定义*: 刻画施事带有意图的行动。在 Activity 之上增加意向性约束。
*Core FE*: [Agent/施事、Act/行动、Purpose/行动目的、Means/手段]
*Peripheral FE*: [Condition/条件、Goal/目标、Manner/方式]
*高频词汇*: [act、action、do、perform、carry out、execute、commit]
