# Text
文本是包含有关主题的语言、符号信息的实体，由作者在创建时创建。
它可以是由某种材料等构成的物理实体，也可以是为某个对象建造的。

## 核心FE
- Text: 包含语言信息的实体

## 外围FE
- Author: 创作该文本的人
- Use: 文本被制作的目的/用途
- Topic: 文本所涉及的主题
- Medium: 文本的语言或物理媒介（如 Greek, radio）

## 主题外功能FE
- Beneficiary: 文本为其而制作的人
- Time_of_creation: 文本创作的时间
- Material: 文本的物理材质（如 vellum）
- Containing_text: 包含该文本的更大文本
- Genre: 文本的体裁/子体裁
- Subpart: 构成该文本的更小文本部分

- Title: 文本的标题
- Place: 文本流通/流行的地区
- Descriptor: 文本的特征描述

## FE关系
- 

## 框架关系
Inherits from(Artifact); 
Is Inherited by(Documents,Records); 
Uses(Text_creation);
Is Used by(Law,Topic,Medium,Reference_text)

## 词元
[use.v, employ.v, use.n, avail oneself.v, operate.v, operation.n, apply.v, utilise.v, utilisation.n, application.n, operational.a, employment.n, exercise.vtome.n, fanzine.n, epilogue.n, benediction.n, imprecation.n, eulogy.n, autobiography.n, ballad.n, biography.n, chronicle.n, comedy.n, diary.n, drama.n, elegy.n, epic.n, epigram.n, epistle.n, essay.n, exemplum.n, fable.n]
