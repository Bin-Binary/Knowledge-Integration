# Sequence
这个框架中的词描述了以某种时间有序序列出现的实体。因此，这些实体之间具有某种关系，这些关系可以通过相对时间框架来描述。但是，此时，这个框架与那个框架没有框架关系（尽管这还在讨论中）。此外，需要注意的是，此框架中的单词与Shape中的单词具有隐喻性链接。详细描述紧急情况下采取的步骤的顺序

## 核心FE
- Entity_1: 与 Entity_2 按顺序出现的实体
- Entity_2: 相对于 Entity_1 按顺序出现的实体
- Entities: 按时间顺序出现的实体集合

## 外围FE
- Descriptor: 序列的特征或描述

## 主题外功能FE
- Relation_type

## FE关系
- Entity_1 Excludes Entities（二者互斥，不能同时出现）
- Entity_2 Excludes Entities

## 框架关系
Inherits from(Relation)
