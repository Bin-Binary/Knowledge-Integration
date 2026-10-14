# 框架索引
基于nltk_data.framenet_v17格式化的索引。

## 格式说明
|框架名称|说明|框架关系|完成构建|
- 框架名称：和原名称保持一致
- 说明：原.xml文件中'<frame>'标签下，第一层'<definition>'中的定义; 去除标签；翻译为中文
- 框架关系：原.xml文件中'<frame>'标签下，关联其他框架的'<frameRelation>'
- 完成构建：./frame下有对应的名称的{框架名称}.py文件；是否完成标识Emoji: ✅ / ❌

## 索引表格
|框架名称|说明|框架关系|完成构建|
|:--|:--|:--|:--|
|Abandonment|代理离开一个主题有效地使它不再在他们的控制范围内或作为一个人的财产的正常安全。卡罗琳弃车跳上一辆红色双层巴士。也许他把钥匙留在了点火器里遗弃孩子在许多司法管辖区被认为是严重的罪行。也有比喻性的例子：她抛弃了她的老路。|Inherits from(Intentionally_affect)|❌|
|Abounding_with|位置被主题填充或覆盖。位置作为外部参数实现，主题作为PP补码，以with、in或的开头。注：本框架不包括像“铺面和未铺面道路”这样的形容词的使用，当它们只是指定某个地点的类型时，就像“铺面和未铺面道路”。海湾的水里盛产鱼群。海湾的水里鱼儿很多。道路完全被泥覆盖。|Inherits from(Locative_relation); Is Inherited by(Lively_place); Perspective on(Distributed_abundance); Uses(Abundance); Is Used by(Mass_motion,Expensiveness); See also(Distributed_position)|❌|
|Absorb_heat|一个实体（通常是食物）暴露给一个热源，它也可以指定温度。通常，实体作为这个过程的结果经历了某种变化。培根正在锅里煎，盘子里已经有一大堆鸡蛋冒着热气。如果它在400度煮一个小时，那它就会变成一堆灰！|Inherits from(Transition_to_a_quality)|❌|
|Abundance|在一个地方出现的集合的数量有一个特定的度量。集合的度量仅仅是指该度量如何从指定类型的集合的范数发散。度可以进一步细化度量与范数的关系。在融雪流淌的土地上，美丽无比。大气中充满了生命的碎屑。最近有一项发现，在太平洋海底几百米以下的岩石中盛产外来微生物。|Inherits from(Gradable_attributes); Is Inherited by(Scarcity); Is Used by(Abounding_with)|❌|
|Abusing|在这种情况下，施虐者反复以残忍和暴力的方式对待受害者，包括身体上的伤害或强迫受害者违背其意愿进行性行为。受害者通常缺乏反抗或还击的力量。可以指出滥用的类型。也可能有一个度。她的父亲辱骂了她的母亲。|Inherits from(Committing_crime); Uses(Cause_harm)|❌|
|Access_scenario|由于/尽管存在障碍，主题无法进入或访问Useful_location。|Is Perspectivized in(Having_or_lacking_access,Openness)|❌|
|Accompaniment|在事件或关系中，共同参与者与参与者具有相同的角色。市长连同三名保镖和他的司机一起被杀。医生告诉我服用常规避孕药和新药结合，我的症状就会痊愈。|Inherits from(Relation)|❌|
|Accomplishment|在Agent对目标进行工作的一段时间后，Agent会设法实现该目标。目标可以是一个期望的状态，或者被概念化为一个事件。Jeremey乖乖地完成了这个任务。作为回应，首相只是列举了他在自由市场方面的成就。|Uses(Intentionally_act)|❌|
|Accoutrements|佩戴者佩戴的配饰是由某种材料制成的，可能具有某种风格。大部分配饰都是非必需品（服装）的物品。她头上戴着一顶黑色天鹅绒帽子。|Inherits from(Artifact); Is Used by(Wearing,Undressing,Dressing)|❌|
|Accuracy|Agent参与了一个活动，其成功程度取决于该活动的参数，该参数与一个或多个连续变量（例如，数量、位置、时间）的特定值集相匹配。代理人，或转喻为工具或手段行动，用活动中的地点、时间或数量与预期事件所必需的地点、时间或数量之间的实际或预期偏差来描述。朗维尤测距仪精确到每百码一英尺以内。他的估计偏离了一个数量级。叉车操作员的目标必须相当准确。每日测量的精度取决于许多因素。|Inherits from(Inclination); Uses(Success_or_failure,Measurable_attributes)|❌|
|Achieving_first|认知者将新的观念引入社会。很难想象如果没有爱迪生发明的灯泡，我们的生活会有多大不同。|Inherits from(Intentionally_create); Uses(First_experience); Subframe of(Product_development_scenario); Precedes(Product_development)|❌|
|Active_substance|物质会引起效果。该物质是通过被理解为针对效果的过程产生的。也可以给出组成物质的物质的名称。将变性gp160用作HIV感染患者的治疗剂的原理是增强免疫应答。喹诺酮类药物现在似乎是急性细菌性前列腺炎的首选抗菌药物。激素活性化学物质有可能造成显著的环境伤害。只有在药水喝完之后，有效成分才会形成。DNI沙林毒剂可能是化武垃圾场的剩壳。|Inherits from(Substance)|❌|
|Activity|这是持续性活动的抽象框架，在该框架中，Agent进入Activity的一个正在进行的状态，在一段时间内保持该状态，并通过完成或停止离开该状态。代理的活动应该是有意的。这个框架主要是为了继承普通的FE，并为Activity的开始、进行、完成或停止阶段提供框架结构，每个阶段都构成了这个框架的一个子框架。这个框架应该与Process框架进行比较。|Inherits from(Process); Is Inherited by(Apply_heat); Has Subframe(s)(Activity_finish,Activity_ongoing,Activity_ready_state,Activity_prepare,Activity_pause,Activity_stop,Activity_abandoned_state,Activity_done_state,Activity_paused_state,Activity_start,Activity_resume)|❌|
|Activity_abandoned_state|代理处于活动的未完成部分。|Inherits from(Process_uncompleted_state); Uses(Process_stopped_state); Subframe of(Activity); Is Preceded by(Activity_stop)|❌|
|Activity_done_state|座席已完成活动。我终于打扫完公寓了。10月前完成了新的西夫大道的建设。|Inherits from(Process_completed_state); Subframe of(Activity); Is Preceded by(Activity_finish)|❌|
|Activity_finish|代理完成了一个Activity，这个Activity就不能再逻辑上继续了。这个框架是Activity的一个子框架。詹森周日深夜完成了评卷工作。期末考试结束后，艾娃扔掉了她的笔记。|Inherits from(Intentionally_act,Process_end); Is Inherited by(Finish_game); Subframe of(Activity); Precedes(Activity_done_state); Is Preceded by(Activity_ongoing)|❌|
|Activity_ongoing|代理正在执行活动的部分，其中存在动态稳定性。曼尼没有注意到从窗前冲过来的人群，继续吃着他的午餐。继续实现梦想！|Inherits from(Process_continue); Is Inherited by(Retaining); Is Used by(Cause_to_move_in_place,Being_active,Lively_place); Subframe of(Activity); Precedes(Activity_pause,Activity_finish,Activity_stop); Is Preceded by(Activity_start,Activity_resume)|❌|
|Activity_pause|代理在活动过程中暂停。1992年，政府冻结了定居点建设，以促进和谈。解除核冻结被认为是必要的，以产生所需的电力。|Inherits from(Process_pause); Uses(Eventive_affecting); Subframe of(Activity); Precedes(Activity_paused_state); Is Preceded by(Activity_ongoing)|❌|
|Activity_paused_state|代理保持在活动的特定阶段，而不在活动中进行。|Inherits from(Process_stopped_state); Subframe of(Activity); Precedes(Activity_resume); Is Preceded by(Activity_pause,Activity_stop)|❌|
|Activity_prepare|Agent为Activity做准备。部队正在为任务做准备。船只正准备离开码头。|Is Perspectivized in(Preliminaries); Uses(Eventive_affecting); Subframe of(Activity); Precedes(Activity_ready_state)|❌|
|Activity_ready_state|主角处于初始状态，在开始参与Activity之前，但Activity执行的所有前提条件都已满足。在许多情况下，主角是一个有意的代理人，但也有其他用途，在这种情况下，代理人是一个对活动至关重要的实体。或者，Activity可以用Salient_entity来表示，Salient_entity代表Activity。这个Salient_entity也可以是意向代理，但不必是。她还没准备好！我想他已经准备好开口了。英国政府准备好在护照-身份证上大转弯了吗？看看萨尔是否准备好去浴缸了。世界终于为他准备好了！|Inherits from(Process_initial_state); Is Inherited by(Be_on_alert); Is Used by(Standing_by); Subframe of(Activity); Precedes(Activity_start); Is Preceded by(Activity_prepare)|❌|
|Activity_resume|Agent恢复参与Activity。活动的进度从中断前开始保留。将很快恢复正常服务。金沙萨政府恢复支持卢旺达反政府武装。|Inherits from(Process_resume); Subframe of(Activity); Precedes(Activity_ongoing); Is Preceded by(Activity_paused_state)|❌|
|Activity_start|代理发起正在进行的活动的开始，他将持续参与其中。与此同时，城邦在希腊大陆南部的影响力开始增长。很自然，我开始哭着离开工作。|Inherits from(Process_start); Uses(Eventive_affecting); Subframe of(Activity); Precedes(Activity_ongoing); Is Preceded by(Activity_ready_state)|❌|
|Activity_stop|代理在未完成活动的情况下终止活动。在这场诉讼之后，该公司停止了生产这个曾经非常有利可图的玩具。1988年9月，橄榄球俱乐部终止了与阿盖尔的谈判。|Inherits from(Process_stop); Is Inherited by(Halt); Uses(Eventive_affecting); Subframe of(Activity); Precedes(Activity_abandoned_state,Activity_paused_state); Is Preceded by(Activity_ongoing)|❌|
|Actually_occurring_entity|在上下文显著的非现实世界的背景下，例如假设的、想象的、模拟的、预期的、投影的或梦想的世界，在现实世界中的关系或事件中遇到的类型的实例被呈现为不同于在非现实世界中发现的实例。当然，预期类型的真实世界实例也可能呈现为未发生，如下面的最后一个示例。实际结果可能会有所不同。实际结果可能会有所不同。在场的还有实际的警察，他现在年长20岁，正在帮助选角和准备将在银幕上扮演他的年轻演员。在场的还有这位现年20岁的警察，他正在帮助选角和准备这位将在银幕上扮演他的年轻演员。当然，具备所有这些功能的实际汽车根本不存在。当然，具备所有这些功能的汽车根本不存在。|Inherits from(Entity)|❌|
|Addiction|这个框架涉及瘾君子对瘾君子、瘾君子成瘾的物质或行为的生理或心理强迫依赖。虽然她从来不是毒品的忠实粉丝，但她立刻就迷上了那种名牌毒品。他是个可卡因瘾君子。街对面的房子里住着一些可卡因瘾君子。|Inherits from(Gradable_attributes)|❌|
|Adding_up|Cognizer在输入数字的基础上通过加法计算出结果。把你的积蓄加起来。这是通过将治疗特定疾病的费用相加而得到的累计数字。后来，当他不厌其烦地把账单加起来时，他发现实际花费是1481法郎，大约140英镑：多收了40英镑，学校舞会上售出的门票数量超过1000英镑。|Uses(Amounting_to)|❌|
|Adducing|发言方提到了填充角色的Specified_entity，从而提供了支持发言方观点的信息。他引用了达尔文引证的主要原始观察作为他的理论的证据。墨西哥指出，干旱已进入第八年，以避免从水库中释放德克萨斯州每年1100亿加仑的全部水量。反对者会立即指出这种简单的，有人会说是头脑简单的，等级制度缺乏稳定性。她原以为他们的会面地点是餐厅，但这位女士却给她下榻的酒店起了名字。DNI二阶神经模式位于哪里？达马西奥在他1994年的著作中已经指出了扣带皮层。|Uses(Statement); Is Used by(Reference_text)|❌|
|Adjacency|地图位于地附近。这相当于图和地构成或与一个区域相关联，每个区域与另一个区域接触。这两套房子是相邻的，所以她一起买了。与她相邻的卧室要小得多。公园与一个非常高档的社区接壤。焊接时，请确保相邻引脚不会过热。DNI本框架旨在涵盖富有成效的隐喻案例，例如在“相邻网页”中发现的那些——指那些通过共享超链接而隐喻“共享边界”的页面，以及许多以其他方式认知关联的实体的其他案例。还有一些不那么富有成效的隐喻也打算被包括在这个框架中，例如，“近乎疯狂的行为”、“洁癖仅次于敬虔”，尽管传统上我们不认为“近乎疯狂”等。尽管这些表达听起来很有创意，它们是可以立即理解的，在上下文中没有异议的。|Inherits from(Locative_relation)|❌|
|Adjusting|代理改变一个复杂实体中关于某些特征的一部分，以达到某些受特征影响的目的。复杂实体通常是一个设备或机制，但也可能是一个抽象实体，如经济。此外，完整的实体可以用来代替部分。她来的时候我需要把恒温器调到80度左右。第一次没用，所以她不得不稍微调整一下烤箱。格林斯潘表示相信，目前的利率调整并不是一种过度补偿。|Inherits from(Intentionally_affect); Uses(Cause_change)|❌|
|Adopt_selection|代理有一个属性，它可以接受不同的值，代理选择并开始为该属性使用某个值。属性包括物理（形状、颜色）和抽象（信念、实践）类型。对于这个框架中的一些LU，通常只需要表示Value，而Attribute是隐式的。（通常这种隐性属性可以在值上被赋予第二层表达。请注意，在下面的前两个示例中应该假定这样的第二层注释。）他们嘲笑他们的对手，并假定一种优越的知识的架势。有时，在讨论道德争议性问题时，教师应该采取中立的立场。一个人不必做出“我将此作为我的立场”的声明来这样做。|Uses(Choosing)|❌|
|Aesthetics|一个实体被判定为在感官上令人愉悦或智力上令人感兴趣的（通常是含蓄的）法官。我们几次看到这艘挂着红帆的漂亮船。我们在海滩上露营，清晨在农田里散步，非常愉快。|Inherits from(Desirability); Is Used by(Artistic_style)|❌|
|Affirm_or_deny|说话者使用语言向某些收件人肯定或否认信息的真实性。代替（或除了）说话者之外，也可以提到媒体。同样，也可以声明一个Topic而不是Message。她肯定了自己对事业的忠诚。他否认他曾经相信上帝的存在。BBC新闻证实了有关难民的说法。|Inherits from(Statement)|❌|
|Age|一个实体已经存在了一段时间，即时代。年龄可以被描述为年龄属性的值，或者程度修饰符可以表示年龄与标准的偏离。表达者展示了实体时代的品质。这栋建筑有两万年的历史了。我爷爷真的很老了小弟才5周大。人群中传来一个狡诈的老声音。他当时的年龄是23岁。55岁或以上的人应咨询医生。我有一个13岁的表弟我奶奶老了，这个框架中的LU出现了一些额外的模式，这些模式不是由特定的词头授权的，而是由结构授权的。此外，还有一些模式可以唤起这个框架，而没有任何公开的词法头，这些都是这个框架的一部分。她今年45岁。比利13岁。|Inherits from(Measurable_attributes); Is Used by(People_by_age,Aging)|❌|
|Aggregate|此框架包含表示个体的集合的名词。Aggregate可以通过Aggregate_property来描述。一大群邮政工人涌向我的办公室。|Is Inherited by(Store,Organization,Entourage,Convoy,Product_line,Team)|❌|
|Aging|一个实体正在经历年龄的变化，通常伴随着某种退化或状态的改变。这种树皮老化变黑。美国将以先进技术升级老化的导弹防御系统。|Inherits from(Eventive_affecting); Uses(Age)|❌|
|Agree_or_refuse_to_act|发言人要么同意，要么拒绝参与对话者提出的提议行动。他们同意在今天的报纸上发表社论来表达他们的愤怒。车祸发生后，该男子拒绝接受血液，严重妨碍了他的治疗。|Inherits from(Respond_to_proposal)|❌|
|Agriculture|在这个框架中，农学家种植食物。农业者种植粮食的地点或土地常被表示为。鼓励农民种植豆类、玉米等基本粮食作物。养虾似乎是灾难的良方有些田地可能只在旱季耕种|Inherits from(Attempt_obtain_food_scenario); Is Perspectivized in(Growing_food); Has Subframe(s)(Planting,Food_gathering)|❌|
|Aiming|Agent调整Instrument，使其能够与难以访问的Target_location直接交互。通常，在Target_location有一个Targeted实体，它在它的位置被提到。如果你把武器瞄准别的地方，我就更有可能开口了。此次出击的目标主要是再补给点，但其中包括几个平民区。一个好的射手在每次射击前仍应瞄准片刻。INI INI|Inherits from(Manipulation); Subframe of(Attempt_distant_interaction_scenario); Precedes(Hit_or_miss)|❌|
|Alignment_image_schema|对齐匹配区域与相对线性的地面具有相同的方向。对齐_不匹配区域垂直于地面定向。|Inherits from(Image_schema)|❌|
|Alliance|在分开工作一段时间后，两个或两个以上的组织成员或个人成员现在被组织成一个联盟，以便他们可以更好地追求一些共同的目标。以前单独的成员可分别作为成员_1和成员_2提出。他们组成了一个松散的联盟。|Uses(Organization,Competition)|❌|
|Alternatives|存在着许多可能在未来发生的不同情况。（在某些情况下，情况是同时发生的或过去的，只有对已经发生的情况的知识是在将来发生的）。在大多数情况下，有一个代理人参与，他必须考虑哪些可能的情况将或应该发生。还可以提到与情况深度相关的突出实体。你对你女儿只有两个选择。虽然这个框架的所有成员都表示可能的情况，但原则上，这个框架可以在以下基础上分为多个子类型：1。Future.n，以及大多数的替代性.n和可能性.n的使用都只是一个简单的可能情况（不一定是一个情况），没有代理；其余的框架将从这个继承。2. Use.n唤起了用Salient_entity（即目的）可以做的不同可能的事情，因此使用Use框架；在这个框架中，目标表示可以实现的目的。3. way.n唤起可能导致结果（不一定是目的）的不同事件；此框架应使用Means框架。在此帧中，目标表示可能的方法操作。4. option.n、Choice.n以及其他的许多情况，都会唤起一个隐式或显式的Agent可以随意带来的可能的情况。可以提到实现这些情况所能达到的目的。与目的相关的突出实体可以代替目的出现。|Perspective on(Alternativity); Is Used by(Time_period_of_action,Opportunity)|❌|
|Alternativity|在这个框架中，有一个说话者希望主要关注的Profiled_alternative，它与Objecting_alternative是互斥的。两者在相同的参与者的同一上下文中都是不可能成立的，尽管所描述的情况可能在不同的时间对相同的实体是成立的，或者在同一时间对不同的实体是成立的。从这个框架继承的框架（例如否定）可能表明哪一个备选方案是假设的情况，但在与这个框架相关的其他框架（例如Conditional_scenario和替代品）中，两个备选方案都被表示为可能，而哪一个是真的仍然是一个悬而未决的问题。|Is Inherited by(Negation,Conditional_scenario); Is Perspectivized in(Alternatives,Presentation_of_mitigation); Is Used by(Causation_scenario)|❌|
|Amalgamation|这些词指的是部分合并形成一个整体。（部分也可以编码为Part_1和Part_2）。经历过程的各部分之间存在对称关系，之后部分被消耗，不再是在整体中容易识别或可分离的不同实体。两个水滴融合，然后更快地沿着窗玻璃向下传播。|Inherits from(Reciprocality)|❌|
|Amassing|一个接收者（可能是也可能不是代理人）最终拥有一个质量主题（它可以被概念化为单个质量实体，也可以是一组单独的实体）。一些词汇单位（例如库存）专门表示有意的接收者。这个框架与聚集_up的区别在于，这个框架特指实体的获取和（根据预期）长期占有，而不是（如聚集_up框架中）简单地谈论使一组实体位于同一个地方。总之，聚集关注的是（共同）地点，而聚集关注的是拥有。沼泽积碳达数千年之久。|Inherits from(Getting)|❌|
|Ambient_temperature|特定环境下的温度，由时间和地点决定。今天太热了，什么都做不了。每年的这个时候诺姆都很冷上周二真是酷热难耐。明天会很冷。我不能在寒冷中出去。DNI DNI|Inherits from(Temperature)|❌|
|Ammunition|弹药是一种一次性的人工制品，可作为武器中的射弹发射，目的是造成伤害或破坏。这位八十岁的发明家的背心可以抵御穿甲弹。它装备有自动上膛的105毫米火炮，发射反坦克子弹，贫铀弹主要由美国和英国使用。|Inherits from(Artifact); Uses(Weapon)|❌|
|Amounting_to|项目的可量化属性的绝对值是通过将组成项目的个体或部分的属性值相加来确定的。项目不被表示为一个单独的组成部分，但它被属性的概念所预设。或者，数字构成一个隐式集合，其和是与该集合关联的值。在某些情况下，报告的只是构成项的个体的基数，因此实际上值是一个计数。在其他情况下，只能从值推断属性的身份。在这一帧中，现场没有认知者。相反，框架关注的是属性或数字和值之间的关系，无论谁执行计算，这些关系都是稳定不变的。在西德，国防是由武装部队提供的，其人数总计接近50万男女。世卫组织估计，艾滋病累计病例超过150万例。|Is Used by(Adding_up)|❌|
|Animals|本框架中的LU是指除人和植物以外的生物实体，由FE动物标记。我和老公去年收养了一只非常可爱的狗。住在路边农场里的奶牛总是在大声地叫着。|Inherits from(Biological_entity)|❌|
|Annoyance|体验者、表达者或状态有一种被刺激物或与主题有关的烦恼感。佩克被打断了很恼火。玛姬注意到他相当恼火的表情。|Inherits from(Emotions_by_stimulus)|❌|
|Appeal|在刑事诉讼的上诉阶段，罪犯或其代理人以某些理由向上级法院申请推翻下级法院的判决。辩方计划以法官违反法典81.b为由，对法院的判决提出上诉。约翰·迈克尔斯将对他的定罪提出上诉。|Uses(Criminal_process)|❌|
|Appellations|此框架仅适用于用作个人标题的单词。爵位用于一个名字（姓氏或全名），通常指定他们在人为机构内的地位（如酋长、国王、主教、兄弟）或一般社会地位（先生、小姐），也可能表示亲属关系（堂兄、姑姑）。标题和名称的成对可以用作呼语（请参阅关注_获取），而标题本身不一定总是呼语。他向迈斯特将军敬礼，他走进房间。杰克·奥布里船长致祝酒词时，所有人都起立。最高法院首席大法官约翰·罗伯茨坚持自己的立场。1980年美国冰球队队长迈克。埃鲁齐奥内今天满58岁。这个框架的大多数LU与领导或亲属关系框架的LU有关，但有些（如女士、先生、兄弟）只在这里出现。这些LU不同于领导力或亲属关系中正常的LU示例，因为LU简单地用作呼号词或名称的修饰语，以表明个人如何适应一般或特定的社会背景。|Inherits from(Being_named); Uses(Rank); See also(Kinship,Leadership)|❌|
|Apply_heat|厨师将热量应用于食物，其中可以指定热量的温度设置和应用的持续时间。通常用定位词组表示，也可以用定位词组表示。一些烹饪方法涉及使用一种介质（如牛奶或水），通过这种介质将热量传递到食物中。语义上不那么突出的食物或厨师被标记为共同参与者。萨莉用黄油煎了一个鸡蛋。莎莉在特氟龙平底锅里煎了一个鸡蛋。艾伦用切好的西红柿和大蒜煎蛋。此框架与烹饪创建的不同之处在于，专注于处理食材的过程，而不是该过程产生的可食用实体。|Inherits from(Intentionally_affect,Activity); Is Used by(Cooking_creation); Is Causative of(Absorb_heat); See also(Cooking_creation)|❌|
|Appointing|选择者（通常是担任领导角色的个人）任命官员在组织（可以表示为主体）中担任正式角色。新闻秘书授权记者参加会议。|Inherits from(Intentionally_affect); Is Inherited by(Change_of_leadership)|❌|
|Architectural_part|一个实体作为一个（可能是未表达的）整体的一部分集成到建筑物中，该整体可以指整个建筑物，也可以仅仅指建筑物的一个子部分。我们需要厨房的新台面。暴风雨把浴室的屋顶刮掉了。|Inherits from(Shaped_part); Is Inherited by(Connecting_architecture)|❌|
|Arithmetic|此框架描述了一种特定类型的数学场景，其中两个数字（标记为Term1和Term2）通过一些数学运算进行交互。|Inherits from(Reciprocality); Is Inherited by(Arithmetic_commutative,Arithmetic_non-commutative,Mathematical_relationship)|❌|
|Arithmetic_commutative|此框架描述了具有交换性质的算术运算和语句的类型，即运算是双向的，例如加法和乘法。所涉及的术语要么分别标记为Term1和Term2，要么组合为标记为Term的单个名词短语。|Inherits from(Arithmetic); Is Perspectivized in(Commutative_process,Commutative_statement)|❌|
|Arithmetic_non-commutative|这个框架描述了算术运算和语句的类型，它们不是交换的，即运算是单向的，例如减法和除法。由于不可交换的性质，项必须以术语_1和术语_2的形式相互分离，而不是组合的术语FE。|Inherits from(Arithmetic); Is Perspectivized in(Non-commutative_process,Non-commutative_statement)|❌|
|Armor|一种资产，其安全是可取的，由一个覆盖物，即装甲来保护其免受损坏。装甲覆盖部分或全部资产，旨在吸收来自迎面而来的危险的力量。他们除了原始的木制盔甲什么都没有穿。士兵的防弹装甲提供了额外的安全级别。|Uses(Protecting)|❌|
|Arraignment|在法庭审理中，被告被告知对他或她的指控，（通常）进行答辩，如果有的话，由法官决定保释金的数额。莫蒂默和伊莎贝拉于11月被匆匆离开，并在议会传讯。如果法院驳回上诉，这19名年轻男子将在南部城市哈科特港面临以谋杀罪名的法庭提审。|Inherits from(Process); Subframe of(Criminal_process); Has Subframe(s)(Bail_decision,Notification_of_charges,Entering_of_plea); Precedes(Trial); Is Preceded by(Arrest)|❌|
|Arranging|Agent将一个复杂的主题放入特定的配置中，该配置可以是一个正确的顺序，一个正确或合适的顺序，或者一个空间位置。他将元素排列成我们现在称之为周期表的图案。尽量按重要性排序。|Inherits from(Intentionally_affect); Uses(Placing)|❌|
|Arrest|当局指控一名涉嫌犯罪的嫌疑人（指控），并将他/她拘留。警方以过失杀人罪逮捕了哈里。|Inherits from(Intentionally_affect); Uses(Inhibit_movement); Is Used by(Surrendering); Subframe of(Criminal_process); Precedes(Arraignment)|❌|
|Arriving|物体在目标的方向上移动。目标可以表达，也可以从上下文中理解，但它总是由动词本身隐含。星期天，一些学生来到学校。正是他在837年到达奈梅亨，使得维京人撤退。|Inherits from(Eventive_affecting); Is Inherited by(Visiting_scenario_arrival,Vehicle_landing); Is Used by(Having_or_lacking_access); Subframe of(Traversing); Is Preceded by(Departing)|❌|
|Arson|行为人故意纵火焚烧自己或他人的财产，通常是为了收取该财产的保险金。两名男子被控纵火罪。|Inherits from(Offenses); Uses(Intentionally_affect,Setting_fire)|❌|
|Artifact|Artifact是由一个智能实体故意制造或修改的，以用于某种用途。可以指定工件的各种属性，例如它的创建者、创建时间、名称、类型以及组成工件的材质。Artifact可以是物理实体，也可以不是物理实体。有报道称，金日成要求中国分享其核武器技术。|Inherits from(Entity); Is Inherited by(Weapon,Connectors,Clothing,Accoutrements,Law,Buildings,Noise_makers,Ammunition,Fastener,Infrastructure,Vehicle,Body_decoration,Text,Money,Information_display,Controller_object,Key,Medical_instruments,Physical_artworks,Fire_break); Uses(Using); Is Used by(Gizmo,Being_operational); Has Subframe(s)(Artifact_subpart)|❌|
|Artifact_subpart|一个Component在复杂的Artifact的操作中具有独特的功能，除非它是由许多不同的Component组装而成，否则它不被认为是完整的。每个组件也可以用它们的创建者、创建时间或材料来描述。大部分成本来自于发动机零部件的价格。我们需要找到一个1982年的金属零件。|Subframe of(Artifact)|❌|
|Artificiality|在其类别成员身份可疑的上下文中，评估实体是否属于特定Reference_category。与评估Reference_category成员资格相关的一个或多个标准取决于各个词法单元和/或上下文。通常，实体的物质构成、其创建方法或其创建者的身份（和适当的权威）对于适当的类别成员资格至关重要。请注意，Entity也涵盖了行为。在发现你花了几百或几千美元买了假签名之后，要想把钱要回来可能会很困难！当你发现你花了几百或几千美元买了一张BOGUS签名时，要想把钱要回来可能会很困难！一名假警察拦下一辆载有四名真警察的汽车后，将其拦下。BOGUS的一名警察在拦下一辆载有四名警察的汽车后，将汽车靠边停车，被逮捕。如果你们认为你们有证据证明登月是假的，那你们就大错特错了。如果你们认为你们有证据证明登月是假的，那你们就大错特错了。|Inherits from(Gradable_attributes); Is Used by(Forging)|❌|
|Artistic_style|此框架包含LU，这些LU表示一件Artwork所代表的形式。形式也可以代表艺术家作品的整个主体。形式可以进一步通过某些艺术品的创作时间或其他描述符来表征。她的画风是传统与现代的完美融合。这件作品的奇思妙想风格非常有效。|Uses(Aesthetics)|❌|
|Assemble|在这个框架中，一群个体有意地走到一起，形成一个组。或者，在语法上更突出的Party_1与Party_2组合在一起，表示为一个倾斜短语。如果选择了这种不对称的解释，则目的只与第_1方有关。我们聚集在院子里，谈论我们未来的计划。我们的学习小组今天在外面开会。道奇队明天在道奇体育场迎战旧金山巨人队。|Inherits from(Come_together,Intentionally_act); Precedes(Meet_with)|❌|
|Assessing|评估者根据该现象的某些特征来检查该现象，以确定其价值。这个值是决定现象的可接受性的一个因素。在某些情况下，使用方法（包含评估者）来确定现象的值。然后对每家公司的盈利潜力进行评估。CNI从试点研究的证据来看，对试验对象造成损害的风险被认为过高，无法继续进行。他仔细权衡了自己的选择。|Inherits from(Cogitation)|❌|
|Assigned_location|一个人被分配一个待在的地方，通常是为了完成一项任务。车站可能根据其特征（例如，供应商的摊位）具有预期用途，也可能临时分配用途。留在驻地的警卫不知道下面两层楼发生了什么。回到你的岗位！|Inherits from(Locale); Uses(Being_obligated)|❌|
|Assistance|帮助者通过实现受益方拥有的目标而使受益方受益。一个参与实现目标的实体可以代替它。此框架具有独特的帧到帧关系：它继承自并使用Intentionally_act框架。这是FrameNet的框架关系的非典型。你会帮政府找到你哥哥吗？也许斯蒂芬应该协助他完成最后的手稿。他们从心理上帮助我克服了我所遭受的身体上的损失。你向他展示了如何为自己挺身而出，并成为他的朋友，给了他巨大的帮助。他把援助带给他的军队，使他们在任何地方遇到困难，他大大地帮助了他们。|Inherits from(Intentionally_act); Is Inherited by(Supporting); Uses(Intentionally_act)|❌|
|Asymmetric_reciprocality|关于主角_1作用于主角_2或与主角_2有关的互惠性的观点。关系或事件被解释为不对称的，因为主角_1被表示为更有代理性，如果代理参与（如在对话中，参与），而主角_2被表示为更有被动性。在比较或其他关系（例如相似、接近）的情况下，Protagonist_2被解释为适合作为Protagonist_1的参考，通常是因为Protagonist_2在时间上更稳定和/或更显著和更广为人知。|Perspective on(Reciprocality)|❌|
|Atonement|代理人过去犯了错误，现在正在进行修正。也可以表示修正的充分程度。他以善行赎罪。|Inherits from(Intentionally_act); Uses(Forgiveness)|❌|
|Attaching|连接框架包括两种情况：一种是某人导致一个事物与另一个事物物理连接的场景，另一种是某人导致两个事物相互连接的场景。在第一个框架中，该框架包括一个代理，它通过操纵连接器将项目附加到目标，在项目和目标之间创建非对称关系。在第二种中，代理将两个项目相互连接，其中每个项目作为另一个项目的目标，在两个项目之间创建对称关系。在这两种情况下，Connector仍然是绑定两个实体（或Item和Target，或两个Item），而不创建一个新的实体。强盗把哈利绑在椅子上。一定要把他的手腕绑得越紧越好。|Inherits from(Intentionally_affect); Is Used by(Connectors); Is Causative of(Becoming_attached)|❌|
|Attack|攻击者对受害者（通常但不总是有知觉的）进行人身攻击，造成或意图造成受害者身体伤害。除了通常的地点、时间、目的、解释等之外，攻击者使用的武器也可能会被提及。有时，地点被以转喻的方式用于代表攻击者或受害者，在这种情况下，地点FE将被注释在第二个FE层上。他一走出酒吧，就被四个戴滑雪面具的男人撞上了。他入侵伊拉克只是为了掩盖其他缺点吗？然后，乔恩-奥的部队从一排低山丘陵伏击了他们的左翼。|Inherits from(Intentionally_affect); Is Inherited by(Besieging,Invading,Suicide_attack,Counterattack); Perspective on(Hostile_encounter); Is Used by(Defending)|❌|
|Attempt|Agent试图实现一个目标。结果也可以明确提及。约翰试图爬山。珠穆朗玛峰。这是攀登珠穆朗玛峰的又一次失败的尝试。|Inherits from(Intentionally_act); Is Inherited by(Work,Attempt_suasion); Perspective on(Attempt_action_scenario); See also(Attempt_means)|❌|
|Attempt_action_scenario|此框架表示尝试的核心动作，其中Agent有一个目标，并执行他们认为将实现目标的某些手段动作。有关更多信息，请参阅其两个透视帧。|Is Perspectivized in(Attempt,Attempt_means); Subframe of(Attempting_and_resolving_scenario); Precedes(Result_of_attempt_scenario)|❌|
|Attempt_distant_interaction_scenario|智能体尝试使用某种工具（可能是身体部位，例如手）与相对较远或间接可达的目标进行交互。Agent操纵仪器并将其置于目标位置的能力是个问题。最常见的远距离交互类型包括智能体试图通过弹道方式移动仪器以使其与目标接触（例如，射击场景），或者智能体试图指挥仪器以使目标位置的感知能够被检查。|Inherits from(Attempting_and_resolving_scenario); Is Inherited by(Shooting_scenario); Uses(Manipulation); Has Subframe(s)(Aiming,Hit_or_miss)|❌|
|Attempt_means|Agent试图使用某些手段来实现目标。约翰试图用撬棍开门。他们试图打开窗户以抢劫商店。通常情况下，参与“手段”行动的实体代表“手段”，类似地，“目标”可以用与“目标”情况相关的实体转喻来表示：约翰在门上试了一根撬棍。他们试图通过窗户来抢劫商店。与尝试框架不同，“手段”侧重于“手段”，而“目标”往往是隐含的。这个框架回答的问题是如何尝试某事，而不是正在尝试什么。通过用“给X一个尝试”来解释句子，可以最可靠地区分这些帧，因为“给尝试”只属于这个帧。|Inherits from(Using); Perspective on(Attempt_action_scenario); See also(Attempt)|❌|
|Attempt_obtain_food_scenario|一个寻找者正在尝试获取食物，并在地面的上下文中寻找食物。|Inherits from(Attempting_and_resolving_scenario); Is Inherited by(Hunting_scenario,Agriculture)|❌|
|Attempt_obtain_mineral_scenario|代理人试图获得不可再生资源，通常是固体矿物或金属，但也包括油、水和其他有价值的物质。|Inherits from(Attempting_and_resolving_scenario); Is Inherited by(Mining)|❌|
|Attempt_suasion|说话者通过语言表达他的愿望，使收件人以某种有助于促成内容中描述的事件或状态的方式采取行动。并不意味着受送达人形成行为的意思表示，更谈不上行为。史密瑟斯先生总是鼓励员工们加班加点工作。丹尼斯·罗德曼建议在任何事情上都要适度。最典型的内容是指收件人将自己执行的行动，但（在非限定内容从句的配价的情况下）可能只是指他们有间接影响的情况，如下面的情况。当我和她谈话时，我建议把他撤职。|Inherits from(Attempt); Uses(Communication,Subjective_influence); Is Used by(Suasion)|❌|
|Attempting_and_resolving_scenario|智能体心中有一个特定的目标，然后使用一些他们认为会实现目标的手段。只要手段动作的结果与目标匹配，代理就会成功或失败。|Inherits from(Intentionally_act); Is Inherited by(Attempt_distant_interaction_scenario,Attempt_obtain_food_scenario,Attempt_obtain_mineral_scenario); Has Subframe(s)(Result_of_attempt_scenario,Attempt_action_scenario)|❌|
|Attending|Agent以一种相对非参与性的方式进入Event。安哥拉游击队将参加9月在扎伊尔举行的会议。下雨的时候我们就去看电影。他出席葬礼并没有被忽视。|Inherits from(Intentionally_act)|❌|
|Attention|这个框架涉及到感知者处理和考虑在地面中的图形印象的准备状态。感知者往往不知道该图形是否存在于地面中。或者，表达者可以被表示为表现出感知者的专注状态的迹象。立法者提醒消费者警惕二恶英含量。他们需要一个专注的凝视，一个仔细的计算部分。|Inherits from(State); Is Used by(Searching_scenario,Perception_active,Emotions_of_mental_activity)|❌|
|Attention_getting|这个框架涵盖了用来引起某人注意的术语，包括感叹词（例如，嘿，哟）和某些地址术语（Address_term），后者可以起到引起注意的功能。嘿。嘿，孩子。嘿，孩子，快过来！|Uses(Referring_by_name)|❌|
|Attitude_description|这个框架中的词汇单位是一个认知者对某一事件的态度或看法的描述。卡尔对谈判的态度越来越悲观。无知的好处来自于生活在一个人们对生活持乐观态度的社会中。在很多情况下，State_of_affairs可以在没有Cognizer的情况下进行表达，如下所示：目前形势相当严峻。|Inherits from(Social_behavior_evaluation); Uses(Emotions)|❌|
|Attributed_information|命题归属于说话者或文本。据印度报业托拉斯周四在其网站上发表的一篇文章称，这名女子被确认为31岁的Aafia Siddiqui，上周他和另外两名男子一起被美国官员追捕，其中一名男子的最后已知住址是佛罗里达州米拉马尔。此外，根据第I3.5b节，支柱剪力连接件沿支承梁长度的间距不得超过36？根据教皇的说法，穆斯林信仰同一个上帝，根据耶稣的说法，穆斯林是天堂中最伟大的。|Uses(Statement)|❌|
|Attributes|实体具有具有某些值的特定属性。这个框架主要是为了继承。|Is Inherited by(Scope,Gradable_attributes,Race_descriptor)|❌|
|Authority|代理具有沿着特定域的线路影响主题的手段。在某个领域内，存在着影响力或权力的不平衡，倾向于代理（通常由于某些来源）而非主题。他对臣民的权威是上帝赋予他的。国会有权制定法律。只有国王有权宣战。|Inherits from(Influencing_potential)|❌|
|Avoiding|Agent在某些情况下避免了不受欢迎的情况。这种情况可能是一种活动（例如上学），也可能是这种活动或情况的转喻（例如路边摊）。在这个框架中，从行为者的角度来看，这种情况是不受欢迎的（例如逃避），并且与这种情况对其他人是特别不受欢迎的（例如忍让）或从外部道德的角度来看（例如弃权）的场景形成对比。迈克不惜一切代价避开他的上司。|Inherits from(Intentionally_act); Is Inherited by(Evading,Dodging)|❌|
|Awareness|Cognizer在他们的世界模型中有一段内容。内容不一定是由于即时感知而存在的，而通常是由于从感知中的演绎而存在的。在某些情况下，内容的推演隐含地基于对信息来源的信心（相信），在某些情况下基于逻辑（思考），而在另一些情况下，推演的来源被揭秘（知道）。你的老板知道你的承诺。请注意，这个框架正在经历某种程度的重新考虑。许多目标将被移动到意见框。该框架表明认知者认为某件事是真实的，但意见（相对于内容）并不是预设为真实的；相反，它被认为是一个潜在的差异点，如下面的：我认为你是真棒。然而，在将保留在感知框架中的使用中，内容是预设的。这个框架也不同于确定性框架，因为它不描述Cognizer与内容的关系，而是预设它。在确定性中，信心或确定性的程度可以表达为一个单独的框架元素，例如：她绝对知道他将在那里。|Inherits from(Mental_activity); Is Inherited by(Grasp,Expectation); Perspective on(Awareness_situation); Uses(Information); Is Used by(Religious_belief,Secrecy_status,Examination,Certainty,Remembering_information,Fame,Representing,Impression); See also(Opinion,Certainty)|❌|
|Awareness_situation|Cognizer通过演绎、推理或类似的方法从可感知物中获得信息，在他们的世界模型中具有一段内容。|Is Perspectivized in(Awareness); Is Used by(Awareness_status)|❌|
|Awareness_status|一些内容是认知者心智模型的一部分。认知者不是通过直接感知，而是通过对感知现象的推理来达到心智模型。或者，已知特定对象的角色适用于该对象。这个事实是很多人都知道的。据推测的凶手最后一次被看到是在州际公路上向南行驶。|Uses(Awareness_situation)|❌|
|Bail_decision|这一框架涵盖了刑事诉讼过程中的一个步骤，在这个步骤中，法官决定被告是否应该被保释，如果应该，保释金的数额应该是多少。挪威格里姆斯塔德的托尔森获准10万美元保释，直到6月18日。他被提赛德地方法官批准有条件保释。|Inherits from(Intentionally_act); Uses(Communication); Subframe of(Arraignment); Is Preceded by(Entering_of_plea)|❌|
|Basis_for_attribute|对于确定或传达有关轨迹的类似类型的信息来说，关于地标的一段信息更易访问和有用。在这种情况的解释中，有一个（更多）轮廓化的元素，即轨迹，和一个未或更少轮廓化的元素，即地标。结合示意图定义的Profiled_region（具有与地标的预定义关系），地标作为理解轨迹的状态或位置的基础。棚子里的猫猛烈地咕噜着。猫周围的棚子晃动着。我们必须在中午之前离开。不过，在20世纪90年代，DNA被读取的速度加快到了高速度。|Inherits from(Relation); Is Inherited by(Locative_relation,Time_vector,Temporal_collocation)|❌|
|Be_in_agreement_on_action|两个（或更多）人（双方，也可编为第1方和第2方）有一个协议。双方都被理解为对某一义务的承诺，这种关系被理解为是对称的或对等的。可以使用主题表达式来指示所覆盖的领域，而不是具体提到义务。美国和俄罗斯达成协议，共享导弹发射的早期预警数据。|Is Inherited by(Having_commercial_agreement); Uses(Make_agreement_on_action)|❌|
|Be_in_agreement_on_assessment|认知者在他们的观点中具有相似性（或不相似性）。Cognizers可以单独表示，Cognizer_2是建立Cognizer_1的基础。而不是具体的意见，可以指定对其持有类似或不同意见的现象，即主题。当认知者的意见被理解为对问题的回答时，特定的意见也可以不被提及。格里博士和庞德先生的印象一致。这个文案编辑和我在事情上的看法大多是一致的。我同意你的观点，所有的事情都应该被监控，以防止这个人浪费时间，保护公司的利益。|Inherits from(Similarity); Uses(Opinion); Is Used by(Quarreling,Point_of_dispute)|❌|
|Be_on_alert|主角已经意识到可能的危险（危险事件或可能参与对主角有害的事件的危险实体），并准备好参与应对该危险的活动。在附近的一个大院遭到袭击后，所有部队都处于高度戒备状态，以防范可能的入侵者。我们处于警戒状态以阻止任何试图潜入的人。我们要警惕可能的破坏。|Inherits from(Activity_ready_state)|❌|
|Be_subset_of|Part被认为是由Total描述的集合的成员。Part和Total子集-超集之间的关系，而不是part-整体（就像在Part_whole和include框架中一样）。尼尔森医生是世界上最重要的人吗？最重要的岩土工程专家。餐厅-Pizzeria Dante是佛罗伦萨为数不多的几家餐厅之一，在这里你可以找到典型的托斯卡纳菜肴和鱼类菜肴以及一流的披萨。|Inherits from(Being_included); Is Inherited by(Membership); Perspective on(Set_relation)|❌|
|Be_translation_equivalent|在表示特定内容的能力方面，Target_representation系统中的Target_symbol与Source_representation系统中的Source_symbol是等价的。就业地区一词翻译为法语的区d'emploi。就业地区一词翻译为法语的区d'emploi。该术语翻译为俄语raznorechie（字面意思为“异语”）。该术语翻译为俄语raznorechie（字面意思为“异语”）。|Uses(Translating); See also(Have_as_translation_equivalent)|❌|
|Bearing_arms|主角有（或没有）武器。还可以描述主角的武装程度。主角通常是一个人，但可能是一个有辅助武器的装置。显然，嫌犯手持猎枪。在她从袜子抽屉里拿出点45手枪后，她觉得自己有足够的武装，可以面对任何进来的人。战斧导弹的热量很大。拥有携带许可证的个人可以在符合现有州和地方法律的情况下继续在“学校区域”内携带。|Inherits from(State); Uses(Weapon); Is Used by(Shooting_scenario)|❌|
|Beat_opponent|胜利者战胜了失败者。下棋他总是赢我。|Uses(Win_prize)|❌|
|Becoming|一个Entity最终会有一些Final_ality——一个关于Entity的新事实。或者，根据一组特征的变化，该实体新满足成为Final_category成员的条件。天气转冷。你今天可以成为一名消防员了！这个框架应该与Transition_to_state框架相比较，后者在允许对最终情况进行任意描述方面更加通用：我们最终告诉他离开。没有办法在become框架中有效地解释这样的句子。|Inherits from(Transition_to_state); Is Inherited by(Transition_to_a_quality)|❌|
|Becoming_a_member|一个新成员成为一个社会构建的组的成员。7个新成员和这3个国家在5年前加入了联盟。大多数新生入学大学时不申报专业。它代表了每一个应征入伍保护我们的家庭和服务于社区的男女。|Inherits from(Intentionally_act); Is Inchoative of(Membership)|❌|
|Becoming_attached|一个项目被附加到目标上，一个连接器在项目的句柄和目标（或它的某些部分）之间形成了一个纽带。或者，多个Item之间可以形成一个绑定关系。按照计划，船体的前部悄悄地附在对接装置上。细胞结合在一起。|Inherits from(Transition_to_a_quality); Is Inchoative of(Being_attached)|❌|
|Becoming_aware|这个框架中的词与Cognizer在他们的世界模型中添加一些现象有关。它们与信词相似，只是后者通常涉及从证据的推理。这个框架中的词直接表示世界上的实体，并表示对这些实体的认识，而不一定给出任何关于认知者的信仰或知识的内容的信息。这些词也类似于感知词，因为生物通常通过感知事物而意识到它们。当晚晚些时候，他们在红厅邨公寓内发现了勉强活着的受害者。几乎立即，警察发现了锻铁地窖大门荡开。在桌子上的袋子里，我依稀可以辨认出两瓶酒和几盒蛋糕和其他好东西。路过的人远远地认出了它，因为煤尘的云层使空气变暗。一般语法观察：此框架中的动词的被动形式可以与表示现象的外置从句发生：那一年，人们发现消费者更喜欢旧的模式。人们并不总是认识到在晚宴上花费了多少工作。|Inherits from(Perception); Is Used by(Scrutiny)|❌|
|Becoming_detached|Become_detached框架涵盖了两种情况：一种是一个事物在物理上与其他事物分离的场景，另一种是两个事物在物理上与其他事物分离的场景。在第一个中，框架包含一个从源分离的项目，在项目和源之间创建了非对称关系。在第二个中，项目彼此分离，其中每个相对于另一个充当源，在两个项目之间创建对称关系。以前附加的项目重新显示为它们所在的两个独立或可能独立的实体。这艘船与码头脱钩了。|Inherits from(Transition_to_a_quality); Is Inchoative of(Being_detached)|❌|
|Becoming_dry|实体失去水分，结果是处于干燥状态。板干得很快。|Inherits from(Transition_to_a_quality); Is Inchoative of(Being_dry)|❌|
|Becoming_separated|一个整体分成若干部分，或者一个整体的一部分，称为第_1部分，与其余的部分，第_2部分分开。这条小河道蜿蜒穿过沼泽和湿地，分成几个较小的河道，流入圣克莱尔湖。只要把一个掰开，如果轭很快与白色分离，它们很可能是坏的。|Is Inherited by(Fragmentation_scenario)|❌|
|Becoming_silent|在这个框架中，发言人停止发言，有时是关于一个特定的主题。也可以指示Expressor。这个框架中的单词使用频率非常高，以至于某些单词和短语（而不是另一个单词，静默，嘘）只能这样使用。最后，简闭嘴了他的车祸。孩子们的笑声安静了下来。不知怎的，他设法控制住了自己的舌头。||❌|
|Becoming_visible|之前对感知者不可见的实体变为可见。日落时分舰队出现在地平线上。上尉命令他的人在X挖掘，一个箱子的角落出现了。|Inherits from(Transition_to_a_quality); Is Used by(Perception)|❌|
|Behind_the_scenes|艺术家在完成电影、戏剧、电视节目或其他类似作品的各种任务中的工作。艺术家从不出现在舞台上或镜头前。一些（例如，导演）可能会与制作的演员（屏幕上的参与者）互动。通常情况下，特定的制作是为了由分销商、特定的工作室或在特定的媒体中进行分发而制作的。艺术家可分为类型或特定媒介的作品。史蒂文·斯皮尔伯格为环球影业执导了几部电影。环球影业和Amblin Entertainment为MCA制作了《侏罗纪公园》。令人惊讶的是，这位电影制片人竟然愿意为一家有线电视公司工作。独立制片人往往在规模较小的电影节上大获全胜。|Uses(Performing_arts)|❌|
|Being_active|Agent被描述为执行一个Activity，花费一些精力。座席可能在特定角色中处于活动状态。或者，Activity本身可以被描述为有一个正在花费精力的Agent。在某些情况下，Activity可能会涉及一个Salient_entity，它可以代替它。天空是一名朝鲜战争老兵，他积极反对越南，并继续抗议目前在伊拉克的战斗。她活跃于社区，为年轻女性建立家长小组、生活技能计划、分享圈子和各种土著文化活动。约翰·科尔维尔作为弗吉尼亚州和马里兰州的土地投机者相当活跃。|Inherits from(Gradable_attributes); Uses(Activity_ongoing)|❌|
|Being_at_risk|资产处于暴露于有害事件或可能受到有害事件影响的状态，该事件可以通过引用危险实体来转喻唤起。表示相对安全（即没有风险）的词也在此框架中。如果你是一个农民，你有可能因为工作中接触到噪音而导致听力损失。没有一个孩子能够不受“我的朋友”正在做的事的诱惑。我们的国家正在犯一个灾难性的错误，以为我们可以从人民那里获得安全：只有人民才有安全。除非你有防止窃听的安全，否则你就没有防止冒充的安全。|Inherits from(Gradable_attributes); Is Inherited by(Precariousness); Perspective on(Risk_scenario); See also(Run_risk)|❌|
|Being_attached|项目通过句柄，通过连接器连接到目标，或项目彼此连接。可能会有一个依赖状态，这个依赖状态主要取决于被附加的项目。我的大拇指被胶水管粘住了。犯人的腿被铐住了。|Inherits from(Reciprocality,State); Is Used by(Being_detached)|❌|
|Being_awake|主角在某个时间和地点醒着。这就要求主角对周围环境的认知水平比睡着时更高。他醒了！|Subframe of(Sleep_wake_cycle); Precedes(Fall_asleep,Getting_up); Is Preceded by(Waking_up)|❌|
|Being_born|这个框架涉及儿童（一般是人类）在特定时间和地点的生命的开始。亲戚也可以提到。小洁西昨晚8点来到这个世界。|Inherits from(Coming_to_be); Perspective on(Birth_scenario); Subframe of(Cycle_of_life_and_death); Precedes(Dying,Death)|❌|
|Being_contained_within|在这种情况下，轨迹包含在地标中。此帧仅用于将包含帧（与LU(如include.v）)与Internal_profile_relation帧（与LU(如Inside.prep）)相关联。|Inherits from(Interior_profile_relation); Perspective on(Containment_scenario)|❌|
|Being_detached|项目从源分离，或项目从彼此分离。将铲雪车从车辆上断开后，将提升油缸延伸至其行程末端，并在铬合金杆上涂上一层薄薄的润滑脂。未附着在雕刻表面的金叶脱落。5点到5点30分（取决于一年中的时间），船被解泊并装货。|Uses(Being_attached)|❌|
|Being_dry|物品处于干燥状态。带状疱疹是干的。苹果完全脱水了。拖把是干的。|Inherits from(Gradable_attributes)|❌|
|Being_employed|雇员在某一特定领域工作，或在某一特定任务上工作，雇主为此向雇员支付报酬。无证外国人在Laing Builders公司担任建筑承包商。|Perspective on(Employment_continue); Subframe of(Employee_scenario); Precedes(Quitting); Is Preceded by(Get_a_job)|❌|
|Being_in_captivity|主题被一个代理或原因控制。20名士兵被囚禁了一个多月才被释放我从未释放过我的俘虏。她不敢相信自己被囚禁在自己家里。|Is Inherited by(Being_incarcerated); Uses(Inhibit_movement)|❌|
|Being_in_category|一个项目属于一个类别（通常是隐含的），由一个认知者设想。对我来说，这算是历史虚构，因为它是基于真实事件。|Uses(Categorization)|❌|
|Being_in_control|Control_entity可以控制从属实体、从属情境或从属变量。她在两天内就控制了帝国。这个框架与Control的不同之处在于，Controlling_entity并没有完全声明当前正在控制从属实体、从属状态或从属变量，而是关注它，并且能够使情况在任何时候与期望的状态相对应。|Inherits from(Control); Is Inherited by(Dominate_competitor); Is Used by(Kidnapping)|❌|
|Being_in_effect|特定的Binding_principle是（或不）有效的，也就是说，Binding_principle的任何义务、限制和任何其他方面都是（或不）有效的。Binding_principle可以表示为在特定的持续时间内生效，或在特定的时间或地点生效，或在特定的情况下生效。这项法律只在今年的最后三周生效。法定湿地定义立即生效。本合同对各方均有约束力。虽然在这个框架中生效，但是在Execute_plan框架中生效。这在一定程度上是因为使（撤离）计划生效是实际执行该计划（撤离），而使计划生效是确定在未来该计划可能必须执行，即使计划具有约束力。类似的观察也可以用于生效。|Uses(Obligation_scenario); Is Used by(Enforcing); See also(Execute_plan)|❌|
|Being_in_operation|设备或机器处于（或不处于）服务状态。请注意，被破坏或正常工作与被打开或关闭是一个单独的问题。后一个概念是当前框架所关注的。可以指定设备使用的时间和地点，也可以指定背景用户打开或关闭设备的目的。电视开着我来的时候灯已经关了。|Inherits from(State); Uses(Gizmo)|❌|
|Being_incarcerated|囚犯因犯罪而受到的惩罚是在监狱中被禁锢一段特定的时间。菲尔在Pelican Bay服刑。|Inherits from(Being_in_captivity); Is Used by(Fugitive)|❌|
|Being_included|部分被描述为整体的子集或组成子部分。这与包含框架形成对比，其中从整体的观点来看同样的关系。|Is Inherited by(Be_subset_of,Part_piece); Perspective on(Inclusion_scenario)|❌|
|Being_located|主题相对于位置处于稳定的位置。我们的办公室位于85号州际公路以南两英里处。|Inherits from(State); Is Inherited by(Visiting,Presence); Uses(Locative_relation); Is Used by(Bounded_entity)|❌|
|Being_named|这个框架涉及的实体通常被特定的名称所指代。她的名字叫萝拉。|Is Inherited by(Appellations); Is Used by(Namesake,Referring_by_name)|❌|
|Being_necessary|从属关系状态有一个要求作为获得或发生的前提条件。如果没有大陆入侵日本，为了赢得二战的胜利，原子弹轰炸可能不是必要的。我们将采取必要的措施，不管左翼的叫喊声如何。DNI两个代币是县与县之间的旅行所必需的。|Perspective on(Requirement_scenario); Is Used by(Required_event,Taking_time)|❌|
|Being_obligated|在某种情况下，通常是隐性的，要求责任方履行某种职责。如果他们不履行义务，可能会出现一些不希望发生的后果，这些后果可以公开声明，也可以不公开声明。打击对兄弟会的任何攻击是我的职责。这个国家有责任支持公民表达自己的权利。我有义务支付，否则他们会加倍罚款。注：将此框架与似然框架和Preconditions框架进行对比，后者涉及许多相同的引理。许多可能期望在这里找到的LU（应该，必须，必须）实际上在require_event框架中。我们的分析是，这些LU并不直接引起义务，尽管它们经常被用于与义务的理解一致的上下文中，并且在语用上被强化为（可撤销地）暗示义务。|Perspective on(Obligation_scenario); Is Used by(Assigned_location,Temporary_leave); See also(Required_event)|❌|
|Being_obligatory|在某种情况下，通常是隐性的，责任方需要履行。如果不履行该义务，可能会对责任方造成某种不希望的后果，这种后果可以公开声明，也可以不公开声明。将此帧与正在等待的帧进行比较。我们有必要去理解和个人化耶稣对他的门徒们说的话。当我在HS时，为了参加任何其他的合奏，军乐队是强制性的。INI保险应该是强制性的吗？|Perspective on(Obligation_scenario)|❌|
|Being_operational|具有理解功能的对象是否处于准备好执行该功能的状态。遥控器快坏了。把那块破表递给我，让我把它扔掉。|Inherits from(Capability); Uses(Render_nonfunctional,Artifact)|❌|
|Being_pregnant|这个框架从父母的角度描述了怀孕和生育孩子的经历。||❌|
|Being_questionable|在这个框架中，一个实体或行为是可疑的或受到质疑的。一般的含义是，实体或行为提供了关于（通常是隐含的）社会行为者的某些（尚未证实的）社会不受欢迎的结论的证据。（这样的结论通常包括某人在说谎，或者有人犯了罪）。我们在他的桌子上发现了一些可疑的支票。你在警察到来之前离开派对很可疑。|Inherits from(Social_behavior_evaluation)|❌|
|Being_relevant|现象与认知者的某种认知行为（奋进）有关。在许多LU中，Cognizer是空实例化的，并隐含为Endeavor的说话者或另一个参与者。这本书与我的论文非常相关。这本书与我的论文非常相关。|Inherits from(Cognitive_connection)|❌|
|Being_rotted|一个有机物品，病人，已经经历了自然的过程腐烂和腐烂，并可能表达了腐烂发生的程度。椰奶变得酸败了。|Inherits from(Gradable_attributes); Uses(Being_wet)|❌|
|Being_up_to_it|实体满足参与一项活动的前提条件，该活动被判定为它难以参与，这可能是由于实体的固有属性，也可能是暂时的情况。程度修饰符可以指示实体超过或低于最低要求的程度。小汤米没有起床，因为他病得很厉害。|Inherits from(Capability)|❌|
|Being_wet|一个物品处于潮湿状态，其中提到了润湿液体的可能性，以及潮湿程度。拖把被昨晚的雨淋得湿透了。|Inherits from(Gradable_attributes); Is Used by(Being_rotted)|❌|
|Besieging|袭击者是一群武装力量，包围了受害者、军事地点和其中的人们，试图切断受害者与外部的联系，目的是迫使他们投降，或者削弱他们，以便入侵成功。攻城成功后通常是攻击者控制（受害者所持有的土地）。夏末时，一个伟大的英国东道主围攻丹麦的坦普斯福德要塞并夺取了它，杀死了东盎格利亚的最后一位丹麦国王。|Inherits from(Attack)|❌|
|Beyond_compare|与它的竞争对手相比，标准相对于某些变量而言处于规模的高端。竞争对手通常在语法上无法实现。纳税人正在支持一个在浪费方面无与伦比的系统。客厅是一个无比肮脏的地方。她嫉妒她母亲无与伦比的美貌。当没有显性变量时，必须从上下文来理解。他是当时其他任何政治家都无法比拟的。当目标作为谓词的修饰符出现时，它被标记为标准，而不是变量。他们是彼此无可比拟的针锋相对者。|Uses(Surpassing)|❌|
|Billing|开票机构以书面形式告知债务人欠欠欠方（通常与开票机构相同）一定数额的款项，由欠方提供的某些货物（包括服务），或清偿欠方对欠方的债务。|Uses(Commerce_collect)|❌|
|Biological_area|这个框架包含的词表示大的生态区域以及以存在的生命类型为特征的较小的位置——换句话说，由生物群定义的地理位置。我在洛温北部崎岖的草原上呆了很长时间。|Inherits from(Locale)|❌|
|Biological_classification|这个框架与科学分类学有关。这个框架中的词汇单位包括七个主要的分类，其中有机体是根据共同的生物特征进行分组的。这些分类在此框架中被标记为Rank。等级的成员或子类型通常用表示目标的名词来表示。节肢动物门包含甲壳类、昆虫、蜘蛛和其他令人毛骨悚然的爬行类。雪豹属于动物王国。|Inherits from(Type); Uses(Biological_entity)|❌|
|Biological_entity|这个框架中的LU是指由FE生物体标记的生物实体。有机体被描述为可能是活的，或具有自然发生的生物过程和功能的东西；然而，生命的概念经常被比喻为类似于或行为仿佛具有有机生命的非有机实体。美国宇航局也许有一天会发现来自另一个星球的新生命形式。|Inherits from(Entity); Is Inherited by(People,Animals,Plants); Is Used by(Dead_or_alive,Gusto,Biological_classification)|❌|
|Biological_mechanisms|触发机制引起生物系统的变化。反射增加心输出量。||❌|
|Biological_urge|体验者处于一种生物冲动发出信号，需要进行某种动作，如吃、喝、停止劳累、睡觉、反胃或做爱的状态。还可以指出与冲动发生相关的持续时间、时间、地点或强度程度。在这个框架中，体验者不一定想要执行能够满足冲动的动作，并且没有与冲动相关联的特定焦点。迈克觉得饿了。饭后山姆口渴。|Inherits from(Gradable_attributes)|❌|
|Birth_scenario|后代是母亲和父亲所生，统称为父母。此事件发生在特定的时间和地点。|Inherits from(Event); Is Perspectivized in(Giving_birth,Being_born); Subframe of(Sexual_reproduction_scenario)|❌|
|Board_vehicle|旅行者登上他们打算作为乘客或司机使用的交通工具。1834年12月5日，我们登上了海列斯庞特号商船。她先于他上了火车。9月19日，该营展开围攻，向南进入约40英里外的剑鱼训练区。|Uses(Ride_vehicle)|❌|
|Body_decoration|这个框架涉及到人类身上或应用于他们身体上的装饰。艾比很少涂口红。|Inherits from(Artifact); Uses(Body_parts)|❌|
|Body_description_holistic|这个框架涵盖了整个人体的描述，被视为格式塔（相对于基于显著身体部位的描述）。框架元素为个体和图。查克是肌肉型的。查克有一个肌肉发达的身体。|Inherits from(Gradable_attributes)|❌|
|Body_description_part|这个框架涉及的是基于一个人身体的突出部分来描述一个人的词。他是个金发碧眼的家伙。他是个钉子腿。|Inherits from(Gradable_attributes); Uses(Body_parts)|❌|
|Body_mark|在此帧中，Body_mark出现在持有者的身体上。它可以位于附件中，并具有描述符。也可以指出原因。它可能是暂时的，也可能是永久的。马克背上有一颗癌变的黑痣。|Inherits from(Physical_entity); Uses(Body_parts)|❌|
|Body_movement|此框架包含Agent使用他/她身体的某个部分执行的动作或动作。此框架中的许多词作为通信的混合出现，其中的动作有一个收件人。例如，帕特向金点头。这些例子与“沟通”不同，手势不需要表达特定的信息，如“她点头让他坐下”。由于此帧涉及特定类型的运动，因此它包含源自运动帧的帧元素Source、Path、Target和Area。所有这些框架元素通常用PP补体来表示。男孩从桌子底下甩了甩腿。|Uses(Motion,Body_parts); Is Used by(Facial_expression)|❌|
|Body_parts|这个框架涵盖了主体部分(s) (BP)的词，它可以由描述符（Descriptor）来表征。BP的位置可以根据其附件或其定向位置来标识。还可以指示BP的子区域。为了对抗翻滚，他不得不用右臂抵住腿。狗在泥地里丈量着它的金发肚皮。|Inherits from(Shaped_part); Is Used by(Hair_configuration,Wearing,Body_movement,Manipulation,Body_description_part,Body_decoration,Body_mark,Medical_conditions)|❌|
|Bond_maturation|金融工具（债券或保险）在一定时间满足了一个条件，在该条件之后，金融工具的发行人在法律上有义务根据该工具的原始原则和利率向持有人支付货币价值。债券到期时满值为30年。|Uses(Repayment)|❌|
|Borrowing|借款人在知道借款人必须在一段时间后将标的物归还贷款人的情况下占有该标的物。此框架与借贷框架的区别在于，此框架在活动句子中描述借款人，而借贷框架描述借贷人。目前，这个框架既包括传递事件本身，也包括事件的结束状态，如下面的前两个示例所示：我是从教授那里借来的关于模态粒子的书。我向他借了这本书，很早以前就还了。我不仅要借一件长袍，还被借给我一件夹克！女孩从她姐姐那里借了几天车。与其他暂时占有的方式（例如，“把东西放在口袋里一段时间”）一起，这个框架用于非字面上指代盗窃。在这种用法中，借款人是小偷，出借人是受害者，主题是货物：没有人在看，所以我向她借了。|Inherits from(Receiving); Perspective on(Temporary_transfer_scenario)|❌|
|Boundary|此框架包含描述两个实体之间边界的词语。在许多情况下，边界是实体和一些未命名空间之间的边界，通常被认为是空的。峡谷是两州的边界。|Is Used by(Bounded_entity)|❌|
|Bounded_entity|这是一个有界区域的抽象框架，主要用于FE继承。|Inherits from(Physical_entity); Uses(Boundary,Being_located); Is Used by(Containers,Locale,Shapes)|❌|
|Bounded_region|相对于地面，外部、表面、边界和内部被挑选出来。这个地面可以只占据边界（在这种情况下，内部是负空间），或者地面可以填满内部。|Inherits from(Image_schema); Is Inherited by(Region_with_portal); Is Used by(Interior_profile_relation)|❌|
|Bragging|演讲者谈论一个主题，这个主题可能是演讲者所执行的行动，也可能是他们所联系的实体或状态，以表明演讲者是值得钦佩的。演讲者可以给出一个明确的理由，为什么这个主题对他们的信用有帮助。或者，可以使用Message框架元素直接描述说话者说了什么，让更具体的原因被推断出来。而不是说话者，行动可以被转喻地归于媒介，或者可能是表达者。土耳其官员吹嘘向一位著名的美国政治家提供了“数万美元的秘密付款”。然后，他吹嘘自己的家族，但没有提到伊曼纽尔·昂加罗，后者形容这一遗漏是“可悲的”。新闻稿吹嘘“墨盒和系统之间的直接连接”意味着不再需要将灰尘吹出游戏墨盒。70年代的漫画如Chevy Chase和Steve Martin夸大了他们的自我主义，并吹嘘他们的优越感。|Inherits from(Judgment_communication)|❌|
|Breaking_apart|一个整体分裂成若干个小部分，导致整体的损失（在大多数情况下，没有一个小部分具有单独的功能）。飞机在半空中剧烈地碎裂。后来，我终于意识到，一定是陨石碎裂成至少3块大碎片的情况。这些动词中的许多也可以隐喻地指代制度的分裂。（参见“分裂”的框架。）|Perspective on(Fragmentation_scenario)|❌|
|Breaking_off|单个子部分从整体中分离出来。原来的剑可能很早以前就从雕像上砍下来了。|Perspective on(Fragmentation_scenario)|❌|
|Breaking_out_captive|代理人违背俘虏者的计划或愿望，在俘虏的地点结束俘虏。由于他的伪装，他的同伙将他从新星监狱中解救出来。|Inherits from(Intentionally_affect)|❌|
|Breathing|智能体使空气在一个方向上移动，通常指定是进入身体还是离开身体。李呼吸着沙漠的热气。|Uses(Fluidic_motion)|❌|
|Bringing|此框架涉及主题和代理和/或承运人的移动。Agent（一个人或其他感知实体）通过在运动过程中移动主题来控制共享路径。换句话说，Agent在指导主题的运动中具有整体的运动。承运人可以是一个单独的实体，也可以是代理人的主体。常量位置可以是Agent身体的一个子区域，也可以是Agent使用的车辆的（子区域）。卡尔背着书穿过校园来到图书馆。卡尔用他的卡车把书穿过校园送到图书馆。卡尔用卡车把书穿过校园送到图书馆。卡车用特别设计的箱子将这些书运送穿过校园送到图书馆。FE包括Path、Target和Source。当路径被理解为不规则时，面积是包含运动的区域。这个框架强调的是运动的路径，而不是填充或放置中的源或目标。|Is Inherited by(Smuggling); Uses(Cause_motion,Motion); Is Used by(Sending,Convoy); See also(Passing,Sending,Motion,Cause_motion)|❌|
|Building|此框架描述装配或构造动作，其中代理将组件连接在一起以形成已描述的创建实体（Created_entity），因此是动词的对象。杰克用砖头盖了一座新房子。我们把飞机粘在一起。|Inherits from(Intentionally_create)|❌|
|Building_subparts|这个框架包括命名可被人占用的建筑物的子部分的单词。玛丽怒气冲冲地离开了房间。|Uses(Locale); Subframe of(Buildings)|❌|
|Buildings|此框架包含的词语，其名称为永久性固定结构，形成一个围护结构，并提供对元素的保护。这座建于1635年的巴洛克式教堂内部装饰非常丰富。城市之旅包括16世纪的变容修道院和先知以利亚教堂一座古老的石头教堂矗立在田野中，杰克按照当时的风格建造了他的房子。|Inherits from(Artifact); Uses(Locale_by_use); Has Subframe(s)(Building_subparts)|❌|
|Bungling|代理错误地执行操作。受影响的患者可能会在行动中被转喻提及。米奇把挥杆弄糟了。茱莉亚把蛋糕弄糟了。|Uses(Intentionally_act,Intentionally_affect)|❌|
|Burying|代理或原因将一个表面（通常是地面）下的主题置于目标位置。嫌犯在逃离警察时将枪埋在地下。|Inherits from(Placing)|❌|
|Business_closure|业务区域设置（实体）停止提供服务并关闭。埃克森美孚破产了。|Inherits from(Endeavor_failure,Locale_closure); See also(Endeavor_failure)|❌|
|Businesses|所有者拥有或经营提供产品（可能是商品或服务）的企业。消费电子公司苹果近年来人气爆棚。|Uses(Commerce_scenario)|❌|
