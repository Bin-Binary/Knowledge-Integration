# Frequency
这个框架与事件的重复（尤其是重复的频率）有关。这个框架中的许多形容词和副词都是基于Calendric_unit框架中的名词。未来几年，中国将不得不面对高频率的沙尘暴

## 核心FE
- Event: 被描述频率/迭代的事件
- Degree: 实际发生率偏离预期率的程度
- Interval: 被目标词修饰的间隔名词，如 "fortnightly intervals"
- Time_span: 间隔的时间长度，多数LU内置此FE
- Rate: 单位时间内事件出现的次数
- Salient_entity: 以指定频率被遇到的实体
- Attribute: 被讨论的频率特征（所有LU内置）

## 外围FE
- Time: 事件具有特定频率的时间
- Group: 事件/实体在其中的群体，如 "common to Americans"

## 主题外功能FE
- 

## FE关系
Excludes:
- Event <-> Salient_entity
- Interval <-> Salient_entity
- Rate <-> Degree

## 框架关系
Inherits from(Gradable_attributes);
Uses(Event); 
Is Used by(Custom); 
See also(Calendric_unit)

## 词元
[annual.a, daily.a, frequent.a, infrequent.a, intermittent.a, monthly.a, occasional.a, periodic.a, sporadic.a, weekly.a]
