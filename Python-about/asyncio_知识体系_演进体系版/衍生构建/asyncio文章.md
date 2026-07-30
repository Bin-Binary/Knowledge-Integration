# Asyncio，并发困境下的野望

## 并发的困境真相

程序要运行离不开CPU的计算操作，那它计算的数据哪来？靠I/O来搬运。两者紧密合作成就了计算机领域的百花齐放。

但是，CPU与I/O在执行速度上存在夸张的鸿沟。CPU一级缓存访问约1纳秒，磁盘I/O约10毫秒，网络I/O可达百毫秒甚至秒级——纳秒 vs 毫秒~秒，约10^6倍速度差。

下面通过一个演示动画直观感受一下：

(./问题演示_GIF/N0_timing_conflict.gif)

演示中的工作方式，即step-by-step、严格按顺序执行的方式，就是同步执行。同步执行遇到慢I/O时，CPU在等待I/O期间算力被浪费，无法利用这段时间执行其他任务。这种现象就是"并发的困境"。

"CPU极快，I/O极慢"这个物理事实导致的并发问题，是所有高并发方案都必须面对的共同困境。这不单单是Python的问题——nginx、Node.js、Go scheduler都在自己的场景下给出了答卷。

Python实现高并发是演进式的。Asyncio之前有多线程方案，但由于语言本身架构约束叠加物理约束，多线程在Python里有一系列弊端（GIL限制、8MB栈/线程的内存成本、内核态抢占式调度带来的竞态与不可复现bug），这里不展开赘述。

为了实现高并发，同时规避多线程的弊端，Asyncio采用了异步模型。一句话概括核心思想：**在单线程内重叠I/O等待——遇到I/O就跳过，去执行其他就绪任务**。

当任务A发起I/O操作并等待结果时，让它先让出执行权去执行任务B。等任务A的I/O完成了，再让控制流回来继续执行任务A剩下的部分。在时间轴上这样安排：任务A的I/O等待时间被任务B的计算"填充"。这样的工作方式就是异步。

---

## 异步的两个前提：非阻塞守权，多路复用提效

知易行难。想要从同步转到异步，必须满足两个前提条件：

1. I/O模型转换：阻塞I/O → 非阻塞I/O
2. 就绪检测：单一等待 → I/O多路复用

为什么缺一不可？一句话概括：**非阻塞"守权"，多路复用"提效"**。

**先看非阻塞。** 在阻塞模型下，遇到阻塞式系统调用时线程会被挂起，等待I/O完成。阻塞的本质是当前线程向操作系统交出了CPU控制权——线程被"冻结"，在等待某个操作（网络I/O、磁盘I/O、用户输入）期间自身无法进行任何操作。阻塞模型连"跳过I/O去执行其他任务"的资格都没有。

下面代码演示一个极端场景：连接一个不存在的端口。在I/O（这里是网络连接）没有返回时，绝不可能执行后面的"简单计算"部分。直到超时，线程还处于挂起状态。

(./问题演示_GIF/阻塞模型演示.png)

所以，阻塞模型下，从同步到异步根本没可能。

你可能会想：不让当前线程被挂起不就行了？对，这就是非阻塞模型。**非阻塞的核心作用就是"守权"——守住CPU控制权**。前提是OS支持非阻塞模式。好消息是它支持——`O_NONBLOCK`。I/O操作不阻塞线程，立即返回EAGAIN。

(./问题演示_GIF/非阻塞效果演示.png)

同样的代码演示：连接一个不存在的端口，但这次不设超时。阻塞模型会一直等下去。非阻塞模型下，它没有等待I/O完成，而是立即执行了后面的"简单计算"部分。非阻塞模型解决了线程被挂起的问题，使同步到异步的转变成为可能。

**再看多路复用。** 事情到了这一步，还处于"顾头不顾腚"的阶段。不等I/O完成不代表不处理I/O；要处理就得知道什么时候可以处理。非阻塞得到EAGAIN时，知道的是"现在没数据"，但不知道"什么时候会有数据"。之后没有任何信号、中断、回调来告诉你"好了"。你的代码只有两种选择：

1. 不再检查，丢掉这个I/O——后果是I/O永远不会被处理。
2. 不断轮询——那会怎样？下面代码演示10毫秒的轮询：

```
一个I/O就绪检测仅运行10毫秒就轮询了1993次，CPU使用率明显上升。
```

如果是100个、1000个就绪检测呢？I/O操作从发起到拿到结果一定有"等待"阶段，这是物理事实。非阻塞辛苦让线程保留了CPU控制权，如果在可预见的等待期间用来不断轮询"I/O就绪了吗"，纯属资源浪费。更糟糕的是，这种浪费和就绪检查数量成正比。同步到异步是为了解决CPU算力浪费，轮询的做法是在亲手消除异步带来的好处。

究其原因：非阻塞I/O本身没有通知机制。如果操作系统能代为"等待"然后通知，是不是就可以避免？

操作系统支持这样的事件通知机制——多路复用。**它的核心提效在于：一次调用获取N个I/O的就绪状态，从O(N)降为O(ready)**。多路复用把I/O分为两步：
- 等通知（阻塞，线程睡眠，OS代劳）
- 操作（非阻塞，线程工作，立即返回）

非阻塞I/O缺的通知机制，由select/epoll的阻塞来补。

(./问题演示_GIF/多路复用提效演示.png)

代码演示：60个连接中只有2个就绪，轮询每轮必须read()全部60个连接→60×5=300次，其中298次EAGAIN白跑。多路复用一次select返回就绪的2个，只对这2个read()→5次select+2次read=7次。扩大到10000连接，差距就是轮询5万次 vs 多路复用约15次。这就是O(N)→O(ready)的提效。

---

## 但是，select()不是又在阻塞吗？

事件就绪后，内核态切换到用户态，线程拿到了CPU控制权，但它怎么知道交给谁、执行什么？

这就是事件循环要解决的问题。

### 事件机制与回调

I/O状态的变化（未就绪→就绪）被多路复用封装为"就绪事件"。事件机制就是一套管理和响应这些事件的框架——事件注册→事件触发→事件处理。

具体流程：当单线程遇到I/O操作时，用一个Handle封装回调函数和参数，在EventLoop内部注册fd到Handle的映射，然后调用`selector.select()`交出控制权给内核等待I/O事件。内核监听到I/O就绪后，通知用户态，EventLoop执行对应的回调。

但这里有一个很反直觉的现象：我们费尽心思用非阻塞保住了控制权，转头却在`selector.select()`里把线程阻塞了。这不又回到同步阻塞的老路了吗？

要回答这个问题，必须严格区分"什么被阻塞了"和"为什么被阻塞"。这涉及到网络I/O本质的两步走：

1. **等待阶段（等数据就绪）**：网卡接收数据，内核把数据写入Socket的接收缓冲区。
2. **操作阶段（搬数据）**：调用recv()，把数据从内核缓冲区拷贝到用户态内存。

我们说的"阻塞"和"非阻塞"，到底是在阻塞哪个阶段？从三个维度看：

**维度一：被绑架 vs. 开盲盒**

同步阻塞：调用`sock_A.recv()`，线程被挂起，和sock_A死死绑定。如果A的数据10个小时后才来，线程就挂10个小时，哪怕sock_B、sock_C的数据早就准备好了——被单点绑架。

多路复用：调用`select()`，线程挂起，但此时线程是在同时等待10000个socket。只要其中任何一个数据准备好，内核就会唤醒你，此时的`recv()`是非阻塞的，可以处理已经就绪的数据——开盲盒，谁先来处理谁，绝不死等某一个。

**维度二：被迫交出 vs. 主动让出**

同步阻塞（被迫）：在执行业务逻辑的中途，被操作系统强行夺走控制权，上下文直接断绝。

多路复用（主动）：在EventLoop里，把所有就绪回调都处理完了，就绪队列空了，发现当前无事可做，才主动调用`select()`进入休眠。休眠前给操作系统定了规矩：如果有I/O来了就唤醒，或者到了多长时间无论如何都唤醒。

**维度三：CPU视角的零浪费**

非阻塞轮询：线程不交出CPU控制权，CPU满载跑while True，发热巨大但没干正事。

多路复用的阻塞：线程阻塞，CPU被彻底释放去执行别的进程。网卡中断传来时内核唤醒线程，CPU才开始执行回调。此时CPU执行的每一行代码，都是在处理确实已经就绪的数据，没有任何浪费。多路复用的阻塞，是对CPU资源的尊重——没有活儿的时候，绝不占用CPU哪怕一个周期。

等待期间的阻塞（通过多路复用）是可以接受的，我们真正要的是操作期间的非阻塞。等待时主动休眠，操作时绝不阻塞——两者结合，才真正实现单线程内的I/O重叠。

---

## EventLoop的调度设计：三队列、重入与timeout

理解了为什么等待阶段该阻塞，接下来看EventLoop怎么落地。

### 结构：为什么必须三条队列？

我们先把事件源归为两类：I/O事件和定时器事件。两类事件各自携带一个关键属性，属性差异直接决定容器的形态。

I/O事件到达时间不可预知——数据到达就是就绪态，排队等着被执行。定时器事件的到达时间预先指定——没到指定时间就是等待态，需要按时间排序。

由此产生两条天然约束：

**约束一：排序规则互斥。** I/O就绪事件遵循FIFO——谁先就绪谁先执行；定时器事件按时间戳排序——1秒后到期的必须排在5秒前面。一条队列无法同时满足两种排序规则。

**约束二：状态隔离。** I/O事件只有一种状态——就绪，直接入队即可。定时器事件有两种状态——等待和就绪。等待时不能执行，到期后和I/O事件没有区别。两者不能混在一个容器里。

还有一个隐式约束：

**约束三：防止饥饿。** 如果其中一个容器先出现就绪事件，且期间源源不断有新就绪事件到来，另一个容器中的事件会不断累积不能被消费。

这三条约束共同导致EventLoop必须采用分容器 + 统一就绪队列的设计：

- `_ready`: 就绪回调队列（deque，FIFO）
- `_scheduled`: 定时回调堆（heapq，按_when排序）
- `_selector`: I/O多路复用器（注册fd→回调映射）

三个事件源的到期事件统一汇入_ready，_ready只负责一件事：按FIFO消费就绪回调。

### 时序：重入问题与批次边界

_ready有一个关键特性：消费即生产。回调执行期间可能通过`call_soon()`产生新回调，新回调直接追加到_ready队尾。

想象一个TCP Echo服务器：读回调从socket读到数据，想立刻写回。但socket写缓冲区可能满了，不能直接写，于是调用`call_soon()`将写回调注册。`call_soon()`的内部实现正是把写回调追加到_ready末尾。

于是就在消费_ready的过程中，新的待消费项又被生产回了同一个_ready队列。极端情况下，消费同时源源不断生产——"无限消费"，永远回不到`select()`，I/O检查被饿死。

既然会饿死I/O检查，为什么还要这样设计？

答案是效率和止损的平衡。效率：服务器读后立即回复，这在逻辑上是"处理一个请求"的原子操作。如果写回调不被放入_ready立即执行，而是等到下一轮，这次"请求-响应"的生命周期就被强行延后，打破上层应用预期。

止损：如果`call_soon()`添加的回调必须等到下一次`_run_once()`才能执行，那么当_ready消费完后进入select等待I/O时，写回调虽然早已就绪却要被迫等待select返回。这等于让一个完全可以立即执行的任务，去等待相对慢得多的I/O——调度上的巨大不公平。

解决方案是批次边界：每轮_run_once消费回调前，先记下_ready当前的队列长度n，本轮只消费这n个，执行期间新增的不管。这保证了消费阶段不会因为回调嵌套而无限延长，让select()有机会在下一轮被调用。

### timeout：阻塞还是不阻塞？

批次消费完之后，_ready暂时空了。该轮到select()了。问题来了：select()要不要阻塞？

不阻塞（timeout=0）：select立刻返回，走一遍用户态→内核态→用户态的切换。如果没有新就绪事件，白跑。如果_ready频繁非空——繁忙服务器上是常事——每轮都做一次无意义的select(0)，CPU空转。

阻塞等待：有新事件才唤醒。但如果_ready里其实还有回调呢？select阻塞期间这些回调就饿在那。

asyncio的做法是根据当前状态切换：
- _ready非空 → timeout=0。不阻塞，立即处理已有回调。
- _ready空，有定时器 → timeout=最近定时器的到期时间减去现在。
- 两者皆空 → timeout=None。无限休眠，完全不占CPU。

这个三层判定不是优化细节——是正确性和性能之间的开关。选错了，要么饿死回调，要么CPU空转。

---

## 异步带来的复杂性

到目前为止，EventLoop能够轮询I/O就绪、能够调度定时器、能够消费回调——但它调度的"任务"还是传统函数。传统函数在异步场景有一个致命问题：一旦开始执行就占满调用栈直到返回，无法在I/O等待点主动暂停。这是物理上的约束——C语言就是这样设计的，函数调用栈是一根连续的链条，没有人能在中间剪一刀再接回去。

如果只是回调嵌套回调，遇到I/O照样得等。这不又回去了？

要打破这个局面，就必须让函数能在I/O等待点主动暂停、交出控制权、保存当前状态、等I/O就绪后再恢复——协程。

但问题没有结束。引入协程之后，你会发现同步编程里很多"理所当然"的事情都消失了。这些事情不是逐个发现的——当你放弃了串行执行，它们就像一件衣服上的四颗扣子，撕开的同时全部崩掉：

**第一个：执行上下文放哪？** 同步模型里，函数执行期间栈帧天然连续，函数返回自动释放。但协程暂停了——局部变量、指令位置保存在哪？谁来保管这些"暂停的灵魂"？

**第二个：结果怎么传回来？** 同步模型里，`result = read()`——返回值就在栈上的变量里，天经地义。但协程await之后栈帧退场了，它不是"阻塞在原地等"，而是"先撤了，等别人叫醒"。结果在未来某个时刻到达时，接收结果的人已经不在原地了。

**第三个：执行顺序还能保证吗？** 同步模型里，语句一行接一行，执行顺序就是书写顺序。但当你有了成百上千个可以切来切去的控制流碎片——谁先谁后？谁能取消？谁依赖谁？

**第四个：任务的生命周期谁管？** 同步模型里，函数返回意味着资源可以安全释放、子任务全部完成。但协程世界里，一个Task可能在父协程结束后还在跑，异常可能被静默吃掉，没有人替它收尸。

这四件事不是Python的问题，不是asyncio的问题。Node.js的callback hell踩了前两个，Go的goroutine泄漏踩了第四个，Java的CompletableFuture链式调用踩了第一个。任何异步系统都绕不开这四道坎。

但解决有先后——必须先修地基再盖楼。得先让函数能暂停和恢复，才能有一个"挂起点"来接收结果；有了结果锚点才能桥接内核边界；有了完整数据流才能做时序协调；有了协调才能做生命周期管理。

---

## 让函数能暂停——协程与Task

先解决最基础的：上下文悬空。

传统函数调用栈是刚性的：main→f()→g()→h()，整条链一气呵成，不能"断开再接上"。h()阻塞→g()阻塞→f()阻塞→main阻塞——一阻全阻。EventLoop虽然能监听I/O就绪并执行回调，但回调本身就是一个函数——它开始执行后就不能被中断，直到返回。

Python的协程（generator/coroutine）提供了yield/await机制——这是一种结构断点。当协程执行到`await some_io()`时：

1. 当前指令位置、局部变量被冻结——不是保存在C栈上，而是保存在生成器帧对象中（堆上）。
2. yield出一个Future对象。
3. 控制权从协程返回给调用者（EventLoop的_run_once）。
4. 栈帧回退，但协程的"灵魂"（状态）还活着，在堆上等待。

Task就是把这个"活着的灵魂"包装为EventLoop可调度的单元。它持有协程对象，用两个函数交替驱动：

- **__step（推）**：调用`coro.send()`推动协程前进到下一个await断点。协程yield出一个Future后，如果这个Future还没完成，__step就在Future上注册`add_done_callback(self.__wakeup)`，然后把Future设为`_fut_waiter`——这是断点锚定，标记了"我在等谁"。Task挂起，从_ready中消失。

- **__wakeup（拉）**：当被等待的Future就绪时，Future通过回调链将__wakeup注入_ready。__wakeup执行时取出future.result()，然后调用`self.__step(exc)`——把结果或异常传回协程，协程从断点处恢复执行。

这个双阶段驱动是asyncio最核心的设计。本质上它是把"传统函数调用栈的连续压栈"切成了可暂停的片段。每个await都是结构断点——断点前协程在跑，断点处状态冻结，断点后EventLoop可以自由切换到其他就绪的Task。

取消信号怎么在断点间传播？Task可能挂在Future上等待，也可能正在_ready中排队等待被__step驱动。cancel()调用时，如果Task挂在Future上，cancel会调用`_fut_waiter.cancel()`传播到下游，同时置`_must_cancel=True`。下次__step执行时检测到_must_cancel，向协程注入CancelledError。如果在_ready中排队，__step被调度时同样检测并注入。无论哪种状态，取消信号都不丢。

---

## 让结果能传回来——Future

栈帧能暂停了，协程能挂起了。但`await`之后，结果怎么传回来？

同步函数里，`result = read()`——结果直接出现在栈上的变量里。但协程await之后栈帧回退了——它不是"阻塞在原地等"，而是"退场了，等别人叫醒"。那么谁来保存这个结果？谁在结果到达时通知"回来取"？

这就是Future。它是一个有限状态机，只有三个状态：

```
PENDING → FINISHED（成功设值）
PENDING → CANCELLED（被取消）
```

转换是单向不可逆的。为什么？因为并发场景下多个生产者可能争抢设值——两个set_result同时到达，谁赢？如果允许覆盖，第二个调用者永远不知道"我的结果被踩了吗"。只有单向不可逆才能保证结果的唯一性：先成功转换状态的赢，其余的静默返回失败。

Future的核心机制是回调链。当有人调用`future.set_result(value)`时，_state从PENDING转为FINISHED，然后触发`__schedule_callbacks`——遍历_callbacks列表，把每一个已注册的回调通过`call_soon`注入_ready。Task.__wakeup就在其中。下一个_run_once循环中，Task被唤醒，取出结果，继续执行。

这就是跨任务边界的唤醒通道：Task_A await Future后挂起→Task_B调用future.set_result()→Future把Task_A.__wakeup推入_ready→Task_A恢复。

但这里有一个边界条件：如果set_result之后才有人注册回调怎么办？add_done_callback在状态非PENDING时会直接call_soon立即调度——不走_callbacks队列。两条回调路径看似多余，防止的是"晚注册的等待者永远收不到通知"这个更致命的bug。

---

## 填补断崖：把内核I/O事件转化为Future的set_result()

Future只是一个用户态的状态容器。它不知道操作系统何时产生数据。谁来调用`set_result()`？

需要一个组件下探到内核I/O边界，把selector/IOCP的通知翻译为Future的状态变迁。这就是Transport和Protocol的1:1配对。

**Transport管"怎么收发字节"**。它持有非阻塞socket，注册到EventLoop的selector上。当selector报告fd可读时，Transport._read_ready()被EventLoop回调，执行`sock.recv()`从内核缓冲区读取字节，然后调用`protocol.data_received(data)`把数据交给业务层。当业务层需要写数据时，调用`transport.write(data)`，Transport将数据暂存写缓冲区，注册fd可写事件，待selector通知可写时执行`sock.send()`。

**Protocol管"收到字节后做什么"**。它只实现connection_made、data_received、connection_lost等回调接口，完全不知道socket的细节。当它从data_received中收到完整数据后，调用`future.set_result()`完成状态锚定。

为什么必须分离？如果Transport内置业务逻辑，插入SSL层就需要重写整个I/O层。如果Protocol知道socket细节，就无法跨平台。分离后，加SSL只需一个SSLProtocol夹在中间——对下的Transport和对上的Protocol都不需要改动。

还有一个容易被忽略的设计：写缓冲流控。非阻塞write()可能只写入部分数据，剩余暂存_transport._buffer。如果业务层持续write()不节制，_buffer无限膨胀直至内存爆满。Transport的做法是：当_buffer超过阈值（64KB），调用`protocol.pause_writing()`通知"暂停生产"；当清空后调用`resume_writing()`。业务层如果不响应pause/resume，流控形同虚设——这是Transport和Protocol之间的隐式契约。

至此，从内核I/O就绪→Transport读字节→Protocol解析→Future.set_result()→Task.__wakeup→协程恢复的完整数据流闭环建立。

---

## 让并发有序——同步原语

I/O通道通了。协程能暂停和恢复了。结果能传回来了。

但现在有一千个Task在跑。它们要访问同一个共享状态。在单线程里没有真正的"并发写入"问题——同一时刻只有一个协程在执行，两个await之间代码是原子的。但如果一个协程在"检查状态"和"修改状态"之间await了——另一个协程可能插进来改了状态，第一个协程恢复后基于过时信息继续操作，逻辑错误。

这不是数据竞争（单线程没有数据竞争），这是**逻辑互斥违反**——你await的间隙里世界变了。

asyncio的同步原语族就是解决这个问题的：Lock、Event、Condition、Semaphore。它们的核心实现出奇统一——内部全部使用Future作为等待器。

以Lock为例：协程A调用`await lock.acquire()`。如果锁空闲，直接获取，不创建Future（快速路径）。如果锁已被协程B持有，acquire内部创建一个Future，把自己放进去，然后await这个Future——协程A挂起。当协程B调用`lock.release()`时，从等待队列取出协程A的Future，调用`set_result()`——协程A的__wakeup被注入_ready，下一轮恢复执行，获得了锁。

这里有一个精妙之处：所有同步原语的"等待"行为都是通过await Future实现的，所有"唤醒"都是通过Future.set_result()实现的。纯用户态，没有任何系统调用。正因为整个协调机制依赖的是Future→call_soon→Task.__wakeup这个单线程闭环，所以它可以轻松运行数万个协程而不需要内核参与。

Queue是这个家族的实用成员：生产者满时等消费者，消费者空时等生产者——两端各自await各自的Future，互相唤醒。和Go的channel不同，asyncio的Queue没有容量上限语义（可以用maxsize限制），但零拷贝直接传递对象是同样的高效。

---

## 让任务有家——结构化并发

最后一块：宏观秩序。

裸`create_task()`创建一个Task后，它就开始跑了。但谁来管它的生命周期？父协程退出后它可能还在跑——这叫"孤儿Task"；它如果抛了异常，异常去了哪？——默认只打一行日志，程序静默继续跑；外部想取消它，怎么保证取消信号能传到？

这三个问题的本质是同一个：Task没有作用域约束。

**TaskGroup** 解决了这个问题。它的核心语义是：`async with`块内的所有Task，在退出块之前必须全部完成。如果其中任何一个Task异常退出，块内其他Task会被取消，异常被收集为ExceptionGroup向上传播。

这看似只是"语法糖"，但实际上解决了一个根本问题：异常不能再被静默吞掉。裸create_task的异常只打日志，因为Task创建时没有"有人会来收这个异常"的契约。TaskGroup建立了这个契约——用户在async with作用域内显式声明"这些Task归我管"，退出时所有结果或异常强制归集。

**Timeout** 是另一块拼图。它解决的是"把时间限制转化为协程可感知的取消"。核心机制是：进入`async with timeout(5)`时创建一个TimerHandle，5秒后触发；触发时调用`task.cancel()`向被包装的协程注入CancelledError；退出timeout块时调用`task.uncancel()`——这里有一个精巧设计：`_cancelling`计数器。cancel()+1，uncancel()-1。如果timeout触发了cancel但协程内部已经捕获并处理了（cancelling归零），那么timeout不抛异常。只有当cancel没有被内部消化时（cancelling>0），timeout才抛出TimeoutError。这区分了"超时取消"和"外部取消"——如果外部cancel和timeout叠在一起，uncancel不能误恢复应该传播的外部取消。

**Runner** 是最外层的容器：管理EventLoop从创建到关闭的完整生命周期——创建loop→运行主协程→清理异步生成器和线程池→关闭loop→处理信号。

---

## 闭环：一次完整的旅程

现在回头看`asyncio.run(main())`这一行代码背后发生了什么：

```
Runner.__enter__ → 创建EventLoop
  Runner.run(main) → Task包装main协程 → __step首次驱动入_ready
    main协程执行到 await some_io()
      → Task.__step: coro.send()推进到yield断点
      → 协程yield Future → __step注册__wakeup到Future
      → Task挂起，_fut_waiter锚定
    EventLoop._run_once每轮循环:
      → 计算timeout（三层判定）
      → select(timeout)等待内核I/O通知
      → 到期定时器从堆移入_ready
      → 消费n个就绪回调（批次边界）
    selector通知fd可读 → Transport._read_ready()
      → sock.recv()读字节
      → protocol.data_received(data)
      → 业务层解析后调用 future.set_result()
      → __schedule_callbacks遍历回调列表
      → call_soon(Task.__wakeup)入_ready
    Task.__wakeup被消费 → 取future.result()
      → call self.__step(exc)恢复协程
  main协程继续执行...
  Runner.run退出 → shutdown_asyncgens + shutdown_executor → loop.close
Runner.__exit__ → 资源释放
```

这条链上每一环都能往前回溯到选择异步时崩掉的那四件事：执行上下文放哪——Task和__step/__wakeup接住了；结果怎么传回来——Future和回调链接住了；执行顺序还能保证吗——同步原语接住了；任务的生命周期谁管——TaskGroup和Timeout和Runner接住了。

这不是巧合。选择异步的那个瞬间，四项保证同时崩塌。重建不是"走一步看一步"的偶然发现，而是必须按照构建依赖——先修地基再盖楼——逐一重新建立。EventLoop用三队列和timeout开辟了时序空间，协程在里面暂停和恢复，Future锚定了未来的结果，Transport桥接了内核与用户态，同步原语协调了碎片化的控制流，TaskGroup收束了满天飞的任务。

这就是asyncio的完整设计理性。

---

## 附录

### 多线程弊端简述

操作系统抢占式调度线程。"抢占式"+"线程"叠加GIL会导致：内核态隐式切断产生不可复现的"幽灵BUG"；线程共享内存迫使全面加锁，锁竞争和死锁风险随规模指数增长；GIL使CPU密集型多线程无加速；每个线程默认8MB栈内存——1万并发=80GB内存。

### Asyncio解决了多线程的哪些痛

协程只在await处显式让出控制权，两个await之间代码完全原子，大多数场景不需要锁。整个事件循环跑在一个线程里，GIL不再是被争抢的资源。协程是用户态对象，创建成本极低，切换只是函数调用级操作，轻松运行数万协程。


## 演示

### 轮询
```python
import socket, time

def step2_nonblocking_and_busy_wait():
    sock = socket.socket()
    sock.setblocking(False)
    print("[非阻塞模型] 尝试连接...")
    try:
        sock.connect(("1.1.1.1", 9999))
    except BlockingIOError:
        print("[非阻塞模型] 连接进行中，线程没卡死，可以干别的！")
    print("[非阻塞模型] 但怎么知道连接成功了？只能死循环问 OS...")
    start = time.perf_counter()
    loops = 0
    while time.perf_counter() - start < 0.01:
        try:
            sock.send(b"")
            break
        except (BlockingIOError, OSError):
            loops += 1
    print(f"[非阻塞模型] 10ms 内循环问了 OS {loops} 次！")

step2_nonblocking_and_busy_wait()
```

### 多路复用提效证明
```python
import socket, select, time, threading

N = 60
server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(("127.0.0.1", 0))
port = server.getsockname()[1]
server.listen(N)

server_conns = []
def accept_all():
    for _ in range(N):
        conn, _ = server.accept()
        server_conns.append(conn)
    server_conns[10].send(b"Hi")
    server_conns[50].send(b"Yo")

threading.Thread(target=accept_all, daemon=True).start()

client_conns = []
for _ in range(N):
    s = socket.socket()
    s.connect(("127.0.0.1", port))
    s.setblocking(False)
    client_conns.append(s)

time.sleep(0.3)

mux_calls, mux_reads, mux_hits = 0, 0, 0
for _ in range(5):
    r_list, _, _ = select.select(client_conns, [], [], 0.1)
    mux_calls += 1
    for s in r_list:
        try:
            data = s.recv(64)
            mux_reads += 1
            if data: mux_hits += 1
        except OSError: pass

server_conns[10].send(b"Hi"); server_conns[50].send(b"Yo")
time.sleep(0.1)

poll_reads, poll_hits = 0, 0
for _ in range(5):
    for s in client_conns:
        try:
            data = s.recv(64)
            poll_reads += 1
            if data: poll_hits += 1
        except BlockingIOError: poll_reads += 1
        except OSError: pass

total_mux = mux_calls + mux_reads
print(f"connections={N}, ready=2, rounds=5\n")
print(f"polling:  {poll_reads} read() calls, {poll_hits} hits, waste={poll_reads-poll_hits} ({(poll_reads-poll_hits)/poll_reads*100:.0f}%)")
print(f"mux:      {mux_calls} select + {mux_reads} read = {total_mux} calls, {mux_hits} hits")
print(f"\n=> {N} connections only 2 ready: polling={poll_reads} vs mux={total_mux}")
print(f"=> 10000 connections 5 rounds: polling=50000, mux~15")
print(f"=> poll is O(N), mux is O(ready)")

for s in client_conns: s.close()
for s in server_conns: s.close()
server.close()
```
