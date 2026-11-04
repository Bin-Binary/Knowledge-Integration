# Activity
这是持续性活动的抽象框架，在该框架中，Agent进入Activity的一个正在进行的状态，在一段时间内保持该状态，并通过完成或停止离开该状态。代理的活动应该是有意的。这个框架主要是为了继承普通的FE，并为Activity的开始、进行、完成或停止阶段提供框架结构，每个阶段都构成了这个框架的一个子框架。这个框架应该与Process框架进行比较。

## 核心FE
- Agent: 从事活动的主体

## 外围FE
- Place: 活动的地点
- Time: 活动的时间
- Manner: 活动的方式
- Duration: 活动持续的时长

## 主题外功能FE
- Activity: Agent 所从事的活动

## FE关系
-

## 框架关系
Inherits from(Process); 
Is Inherited by(Apply_heat); 
Has Subframe(s)(Activity_finish,Activity_ongoing,Activity_ready_state,Activity_prepare,Activity_pause,Activity_stop,Activity_abandoned_state,Activity_done_state,Activity_paused_state,Activity_start,Activity_resume)

## 词元
[-]
