## E06: Selector + Proactor

```
╔═══════════════════════════════════════════════════════════╗
║  【I/O 多路复用器】Selector / Proactor                     ║
║  编号: E06 | 来源: asyncio.selctors / asyncio.proactor   ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 I/O 多路复用的操作系统机制封装，Selector (select/poll/epoll) 用就绪通知模型，Proactor (IOCP) 用完成通知模型，二者实现同一功能的不同 OS 抽象。

【冲突溯源】 归属于 S3 推导链节点 N3 的设计选择 D4（边界闭合）

【设计内因】 D4工程目标: 屏蔽OS差异，统一为select(timeout)/_poll(timeout)接口，使上层EventLoop无需感知内核I/O通知的机制差异
  通用困境: {就绪通知vs完成通知困境(边界): 操作系统I/O多路复用分为两种根本不同的模型——就绪通知(select/epoll: "可以读了")和完成通知(IOCP: "读完了")，二者的注册/通知/数据获取流程完全不同，统一抽象是所有跨平台异步框架的难题; 最优机制选择困境(性能): 同一OS上存在多种I/O多路复用机制(select/poll/epoll/kqueue)，必须在运行时自动选择最优实现——简单机制有问题规模限制，高效机制有兼容性风险}
  SC1(边界): [就绪vs完成]Selector和Proactor的回调签名和数据流方向完全不同——Selector返回(fd, events)让用户态读，Proactor返回(overlapped, bytes)已读完——若不统一接口则EventLoop需两套处理逻辑[接口契约] → 统一select(timeout)接口: Selector.select()返回[(fd, events)]由EventLoop._process_events分发，Proactor._poll()返回已完成的overlapped由EventLoop._process_events分发，上层只看到"有I/O事件需要处理" | 代价: 两种模型的内部差异无法完全抹平——Proactor模式下Transport.recv是_RecvOverlapOp(先发异步操作再等完成)，Selector模式下Transport直接调用sock.recv()
  SC2(实体): [最优机制]select()有fd数量限制(1024)且O(n)扫描——千级并发连接下性能不可接受，必须自动选择epoll/kqueue[性能] → DefaultSelector自动选择: selectors模块在导入时检测可用的最高效机制(epoll>kqueue>poll>select)，DefaultSelector指向最优实现 | 代价: 不同平台行为不一致—Linux用epoll(水平触发)、macOS用kqueue、Windows只能select(非IOCP场景)，调试需考虑平台差异
  SC3(边界): [就绪vs完成]Proactor模式下异步操作必须在poll前发起(WSARecv)——若不提前发起则IOCP无完成事件可返回，与Selector的"先注册fd再等就绪"模式时序相反[边界条件] → Proactor.recv()预发起: Transport在连接建立时就调用_proactor.recv(sock, bufsize)发起WSARecv操作，IOCP完成时直接返回数据 | 代价: Proactor模式需要为每个I/O操作维护overlapped结构(_cache字典)，内存开销大于Selector模式

【结构】"它长什么样？" ★
两种模式二选一，不可同时使用：
- Unix: `_SelectorEventLoop` → `selectors.DefaultSelector` → epoll/kqueue/poll
- Windows: `_ProactorEventLoop` → `overlapped.IOCP`

设计意图：屏蔽 OS 差异，统一为 `select(timeout)` / `_poll(timeout)` 接口。

【时序】"它按什么顺序动？" ★★
I/O 多路复用的阻塞→唤醒时序：

```
Selector 模式 (ready-triggered / level-triggered):
  selector.register(fd, events, data=transport)
  → fd 添加到监听集合

  selector.select(timeout):
    → 阻塞直到:
      - 至少一个 fd 就绪 (readable/writable)
      - 或 timeout 到期
      - 或被信号中断
    → 返回 [(fd, events), ...]
    → 每个 (fd, events) 对应一个 Transport 回调

  醒后: EventLoop 遍历返回列表，调用 transport._read_ready/_write_ready

Proactor 模式 (completion-triggered):
  先发起异步操作: WSARecv(sock, overlapped)
  → 操作挂起，不阻塞

  proactor._poll(timeout):
    → GetQueuedCompletionStatus(timeout)
    → 返回已完成的 overlapped 操作
    → 调用对应的 callback (future.set_result)

  区别: Selector 告诉你"可以读了"，Proactor 告诉你"读完了"
```

【实体】"它的最小数据单元？" ★
- Selector: `_selector` (底层 selector 对象)，`_map: {fd: SelectorKey}`
- Proactor: `_iocp` (IOCP 句柄)，`_cache: {overlapped: operation}`

【边界】"它在哪里交出控制权？" ★★★
**系统调用跨越内核边界**：

```
┌─────────────────────────────────────────────────┐
│  用户态                                          │
│  selector.select(timeout)                       │
│    → 系统调用: epoll_wait() / WaitForMultiple.. │
└──────────┬──────────────────────────────────────┘
           │ syscall 边界
┌──────────▼──────────────────────────────────────┐
│  内核态                                          │
│  epoll 实例监控 fd 集合                          │
│  IOCP 完成队列等待                               │
│  → I/O 就绪/完成 → 返回到用户态                   │
└──────────┬──────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────┐
│  用户态                                          │
│  EventLoop 处理返回的事件                         │
│  → 调用 Transport 回调                           │
└─────────────────────────────────────────────────┘
```

这是 asyncio 最底层的边界——系统调用是用户态→内核态的唯一通道。所有异步 I/O 的"非阻塞"语义建立在此边界上：select/poll 让出线程给内核，内核在有事件时唤回。

【内部关联】
- EventLoop._run_once:selector.select() --[系统调用(轮询者→内核边界)]--> 内核  [E01→内核边界]
- Selector.select() --[就绪返回(事件检测者→事件分发者)]--> EventLoop._process_events  [E06→E01]
- Selector.register(fd, events, data) --[注册(I/O监听注册者←传输注册方)]←-- Transport  [E06←E05]
- Proactor._poll() --[完成返回(完成检测者→事件分发者)]--> EventLoop._process_events  [E06→E01]
- Proactor.recv() --[发起异步操作(操作发起者←传输请求方)]←-- Transport  [E06←E05]

【示例】
```python
# Unix: _SelectorEventLoop 默认使用 epoll
import selectors
sel = selectors.DefaultSelector()  # → EpollSelector
sel.register(sock, selectors.EVENT_READ, data=transport)
events = sel.select(timeout=1.0)   # → epoll_wait()
for key, mask in events:
    key.data._read_ready()         # → Transport 回调

# Windows: _ProactorEventLoop 使用 IOCP
# recv = loop._proactor.recv(sock, bufsize)
# → WSARecv + overlapped → future
# → IOCP 完成通知 → future.set_result(bytes_read)
```

---

## E07: 同步原语族

```
╔═══════════════════════════════════════════════════════════╗
║  【协程间协调器】同步原语族                                ║
║  编号: E07 | 来源: asyncio.locks / asyncio.semaphore      ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 基于 Future 的协程间时序协调机制，提供互斥、信号量、条件变量等同步语义，全部通过 _waiters Future 队列实现阻塞/唤醒。

【冲突溯源】 归属于 S3 推导链节点 N4 的设计选择 D5（时序补充）

包含的实体：`Lock`, `Event`, `Condition`, `Semaphore`, `BoundedSemaphore`

【设计内因】 D5工程目标: 提供标准同步语义(Lock/Event/Condition/Semaphore)，将线程同步语义适配到单线程协程世界，保证acquire/release的时序协调正确
  通用困境: {等待队列抽象困境(时序+实体): 所有同步原语的核心是"条件不满足时挂起+条件满足时唤醒"——挂起需要创建占位对象(Future)入队，唤醒需要从队列取出并set_result，这个模式在Lock/Event/Semaphore中完全相同，但各自的条件判断逻辑不同; 快速路径vs等待路径分支困境(时序): 无竞争时acquire应立即返回(快速路径)，有竞争时才创建Future挂起(等待路径)——若总是创建Future则无竞争场景下产生不必要的对象分配和调度开销}
  SC1(时序): [快速vs等待]无竞争时acquire必须直接返回而不创建Future——若每次acquire都创建Future则即使无竞争也有call_soon→__wakeup→__step的调度链开销[性能] → 快速路径检查: Lock检查!_locked直接置位返回True, Semaphore检查_value>0直接递减返回, 不创建Future | 代价: acquire有两条代码路径(快速/等待)，实现和维护需保证二者语义一致
  SC2(时序): [等待队列]有竞争时acquire必须创建Future挂起等待——若不挂起则acquire立即返回但锁未持有，违反互斥语义[正确性] → _waiters Future队列: fut=loop.create_future()入_waiters, await fut挂起, release时从_waiters取出fut.set_result(True)唤醒首名等待者 | 代价: _waiters是deque保FIFO但不保证公平性(新acquire可能抢到快速路径)
  SC3(时序): [等待队列]Event.set()必须唤醒所有等待者且不可遗漏——若只唤醒一个则其他await event.wait()的协程永久挂起[正确性] → 遍历唤醒: Event.set()遍历_waiters逐一set_result(True)后clear(), Lock.release()只popleft首名等待者(互斥语义) | 代价: Event.set()唤醒所有等待者但它们的执行顺序取决于EventLoop._ready的调度顺序而非_waiters的顺序
  SC4(边界): [快速vs等待]Condition.wait()必须先释放Lock再挂起——若持有Lock挂起则其他协程无法进入临界区(死锁)[正确性] → wait()中先self.release()释放底层Lock, await fut挂起, 被唤醒后await self.acquire()重新获取Lock | 代价: wait→notify→re-acquire之间有微小的时间窗口，其他协程可能在这个窗口抢到Lock(非公平)

【结构】"它长什么样？" ★★
全部基于 `_waiters: deque[Future]` 的相似结构：

```
Lock:       _locked=False, _waiters=deque[Futures]
Event:      _value=False, _waiters=deque[Futures]
Condition:  _lock=Lock,  _waiters=deque[Futures]  (Lock + 额外等待队列)
Semaphore:  _value=int, _waiters=deque[Futures]
BoundedSemaphore: _value=int, _bound=int, _waiters=deque[Futures]
```

设计意图：统一模式——等待者创建 Future 并入 _waiters，释放者从 _waiters 取出 Future 并 set_result。每个原语只有一个核心状态字段（_locked / _value）驱动行为。

【时序】"它按什么顺序动？" ★★★
**acquire → await Future → release → set_result 的时序协调**：

```
Lock.acquire():
  if not _locked:
    _locked = True              ← 快速路径：无竞争直接获取
    return True
  else:
    fut = loop.create_future()  ← 创建等待 Future
    _waiters.append(fut)
    await fut                   ← 挂起当前 Task（yield fut → _fut_waiter=fut）
    return True                 ← 被唤醒后返回

Lock.release():
  _locked = False
  if _waiters:
    fut = _waiters.popleft()
    fut.set_result(True)        ← 唤醒等待者 → __schedule_callbacks
                                  → call_soon(waiter.__wakeup)
                                  → 下轮 __step 恢复

Event.set():
  _value = True
  for fut in _waiters:
    fut.set_result(True)        ← 唤醒所有等待者
  _waiters.clear()

Event.clear():
  _value = False                ← 后续 wait() 将创建新 Future

Condition.wait():
  fut = loop.create_future()
  _waiters.append(fut)
  self.release()                ← 释放底层 Lock，允许其他协程进入
  await fut                     ← 等待 notify
  await self.acquire()          ← 重新获取 Lock

Condition.notify(n=1):
  for i in range(n):
    fut = _waiters.popleft()
    fut.set_result(True)        ← 唤醒 n 个等待者

Semaphore.acquire():
  if _value > 0:
    _value -= 1                 ← 快速路径
    return True
  else:
    fut = loop.create_future()
    _waiters.append(fut)
    await fut                   ← 等待
    return True

Semaphore.release():
  _value += 1
  if _waiters:
    _value -= 1                 ← 直接传递给等待者，不浪费
    fut = _waiters.popleft()
    fut.set_result(True)
```

时序核心：每个原语都是"条件检查 + Future 挂起 + set_result 唤醒"的三段式。这是所有同步原语统一的时间协调模式。

【实体】"它的最小数据单元？" ★★
- Lock: `_locked: bool` — 驱动 acquire 快速/等待分支
- Event: `_value: bool` — 驱动 wait 快速/等待分支
- Semaphore: `_value: int` — 驱动 acquire 计数递减/等待分支
- Condition: `_lock: Lock` + 自有 `_waiters` — 复合结构
- 所有原语共享: `_waiters: deque[Future]` — 等待队列，驱动唤醒

【边界】"它在哪里交出控制权？" ★
纯用户态，无系统调用边界。所有协调通过 Future 的 set_result → call_soon 在 EventLoop 内完成。

【内部关联】
- Lock.release() --[唤醒(释放者→获锁等待者)]--> Future.set_result(True) → waiter.__wakeup  [E07→E03]
- Event.set() --[广播唤醒(信号发布者→信号等待者)]--> Future.set_result(True) → waiters  [E07→E03]
- Condition.wait() --[释放(等待者→锁释放者)]--> Lock.release()  [E07 自环]
- Condition.notify() --[选择唤醒(通知者→被通知者)]--> Future.set_result(True)  [E07→E03]
- Semaphore.release() --[唤醒(令牌归还者→令牌等待者)]--> Future.set_result(True)  [E07→E03]
- 同步原语._waiters --[创建(占位创建者→Future工厂)]←→ loop.create_future()  [E07→E03]

【示例】
```python
lock = asyncio.Lock()

async def worker(n):
    async with lock:            # acquire() → _locked=True 或 await Future
        print(f"worker {n} working")
        await asyncio.sleep(0.1)
    # release() → _locked=False → 唤醒下一个等待者

async def main():
    await asyncio.gather(*[worker(i) for i in range(3)])
    # 串行执行：worker 0 → worker 1 → worker 2
```

---

## E08: Queue

```
╔═══════════════════════════════════════════════════════════╗
║  【异步数据通道】Queue                                     ║
║  编号: E08 | 来源: asyncio.queues                         ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 异步生产者-消费者数据通道，通过 Future 队列协调 put/get 的时序，实现有界缓冲的流控。

【冲突溯源】 归属于 S3 推导链节点 N4 的设计选择 D5（时序补充）

【设计内因】 D5工程目标: 提供异步生产者-消费者数据通道，双向协调put/get时序，支持有界缓冲流控和任务完成同步(join/task_done)
  通用困境: {双向等待困境(时序): 生产者-消费者系统中，生产者等消费者腾出空间(get)、消费者等生产者提供数据(put)——两个方向的等待必须独立协调，否则死锁(生产者满时put挂起但消费者也在等put); 直接传递优化困境(时序+性能): 有消费者等待时生产者数据可直接传递不经缓冲区——零拷贝减少一次入队出队，但与缓冲区路径的语义一致性需保证}
  SC1(时序): [双向等待]_queue空时get必须挂起等待——若不挂起则返回None或抛异常，语义上不符合"阻塞直到有数据"的契约[正确性] → _getters Future队列: _queue空时fut=loop.create_future()入_getters, await fut挂起, put时从_getters取出fut.set_result(item) | 代价: 需要维护两个方向的独立等待队列(_getters+_putters)
  SC2(时序): [双向等待]maxsize>0时_queue满put必须挂起等待——若不限制则_queue无限增长OOM，但不挂起则生产者不知道已满[边界条件] → _putters Future队列: _queue满时fut=loop.create_future()入_putters(附item), await fut挂起, get时从_putters取出(fut, item)将item入_queue并fut.set_result(True) | 代价: _putters中暂存了(fut, item)对——item引用被持有，若item大则内存占用持续
  SC3(时序): [直接传递]有_getters等待时put应直接传递不经_queue——若先入_queue再由get取出则多一次append+popleft的开销[性能] → 零拷贝: put时若_getters非空则getter.set_result(item)直接传递，不经_queue缓冲 | 代价: 直接传递和缓冲传递是两条代码路径，调试时数据流判断更复杂
  SC4(实体): [任务完成同步]join必须等待所有已put的item被task_done——若_unfinished_tasks计数不准则join提前返回(数据丢失)或永久挂起(卡死)[正确性] → _unfinished_tasks计数器: put时+1, task_done时-1, 归零时_set_result唤醒joiners | 代价: 调用方必须每get一次就task_done一次——若忘记调用则join永久挂起(编程契约易违约)

【结构】"它长什么样？" ★★
三队列复合结构：
- `_queue: deque` — 实际数据缓冲
- `_getters: deque[Future]` — 等待数据的消费者
- `_putters: deque[Future, item]` — 等待空间的阻塞生产者（maxsize 满时）

设计意图：_getters 和 _putters 各自是独立的等待队列，两个方向独立协调。当 _queue 有数据时 get 立即返回，当 _queue 有空间时 put 立即返回，否则挂起。

【时序】"它按什么顺序动？" ★★★
**put → await putter; get → await getter 的时序协调**：

```
put(item):
  if _getters:                          ← 有消费者在等
    getter = _getters.popleft()
    getter.set_result(item)             ← 直接传递，不经 _queue（0-copy 优化）
    _unfinished_tasks += 1
  elif self.full():                     ← _queue 满（maxsize > 0）
    fut = loop.create_future()
    _putters.append((fut, item))        ← 生产者挂起
    await fut                           ← 等待消费者腾出空间
    _unfinished_tasks += 1
  else:                                 ← _queue 有空间
    _queue.append(item)                 ← 入队
    _unfinished_tasks += 1

get():
  if _putters:                          ← 有阻塞的生产者
    fut, item = _putters.popleft()
    _queue.append(item)                 ← 先让生产者的数据入队
    fut.set_result(True)                ← 唤醒生产者
    if _getters:                        ← 还有其他消费者在等？
      # 循环处理
    return item if not _queue else _queue.popleft()
  elif _queue:                          ← _queue 有数据
    item = _queue.popleft()
    _unfinished_tasks -= 1
    return item
  else:                                 ← _queue 空
    fut = loop.create_future()
    _getters.append(fut)                ← 消费者挂起
    return await fut                    ← 等待生产者

task_done():
  _unfinished_tasks -= 1
  if _unfinished_tasks == 0:
    if _joiners:
      for fut in _joiners:
        fut.set_result(True)            ← 唤醒 join 等待者

join():
  if _unfinished_tasks == 0:
    return
  fut = loop.create_future()
  _joiners.append(fut)
  await fut                             ← 等待所有 task_done
```

时序核心：**双向协调**——put 和 get 互相唤醒。生产者满时挂起等待消费者，消费者空时挂起等待生产者。这是比单向同步原语更复杂的时序协调。

【实体】"它的最小数据单元？" ★★
- `_maxsize: int` — 队列容量上限，0 表示无限；驱动 full() 判断和 putter 创建
- `_unfinished_tasks: int` — 未完成的任务计数；驱动 join() 的完成判断
- `_queue: deque` — 实际数据存储
- `_getters` / `_putters` — 两个方向的等待队列

【边界】"它在哪里交出控制权？" ★
纯用户态，同 E07。通过 Future.set_result → call_soon 在 EventLoop 内协调。

【内部关联】
- Queue.put(item) --[直接传递(生产者→饥饿消费者)]--> getter.set_result(item)  [E08→E03]
- Queue.get() --[唤醒生产者(消费者→阻塞生产者)]--> putter.set_result(True)  [E08→E03]
- Queue.task_done() --[完成信号(消费确认者→汇合等待者)]--> joiner.set_result(True)  [E08→E03]
- Queue._getters --[创建(等待占位者→Future工厂)]←→ loop.create_future()  [E08→E03]
- Queue._putters --[创建(等待占位者→Future工厂)]←→ loop.create_future()  [E08→E03]

【示例】
```python
q = asyncio.Queue(maxsize=2)

async def producer():
    for i in range(5):
        await q.put(i)    # 0,1 直入; 2 时 _queue 满 → await putter
        print(f"produced {i}")
    await q.join()        # 等待所有 task_done

async def consumer():
    for i in range(5):
        item = await q.get()   # _queue 有数据直接取; 空则 await getter
        print(f"consumed {item}")
        q.task_done()          # _unfinished_tasks -= 1
```

---

## E09: StreamReader + StreamWriter

```
╔═══════════════════════════════════════════════════════════╗
║  【流式I/O接口】StreamReader / StreamWriter                ║
║  编号: E09 | 来源: asyncio.streams                        ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 Protocol/Transport 的高层封装，将回调驱动的 I/O 转化为 async/await 流式接口，同时实现数据缓冲与背压流控。

【冲突溯源】 归属于 S3 推导链节点 N3/D4（Transport 边界桥接）+ N4/D5（流控时序协调）

【设计内因】 D4+D5工程目标: 将Protocol/Transport的回调驱动I/O转化为async/await流式接口，同时实现数据缓冲与drain()流控
  通用困境: {回调→协程范式转换困境(边界+时序): 底层I/O是"推"模型(内核通知→回调执行)，上层是"拉"模型(await read()→需要数据时才执行)——两种范式的转换需要缓冲区解耦和Future桥接; 缓冲区膨胀困境(边界): 回调推入数据的速度可能远快于用户态消费速度——若无背压机制则bytearray缓冲区无限膨胀，这是所有流式I/O接口的共性问题(Netty的WaterMark、Node.js的drain事件都是同源解法)}
  SC1(边界): [回调→协程]Protocol.data_received()是回调推数据，用户await read()是拉数据——二者时序解耦需缓冲：回调到达时用户可能还没调read()[正确性] → _buffer+waiter: feed_data()向_buffer.extend(data)，若_waiter存在则waiter.set_result(True)唤醒read()，若无waiter则数据暂存_buffer | 代价: _buffer是bytearray可能膨胀(需要_limit保护)
  SC2(实体): [缓冲区膨胀]底层连续推入数据而用户未及时消费——_buffer无限增长直至OOM[边界条件] → _limit流控阈值: feed_data()检查len(_buffer)+len(data)>_limit时抛出exceptions.LimitOverrunError(读操作)或关闭连接，从源头阻止膨胀 | 代价: _limit检查在feed_data()中执行(Protocol回调上下文)，此时抛异常会中断Transport的数据读取链
  SC3(边界): [回调→协程]write()后数据进入Transport._buffer但不等待实际发送——若连续write()则 Transport缓冲区膨胀，但用户态无感知[边界条件] → drain()背压: await writer.drain()检查transport._paused，若暂停则创建Future挂起等待resume_writing()回调，清空后Future.set_result唤醒 | 代价: drain()是可选的——用户可以选择不drain()但冒险缓冲区膨胀(编程契约而非强制)

【结构】"它长什么样？" ★★
Reader↔Writer 配对，Protocol 桥接：

```
StreamReader                  StreamWriter
  ├── _buffer: bytearray        ├── _transport: Transport
  ├── _limit: int               ├── _reader: StreamReader
  ├── _waiter: Future | None    └── write(data) / drain()
  └── feed_data()/read()

桥接:
  _protocol = StreamReaderProtocol(reader)
    → Protocol 子类，回调中调用 reader.feed_data()
    → 同时持有 reader 和 client_connected_cb

创建链:
  loop.create_connection(ProtocolFactory)
    → transport = Transport(sock, protocol)
    → protocol.connection_made(transport)
    → reader._transport = transport
    → writer = StreamWriter(transport, protocol, reader)
```

【时序】"它按什么顺序动？" ★★
数据到达→缓冲→读取 和 drain() 流控：

```
数据读取时序:
  ① 内核 → selector → Transport._read_ready()
  ② Transport._read_ready() → sock.recv() → data
  ③ transport._protocol.data_received(data)  ← Protocol 回调
  ④ StreamReaderProtocol.data_received(data)
       → reader.feed_data(data)
       → reader._buffer.extend(data)
       → if reader._waiter:
           waiter.set_result(True)  ← 唤醒正在 await read() 的协程
  ⑤ user: data = await reader.read(n)
       → if _buffer: 直接返回
       → else: _waiter=future; await future; 返回 _buffer 数据

drain() 流控时序:
  ① writer.write(data) → transport.write(data) → _buffer 扩展
  ② await writer.drain()
       → if transport._paused (缓冲区超 _limit):
           waiter = loop.create_future()
           _waiters.append(waiter)
           await waiter              ← 等待 transport 缓冲区清空
       → transport._write_ready() → sock.send()
       → buffer 回降 → protocol.resume_writing()
       → StreamReaderProtocol.resume_writing()
           → for waiter in _waiters: waiter.set_result()
```

【实体】"它的最小数据单元？" ★★
- StreamReader: `_buffer: bytearray`（数据缓冲），`_waiter: Future`（read 等待点），`_limit: int`（缓冲区上限，驱动流控）
- StreamWriter: `_transport: Transport`（写入通道），`_reader: StreamReader`（关联读取端用于 drain）

【边界】"它在哪里交出控制权？" ★★★
**Protocol.data_received() 跨越边界接收 → StreamReader 缓冲 → 用户读取**：

```
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  Transport 层     │  回调    │  Protocol 层      │  缓冲    │  StreamReader 层  │
│  (字节 I/O)       │────────→│  (边界桥接)       │────────→│  (用户读取)       │
│                   │         │                   │         │                   │
│  _read_ready()    │ data    │  data_received()  │ feed   │  _buffer         │
│  sock.recv()      │────────→│  → feed_data()    │───────→│  _waiter         │
│                   │         │                   │         │  read() / drain() │
└──────────────────┘         └──────────────────┘         └──────────────────┘
      ↑ 内核边界面              ↑ 边界桥接点                   ↑ 用户态 API 面
   (E05/E06)                (Protocol 将回调                (await 接口)
                            转为缓冲+唤醒)
```

边界的关键：Protocol 是 Transport 回调世界和 StreamReader await 世界的**翻译层**。data_received → feed_data → _waiter.set_result 是从"回调推"到"await 拉"的边界转换。

【内部关联】
- StreamReaderProtocol.data_received(data) --[缓冲(回调转发者→缓冲消费者)]--> StreamReader.feed_data(data)  [E09 自环]
- StreamReader._waiter.set_result(True) --[唤醒(数据到达者→阻塞读取者)]←-- feed_data  [E09→E03]
- StreamWriter.write(data) --[数据传递(用户API→传输层)]--> Transport.write(data)  [E09→E05]
- StreamWriter.drain() --[流控(背压等待者←缓冲管理者)]←→ Transport._paused / resume_writing  [E09↔E05]
- Transport._read_ready() --[数据回调(字节搬运者→协议桥接者)]--> Protocol.data_received()  [E05→E09]
- Protocol.resume_writing() --[流控解除(阻塞管理者→背压等待者)]--> StreamReader._waiters.set_result()  [E09→E03]

【示例】
```python
reader, writer = await asyncio.open_connection('127.0.0.1', 8888)

writer.write(b"hello\n")
await writer.drain()           # 等待缓冲区清空（流控）

data = await reader.readline() # _buffer 有数据→直接返回; 空→await _waiter
print(data)

writer.close()
await writer.wait_closed()
```

---

## E10: TaskGroup

```
╔═══════════════════════════════════════════════════════════╗
║  【结构化并发】TaskGroup                                   ║
║  编号: E10 | 来源: asyncio.taskgroups                     ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 基于 async with 的结构化并发作用域，确保作用域内所有 create_task 创建的 Task 在退出前全部完成，并将任何子 Task 异常传播到父作用域。

【冲突溯源】 归属于 S3 推导链节点 N5 的设计选择 D6（结构补充→闭环）

【设计内因】 D6工程目标: 实现结构化并发作用域，确保async with块内所有Task在退出前完成或取消，且子Task异常不静默丢失
  通用困境: {任务逃逸困境(结构): 无作用域约束的并发任务可在父级退出后继续运行，资源泄漏但无人负责——结构化并发是近年Go(errgroup)/Rust(JoinSet)/Swift(TaskGroup)共同趋近的方向; 异常静默丢失困境(实体+结构): 协程中的异常若不被收集和传播则被EventLoop默认handler吞掉——裸create_task的异常只打印日志不传播，调用方永远不知道失败; 取消级联困境(时序): 一个子Task失败时其余子Task应取消，但取消顺序和等待语义需精确——取消发出后仍需等待被取消Task完成(它们可能catch了CancelledError)}
  SC1(结构): [任务逃逸]裸create_task()无作用域约束——Task在父协程结束后继续运行(孤儿Task)，资源无人清理，异常无人处理[正确性] → async with作用域约束: _tasks=set()记录所有create_task的Task, __aexit__中while _tasks: await _on_completed_fut, 确保退出前_tasks为空 | 代价: 作用域内Task不可逃逸——若子Task内部又create_task(非tg.create_task)则该孙Task不在管理范围
  SC2(实体): [异常丢失]子Task异常若不收集则被EventLoop默认handler吞掉——裸task的exception只打印日志，调用方无法获取[正确性] → _on_task_done收集异常: 每个Task.add_done_callback(_on_task_done), 完成时检查task.exception(), 非空则append到_errors, __aexit__中raise ExceptionGroup(errors) | 代价: 所有子Task的异常被打包为ExceptionGroup——调用方需用except*语法匹配(3.11+新语法)
  SC3(时序): [取消级联]任一子Task异常时应取消其余子Task——但cancel()只是请求，Task可能catch CancelledError不死，必须等待它们真正结束[边界条件] → _abort()取消+while等待: _abort()对所有_tasks执行task.cancel(), 之后仍然while _tasks: await _on_completed_fut等待所有Task完成(包括被取消的Task) | 代价: 取消传播是尽力而非即时的——被取消Task的收尾时间不确定，__aexit__可能等待较久
  SC4(边界): [取消级联]外部取消(parent被cancel)应穿透TaskGroup——若__aexit__中await _on_completed_fut被外部CancelledError中断，需正确处理[边界条件] → __aexit__中except CancelledError: self._abort(None), 重新取消所有子Task并继续等待 | 代价: 外部取消和内部异常取消的语义相同(都走_abort)，无法在外部取消时做差异化处理

【结构】"它长什么样？" ★★★
**async with 作用域约束所有 create_task 的 Task**：

```
TaskGroup 结构化生命周期:

  async with TaskGroup() as tg:
      │
      ├── tg.create_task(coro1)  → task1 加入 tg._tasks
      ├── tg.create_task(coro2)  → task2 加入 tg._tasks
      ├── ...
      │
      └── ── 退出 async with ──
            │
            ├── ① 等待所有 tg._tasks 中的 Task 完成
            ├── ② 若任一 Task 抛异常 → 取消其余 Task
            ├── ③ 收集所有异常 → 抛出 ExceptionGroup
            └── ④ 确保 _tasks 为空后才退出

  核心不变量：
  - 进入 __aenter__ 时：_tasks 为空（或仅初始 Task），边界清晰
  - 退出 __aexit__ 时：所有 _tasks 已完成，无逃逸 Task
  - 任何子 Task 异常不会静默丢失，必然传播
  - 取消信号 __aexit__ → task.cancel() → 级联取消

  结构突破的本质：
  传统 asyncio.gather() 无结构约束——Task 创建后可自由逃逸
  TaskGroup 的 async with 约束了 Task 的生命周期作用域
  这是从"自由并发"到"结构化并发"的范式转换
```

【时序】"它按什么顺序动？" ★★
创建→运行→等待→异常传播：

```
__aenter__():
  self._parent_task = current_task()
  return self

create_task(coro):
  task = Task(coro)
  self._tasks.add(task)
  task.add_done_callback(self._on_task_done)  ← 每个完成触发检查
  return task

__aexit__(exc_type, exc_val, exc_tb):
  if exc_type is not None:           ← 作用域内自身有异常
    self._abort(exc_val)             ← 取消所有子 Task

  # 等待所有子 Task 完成
  while self._tasks:
    self._on_completed_fut = loop.create_future()
    try:
      await self._on_completed_fut   ← 等待最后一个 Task 完成
    except CancelledError:
      self._abort(None)              ← 外部取消

  # 检查子 Task 异常
  if self._errors:
    raise ExceptionGroup("task group", self._errors)

_on_task_done(task):
  self._tasks.discard(task)
  if task._exception:
    self._errors.append(task._exception)
    self._abort(None)                ← 取消其余 Task
  if not self._tasks and self._on_completed_fut:
    self._on_completed_fut.set_result(None)  ← 唤醒等待

_abort(exc):
  for task in self._tasks:
    task.cancel("task group abort")
```

【实体】"它的最小数据单元？" ★★
- `_tasks: set[Task]` — 当前作用域内活跃的 Task 集合，驱动"等待全部完成"
- `_errors: list[Exception]` — 子 Task 产生的异常集合，驱动"异常传播"
- `_on_completed_fut: Future` — 用于 await 等待所有 Task 完成的通知点
- `_parent_task: Task` — 父 Task，用于检测结构化违规（如在 async with 外 create_task）

【边界】"它在哪里交出控制权？" ★
同线程内，无跨线程边界。所有协调通过 Future.set_result 和 Task.cancel 在同一 EventLoop 内完成。

【内部关联】
- TaskGroup.create_task(coro) --[受控创建(作用域管理者→受管单元)]--> Task(coro)  [E10→E04]
- TaskGroup._on_task_done(task) --[完成通知(生命周期监督者←完成者)]←-- Task.add_done_callback  [E10←E04]
- TaskGroup._abort(exc) --[取消传播(异常响应者→被取消者)]--> Task.cancel("task group abort")  [E10→E04]
- TaskGroup._on_completed_fut.set_result() --[全部完成信号(计数者→等待者)]←-- _on_task_done  [E10→E03]
- TaskGroup.__aexit__ --[异常传播(收集者→调用方)]--> ExceptionGroup(errors)  [E10→调用方]

【示例】
```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(work1())
    tg.create_task(work2())
    tg.create_task(work3())
# __aexit__: 等待 work1/2/3 全部完成
# 若 work2() 抛异常 → 取消 work1/3 → ExceptionGroup

# 对比 gather:
tasks = await asyncio.gather(work1(), work2(), work3())
# return_exceptions=False 时同样取消，但无结构化作用域约束
```

---

