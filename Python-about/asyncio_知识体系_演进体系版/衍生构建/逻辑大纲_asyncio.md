# asyncio 设计理性文章系列——逻辑大纲

> 本大纲服务于7篇主体文章，每篇遵循四段式结构：通用困境→具体困境实例化→被迫选择→代价+悬念。
> 遵循护城河原则：不暴露方法论术语，读者感受"自然推导"。

---

## 第1篇：速度鸿沟逼出的死角

**通用困境**：高速处理单元与低速I/O设备存在速度鸿沟——串行等待模型下处理单元被迫空转

1. **通用困境展开**
   - CPU周期~10ns vs 磁盘I/O~10ms vs 网络I/O~1-100ms——10^6倍差距
   - 这不是Python的问题，不是asyncio的问题。nginx、Node.js、Go scheduler、Java NIO、Rust tokio面对的是同一道鸿沟
   - 串行等待 = CPU在I/O期间空转 = 时间轴上的并发断裂
   - 写一段代码：同步http请求10个URL，感受CPU空等2秒

2. **具体困境实例化**
   - 在单线程Python中的窘境：多线程受GIL限制(8MB栈/线程、上下文切换开销、竞态条件)
   - C10K问题的本质：不是连接数大，而是10K个连接中99%的时间在等I/O
   - 写崩溃代码：用threading处理10000个连接——线程数打满OS限制，内存撑爆
   - 唯一出路浮现：在单线程内重叠I/O等待——"遇到I/O就跳过，去执行其他就绪任务"

3. **被迫的设计选择：EventLoop接管控制权**
   - "你试试不引入事件循环"——没有调度器，谁来决定"接下来执行谁"？
   - EventLoop做的事：轮询I/O就绪(selector/epoll) + 维护就绪回调队列 + 逐个执行
   - 设计内因展开：为什么是三队列分离(_ready+_scheduled+_selector)而非单队列？
   - 写崩溃代码：单队列混合存储——FIFO回调饿死定时器，或定时排序破坏FIFO
   - timeout是生死枢纽：_ready非空→0/堆顶→差值/皆空→无限，一行计算保三条命
   - ntodo快照：回调嵌套饿死I/O检查——写崩溃代码演示无限call_soon导致永远回不到select()

4. **代价+悬念**
   - 代价：EventLoop能跳过I/O等待了，但它调度的"任务"仍然是传统函数——传统函数一旦开始执行就占满调用栈直到返回，无法在I/O等待点暂停交出控制权
   - 更深层的代价：跳出时序的瞬间，你同时丧失了四样东西——执行上下文无处安放、I/O结果无法传回、多控制流碎片缺乏协调、满天飞的任务缺乏管理
   - 悬念："EventLoop能跳过I/O了，但它找到的还是传统函数——一个不能暂停的执行者。世界碎了，碎成什么样子？"

---

## 第2篇：选择异步的那个瞬间，世界碎了

**通用困境**：选异步=四项保证同时丧失（上下文/结果/时序/秩序）

1. **通用困境展开**
   - 同步模型隐含的四项保证：(1)函数执行期间栈帧连续(2)返回值直接可达(3)执行顺序可预测(4)资源有天然作用域
   - 这四项保证不是"好特性"，而是同步模型的数学性质——只要你是串行的，它们自动成立
   - 选择异步 = 放弃串行 = 四项保证同时丧失，无一幸免
   - 这是所有异步系统的共性问题：Node.js的callback hell丧失(1)(2)，Go的goroutine泄漏丧失(4)，Java的CompletionStage链丧失(1)

2. **具体困境实例化**
   - 丧失1(上下文悬空)：EventLoop回调执行时，前一个回调的局部变量、指令位置已经消失了——"我从哪里来？"
   - 丧失2(结果不可达)：I/O操作的结果在未来某个时刻到达，但调用者的栈帧已经不存在了——返回值变成跨越时间的幽灵
   - 丧失3(时序失控)：成百上千个切分后的控制流碎片——谁先谁后？谁能取消？谁依赖谁？
   - 丧失4(秩序崩塌)：满天飞的任务——谁管生命周期？父级退出后子任务还在跑？异常被谁吃掉了？
   - 写崩溃代码：裸EventLoop + 回调模式——callback hell演示所有四项丧失

3. **代价集群的性质**
   - 这四项丧失不是逐个发现的，而是选择异步时**同时丧失**的
   - 后续必要存在的每一个概念(Task/Future/同步原语/TaskGroup)都可以追溯到这四项丧失
   - 但重建有顺序——必须先修地基再盖楼：先恢复上下文(栈帧)，才能交付结果(需要有挂起点)

4. **代价+悬念**
   - 代价：四项丧失意味着需要四个新机制来分别重建，这不是一个方案能解决的
   - 悬念："最基础的是第一项——上下文悬空。没有它，其他三项连重建的资格都没有。必须先让函数能暂停。"

---

## 第3篇：结果如何穿越断路

**通用困境**：异步系统中调用者让出控制权后，I/O操作的结果无法传回给已退场的调用者——结果在未来某个时刻到达，但调用者的栈帧已经不存在了

1. **通用困境展开**
   - 同步函数：`result = read()`——result直接在栈上，理所当然
   - 异步世界：你让出执行权后，栈帧消失了——谁接收result？result存在哪里？
   - JavaScript的Promise、Java的CompletableFuture、C++的std::future——所有异步系统都发明了某种"占位对象"
   - 核心问题模式：需要"可以被await、可以被注册回调、可以被设值"的实体

2. **具体困境实例化**
   - 协程await一个I/O操作后挂起自身，但它需要一个"未来的结果"作为锚点
   - 写崩溃代码：没有Future——协程await后挂起，但无人通知它恢复(回调注册到哪里？)
   - 既然协程已经退场，就必须有一个跨时间的实体来锚定结果

3. **被迫的设计选择：Future(状态容器PENDING→FINISHED) + 回调(跨任务唤醒接口)**
   - "你试试不引入状态机"——如果Future可被多次设值，并发场景下"谁赢？"导致语义崩溃
   - 三态单向状态机：PENDING→FINISHED/CANCELLED不可逆
   - set_result()触发__schedule_callbacks()→call_soon→唤醒等待者
   - 已完成Future上注册回调也要在下一轮执行(add_done_callback即时检查)
   - 设计内因：结果唯一性、唤醒可靠性、就绪后注册、set_result/cancel竞争——逐一展开

4. **代价+悬念**
   - 代价：Future只是用户态的状态容器——它不知道底层操作系统何时产生数据。用户态Future与内核态I/O事件之间存在边界鸿沟
   - 悬念："Future能锚定结果了，但谁来调用set_result()？答案是：必须有东西下探到内核边界。"

---

## 第4篇：切断栈帧的人

**通用困境**：异步系统中任务让出控制权后，执行上下文无处安放——回调驱动的控制流被切碎，每个碎片丢失了"我从哪里来"的信息

1. **通用困境展开**
   - 传统函数调用栈是刚性的：main→f()→g()→h()，整条链不能"断开再接上"
   - h()阻塞→g()阻塞→f()阻塞→main阻塞——一阻全阻
   - Node.js的callback hell、Java的CompletionStage链式调用、C的显式状态机——都是同一困境的不同应对
   - 核心需求：断开栈帧的能力——暂停h()时，不阻塞g()、f()

2. **具体困境实例化**
   - EventLoop能监听I/O就绪事件，但它调度的"任务"仍然是传统函数
   - 传统函数一旦开始执行就占满调用栈直到返回——无法在I/O等待点暂停
   - 写崩溃代码：在EventLoop回调中调用阻塞read()——整个循环停转
   - 写崩溃代码：用嵌套回调代替暂停——callback hell，三层嵌套后已不可读

3. **被迫的设计选择：协程(yield/await切断栈帧) + Task(保存断点+驱动)**
   - "你试试不切断栈帧"——回调驱动的世界里，要么callback hell要么栈帧切断
   - 协程的yield/await就是栈帧断点——暂停时状态保存到generator/coroutine对象(堆上)
   - Task.__step/__wakeup双阶段驱动："推"协程到断点，"拉"回协程续行
   - _fut_waiter：跨任务边界配对的锚点
   - 取消传播的时机困境：cancel到达时Task可能在Future上或在_ready排队——_must_cancel延迟注入覆盖两种状态
   - 设计内因展开：驱动-悬挂双段、取消注入时机、上下文隔离(_context副本)

4. **代价+悬念**
   - 代价：栈帧虽然切断了，但调用者await后也退场了——结果怎么传回给已退场的调用者？
   - 等等——这篇和第3篇的顺序问题。根据文章规划，第3篇讲Future(结果传回)，第4篇讲协程(栈帧切断)。但从构建依赖看，D2(协程)在D3(Future)之前？

   > **修正**：文章叙事顺序与构建依赖序不同。叙事上，"结果如何穿越断路"(Future)在"切断栈帧的人"(协程)之前——这符合读者认知：先感到"结果传不回来"的痛苦，再解释"因为栈帧断了所以传不回来"。
   >
   > 而实际的构建依赖是D2→D3(需要协程的挂起点作为结果交付目标)。文章叙事需要处理这个倒序——第3篇先提出Future的必要，然后在第4篇揭示"Future的await需要栈帧切断才能工作"，两者互为因果但叙事上有侧重。

   修正后第4篇的代价+悬念：
   - 代价：协程能暂停和恢复了，但取消信号如何跨Task传播？超时取消和外部取消如何区分？(为E11铺路)
   - 悬念："协程恢复了线性执行的感觉——但I/O完成事件还在内核那边。怎么把内核的通知接到用户态的Future上？"

---

## 第5篇：内核边界的桥

**通用困境**：用户态异步框架必须跨越内核/用户态边界获取I/O完成通知

1. **通用困境展开**
   - Future是纯用户态对象，它不知道fd何时可读/可写
   - 操作系统是I/O的真正执行者——数据在内核缓冲区，通知在内核的事件队列
   - libuv的uv__io_poll、Java NIO的Selector、Go的netpoller——每个异步框架的底层都有"用户态如何感知内核I/O事件"的解决
   - 核心鸿沟：系统调用是用户态→内核态的唯一通道，且阻塞时会放弃线程

2. **具体困境实例化**
   - set_result()必须由某个"知道I/O完成"的实体来调用，但谁是这个"某个人"？
   - 写崩溃代码：Future创建后等待set_result()——但如果没人桥接内核，Future永远PENDING
   - 两种OS模型差异：Selector(就绪通知"可以读了") vs Proactor(完成通知"读完了")——同一功能的不同抽象

3. **被迫的设计选择：Transport封装底层非阻塞I/O + Protocol处理业务逻辑**
   - "你试试不分离传输和业务"——Transport内置业务逻辑则无法插入SSL，Protocol知道socket细节则无法跨平台
   - 1:1配对：Transport持有_protocol引用调用回调，Protocol通过transport.write()发送数据
   - Transport._read_ready()：selector通知→sock.recv()→protocol.data_received()——从内核到用户态的完整路径
   - 写流控：非阻塞写的速度远快于内核排空——_buffer暂存+pause_writing/resume_writing背压
   - SSLProtocol中间层插入：MemoryBIO解耦SSLObject与socket——透明加密的关键创新
   - Selector/Proactor统一接口：select(timeout)/_poll(timeout)屏蔽OS差异

4. **代价+悬念**
   - 代价：I/O通道通了——从内核到协程的完整数据流闭环。但并发不等于混乱：多个Task并发执行时，需要协调对共享资源的访问
   - 悬念："I/O通道通了。但现在有一千个Task在跑——谁等谁？谁先谁后？谁通知谁？"

---

## 第6篇：重建秩序

**通用困境**：(A)并发系统中协作任务需要时序协调——无协调则逻辑互斥违反(单线程)或数据竞争(多线程)；(B)并发任务逃逸——无作用域约束的任务可在父级退出后继续运行，异常静默丢失，取消信号无法级联传播

1. **通用困境A展开：时序协调**
   - Go的sync.Mutex/channel、Java的synchronized/CountDownLatch、Rust的Mutex/mpsc::channel——都是同一类问题
   - 单线程协程中的"同步"不是互斥保护(无并发访问)，而是时序协调——"我等你干完再继续"
   - 纯用户态，无系统调用——所有协调通过Future.set_result→call_soon在EventLoop内完成

2. **具体困境A实例化：同步原语族**
   - 统一模式：等待者创建Future并入_waiters，释放者取出Future并set_result
   - "你试试不用同步原语"——写崩溃代码：多个协程竞争修改共享状态，逻辑互斥违反
   - 快速路径vs等待路径：无竞争时直接返回(不创建Future)，有竞争才挂起
   - Lock/Event/Condition/Semaphore——各自的条件判断逻辑不同但等待/唤醒模式相同
   - Queue：双向协调——生产者满时等消费者，消费者空时等生产者；零拷贝直接传递优化

3. **通用困境B展开：任务逃逸**
   - 结构化并发近年趋势：Go(errgroup)、Rust(tokio::task::JoinSet)、Swift(TaskGroup)
   - 裸create_task()的问题：无作用域约束(孤儿Task)、异常静默丢失(只打日志)、取消无法级联
   - 需要async with作用域约束——TaskGroup、Timeout、Runner三层闭环

4. **被迫的设计选择：TaskGroup + Timeout + Runner**
   - TaskGroup："你试试用裸create_task管理100个子任务"——异常丢了、取消乱了、不知道何时全部完成
   - async with作用域约束：退出块时所有Task完成或取消，异常收集为ExceptionGroup
   - _abort()取消+while等待：取消是请求而非即时——仍需等待被取消Task完成
   - Timeout：TimerHandle→task.cancel()→uncancel()——将时间边界转化为异常边界，区分超时取消与外部取消
   - Runner：EventLoop的完整生命周期——创建→驱动→清理异步生成器和线程池→关闭→信号处理

5. **代价+悬念**
   - 代价：秩序重建完毕。时序重叠(EventLoop)、上下文保存(协程+Task)、结果锚定(Future)、内核桥接(Transport+Protocol)、时序协调(同步原语)、生命周期管理(TaskGroup+Timeout+Runner)——六项机制各归其位
   - 悬念："每一块都就位了。但它们真的闭合了吗？需要一个入口把所有东西组装起来，从同步世界走进异步世界再安全返回。"

---

## 第7篇：闭环

**通用困境**：异步系统需要一个结构化入口——从同步世界进入异步世界，执行主任务，清理资源，安全返回同步世界

1. **用户视角的完整闭环**
   - 读者已看完六篇，心中有了完整拼图。本篇做最终验证：拼上之后，闭环成立吗？
   - 从asyncio.run(main())出发，追踪完整执行路径：
     ```
     Runner.__enter__ → EventLoop创建
       → Runner.run(main) → Task驱动main协程
         → main协程await I/O → Task.__step挂起 → EventLoop._run_once轮询
           → selector通知 → Transport._read_ready → Protocol.data_received → Future.set_result
           → __schedule_callbacks → call_soon(Task.__wakeup) → Task.__step恢复
         → main协程await lock/queue → 同步原语Future挂起/唤醒
         → async with TaskGroup → 作用域约束
         → async with timeout → TimerHandle→cancel→uncancel→TimeoutError
       → Runner.run退出 → shutdown_asyncgens + shutdown_executor → loop.close
     Runner.__exit__ → 资源释放
     ```
   - 每一环都能回溯到前六篇的困境和选择——不是巧合，是必然

2. **代价回顾：你失去了什么，换来了什么**
   - 失去：同步模型的简洁——函数调用就是函数调用，返回值就在栈上
   - 换来：在单线程内重叠I/O等待——CPU不再空转，吞吐量突破I/O瓶颈
   - 代价的代价：需要六个概念(EventLoop/协程+Task/Future/Transport+Protocol/同步原语/TaskGroup)来重建同步模型自动给你的四项保证
   - 这不是Python的问题——Go需要goroutine+channel+WaitGroup，Rust需要tokio的spawn+JoinHandle+Semaphore，Java需要CompletableFuture+ExecutorService+...

3. **跨系统一瞥**
   - 同一个通用困境，不同解法：
     - 速度鸿沟：nginx的事件循环、Go的netpoller+M:N调度、Java NIO的Selector
     - 上下文悬空：Go的goroutine栈(8KB→增长)、Node.js的闭包(callback hell→Promise→async/await)、Rust的Pin<Future>
     - 结果锚定：JavaScript Promise、Java CompletableFuture、C++ std::future、Go的channel
     - 内核桥接：libuv的uv__io_poll、Go的netpoller(epoll集成)、Java NIO的Selector
     - 任务逃逸：Go errgroup、Rust JoinSet、Swift TaskGroup
   - 读者应该感受到：asyncio走过的路，是所有异步系统走过的同一条路

4. **结尾**
   - "你看到的不是asyncio——是所有异步系统走过的同一条路。只是每一步的脚印形状不同。"

---

## 衍生篇A：方法论本身（写给作者，可用方法论术语）

- 0号约束、代价集群、冲突挤压→设计选择→副作用、四维锚点、设计内因四段式——完整方法论复盘
- 演进模型与实现模型的分形结构
- 5W2H缺口补强(Who→角色标注、How much→代价段、What→通用困境)
- 护城河原则的写作实践

## 衍生篇B：通用困境在Go/Node.js/Tokio中的不同解法（写给作者，可用方法论术语）

- 每个S3节点的通用困境，在其他系统中的对应解法
- 同一通用困境→不同具体场景→不同设计选择→不同代价
- 交叉对比表：通用困境×系统 ×{(场景, 选择, 代价)}
