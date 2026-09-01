---
name: multi-style-photo-transformation
description: 当需要对照片进行多范式照片转绘时、调用该技能
---

## 调用方式
skill::multi-style-photo-transformation(mode=<1|2|3>, reference_image=<输入参考图>)
- mode=1：scenes‑gathered‑zine‑v1‑3 撕裂zine拼贴
- mode=2：竖向二分哑光米白画册明信片
- mode=3：surreal pop collage 超现实流行拼贴
- reference_image：必须传入原始参考照片作为素材源

---

## Mode 1｜scenes‑gathered‑zine‑v1‑3 撕裂zine拼贴
### 核心逻辑
识别照片叙事焦点，沿自然物象生成撕口，混合实拍摄影与同场景插画，营造空间层次穿越感，不做固定占比限制。

### 正向约束
1. 优先识别照片叙事焦点，不强制画面占比35%/50%，允许只保留人物、局部水面、局部建筑群。
2. 撕口沿着海岸、水线、树冠、建筑结构轮廓自然生长延展。
3. 摄影区域之外的插画内容，必须来源于同一个原始场景，禁止引入无关素材。
4. 撕口邻近区域保留原照片真实色彩，向外逐步过渡为网点、干刷、丝网印刷的艺术质感。
5. 使用一条连续色彩或者运动轨迹，贯通实拍摄影区域与插画区域，保证视觉流动。

### 禁止项
- 禁止矩形硬贴图
- 禁止均匀白边
- 禁止数码蒙版抠图痕迹

---

## Mode 2｜竖向二分哑光米白画册明信片
### 核心逻辑
竖向构图，米白哑光特种纸基底，大面积留白；上半区完全保留实景照片，下半区做水墨扁平重构插画，极简东方学术版式，无多余装饰。

### 正向约束
1. 上半区（实景层）
完整保留高清写实摄影风景原貌，完全沿用原始景物空间布局、物理轮廓、原生低饱和配色、原生光影质感，零修改。

2. 下半区（水墨重构层）
米色留白基底，水墨扁平重构插画；提取上半区全部景物，解构为极简几何形态；分层平涂柔和色块，搭配毛笔淡墨晕染笔触，彻底摒弃锐利硬边；复刻原图整体色彩调性，剔除细碎纹理、冗余杂物、复杂光影，只保留景物结构神韵。

3. 文字排版
画面最底部居中排版：
- 首行：优雅衬线手写体英文标题
- 次行：字号更小的无衬印英文描述短句

4. 整体质感
米白哑光特种纸底色，大面积留白；遵循极简主义东方建筑风景研究版式逻辑；视觉干净、克制、高级，具备学术感，不添加任何多余装饰元素。

### 禁止项
- 不得改动上半区实景画面
- 下半区禁止锐利硬边、复杂写实纹理
- 禁止多余装饰纹样

---

## Mode 3｜surreal pop collage 超现实流行拼贴
### 核心逻辑
3:4竖版超现实流行拼贴，主体保留原图样貌与原色，背景使用哑光平涂色块，搭配源自原图的巨型幻想物体与小元素组。

画幅：vertical 3:4

### 正向英文Prompt（直接给绘图模型）
keep the subject clearly recognizable, keep its original colors intact, hands empty, no props,
the background replaced by huge flat matte color shapes: 2‑3 flat matte irregular color blocks,
one impossible giant element sourced from original reference image,
small‑size element group in graduated sizes following an arc,
a few white hand‑drawn graffiti strokes, flat matte colors

### 禁止英文约束
no gradients, no shadows, no text, no watermark

### 中文释义便于校验
1. 主体清晰可辨认，保留主体原始色彩；可选约束：双手为空，不带道具
2. 背景替换为2‑3个巨大哑光平涂不规则色块
3. 存在唯一巨型幻想物体，物体素材必须来自参考原图
4. 一组小元素，沿着圆弧轨迹做大小渐变排布
5. 少量白色手绘涂鸦线条
6. 全部使用哑光平涂色彩，禁止渐变、禁止阴影、禁止文字、禁止水印

---

## 执行规则
1. 执行指定mode时，该mode下全部正向约束必须落实，禁止项必须严格规避。
2. 模式之间互相隔离，mode1规则不会带入mode2、mode3。
3. mode3优先使用原始英文prompt输入绘图模型，保证风格还原。
4. 所有衍生插画、巨型元素，素材来源必须来自传入的reference_image，禁止凭空捏造无关物体。

---

## 示例调用
skill::multi-style-photo-transformation(mode=2, reference_image=user_upload_photo.jpg)
