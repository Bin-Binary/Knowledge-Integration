# SKILL
> 'A skill is a reference guide for proven techniques, patterns, or tools. Skills help future agents find and apply effective approaches.'

> 'Skills are: Reusable techniques, patterns, tools, reference guides'

> 'Skills are NOT: Narratives about how you solved a problem once'


## 目录结构与渐进式披露

> 观察Agent在不同的阶段加载不同详细程度（按需加载目录）的信息
> x轴代表Skill的核心目录结构、y轴代表Skill渐进式披露的生命周期、坐标描述：Agent.....

| X\Y | 发现 | 激活 | 执行 |
| :---- | :---- | :---- | :---- |
| SKILL.md | X1Y4 | X2Y4 | X3Y4 |
| scripts/ | - | - | X3Y3 |
| references/ | - | - | X3Y2 |
| asserts/ | - | - | X3Y1 |

### 图示
> SVG图尽量使用填充色圆点表示坐标中的文字描述/文字说明
> XY坐标表示文字描述/文字说明: 第N个X第N个Y, 例如asserts/ 在执行阶段的表示为：X3Y1

X3Y1: 按需加载 asserts/ 下模板、字体、SVG 等资源文件，用于最终输出生成
X3Y2: 按需加载references/ 下参考文档，作为执行上下文补充（如规范、示例）
X3Y3: 按SKILL.md指令调用scripts/ 下脚本，传入参数、捕获输出
X3Y4: 严格按SKILL.md定义的步骤、指令和约束执行任务
X2Y4: 完整加载SKILL.md正文，理解工作流、约束与输出规范
X1Y4: 仅读取name +description，做意图匹配与候选排序，不加载正文

---
## 技能类型与渐进式披露

> 宏观观察Agent在不同的阶段加载不同详细程度（按需加载目录）的信息
> x轴代表Skill的核心目录结构、y轴代表Skill渐进式披露的生命周期、坐标描述：Agent.....

| X\Y | 发现 | 激活 | 执行 |
| :---- | :---- | :---- | :---- |
| SKILL.md | X1Y4 | X2Y4 | X3Y4 |
| scripts/ | - | - | X3Y3 |
| references/ | - | - | X3Y2 |
| asserts/ | - | - | X3Y1 |

### 图示
> SVG图尽量使用填充色圆点表示坐标中的文字描述/文字说明
> XY坐标表示文字描述/文字说明: 第N个X第N个Y, 例如asserts/ 在执行阶段的表示为：X3Y1

X3Y1: 按需加载 asserts/ 下模板、字体、SVG 等资源文件，用于最终输出生成
X3Y2: 按需加载references/ 下参考文档，作为执行上下文补充（如规范、示例）
X3Y3: 按SKILL.md指令调用scripts/ 下脚本，传入参数、捕获输出
X3Y4: 严格按SKILL.md定义的步骤、指令和约束执行任务
X2Y4: 完整加载SKILL.md正文，理解工作流、约束与输出规范
X1Y4: 仅读取name +description，做意图匹配与候选排序，不加载正文

