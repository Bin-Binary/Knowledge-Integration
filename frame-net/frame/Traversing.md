# Traversing
Theme 相对于显著位置改变位置，可表达为 Source/Path/Goal/Area/Direction/Path_shape/Distance

## 核心FE
- Theme: 移动的对象，如 "The officer approached"
- Source: 起点，如 "from Achintree Farm"
- Path: 运动轨迹，如 "through the desert"
- Goal: Theme 到达的目的地，如 "arrived in Paris"
- Distance: 运动距离，如 "twenty feet"
- Area: 运动发生的区域（非单一线性路径），如 "crisscrossed the desert"
- Path_shape: 整体路径构型，如 "in a spiral"
- Direction: 方向，如 "down"

## 外围FE
- Duration: 持续时间
- Speed: 速度
- Manner: 运动的方式
- Means: 运动的手段
- Time: 运动的时间
- Place: 运动的地点

## 主题外功能FE
- Cotheme: 同步移动的第二对象，如 "came with me"
- New_situation: Theme 到达后 Goal 的状态，如 "arrived to a standing ovation"
- Purpose: 到达目的
- Frequency: 到达频率
- Iterations: 迭代次数
- Endpoints: Source 和 Goal 合称

## FE关系
Excludes:
- Area <-> Source/Path/Goal/Distance/Direction

## 框架关系
Inherits from(Event); 
Is Inherited by(Intentional_traversing); 
Perspective on(Motion_scenario); 
Uses(Path_shape); 
Is Used by(Openness); 
Has Subframe(s)(Departing,Arriving)

## 词元
[traverse.v, cross.v, ascend.v, descend.v, crisscross.v, jump.v, leap.v, hop.v, circle.v, pass.v, skirt.v, mount.v]
