# Part_whole
这个框架涉及表示整体实体的一个或多个部分的名词。
零件不是相对于整体的方向、中心或边缘定义的，也不是有序的。我们还注释了Part的属性，例如与它的大小有关。金忘记了故事的一大部分。艾比只吃了蛋糕的上半部分

## 核心FE
- Part: 较大整体的某一部分
- Whole: 拥有所有部分的不可分割实体

## 主题外功能FE
- Part_prop: 部分的属性（如 big section 中的 big）
- Orientation: 决定部分方位的属性（如 top half 中的 top）
- System: 整体内各部分的组织体系
- Name: 在某体系中用于标识部分的标签

## FE关系
- 

## 框架关系
Inherits from(Part_piece); 
Is Inherited by(Shaped_part,Part_orientational,Part_edge,Part_inner_outer,Part_ordered_segments,Rest,Vehicle_subpart,Temporary_group); 
Is Used by(Inclusion,Completeness)

## 词元
[part.n, fragment.n, half.n, segment.n, section.n, eighth.n, fifth.n, hundredth.n, third.n, quarter.n, tenth.n, portion.n, development.n]
