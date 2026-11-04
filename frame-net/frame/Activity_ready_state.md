# Activity_ready_state
主角处于初始状态，在开始参与Activity之前，但Activity执行的所有前提条件都已满足。在许多情况下，主角是一个有意的代理人，但也有其他用途，在这种情况下，代理人是一个对活动至关重要的实体。或者，Activity可以用Salient_entity来表示，Salient_entity代表Activity。这个Salient_entity也可以是意向代理，但不必是。她还没准备好！我想他已经准备好开口了。英国政府准备好在护照-身份证上大转弯了吗？看看萨尔是否准备好去浴缸了。世界终于为他准备好了！

## 核心FE
- Protagonist: 处于就绪状态的主角
- Activity: Protagonist 准备要执行的动作，如 "The students were finally ready to take the exam."
- Salient_entity: `转喻代替` Activity 的实体[1]，如 "Are you ready for a baby?" "I'm ready for the eggs now."


## 外围FE
- Time: Protagonist 处于就绪状态的时间
- Duration: Protagonist 保持就绪状态的持续时长

## 主题外功能FE
- Result: 就绪状态之后导致的状态或事件
- Degree: 修饰就绪程度的可分级属性

## FE关系
Excludes
- Protagonist ↔ Slient_entity

## 框架关系
Inherits from(Process_initial_state); 
Is Inherited by(Be_on_alert); 
Is Used by(Standing_by); 
Subframe of(Activity); 
Precedes(Activity_start); 
Is Preceded by(Activity_prepare)

## 词元
[ready.a, prepared.a, set.a]

## 注解
[1] 用一个与某事物（或活动）有紧密联系、关联性极强的实体（人、物、概念），来代替该事物或活动本身; 转喻的核心不在于“相似性”（那是隐喻/比喻），而在于“相关性”或“邻近性”.
"Are you ready for a baby?" -> 字面实体：Baby（婴儿，一个名词/实体）-> 实际代指的活动：怀孕、生产、或者抚养小孩这一整套长期的生活活动与责任
