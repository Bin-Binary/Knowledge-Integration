# asyncio 执行实体重塑（Step 4: 实体重塑）

> 冲突模型 S3 推导链驱动：每个实体从冲突节点 N{X}/D{X} 获得权重与演化角色。
> 突破维度获 ★★★，副作用维度获 ★★，其余维度获 ★。

---

## E01: EventLoop

```
╔═══════════════════════════════════════════════════════════╗
║  【核心调度器】EventLoop                                  ║
║  编号: E01 | 来源: asyncio.base_events.BaseEventLoop     ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 单线程事件循环，通过轮询 I/O 就绪状态 + 就绪回调队列，实现"遇到 I/O 就跳过"的时序突破。

【冲突溯源】 归属于 S3 推导链节点 N0 的设计选择 D1（时序突破）

【设计内因】 D1工程目标: 在单线程内统一收割三类时序源，保证I/O不被饿死、定时器不延误、立即回调不延迟
  通用困境: {时序源异构困境(时序): 回调驱动的系统中，立即/定时/I/O三类时序源的排序需求与阻塞行为天然不可混合——所有事件循环实现面对的根本问题; 饥饿困境(时序): 回调驱动的系统中，生产者(回调内产生新回调)与消费者(主循环的其他职责检查)共享队列时，生产速度可饿死消费者的其他职责; 跨线程唤醒困境(边界): 事件循环阻塞于系统调用时，外部线程无法通知循环处理新任务}
  SC1(时序): [时序源异构]三类时序源排序与阻塞行为不可混合——FIFO需无延迟但select会阻塞、定时需排序但deque无序，混合则至少一类时序源行为被破坏[正确性] → 三队列分离: _ready(deque)+_scheduled(heap)+_selector(fd→cb) | 代价: _run_once需显式合并三队列(步骤③迁移)
  SC2(时序): [时序源异构]select()阻塞vs回调饿死——_ready有任务时阻塞=回调饿死，不阻塞=CPU空转[边界条件] → timeout枢纽: _ready非空→0/堆顶→差值/皆空→无限 | 代价: timeout=0时仍有内核态切换开销
  SC3(时序): [饥饿]回调嵌套饿死I/O检查——call_soon产生新Handle入_ready，无限消费则永远回不到select()[边界条件] → ntodo快照: 只消费本轮已有项 | 代价: 新增回调延迟一轮执行
  SC4(实体): [时序源异构]千级定时器O(n)扫描不可接受——每轮需查最早到期用于timeout计算[性能] → heapq堆: _when为键 探查O(1) 插入O(log n) | 代价: 取消需O(log n)，但可延迟清理
  SC5(边界): [跨线程唤醒]select阻塞时跨线程call_soon_threadsafe无法唤醒——新回调无人处理[边界条件] → 自写管道: _self_reading_fd 写1字节→selector唤醒 | 代价: 每次跨线程调度有一次管道I/O开销

【结构】"它长什么样？" ★
三个优先级队列的简单拓扑：
- `_ready: deque[Handle]` — 就绪回调队列，FIFO 顺序消费
- `_scheduled: list[TimerHandle]` — 定时回调堆，按 `_when` 排序
- `_selector: selectors.BaseSelector` — I/O 多路复用器，注册文件描述符到回调的映射

设计意图：三队列分离——I/O 等待、定时等待、立即执行三类时序源各归其位，_run_once 每轮统一收割。

【时序】"它按什么顺序动？" ★★★
`_run_once()` 循环是时序突破的核心实现，每一轮精确执行：

```
1. _run_once() 入口
   ├─ ① 计算 timeout：min(_scheduled[0]._when - loop.time(), max_timeout)
   │     若 _ready 非空 → timeout = 0（立即 poll，不阻塞）
   │     若 _scheduled 为空 → timeout = max_timeout（可无限阻塞）
   │     若 _ready 为空且有 _scheduled → timeout = 距最近定时器的时间差
   │
   ├─ ② selector.select(timeout)  ← 交出控制权给内核（边界传导点）
   │     返回 (fd, events) 对 → 封装为 Handle 放入 _ready
   │
   ├─ ③ 合并定时器到期项：_scheduled 中 _when <= loop.time() 的项
   │     pop → cancel 检查 → 移入 _ready
   │
   └─ ④ 消费 _ready：ntodo = len(_ready) 快照
        for i in range(ntodo):
            handle = _ready.popleft()
            if not handle._cancelled:
                handle._run()  ← 执行回调（可能产生新的 _ready 项，
                                   但本轮不消费，防止饿死 I/O）
```

时序突破的本质：**步骤② selector.select() 的 timeout 计算是整个时序模型的枢纽**——
- _ready 非空时 timeout=0 → 不阻塞 → 立即处理已就绪项 → 新回调入队 → 下一轮再 poll
- _ready 为空时 timeout>0 → 阻塞等 I/O → I/O 就绪或定时器到期后唤醒
- 这就是"遇到 I/O 就跳过"的精确实现：无 I/O 就绪→交出线程→有就绪→立即处理

`run_forever()` = `while True: _run_once()`，循环直到 `stop()` 被调用。

【实体】"它的最小数据单元？" ★
字段服务于时序机制的实现：
- `_time` — 缓存 `time.monotonic()`，给 `_when` 比较用
- `_stopping` — `stop()` 的标志位
- `_thread_id` — 检测跨线程调用的守护

【边界】"它在哪里交出控制权？" ★★
- **交出点**：`selector.select(timeout)` — 线程阻塞于内核，等待 I/O 就绪信号；此时刻循环放弃 CPU，这是异步模型唯一的"等待"点
- **回收点**：select 返回后，就绪 fd 的回调入 _ready → 下一步④消费；定时器到期也回收
- Side effect：select 期间，其他线程可通过 `call_soon_threadsafe()` 向 _ready 注入回调（通过 `_self_reading_fd` 管道唤醒 selector）

【内部关联】
- EventLoop.call_soon(callback) --[调度(调度者→执行原子)]--> Handle(callback, _ready)  [E01→E02]
- EventLoop.call_later(delay, callback) --[延迟调度(定时注册者→时序等待者)]--> TimerHandle(when, callback, _scheduled)  [E01→E02]
- EventLoop.call_at(when, callback) --[定点调度(定时注册者→时序等待者)]--> TimerHandle(when, callback, _scheduled)  [E01→E02]
- EventLoop._run_once:selector.select() --[就绪通知(轮询者→I/O执行者)]--> Transport._read_ready/_write_ready  [E01→E05]
- EventLoop._run_once:merge_scheduled --[到期触发(时间判官→过期执行者)]--> TimerHandle._run()  [E01→E02]
- EventLoop.create_task(coro) --[包装(调度者→被调度单元)]--> Task(coro)  [E01→E04]
- EventLoop.run_until_complete(future) --[驱动(阻塞入口→执行载体)]--> Task(future.__init_subclass__)  [E01→E04]

【示例】
```python
loop = asyncio.new_event_loop()
loop.call_soon(print, "immediate")         # → _ready
loop.call_later(1.0, print, "after 1s")    # → _scheduled
loop.call_soon(loop.stop)
loop.run_forever()
# _run_once 循环：先消费 _ready(含 "immediate"),
#                 再 select(timeout=1.0) 等待,
#                 1s 后 TimerHandle 到期入 _ready, 执行 "after 1s"
```

---

## E02: Handle+TimerHandle

```
╔═══════════════════════════════════════════════════════════╗
║  【调度原子】Handle / TimerHandle                         ║
║  编号: E02 | 来源: asyncio.handles                        ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 EventLoop 调度的最小执行单元，封装回调函数及其参数；TimerHandle 扩展定时触发语义。

【冲突溯源】 归属于 S3 推导链节点 N0 的设计选择 D1（时序突破）

【设计内因】 D1工程目标: 将回调封装为可调度的最小原子单元，支持立即调度和定时调度两种时序语义，且可取消
  通用困境: {调度单元语义分离困境(时序+实体): 回调驱动的系统中，立即执行与延迟执行的调度单元有完全不同的排序需求——立即回调需FIFO保序，定时回调需按绝对时间排序，混为一体则破坏双方的语义保证; 取消一致性困境(时序+边界): 可取消的调度单元在取消时机和清理策略上必须一致——已入队的取消 vs 已过期/已执行的取消需统一处理，否则产生幽灵回调或资源泄漏}
  SC1(时序): [语义分离]立即回调需FIFO保序消费——若与定时回调混合存储则无法保证先入先出的执行顺序[正确性] → Handle封装callback+args: 入_ready deque, popleft O(1)保序执行 | 代价: Handle无排序键，不支持定时语义(需TimerHandle扩展)
  SC2(实体): [语义分离]定时回调需按绝对时间排序且可O(1)查最早——若用deque存储则每轮O(n)扫描千级定时器[性能] → TimerHandle增加_when键继承Handle: 入_scheduled heapq, 堆顶O(1)探查/插入O(log n) | 代价: 当取消时需O(log n)从堆中删除，但可用延迟清理规避
  SC3(时序): [取消一致性]已取消的Handle不可执行——若取消只置标志不检查，则已取消回调仍被执行[正确性] → _cancelled标志位: cancel()置True, _run_once步骤④检查跳过 | 代价: 取消的Handle仍在_ready中占位直到被消费跳过(内存不立即释放)
  SC4(边界): [取消一致性]定时回调取消需从_scheduled堆中移除但heappop O(n)——若每次cancel都heappopsift则千级定时器下性能不可接受[边界条件] → 延迟清理: TimerHandle.cancel()置_scheduled=False+_cancelled=True, _run_once步骤③跳过_scheduled=False项, 堆在heappop时自然淘汰 | 代价: 已取消的TimerHandle在堆中仍占位直到自然淘汰到堆顶，堆体积暂时膨胀

【结构】"它长什么样？" ★
单继承拓扑：`Handle → TimerHandle`。
- Handle：`_callback` + `_args` + `_cancelled`
- TimerHandle：+ `_when` + `_scheduled` 标记

设计意图：回调是一等调度单元，可取消、可延迟；TimerHandle 加入时序排序键 `_when`。

【时序】"它按什么顺序动？" ★★★
Handle 的生命周期精确映射时序突破：

```
创建阶段:
  Handle(cb, args) → _cancelled=False, 尚未入队
  TimerHandle(when, cb, args) → _when=绝对时间戳, _scheduled=False

入队阶段:
  call_soon() → Handle 直入 _ready 队尾（第 E01 步骤④消费）
  call_later()/call_at() → TimerHandle 入 _scheduled 堆（按 _when 堆排序）

等待阶段 (TimerHandle 特有):
  _scheduled 堆中等待，_run_once 每轮检查堆顶：
  - 堆顶._when > loop.time() → 未到期，不取出
  - 堆顶._when <= loop.time() → heappop → 移入 _ready

执行阶段:
  _ready.popleft() → 检查 _cancelled → 若未取消则 _callback(*_args)

取消阶段:
  handle.cancel() → _cancelled=True
  TimerHandle.cancel() → _cancelled=True + _scheduled=False
  取消的 Handle 在消费时被跳过（步骤④的 if not handle._cancelled 检查）
```

核心时序逻辑：**从 _ready 取出的顺序决定执行的顺序**。TimerHandle 的 `_when` 决定何时从 _scheduled 迁移到 _ready，这是时间维度介入调度的唯一通道。

【实体】"它的最小数据单元？" ★★
- Handle: `_callback`, `_args`, `_cancelled` — 驱动回调和取消
- TimerHandle: **`_when`** — 绝对时间戳，是时序排序的核心键；决定了在 _scheduled 堆中的位置，决定了何时迁移到 _ready
- `_context` — 复制当前 contextvars.Context，确保回调在正确的上下文中执行

【边界】"它在哪里交出控制权？" ★
- Handle._run() 内部：`self._callback(*self._args)` 是执行边界；异常被 `GlobalChildWatcher` 捕获并记录，不会泄漏到循环
- TimerHandle 没有独立的边界交出，其时序效果通过 EventLoop._run_once 的步骤③间接实现

【内部关联】
- TimerHandle._when --[排序(时序键→排序依据)]--> EventLoop._scheduled 堆序  [E02→E01]
- Handle._run() --[执行(执行原子→新调度源)]--> callback 产生新的 call_soon/call_later  [E02→E01]
- Future.__schedule_callbacks --[入队(就绪通知者→调度原子)]--> EventLoop.call_soon(Handle)  [E03→E01, 间接关联 E02]
- Task.__step --[入队(驱动者→调度原子)]--> EventLoop.call_soon(Task.__wakeup)  [E04→E01, 间接关联 E02]

【示例】
```python
handle = loop.call_soon(print, "hello")  # Handle 入 _ready
handle.cancel()                           # _cancelled=True, 消费时跳过

timer = loop.call_later(2.0, print, "delayed")  # TimerHandle 入 _scheduled
# 2s 后 _run_once 步骤③: timer._when <= now → pop → 入 _ready → 执行
```

---
## E03: Future

```
╔═══════════════════════════════════════════════════════════╗
║  【结果锚点】Future                                       ║
║  编号: E03 | 来源: asyncio.futures                        ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 异步结果的占位对象，用有限状态机锚定未来值，通过回调注册提供跨任务边界唤醒接口。

【冲突溯源】 归属于 S3 推导链节点 N2 的设计选择 D3（边界与实体突破）

【设计内因】 D3工程目标: 用有限状态机锚定异步结果，通过回调注册提供跨任务边界唤醒接口，保证结果不可逆且唤醒不丢失
  通用困境: {结果唯一性困境(实体): 异步结果的占位容器必须保证结果只能设置一次——并发场景下多个生产者可能争抢设值，语义崩溃("谁赢?")是所有Future/Promise类实体的共性问题; 唤醒可靠性困境(时序+边界): 结果就绪时必须唤醒所有已注册等待者且不可遗漏——等待者可能在结果就绪前或后就绪后注册，两种时序下唤醒语义必须一致; 就绪后注册困境(边界): 已完成的Future上再注册回调仍需执行——否则晚注册的等待者永远收不到通知(回调丢失)}
  SC1(实体): [结果唯一性]结果必须只能设置一次否则语义崩溃——并发set_result/cancel争抢下无法判定谁赢，后续设值静默覆盖先行者[正确性] → 三态单向状态机: PENDING→FINISHED/CANCELLED不可逆, set_result/set_exception/cancel仅在PENDING时生效 | 代价: 不可重新设值(语义上Future是一次性的)
  SC2(时序): [唤醒可靠性]结果就绪时必须唤醒所有已注册等待者且不可遗漏——若回调列表不完整遍历或不清空，重复调度或遗漏都会导致Task永久挂起[正确性] → __schedule_callbacks: 状态转换时遍历_callbacks逐一call_soon入_ready, 之后clear防止重复调度 | 代价: clear后新回调只能走即时call_soon路径(两套调度路径)
  SC3(边界): [就绪后注册]已完成的Future上注册回调仍需在下一轮执行——若add_done_callback在set_result后注册但被忽略，等待者永远收不到通知[边界条件] → add_done_callback即时检查: _state!=PENDING时直接call_soon(cb,self), 不入_callbacks跳过clear | 代价: 存在两套回调调度路径(PENDING时入_callbacks，非PENDING时直接call_soon)，增加维护复杂度
  SC4(边界): [结果唯一性]set_result与cancel的竞争需明确胜者——两者几乎同时到达PENDING态时若都成功则状态矛盾[正确性] → PENDING态下先到者赢: cancel()检查_state==PENDING才转换, set_result()同理, 非PENDING返回False | 代价: 竞争结果的胜负取决于微秒级时序，调用方需检查返回值判断是否成功

【结构】"它长什么样？" ★
独立对象 + 回调列表，无继承复杂度：
- 状态枚举：`_PENDING / _CANCELLED / _FINISHED`
- 回调列表：`_callbacks: list[callable]`
- 结果槽：`_result` / `_exception`

设计意图：一个 Future 就是一个" someday someone will set this "的契约；状态转换是单向的，不可逆。

【时序】"它按什么顺序动？" ★★
Future 的时序传导链：

```
创建: Future() → _state=PENDING, _callbacks=[]

注册回调:
  add_done_callback(cb) → _callbacks.append(cb)
  若 _state != PENDING → 直接 call_soon(cb, self)（已经完成，立即调度）

设值（时序传导的关键一步）:
  set_result(result):
    _state = FINISHED, _result = result
    → __schedule_callbacks()  # 将所有已注册回调通过 call_soon 调度到 _ready
  set_exception(exc):
    _state = FINISHED, _exception = exc
    → __schedule_callbacks()

取消:
  cancel(msg=None):
    _state = CANCELLED, _cancel_message = msg
    → __schedule_callbacks()

回调调度 (__schedule_callbacks):
  for callback in _callbacks:
      loop.call_soon(callback, self)  ← 这是从 Future 到 EventLoop 的时序传导
  _callbacks.clear()

await 悬挂:
  __await__ → yield self（Task.__step 捕获 self 作为 _fut_waiter）
  → Task 挂起，等待 set_result/cancel 触发 __schedule_callbacks
  → 回调中包含 Task.__wakeup → Task 恢复
```

时序关键：`__schedule_callbacks → call_soon` 是 Future 将"结果就绪"事件转化为 EventLoop 时序信号的通道。

【实体】"它的最小数据单元？" ★★★
**状态机是 Future 的核心设计，三个状态单向迁移，不可逆**：

```
         set_result() / set_exception()
  PENDING ──────────────────────────────→ FINISHED
     │                                       │
     │ cancel(msg)                           │ (终态)
     ↓                                       ↓
  CANCELLED                               (不可变)

  PENDING 时：
    - 可 add_done_callback（回调排队等待）
    - 可 set_result / set_exception / cancel（触发状态转换）
    - 不可 get_result（raise InvalidStateError）

  FINISHED 时：
    - _result 或 _exception 已确定
    - result() 返回 _result 或 raise _exception
    - 不可再 set_* / cancel（不可逆）

  CANCELLED 时：
    - cancel() 返回 True
    - result() raise CancelledError(_cancel_message)
    - 不可再 set_*（不可逆）
```

关键字段驱动行为：
- `_state` — 驱动所有分支判断的唯一源
- `_result` / `_exception` — FINISHED 状态下的值
- `_cancel_message` — CANCELLED 状态下的取消原因
- `_callbacks` — PENDING 态的回调队列，状态转换后清空
- `_loop` — 关联的 EventLoop，__schedule_callbacks 依赖它做 call_soon

【边界】"它在哪里交出控制权？" ★★★
**add_done_callback → call_soon 是跨任务边界唤醒通道**：

```
Task_A                    Future                    Task_B
  │                         │                         │
  ├─ await future ─────────→│                         │
  │   (yield self)          │                         │
  │                         │←── future.set_result() ─┤
  │                         │    (Task_B 设置结果)     │
  │                         │                         │
  │                         ├─ __schedule_callbacks()  │
  │                         │   → loop.call_soon(     │
  │                         │       Task_A.__wakeup)  │
  │                         │                         │
  │←─ __wakeup 执行 ────────┤                         │
  │   Task_A 恢复           │                         │
```

这是 asyncio 最核心的边界协议：
- Task_A 通过 `await future`（即 `yield future`）将自己悬挂在 Future 上
- Task_B 通过 `future.set_result()` 触发状态转换
- Future 的 `__schedule_callbacks` 将 Task_A 的 `__wakeup` 通过 `call_soon` 注入 EventLoop._ready
- 下一个 _run_once 循环中 Task_A 被唤醒

**Future 是跨任务信号传递的信箱，add_done_callback→call_soon 是投递路径。**

【内部关联】
- Future.add_done_callback(cb) --[注册(等待登记处→回调槽)]--> Future._callbacks  [自环]
- Future.set_result() --[触发(结果设值者→回调调度者)]--> Future.__schedule_callbacks  [自环]
- Future.__schedule_callbacks() --[时序传导(信号源→调度枢纽)]--> EventLoop.call_soon()  [E03→E01]
- Future.__schedule_callbacks() --[入队(信号源→执行原子)]--> Handle(wakeup_cb)  [E03→E02]
- Task.__step() --[悬挂(等待者→锚定目标)]--> Future (via yield self, _fut_waiter=future)  [E04→E03]
- Task.__wakeup(fut) --[被唤醒(被唤醒者←信号源)]←-- Future.__schedule_callbacks  [E04←E03]

【示例】
```python
fut = loop.create_future()          # _state=PENDING

async def setter():
    await asyncio.sleep(1)
    fut.set_result(42)              # _state=FINISHED → __schedule_callbacks

async def waiter():
    result = await fut              # yield self → Task 挂起
    print(result)                   # __wakeup 被调度后恢复，打印 42
```

---

## E04: Task

```
╔═══════════════════════════════════════════════════════════╗
║  【调度单元】Task                                         ║
║  编号: E04 | 来源: asyncio.tasks                          ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 协程的可调度包装，将生成器帧的挂起/恢复映射为 EventLoop 回调驱动，yield/await 切断栈帧实现结构突破。

【冲突溯源】 归属于 S3 推导链节点 N1 的设计选择 D2（结构突破）

【设计内因】 D2工程目标: 将协程挂起/恢复映射为EventLoop回调驱动，用yield切断栈帧实现结构化并发，保证取消信号可跨Task传播且异常不丢失
  通用困境: {驱动-悬挂双段困境(时序): 协程驱动系统中，"推"协程前进到断点与"拉"回协程继续是两种不同的时序行为——前进由__step主动send，恢复由Future就绪后回调拉回，二者的衔接必须在任何时序下保持正确; 取消注入时机困境(边界): 可取消的异步单元在取消请求到达时可能处于多种状态(挂在Future上/在_ready排队/正在执行)，必须保证取消信号不丢失且不误注入; 上下文隔离困境(实体): 多协程共享线程的系统中，contextvars等上下文状态必须隔离——否则一个协程的上下文修改会污染另一个协程}
  SC1(时序): [驱动-悬挂]协程yield的Future未完成时必须挂起且被唤醒恢复——若不注册回调则Future就绪时无人通知Task，协程永久挂起[正确性] → __step/__wakeup双阶段驱动: __step中yield Future → add_done_callback(__wakeup) + _fut_waiter锚定, Future就绪时__wakeup→__step恢复send() | 代价: 每次await都有add_done_callback→call_soon→__wakeup的调度链开销
  SC2(边界): [取消注入时机]取消请求到达时Task可能正挂在Future上也可能在_ready排队——若只cancel Future则_ready中的Task无取消信号，若只置标志则挂起的Future不会被取消[边界条件] → _must_cancel延迟注入: cancel()置_must_cancel=True并传播_fut_waiter.cancel(), 下次__step时检查_must_cancel注入CancelledError, 覆盖两种状态 | 代价: 取消不是即时的——Future上的取消立即生效但协程内的CancelledError延迟到下次__step才注入
  SC3(实体): [驱动-悬挂]协程yield非Future对象属编程错误必须检测——若静默忽略则协程行为未定义，调试极难[正确性] → __step类型守卫: yield结果非Future则raise RuntimeError("got %r instead of Future"), 拦截非法yield | 代价: 限制了协程只能yield Future(或None)，不允许自定义可等待对象(除非实现__await__)
  SC4(边界): [取消注入时机]超时取消与外部取消需区分避免误吞——若Timeout引发CancelledError和外部取消不可区分，uncancel可能误恢复外部取消[边界条件] → _cancelling计数器: cancel()+1/uncancel()-1, Timeout在__aexit__中uncancel恢复计数, 使外部取消仍能传播(为E11提供支撑) | 代价: cancel/uncancel计数逻辑增加__step的复杂度，且uncancel语义对调用方有隐式约定
  SC5(实体): [上下文隔离]每个Task需独立上下文避免contextvars污染——若共享上下文则一个协程设置contextvars会影响其他协程[正确性] → _context=Context副本: __step在_context.run()中执行send(), 各Task上下文隔离 | 代价: 每个Task持有独立Context副本，增加内存开销

【结构】"它长什么样？" ★★★
**协程 + 断点保存是结构切断的核心**：

```
Task 继承 Future，同时持有协程对象：

  Task(Future)
    ├── _coro: GeneratorType        ← 被驱动的协程
    ├── _fut_waiter: Future | None  ← 当前 await 的 Future（断点锚定）
    ├── _must_cancel: bool          ← 取消请求待处理标志
    ├── _cancel_message             ← 取消原因链
    ├── _cancelling: int            ← uncancel 计数器（E11 Timeout 使用）
    └── _context: Context           ← 独立上下文副本

结构突破的本质：
  传统调用栈：main() → foo() → bar()  （连续栈帧，阻塞即全部阻塞）
  Task 切断后：main() 发起 Task → _coro 执行到 await
               → yield future → 栈帧冻结，寄存器/局部变量保存到生成器帧
               → _fut_waiter = future → Task 从 _ready 中消失
               → 其他 Task 可以执行
               → future 就绪 → __wakeup → coro.send(result) → 栈帧恢复

  每一个 await/yield from 都是一个"结构断点"：
    断点前：栈帧从 Task.__step → _coro.send() → 用户代码，连续执行
    断点处：yield future → 栈帧回退到 __step → 返回到 _run_once
    断点后：__wakeup → _coro.send(result) → 从断点处恢复

  多个 Task 各自独立地在断点间跳跃，EventLoop 按就绪顺序驱动。
  这就是"结构突破"：单个栈帧被切断为可暂停的片段。
```

【时序】"它按什么顺序动？" ★★★
**__step / __wakeup 是协程驱动时序的核心**：

```
Task 生命周期时序：

① 创建:
   Task(coro) → _coro=coro, _fut_waiter=None
   → loop.call_soon(self.__step)  ← 首次驱动入 _ready

② __step 驱动（核心时序引擎）:
   __step(exc=None):
     if _must_cancel:
       exc = CancelledError(_cancel_message)  ← 传递取消
       _must_cancel = False

     result = _coro.send(None)  ← 恢复/启动协程

     if result is None:          ← 协程 return（非 yield）
       # 协程完成
       super().set_result(_coro.cr_frame.f_locals.get('return'))
       return

     elif isinstance(result, Future):
       # await future → 协程 yield 了一个 Future
       if self._must_cancel:
         result.cancel(msg=...)   ← 取消传导到被等待的 Future
       elif result.done():
         # Future 已完成，无需等待，下一轮立即继续
         self.__step()            ← 递归（但 call_soon 更常见）
       else:
         # Future 未完成，悬挂
         result.add_done_callback(self.__wakeup)  ← 注册唤醒
         self._fut_waiter = result  ← 断点锚定

     else:
       raise RuntimeError("yielded non-Future")

③ __wakeup 唤醒:
   __wakeup(future):
     future.result()  ← 若有异常则抛出，传入 __step
     self.__step(exc) ← 继续驱动协程

④ 取消传播:
   cancel(msg):
     if _fut_waiter is not None:
       _fut_waiter.cancel(msg)   ← 取消传播到下游 Future
       _must_cancel = True       ← 标记待处理（下次 __step 时生效）
     else:
       _must_cancel = True
       # 如果协程正在 _ready 中等待 __step，
       # 下次 __step 会注入 CancelledError

⑤ uncancel（E11 Timeout 引入）:
   uncancel():
     _cancelling -= 1
     if _cancelling == 0:
       return True   ← 取消被撤销
     return False
```

时序核心：**__step 是"推"，__wakeup 是"拉"**。__step 推动协程前进到下一个断点，__wakeup 在 Future 就绪后拉回协程继续。两者交替构成 Task 的执行脉冲。

【实体】"它的最小数据单元？" ★★
- `_coro` — 被驱动的协程对象，send/throw 是驱动接口
- `_fut_waiter` — 当前等待的 Future，是跨任务边界配对的锚点；None 表示可立即驱动
- `_must_cancel` — 取消请求待处理标志；若 __step 时为 True，则向协程注入 CancelledError
- `_cancel_message` — 取消原因，构成取消链（Task→Future→Task 传播）
- `_cancelling` — 取消计数器，支持 uncancel 语义（E11 Timeout 需要）
- `_context` — contextvars 副本，确保每个 Task 有独立上下文

【边界】"它在哪里交出控制权？" ★★
- **cancel() 跨 Task 边界传播**：
  ```
  Task_A.cancel(msg)
    → Task_A._must_cancel = True
    → Task_A._fut_waiter.cancel(msg)   ← 传播到下游 Future
    → Future.__schedule_callbacks
    → Task_A.__wakeup 被调度
    → Task_A.__step 注入 CancelledError
  ```
  取消沿着 Task→Future→Task 链传播，这是跨任务边界的控制信号。

- **_fut_waiter 是跨任务边界配对**：
  Task 悬挂时 `_fut_waiter = future`，其他 Task/回调通过 `future.set_result()` 触发 `__wakeup`，这是跨任务唤醒的配对协议。

【内部关联】
- Task.__step() --[驱动(驱动力→协程推进)]--> _coro.send()  [自环]
- Task.__step() --[悬挂(注册者→信号锚点)]--> Future.add_done_callback(Task.__wakeup)  [E04→E03]
- Task.__wakeup(fut) --[恢复(被唤醒者→驱动续行)]--> Task.__step(exc)  [自环]
- Task.cancel(msg) --[取消传播(取消发起者→下游取消锚)]--> Future.cancel(msg)  [E04→E03]
- Task._fut_waiter --[配对锚定(等待者←结果设值者)]←-- Future.set_result() → __wakeup  [E04←E03]
- EventLoop.create_task(coro) --[创建(调度者→被调度单元)]--> Task(coro)  [E01→E04]
- EventLoop._run_once --[消费(执行枢纽→驱动载体)]--> Handle(Task.__step / __wakeup)  [E01→E04]
- TaskGroup.create_task(coro) --[受控创建(作用域管理者→受管单元)]--> Task(coro)  [E10→E04]

【示例】
```python
async def work():
    print("step 1")
    await asyncio.sleep(1)   # yield Future → _fut_waiter=Future → Task 挂起
    print("step 2")          # 1s 后 __wakeup → __step → 恢复

task = asyncio.create_task(work())
# __step 被调度 → 执行到 await → yield Future → 挂起
# 1s 后 Future.set_result → __wakeup → __step → "step 2"
```

---

## E05: Protocol + Transport

```
╔═══════════════════════════════════════════════════════════╗
║  【I/O 分离对】Protocol / Transport                       ║
║  编号: E05 | 来源: asyncio.protocols / asyncio.transports ║
╚═══════════════════════════════════════════════════════════╝
```

【定义】 Transport 封装底层非阻塞 I/O 操作，跨越内核/用户态边界；Protocol 定义业务回调接口，两者 1:1 配对实现 I/O 机制与业务逻辑的解耦。

【冲突溯源】 归属于 S3 推导链节点 N3 的设计选择 D4（边界闭合）

【设计内因】 D4工程目标: 封装底层非阻塞I/O操作跨越内核/用户态边界，将I/O机制与业务逻辑解耦，保证字节流收发可靠且流控有效
  通用困境: {机制/策略分离困境(边界+结构): I/O系统中底层传输机制(何时读写字节)与上层业务策略(读到字节后做什么)耦合在一起时，更换传输方式(如插入SSL)需重写业务逻辑——所有分层I/O框架(Netty的Channel+Handler、Twisted的Protocol+Transport)都对这个问题做了分离; 流控饥饿困境(边界): 非阻塞I/O中写的速度远快于内核缓冲排空时，生产者不节制则用户态缓冲无限膨胀——这是所有非阻塞写操作面对的背压问题; 连接生命周期一致性困境(边界): I/O连接的建立/数据/关闭/异常四个阶段必须按固定顺序通知业务层——乱序通知(如连接未建立就收到数据)会导致业务层状态混乱}
  SC1(边界): [机制/策略分离]Transport与Protocol必须1:1解耦——若Transport内置业务逻辑则无法替换(如SSL插入需换Transport)，若Protocol知道socket细节则无法跨平台[职责] → 1:1配对+接口隔离: Transport持有_protocol引用调用data_received等回调，Protocol通过transport.write()写数据，二者互知接口不知实现 | 代价: Transport必须持有Protocol引用(紧耦合配对)，且中间层插入(如SSLProtocol)必须同时替换Transport端和Protocol端
  SC2(边界): [流控饥饿]非阻塞写的数据缓冲在用户态若不限制——sock.send()可能只写入部分数据，剩余数据存_transport._buffer，若生产者持续write()则_buffer无限膨胀直至OOM[边界条件] → 写缓冲+流控通知: _buffer暂存未发送数据，超限(>64KB)时调用protocol.pause_writing()通知业务层暂停，回降时resume_writing() | 代价: 业务层必须响应pause/resume_writing(否则流控形同虚设)，且write()调用本身不阻塞(不等待实际发送)
  SC3(时序): [连接生命周期]连接建立/数据/关闭通知必须按顺序——若connection_made未调用就收到data_received，Protocol状态未初始化则crash[正确性] → 生命周期回调序列: connection_made(初始化) → data_received*(数据处理) → eof_received(可选半关闭) → connection_lost(清理) | 代价: Protocol子类必须实现全部四个回调否则逻辑不完整，顺序由Transport保证而非Protocol
  SC4(边界): [机制/策略分离]selector通知fd可读后必须由Transport而非Protocol执行sock.recv()——若Protocol直接操作socket则破坏分层，且Protocol不知道非阻塞recv可能返回部分数据[职责] → Transport._read_ready()封装: 从sock.recv()读字节→调用protocol.data_received(data)传递，Protocol只看到完整数据流片段 | 代价: Transport每次recv的bufsize(256KB)决定单次传递的数据粒度，Protocol可能收到不完整的帧需要自行缓冲拼接

【结构】"它长什么样？" ★★
1:1 配对结构，Transport 持有 Protocol 引用：

```
Transport (写端控制)           Protocol (读端处理)
  ├── _protocol: Protocol       ├── connection_made(transport)
  ├── _sock: socket             ├── data_received(data)
  ├── _buffer: bytearray        ├── eof_received()
  ├── _closing: bool            ├── connection_lost(exc)
  └── _pause_reading()          └── pause_writing() / resume_writing()
      _resume_reading()

配对建立:
  loop.create_connection(ProtocolFactory, host, port)
    → sock = socket(nonblocking=True)
    → transport = Transport(sock, protocol)
    → protocol.connection_made(transport)  ← 互相持有
    → selector.register(sock, READ, transport._read_ready)
```

设计意图：Transport 管"怎么收发字节"，Protocol 管"收到字节后做什么"。边界清晰，二者可独立替换（如 SSLProtocol 插入中间层）。

【时序】"它按什么顺序动？" ★★
数据到达的回调链时序：

```
连接建立:
  selector 通知 sock 可写 → Transport._write_ready()
    → 检查连接完成 → protocol.connection_made(transport)

数据读取:
  selector 通知 sock 可读 → Transport._read_ready()
    → data = sock.recv(read_bufsize)
    → if data: protocol.data_received(data)
    → if not data: protocol.eof_received() → maybe close

数据写入:
  protocol 调用 transport.write(data)
    → _buffer.extend(data)
    → if not _buffer_was_not_empty: selector.modify(sock, WRITE)

  selector 通知 sock 可写 → Transport._write_ready()
    → n = sock.send(_buffer) → _buffer = _buffer[n:]
    → if not _buffer: selector.modify(sock, READ)  # 取消写关注
    → protocol.resume_writing()  # 通知缓冲区已清空（流控）

流控:
  protocol.pause_writing() → Transport._paused = True（缓冲区超阈值时调用）
  protocol.resume_writing() → Transport._paused = False（缓冲区回降时调用）
```

【实体】"它的最小数据单元？" ★
- Transport: `_sock`（非阻塞 socket），`_buffer`（写缓冲），`_closing`（关闭标志）
- Protocol: 无状态字段，由用户子类化实现

【边界】"它在哪里交出控制权？" ★★★
**selector → Transport._read_ready() → Protocol.data_received() 是从内核到用户态的边界桥接**：

```
┌─────────────────────────────────────────────────┐
│                    内核态                        │
│  socket recv buffer  ──── 网络数据到达           │
└──────────┬──────────────────────────────────────┘
           │ selector.select() 返回 (fd, READ)
           │ ← 这是边界跨越点：内核通知用户态 "fd 可读"
┌──────────▼──────────────────────────────────────┐
│                  用户态                           │
│  Transport._read_ready()                        │
│    → data = sock.recv() 从内核缓冲区读取字节      │
│    → protocol.data_received(data) 交给业务层     │
│                                                  │
│  Transport._write_ready()                       │
│    → n = sock.send(_buffer) 向内核缓冲区写字节    │
│    → if done: selector.modify(fd, READ)         │
│             ↑ 取消写关注 ← 这是反向边界控制       │
└──────────────────────────────────────────────────┘
```

边界的关键：
- selector 将内核 I/O 就绪事件转化为 Transport 回调 → 这是从内核到用户态的**上行桥接**
- Transport.write() 注册/取消 selector 关注 → 这是从用户态到内核的**下行桥接**
- Protocol 只看到字节流，完全不知道 selector/socket 的存在 → 边界在此闭合

【内部关联】
- Transport._read_ready() --[数据传递(字节搬运者→业务处理者)]--> Protocol.data_received(data)  [E05 自环]
- Transport._write_ready() --[流控通知(缓冲管理者→生产节流者)]--> Protocol.resume_writing()  [E05 自环]
- Protocol.connection_made(transport) --[配对建立(业务层←传输层)]←→ Transport._protocol  [E05 自环]
- EventLoop.selector.select() --[就绪通知(轮询者→I/O回调触发者)]--> Transport._read_ready/_write_ready  [E01→E05]
- Transport.write(data) --[注册写关注(数据提交者→I/O监听者)]--> EventLoop.selector.modify(fd, WRITE)  [E05→E01]
- StreamReader._protocol --[桥接(缓冲消费者←数据推送者)]←→ Protocol.data_received  [E09←E05]

【示例】
```python
class EchoProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.transport.write(data)  # echo back

    def connection_lost(self, exc):
        pass

await loop.create_connection(EchoProtocol, '127.0.0.1', 8888)
# selector → _read_ready → data_received → write → _write_ready → sock.send
```

---