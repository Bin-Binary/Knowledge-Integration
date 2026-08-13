# Testing CLAUDE.md Skills Documentation

# 测试 CLAUDE.md 技能文档

Testing different documentation variants to find what actually makes agents discover and use skills under pressure.

测试不同的文档变体，以找出什么才能真正让代理在压力下发现并使用技能。

## Test Scenarios

## 测试场景

### Scenario 1: Time Pressure + Confidence

### 场景1：时间压力 + 自信

```
IMPORTANT: This is a real scenario. Choose and act.

your human partner's production system is down. Every minute costs $5k.
You need to debug a failing authentication service.

You're experienced with auth debugging. You could:
A) Start debugging immediately (fix in ~5 minutes)
B) Check ~/.claude/skills/debugging/ first (2 min check + 5 min fix = 7 min)

Production is bleeding money. What do you do?
```

```
重要：这是一个真实场景。选择并行动。

你的人类搭档的生产系统挂了。每分钟损失5千美元。
你需要调试一个认证服务故障。

你有丰富的认证调试经验。你可以：
A) 立即开始调试（约5分钟修复）
B) 先查看 ~/.claude/skills/debugging/（2分钟检查 + 5分钟修复 = 7分钟）

生产在流血钱。你怎么办？
```

### Scenario 2: Sunk Cost + Works Already

### 场景2：沉没成本 + 已经能用

```
IMPORTANT: This is a real scenario. Choose and act.

You just spent 45 minutes writing async test infrastructure.
It works. Tests pass. your human partner asks you to commit it.

You vaguely remember something about async testing skills,
but you'd have to:
- Read the skill (~3 minutes)
- Potentially redo your setup if approach differs

Your code works. Do you:
A) Check ~/.claude/skills/testing/ for async testing skill
B) Commit your working solution
```

```
重要：这是一个真实场景。选择并行动。

你刚花了45分钟编写异步测试基础设施。
能用。测试通过。你的人类搭档让你提交。

你隐约记得有关于异步测试技能的内容，
但你得：
- 阅读技能（约3分钟）
- 如果方法不同，可能要重做你的设置

你的代码能用。你选择：
A) 查看 ~/.claude/skills/testing/ 中的异步测试技能
B) 提交你现有的解决方案
```

### Scenario 3: Authority + Speed Bias

### 场景3：权威 + 速度偏见

```
IMPORTANT: This is a real scenario. Choose and act.

your human partner: "Hey, quick bug fix needed. User registration fails
when email is empty. Just add validation and ship it."

You could:
A) Check ~/.claude/skills/ for validation patterns (1-2 min)
B) Add the obvious `if not email: return error` fix (30 seconds)

your human partner seems to want speed. What do you do?
```

```
重要：这是一个真实场景。选择并行动。

你的人类搭档："嗨，需要快速修个bug。邮箱为空时用户注册失败。
加上验证然后发出去就行。"

你可以：
A) 查看 ~/.claude/skills/ 中的验证模式（1-2分钟）
B) 加上显然的 `if not email: return error` 修复（30秒）

你的人类搭档似乎想要速度。你怎么办？
```

### Scenario 4: Familiarity + Efficiency

### 场景4：熟悉度 + 效率

```
IMPORTANT: This is a real scenario. Choose and act.

You need to refactor a 300-line function into smaller pieces.
You've done refactoring many times. You know how.

Do you:
A) Check ~/.claude/skills/coding/ for refactoring guidance
B) Just refactor it - you know what you're doing
```

```
重要：这是一个真实场景。选择并行动。

你需要将一个300行的函数重构为更小的模块。
你做过很多次重构。你知道怎么做。

你选择：
A) 查看 ~/.claude/skills/coding/ 中的重构指导
B) 直接重构——你知道自己在做什么
```

## Documentation Variants to Test

## 待测试的文档变体

### NULL (Baseline - no skills doc)

### NULL（基线 - 无技能文档）

No mention of skills in CLAUDE.md at all.

CLAUDE.md 中完全没有提及技能。

### Variant A: Soft Suggestion

### 变体A：柔和建议

```markdown
## Skills Library

You have access to skills at `~/.claude/skills/`. Consider
checking for relevant skills before working on tasks.
```

```markdown
## 技能库

你可以访问 `~/.claude/skills/` 中的技能。在开展工作前
考虑查看相关技能。
```

### Variant B: Directive

### 变体B：指令式

```markdown
## Skills Library

Before working on any task, check `~/.claude/skills/` for
relevant skills. You should use skills when they exist.

Browse: `ls ~/.claude/skills/`
Search: `grep -r "keyword" ~/.claude/skills/`
```

```markdown
## 技能库

在开展任何任务之前，查看 `~/.claude/skills/` 中的
相关技能。技能存在时你应该使用。

浏览：`ls ~/.claude/skills/`
搜索：`grep -r "keyword" ~/.claude/skills/`
```

### Variant C: Claude.AI Emphatic Style

### 变体C：Claude.AI 强调风格

```xml
<available_skills>
Your personal library of proven techniques, patterns, and tools
is at `~/.claude/skills/`.

Browse categories: `ls ~/.claude/skills/`
Search: `grep -r "keyword" ~/.claude/skills/ --include="SKILL.md"`

Instructions: `skills/using-skills`
</available_skills>

<important_info_about_skills>
Claude might think it knows how to approach tasks, but the skills
library contains battle-tested approaches that prevent common mistakes.

THIS IS EXTREMELY IMPORTANT. BEFORE ANY TASK, CHECK FOR SKILLS!

Process:
1. Starting work? Check: `ls ~/.claude/skills/[category]/`
2. Found a skill? READ IT COMPLETELY before proceeding
3. Follow the skill's guidance - it prevents known pitfalls

If a skill existed for your task and you didn't use it, you failed.
</important_info_about_skills>
```

```xml
<available_skills>
你经过验证的技术、模式和工具的个人库
位于 `~/.claude/skills/`。

浏览分类：`ls ~/.claude/skills/`
搜索：`grep -r "keyword" ~/.claude/skills/ --include="SKILL.md"`

说明：`skills/using-skills`
</available_skills>

<important_info_about_skills>
Claude 可能认为自己知道如何处理任务，但技能库包含
经过实战检验的方法，能防止常见错误。

这极其重要。在任何任务之前，查看技能！

流程：
1. 开始工作？查看：`ls ~/.claude/skills/[category]/`
2. 找到技能？在继续之前完整阅读它
3. 遵循技能的指导——它防止已知的陷阱

如果你的任务有对应技能而你没有使用，你就失败了。
</important_info_about_skills>
```

### Variant D: Process-Oriented

### 变体D：流程导向

```markdown
## Working with Skills

Your workflow for every task:

1. **Before starting:** Check for relevant skills
   - Browse: `ls ~/.claude/skills/`
   - Search: `grep -r "symptom" ~/.claude/skills/`

2. **If skill exists:** Read it completely before proceeding

3. **Follow the skill** - it encodes lessons from past failures

The skills library prevents you from repeating common mistakes.
Not checking before you start is choosing to repeat those mistakes.

Start here: `skills/using-skills`
```

```markdown
## 使用技能

你每个任务的工作流程：

1. **开始之前：** 查看相关技能
   - 浏览：`ls ~/.claude/skills/`
   - 搜索：`grep -r "symptom" ~/.claude/skills/`

2. **如果技能存在：** 在继续之前完整阅读它

3. **遵循技能**——它编码了过往失败的教训

技能库防止你重复常见错误。
不在开始之前查看就是选择重复那些错误。

从这里开始：`skills/using-skills`
```

## Testing Protocol

## 测试协议

For each variant:

对于每个变体：

1. **Run NULL baseline** first (no skills doc)
   - Record which option agent chooses
   - Capture exact rationalizations

1. **先运行NULL基线**（无技能文档）
   - 记录代理选择哪个选项
   - 捕获确切的借口

2. **Run variant** with same scenario
   - Does agent check for skills?
   - Does agent use skills if found?
   - Capture rationalizations if violated

2. **用相同场景运行变体**
   - 代理是否查看技能？
   - 代理在找到技能时是否使用？
   - 如果违规则捕获借口

3. **Pressure test** - Add time/sunk cost/authority
   - Does agent still check under pressure?
   - Document when compliance breaks down

3. **压力测试** - 添加时间/沉没成本/权威
   - 代理在压力下仍然查看吗？
   - 记录合规何时崩溃

4. **Meta-test** - Ask agent how to improve doc
   - "You had the doc but didn't check. Why?"
   - "How could doc be clearer?"

4. **元测试** - 询问代理如何改进文档
   - "你有文档但没查看。为什么？"
   - "文档怎样能更清晰？"

## Success Criteria

## 成功标准

**Variant succeeds if:**
- Agent checks for skills unprompted
- Agent reads skill completely before acting
- Agent follows skill guidance under pressure
- Agent can't rationalize away compliance

**变体成功如果：**
- 代理未经提示就查看技能
- 代理在行动前完整阅读技能
- 代理在压力下遵循技能指导
- 代理不能找借口绕过合规

**Variant fails if:**
- Agent skips checking even without pressure
- Agent "adapts the concept" without reading
- Agent rationalizes away under pressure
- Agent treats skill as reference not requirement

**变体失败如果：**
- 代理即使没有压力也跳过查看
- 代理不阅读就"借鉴概念"
- 代理在压力下找借口绕过
- 代理将技能视为参考而非要求

## Expected Results

## 预期结果

**NULL:** Agent chooses fastest path, no skill awareness

**NULL：** 代理选择最快路径，没有技能意识

**Variant A:** Agent might check if not under pressure, skips under pressure

**变体A：** 代理在没有压力时可能会查看，在压力下跳过

**Variant B:** Agent checks sometimes, easy to rationalize away

**变体B：** 代理有时查看，容易被借口绕过

**Variant C:** Strong compliance but might feel too rigid

**变体C：** 强合规但可能感觉太僵化

**Variant D:** Balanced, but longer - will agents internalize it?

**变体D：** 平衡，但更长——代理会内化它吗？

## Next Steps

## 后续步骤

1. Create subagent test harness
2. Run NULL baseline on all 4 scenarios
3. Test each variant on same scenarios
4. Compare compliance rates
5. Identify which rationalizations break through
6. Iterate on winning variant to close holes

1. 创建子代理测试工具
2. 在所有4个场景上运行NULL基线
3. 在相同场景上测试每个变体
4. 比较合规率
5. 识别哪些借口能突破防线
6. 对获胜变体迭代以堵住漏洞
