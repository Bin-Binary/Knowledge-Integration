# Cause_change
代理或原因导致实体发生改变，无论是在其类别成员资格方面，还是在属性的值方面。
在前一种情况下，可以表示Initial_category和Final_category，在后一种情况下，可以指定Initial_value和Final_value。

## 核心FE
- Agent: 引起实体改变的有意识行动者
- Entity: 被引起改变的抽象或具体事物/情境
- Initial_category: 改变前实体所属的类别
- Final_category: 改变后实体所属的类别
- Initial_value: 改变前属性的值
- Final_value: 改变后属性的值

## 外围FE
- Time: 引起改变的时间
- Manner: 行为方式描述
- Purpose: Agent 引起改变的目的
- Means: 引起改变的手段/行动
- Place: 引起改变的地点

## 主题外功能FE
- Degree: 初始与终末类别/值之间的差异程度
- Explanation: Agent 引起改变的回应事态
- Attribute: 实体上可赋值的特征（Core-Unexpressed）
- Cause: 引起实体改变的事件（Core-Unexpressed）
- Containing_event: 包含该改变的更大事件
- Duration: 改变持续的时间长度
- Circumstances: 独立于事件的世界状态
- Role: Agent 在事件中的特定角色
- Event_description: 对目标子句整体的描述
- Period_of_iterations: 迭代事件的重复时段
- Re-encoding: 将当前框架作为更大概念化的组成部分

## FE关系
Excludes:
- Agent <-> Cause
- Initial_category <-> Initial_value
- Final_category <-> Final_value
- Final_value <-> Final_category
- Initial_value <-> Final_category
- Attribute <-> Final_category

Requires:
- Final_value <-> Attribute
- Initial_value <-> Attribute

## 框架关系
Inherits from(Transitive_action); 
Is Inherited by(Change_event_time,Change_event_duration,Exchange_currency); 
Is Used by(Reforming_a_system,Adjusting);
Is Causative of(Undergo_change)

## 词元
[make.v, turn.v, change.v, convert.v, transform.v, modify.v, alter.v, modification.n, alteration.n, conversion.n, transformation.n, vary.v, variation.n, reshape.v, shift.v, deform.v]
