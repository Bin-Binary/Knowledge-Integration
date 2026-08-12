# SKILL
> 'A skill is a reference guide for proven techniques, patterns, or tools. Skills help future agents find and apply effective approaches.'

> 'Skills are: Reusable techniques, patterns, tools, reference guides'

> 'Skills are NOT: Narratives about how you solved a problem once'


## 目录结构与渐进式披露

> Agent在不同的阶段加载不同详细程度（按需加载目录）的信息

| 生命周期阶段 (X轴) | 加载的目录/文件 (Y轴) | Agent的具体行为 |
| :--- | :--- | :--- |
| 1. 发现 | SKILL.md (仅元数据) | 仅读取 name + description，做意图匹配，不加载正文。 |
| 2. 激活 | SKILL.md (完整正文) | 完整加载正文，理解工作流、约束与输出规范。 |
| 3. 执行 | SKILL.md (指令约束) | 严格按正文定义的步骤、指令和约束执行任务。 |
| 3. 执行 | scripts/ | 按指令调用脚本，传入参数、捕获输出。 |
| 3. 执行 | references/ | 按需加载参考文档，作为执行上下文补充。 |
| 3. 执行 | asserts/ | 按需加载模板、字体等资源文件，用于输出生成。 |


---
<!-- ## 技能类型与渐进式披露

> 
 -->

