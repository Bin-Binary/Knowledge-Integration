# 运行时流程说明

## 一、LangGraph 节点顺序

```text
parse_request
  → activate_frames
  → resolve_qualia (pass=1)
  → resolve_relations
  → resolve_candidates
  → self_fill
  → resolve_qualia_2 (pass=2)
  → check_gaps
  → aggregate_questions
  → user_answers
  → recheck
  → 条件分流
      ├─ proceed_to_convergence → converge → execute → END
      ├─ downgrade             → downgrade_with_notice → END
      ├─ escalate              → escalate_to_human → END
      └─ block                 → END
```

## 二、每个节点的职责

### parse_request

- 输入：request、context
- 输出：parsed_intent（action / purpose / patient_type）
- 方式：LLM 开放选择题，从 R-ROLES-00 的 ActionType / PurposeType / EntityType 候选值域中选

### activate_frames

- 输入：parsed_intent.action
- 输出：frame_instances
- 方式：从 ActionType.values[action].frame 查目标框架，构造 FrameInstance

### resolve_qualia (pass=1)

- 输入：frame_instances、entity_registry、context
- 输出：candidates
- 方式：按 frame-name-index.by_qualia_paths 解析 placeholder / entity / fe_source

### resolve_relations

- 输入：frame_instances、candidates
- 输出：candidates
- 方式：按 frame-name-index.by_frame_refs 从其他框架实例的 FE 取

### resolve_candidates

- 输入：frame_instances、entity_registry、unit_registry、artifact_registry、context
- 输出：candidates
- 方式：按 frame-name-index.by_candidate_paths 分发到四种解析器：
  - entity_relation：遍历实体的 relations，过滤目标类型
  - unit_field：读 unit 的字段
  - artifact_field：读 artifact 的字段
  - context_key：从 context 取值

### self_fill

- 输入：frame_instances、candidates
- 输出：frame_instances（更新 FE binding）
- 方式：取候选列表第一个（default_top1）

### resolve_qualia_2 (pass=2)

- 与 pass=1 相同
- 但此时 material 已填，`{material}` placeholder 生效

### check_gaps

- 输入：frame_instances、candidates
- 输出：gaps
- 方式：分类为 required_hard / required_pending / peripheral

### aggregate_questions

- 输入：gaps
- 输出：user_questions
- 方式：只对 required_hard 生成问题

### user_answers

- 输入：user_questions、frame_instances
- 输出：user_answers、frame_instances
- 方式：应用模拟答案（或真实用户输入）

### recheck

- 输入：frame_instances、candidates
- 输出：decision
- 方式：
  - required 全填或有候选 → proceed_to_convergence
  - 有 required hard missing → downgrade
  - 其他 → escalate

### converge

- 输入：frame_instances、candidates
- 输出：frame_instances（更新 binding）
- 方式：按 source 优先级打分，取 top1

### execute

- 输入：frame_instances、decision
- 输出：execution_plan
- 方式：只对 required 且 filled 的 FE 生成 step

### downgrade_with_notice

- 输入：decision、frame_instances
- 输出：execution_plan（status=downgraded）、downgrade_notice
- 方式：生成降级计划 + 通知文本，pending_confirmation=True
- 不执行，等用户确认

### escalate_to_human

- 输入：decision、frame_instances、gaps
- 输出：escalation
- 方式：打包完整上下文，pending_human=True
- 不执行，等人工介入

## 三、候选生成的三个节点

| 节点 | 依据 | 输出 |
|---|---|---|
| resolve_qualia | by_qualia_paths | qualia 推导的候选 |
| resolve_relations | by_frame_refs | 其他框架 FE 的值 |
| resolve_candidates | by_candidate_paths | 注册表或 context 的值 |

三者可叠加，同一 FE 的候选合并后由 converge 收敛。

## 四、状态字段

| 字段 | 内容 |
|---|---|
| request | 用户请求 |
| context | 会话上下文 |
| parsed_intent | 意图解析结果 |
| frame_instances | 激活的框架实例 |
| entity_registry | 实体注册表 |
| unit_registry | 单元注册表 |
| artifact_registry | 产物注册表 |
| candidates | 候选集 |
| gaps | 缺口清单 |
| user_questions | 待问用户 |
| user_answers | 用户回答 |
| decision | 决策 |
| execution_plan | 执行计划 |
| downgrade_notice | 降级通知 |
| escalation | 人工兜底包 |
| trace | 执行轨迹 |

## 五、LLM 调用点

只一处：

| 节点 | 用途 |
|---|---|
| parse_request | 从候选值域选 action / purpose / patient_type |

其余节点均为规则，无 LLM。

## 六、收敛策略

`convergence/decision.py` 定义 source 优先级：

| source | 优先级 |
|---|---|
| explicit | 100 |
| frame | 80 |
| entity | 60 |
| qualia | 40 |
| query / role | 20 |
| default | 10 |

`pick_best` 取优先级最高的候选。