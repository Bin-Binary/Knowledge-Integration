# asyncio 知识提取清单（Python 3.11）

> **步骤**: Step 1 — 知识采集
> **来源**: CPython 3.11 asyncio 模块源码（Lib/asyncio/）
> **原则**: 纯客观提取，所有定义来自源码 docstring（原文或最小改写），无主观解读

---

## 一、事件循环接口与策略（events.py）

### C01 — Handle

| 字段 | 内容 |
|------|------|
| **定义** | Object returned by callback registration methods. |
| **关键属性** | `_callback`, `_args`, `_cancelled`, `_loop`, `_source_traceback`, `_repr`, `__weakref__`, `_context` |
| **关键方法** | `cancel()`, `cancelled()`, `_run()` |
| **源码位置** | `events.py:~33` |
| **关联概念** | 被 **C02** 继承；由 `call_soon()`(C10), `call_soon_threadsafe()`(C13) 返回 |

### C02 — TimerHandle

| 字段 | 内容 |
|------|------|
| **定义** | Object returned by timed callback registration methods. |
| **关键属性** | 继承 Handle 全部属性；新增 `_scheduled` (bool, 是否在调度堆中), `_when` (float, 绝对触发时间) |
| **关键方法** | `cancel()` (override, additionally notifies loop to increment `_timer_cancelled_count`) |
| **源码位置** | `events.py:~132` |
| **关联概念** | 继承 **C01**；由 `call_later()`(C11), `call_at()`(C12) 返回；存入 `BaseEventLoop._scheduled` 堆；实现 `__lt__`/`__le__`/`__gt__`/`__ge__` 用于堆排序 |

### C03 — AbstractEventLoop

| 字段 | 内容 |
|------|------|
| **定义** | Abstract base class defining the event loop interface. ~70+ abstract methods. |
| **关键属性** | N/A (ABC, 全部为 abstract method) |
| **关键方法** | `run_forever()`, `run_until_complete()`, `stop()`, `close()`, `call_soon()`, `call_later()`, `call_at()`, `call_soon_threadsafe()`, `create_task()`, `create_future()`, `add_reader()`, `remove_reader()`, `add_writer()`, `remove_writer()`, `run_in_executor()`, `set_default_executor()`, `subprocess_shell()`, `subprocess_exec()`, `connect_accepted_socket()`, `sendfile()`, `start_serving()`, `create_server()`, `create_unix_server()`, `connect_read_pipe()`, `connect_write_pipe()`, `getaddrinfo()`, `getnameinfo()`, `set_exception_handler()`, `get_exception_handler()`, `default_exception_handler()`, `call_exception_handler()`, `get_debug()`, `set_debug()` |
| **源码位置** | `events.py:~230` |
| **关联概念** | **C07**(BaseEventLoop) 实现此接口；**C04**(Policy) 通过策略创建此接口实例 |

### C04 — AbstractEventLoopPolicy

| 字段 | 内容 |
|------|------|
| **定义** | Abstract base class for event loop policy. An event loop policy manages the event loop per thread. |
| **关键属性** | N/A (ABC) |
| **关键方法** | `get_event_loop()`, `set_event_loop(loop)`, `new_event_loop()` |
| **源码位置** | `events.py:~340` |
| **关联概念** | 决定 **C03/C07** 的创建方式；全局策略通过 `get_event_loop_policy()`/`set_event_loop_policy()` 管理 |

### C05 — get_event_loop()

| 字段 | 内容 |
|------|------|
| **定义** | Return an asyncio event loop. When called from a coroutine or a callback, return the running loop. Otherwise, create and set a new loop. |
| **源码位置** | `events.py:~660` |
| **关联概念** | 依赖 **C06** 判断当前运行状态 |

### C06 — get_running_loop()

| 字段 | 内容 |
|------|------|
| **定义** | Return the running event loop. Raise RuntimeError if there is no running event loop. |
| **源码位置** | `events.py:~640` |
| **关联概念** | 由 `_set_running_loop()`(C07c) 设置线程局部变量；`create_task()`(C18) 依赖此函数 |

### C07a — set_event_loop(loop)

| 字段 | 内容 |
|------|------|
| **定义** | Set the event loop for the current OS thread. |
| **源码位置** | `events.py:~670` |
| **关联概念** | 委托给 **C04**(Policy) 的同名方法 |

### C07b — new_event_loop()

| 字段 | 内容 |
|------|------|
| **定义** | Create and return a new event loop. |
| **源码位置** | `events.py:~680` |
| **关联概念** | 委托给 **C04**(Policy) 的同名方法 |

### C07c — _set_running_loop(loop)

| 字段 | 内容 |
|------|------|
| **定义** | Set the running event loop for the current OS thread. Internal use only. |
| **源码位置** | `events.py:~690` |
| **关联概念** | 仅在 `run_forever()`/`Runner.run()` 内部调用 |

---

## 二、事件循环基础实现（base_events.py）

### C08 — BaseEventLoop

| 字段 | 内容 |
|------|------|
| **定义** | Base implementation of the event loop. Implements ~90% of AbstractEventLoop, leaving I/O multiplexing to subclasses. |
| **关键属性** | `_ready` (deque[Handle], 就绪回调队列 FIFO), `_scheduled` (list[TimerHandle], 定时回调最小堆), `_timer_cancelled_count` (int, 已取消 TimerHandle 计数用于延迟堆压缩), `_closed` (bool), `_stopping` (bool), `_thread_id` (int), `_default_executor` (concurrent.futures.Executor), `_exception_handler` (Callable), `_current_handle` (Handle|None), `_task_factory` (Callable|None), `_asyncgens` (WeakSet), `_clock_resolution` (float) |
| **关键方法** | `run_forever()`, `run_until_complete(future)`, `stop()`, `close()`, `create_task(coro)`, `create_future()`, `_run_once()`, `run_in_executor(executor, func, *args)`, `set_exception_handler(handler)`, `default_exception_handler(context)`, `call_exception_handler(context)`, `set_task_factory(factory)`, `get_task_factory()` |
| **源码位置** | `base_events.py:~40` |
| **关联概念** | 实现 **C03** 接口；**C30**(Selector)/**C33**(Proactor) 派生此类；`_run_once()` 是核心调度循环；`create_task()` 使用 **C17**(Task) |

### C08.1 — _run_once() 核心调度算法

```
1. 计算距最近定时器的超时时间
2. 若 _timer_cancelled_count >= _min_cancelled_timer_count_since_last_sweep: 堆压缩(heapify)
3. 可选: 回收空闲的 default_executor 线程
4. 调用 _poll(timeout) 等待 I/O 事件（selector.select 或 proactor I/O completion）
5. 将 I/O 就绪回调加入 _ready
6. 将到期的 TimerHandle 从 _scheduled 弹入 _ready
7. 执行 _ready 中的所有回调（最多 ntodo 个, 防止饥饿）
```

| 源码位置 | `base_events.py:~1870` |

### C09 — Server

| 字段 | 内容 |
|------|------|
| **定义** | Represents a listening server. Object returned by create_server() and start_serving(). |
| **关键属性** | `_loop`, `_sockets` (list[socket]), `_active_count` (int), `_waiters` (deque[Future]), `_protocol_factory` (Callable), `_serving` (bool), `_is_ssl` (bool), `_ssl_context` (ssl.SSLContext|None) |
| **关键方法** | `close()`, `start_serving()`, `serve_forever()` (async), `wait_closed()` (async), `get_loop()`, `is_serving()` |
| **源码位置** | `base_events.py:~270` |
| **关联概念** | 由 `create_server()`/`start_serving()` 返回；使用 **C41**(Protocol) 工厂 |

---

## 三、回调注册方法（base_events.py 延续）

### C10 — call_soon(callback, *args)

| 字段 | 内容 |
|------|------|
| **定义** | Arrange for a callback to be called as soon as possible. The callback is called once, and it is not thread-safe. |
| **返回** | Handle (**C01**) |
| **源码位置** | `base_events.py:~720` |
| **关联概念** | 回调进入 `_ready` 队列 |

### C11 — call_later(delay, callback, *args)

| 字段 | 内容 |
|------|------|
| **定义** | Arrange for a callback to be called at a given delay from now. Internally delegates to call_at(). |
| **返回** | TimerHandle (**C02**) |
| **源码位置** | `base_events.py:~750` |

### C12 — call_at(when, callback, *args)

| 字段 | 内容 |
|------|------|
| **定义** | Like call_later(), but 'when' is an absolute timestamp (same as loop.time()). |
| **返回** | TimerHandle (**C02**) |
| **源码位置** | `base_events.py:~770` |
| **关联概念** | `call_later` 内部委托 `call_at(loop.time() + delay, ...)` |

### C13 — call_soon_threadsafe(callback, *args)

| 字段 | 内容 |
|------|------|
| **定义** | Like call_soon(), but thread-safe. Wakes up the loop via self-pipe (selector) or PostQueuedCompletionStatus (proactor). |
| **返回** | Handle (**C01**) |
| **源码位置** | `base_events.py:~790` |
| **关联概念** | 跨线程安全写入；依赖 **C14**(self-pipe) 或 proactor 的 APC 机制唤醒 |

### C14 — Self-pipe（内部机制）

| 字段 | 内容 |
|------|------|
| **定义** | Internal self-pipe mechanism for thread-safe event loop wakeup. Writing to _csock signals the loop to wake from select(). |
| **关键属性** | `_ssock` (read end), `_csock` (write end), `_internal_fds` |
| **源码位置** | `selector_events.py:~68` |
| **关联概念** | 被 `call_soon_threadsafe()`(**C13**) 使用；在 `BaseSelectorEventLoop._process_self()` 中读取并清空 |

---

## 四、Future 状态容器（futures.py / base_futures.py）

### C15 — Future

| 字段 | 内容 |
|------|------|
| **定义** | This class is *almost* compatible with concurrent.futures.Future. Differences: result() and exception() do not take a timeout argument and raise CancelledError if the future is cancelled; callbacks are always called via the event loop's call_soon(). |
| **状态机** | `PENDING → CANCELLED` 或 `PENDING → FINISHED`（不可逆） |
| **关键属性** | `_state` (`_PENDING`/`_CANCELLED`/`_FINISHED`), `_result`, `_exception`, `_loop`, `_callbacks` (list of (callback, context) tuples), `_cancel_message`, `_cancelled_exc`, `_asyncio_future_blocking` (int, 0=not awaited, 1=awaited once, 2=yield from) |
| **关键方法** | `result()`, `exception()`, `set_result(result)`, `set_exception(exception)`, `add_done_callback(callback, *, context)`, `remove_done_callback(callback)`, `cancel(msg=None)`, `cancelled()`, `done()`, `__await__()`, `__iter__()`, `get_loop()` |
| **源码位置** | `futures.py:~50` / `base_futures.py:~7` |
| **关联概念** | **C17**(Task) 继承 Future；`add_done_callback` 回调通过 **C01**(Handle) 调度；`_asyncio_future_blocking` 标记 await 是否合法 |

#### C15.1 — Future 状态转换

```
PENDING ──set_result()──→ FINISHED
PENDING ──set_exception()──→ FINISHED
PENDING ──cancel()──→ CANCELLED

FINISHED / CANCELLED: 后续 set_result/set_exception 抛 InvalidStateError
                      后续 cancel 为空操作
```

### C16 — wrap_future(future, *, loop=None)

| 字段 | 内容 |
|------|------|
| **定义** | Wrap a concurrent.futures.Future object in an asyncio.Future. |
| **源码位置** | `futures.py:~350` |
| **关联概念** | 桥接 concurrent.futures 与 asyncio；在 `run_in_executor()` 中隐式使用 |

---

## 五、Task 协程调度（tasks.py / base_tasks.py）

### C17 — Task

| 字段 | 内容 |
|------|------|
| **定义** | A coroutine wrapped in a Future. Task is a subclass of Future that wraps a coroutine. When the coroutine returns, the Task's result is set. When it raises, the exception is set. |
| **继承** | extends **Future**(**C15**) |
| **关键属性（新增）** | `_coro` (coroutine object), `_fut_waiter` (Future|None), `_must_cancel` (bool), `_cancel_message` (str), `_name` (str), `_num_cancels_requested` (int, Python 3.11), `_context` (contextvars.Context copy, Python 3.11) |
| **关键不变量** | Either `_fut_waiter is None` and `__step()` is scheduled via `call_soon()`, OR `_fut_waiter is some Future` and `__step()` is NOT scheduled. |
| **关键方法** | `__step(exc)` (核心驱动, non-public), `__wakeup(future)` (callback for _fut_waiter completion), `cancel(msg=None)`, `cancelling()`, `uncancel()`, `get_coro()`, `get_name()`, `set_name(name)` |
| **禁止操作** | **不允许** 直接调用 `set_result()` / `set_exception()`（应在 `__step` 内部由协程返回值/抛异常设置） |
| **源码位置** | `tasks.py:~90` / `base_tasks.py:~15` |
| **关联概念** | 继承 **C15**；由 **C18**(`create_task`) 创建；**C100**(TaskGroup) 管理集合；**C22**/C23/C25 协作 |

#### C17.1 — __step() 核心驱动逻辑

```
1. 若 _fut_waiter 不为 None：断言 _fut_waiter.done() 且 _fut_waiter callbacks 已清空
2. 设置 _fut_waiter = None
3. 若 _must_cancel：抛 CancelledError 进入协程
4. 在 _context 中调用 coro.send(result / exception)
5. 若 coro 返回 StopIteration(value)：set_result(value)
6. 若 coro 返回 Future/Task：设置 _fut_waiter, add_done_callback(__wakeup)
7. 若 coro 抛 CancelledError：将 cancel 传播到 result
8. 若 coro 抛其他异常：set_exception(exc)
```

| 源码位置 | `tasks.py:~280` |

#### C17.2 — cancel() / cancelling() / uncancel() 机制（Python 3.11 新增）

```
cancel(msg=None):
  _num_cancels_requested += 1
  若 task 未开始(PENDING)：直接 CANCELLED
  若 _fut_waiter 存在：_fut_waiter.cancel(), _must_cancel=True
  返回是否成功请求取消

cancelling(): 返回 _num_cancels_requested
uncancel():   _num_cancels_requested -= 1 (最小为0)
              若降为0：_must_cancel=False
              返回新的 _num_cancels_requested
```

| 源码位置 | `tasks.py:~220` |

### C18 — create_task(coro, *, name=None)

| 字段 | 内容 |
|------|------|
| **定义** | Schedule the execution of a coroutine object in a spawned Task. Return the Task object. Must be called from a running event loop. |
| **源码位置** | `tasks.py:~380` |
| **关联概念** | 依赖 **C06**(`get_running_loop`); 使用 loop 的 `_task_factory` 或默认 `Task(coro)` 构造 |

### C19 — gather(*awaitables, return_exceptions=False)

| 字段 | 内容 |
|------|------|
| **定义** | Run awaitable objects in the asyncio event loop concurrently and return an aggregate list of their results. If return_exceptions is True, exceptions are treated the same as successful results. |
| **关键行为** | 自动将 coroutine 包装为 Task; 所有 awaitable 并发执行; 任一失败时默认取消其余所有; gather 本身被取消则取消所有子任务 |
| **源码位置** | `tasks.py:~660` |
| **关联概念** | 创建 **C17**(Task); 返回 **C15**(Future, 内部 _GatheringFuture) |

### C20 — wait(aws, *, return_when=ALL_COMPLETED)

| 字段 | 内容 |
|------|------|
| **定义** | Wait for the Futures and coroutines given by aws to complete. Coroutines will be wrapped in Tasks. Returns two sets: (done, pending). |
| **return_when** | `FIRST_COMPLETED` — 任一完成即返回; `FIRST_EXCEPTION` — 任一异常或全部完成; `ALL_COMPLETED` — 全部完成 |
| **源码位置** | `tasks.py:~410` |
| **关联概念** | 不返回结果，仅返回完成/未完成集合；使用 Future.add_done_callback() |

### C21 — wait_for(aw, timeout)

| 字段 | 内容 |
|------|------|
| **定义** | Wait for the single Future or coroutine to complete, with a timeout. If timeout is exceeded, cancel the task and raise TimeoutError. |
| **关键行为** | 超时时取消被等待的 task; 处理任务取消与超时的竞争条件 |
| **源码位置** | `tasks.py:~510` |
| **关联概念** | 使用 Task.cancel(); 抛 **C132**(TimeoutError) |

### C22 — as_completed(aws, *, timeout=None)

| 字段 | 内容 |
|------|------|
| **定义** | Return an iterator whose values are futures. When a future from the original set completes, it is yielded by the iterator. |
| **源码位置** | `tasks.py:~580` |
| **关联概念** | 返回 async iterator; 使用 Future.add_done_callback() |

### C23 — shield(arg)

| 字段 | 内容 |
|------|------|
| **定义** | Wait for a future, shielding it from cancellation. The future is not cancelled when the caller (shield) is cancelled. |
| **关键行为** | 外部 cancel 不传递到内部 Future; 内部 Future 自身取消/异常仍传播; 需手动确保内部 Future 最终被清理 |
| **源码位置** | `tasks.py:~780` |
| **关联概念** | 返回 **C15**(Future); **C110**(Timeout) 内部使用类似逻辑 |

### C24 — sleep(delay, result=None)

| 字段 | 内容 |
|------|------|
| **定义** | Coroutine that completes after a given time (in seconds). If result is provided, it is returned to the caller. sleep(0) can be used to yield control to the event loop for one iteration. |
| **源码位置** | `tasks.py:~630` |
| **关联概念** | 使用 `call_later()`(**C11**) 注册 **C02**(TimerHandle); delay=0 时仍会 yield 控制权 |

### C25 — ensure_future(coro_or_future, *, loop=None)

| 字段 | 内容 |
|------|------|
| **定义** | Wrap a coroutine or a Future in a Task. If the argument is already a Task or a Future, return it. |
| **源码位置** | `tasks.py:~880` |
| **关联概念** | 向后兼容函数; 推荐使用 **C18**(`create_task`)(从运行循环中调用) |

### C26 — current_task(loop=None) / all_tasks(loop=None)

| 字段 | 内容 |
|------|------|
| **定义** | `current_task()`: Return the currently running Task, or None. `all_tasks()`: Return a set of all tasks for the loop. |
| **源码位置** | `tasks.py:~45` |
| **关联概念** | `all_tasks` 使用 WeakSet 避免阻止 GC |

---

## 六、协程工具（coroutines.py）

### C27 — iscoroutine(obj)

| 字段 | 内容 |
|------|------|
| **定义** | Return True if obj is a coroutine object. |
| **源码位置** | `coroutines.py:~20` |
| **关联概念** | 委托 `inspect.iscoroutine()`；被 `ensure_future()` 等使用 |

### C28 — iscoroutinefunction(func)

| 字段 | 内容 |
|------|------|
| **定义** | Return True if func is a decorated coroutine function. |
| **源码位置** | `coroutines.py:~30` |
| **关联概念** | 委托 `inspect.iscoroutinefunction()` |

### C29 — _is_debug_mode()

| 字段 | 内容 |
|------|------|
| **定义** | Determine if asyncio debug mode is enabled. Checks os.environ['PYTHONASYNCIODEBUG'] or sys.flags.debug. |
| **源码位置** | `coroutines.py:~40` |
| **关联概念** | 影响 Handle/Task 的 traceback 记录和慢回调检测阈值 |

---

## 七、Selector 事件循环与传输（selector_events.py）

### C30 — BaseSelectorEventLoop

| 字段 | 内容 |
|------|------|
| **定义** | Selector-based event loop, extends BaseEventLoop. Uses selectors module for I/O multiplexing. |
| **继承** | extends **C08**(BaseEventLoop) |
| **关键属性** | `_selector` (selectors.BaseSelector), `_transports` (WeakValueDictionary: fd→Transport), `_ssock` (socket, self-pipe read), `_csock` (socket, self-pipe write), `_internal_fds` |
| **关键方法** | `add_reader(fd, callback, *args)`, `remove_reader(fd)`, `add_writer(fd, callback, *args)`, `remove_writer(fd)`, `_process_events(key_list)`, `close()` |
| **源码位置** | `selector_events.py:~15` |
| **关联概念** | Unix/Windows 通用（Windows 使用 SelectSelector）；`_process_events` 将 I/O 就绪事件转为 `_ready` 回调 |

### C31 — _SelectorSocketTransport

| 字段 | 内容 |
|------|------|
| **定义** | TCP transport using selector. |
| **继承** | extends `_FlowControlMixin`(**C51**) + `Transport`(**C48**) |
| **关键属性** | `_sock` (socket), `_protocol` (Protocol), `_closing` (bool), `_paused` (bool), `_buffer` (deque of bytes), `_conn_lost` (int), `_eof` (bool), `_read_ready_cb` |
| **关键方法** | `write(data)`, `writelines(list_of_data)`, `close()`, `pause_reading()`, `resume_reading()`, `set_write_buffer_limits(high, low)`, `_read_ready()`, `_write_ready()` |
| **源码位置** | `selector_events.py:~680` |
| **关联概念** | 配对 **C41**(Protocol) 使用；继承 **C51**(_FlowControlMixin) 流控 |

### C32 — _SelectorDatagramTransport

| 字段 | 内容 |
|------|------|
| **定义** | UDP transport using selector. |
| **关键方法** | `sendto(data, addr)`, `abort()` |
| **源码位置** | `selector_events.py:~1070` |
| **关联概念** | 配对 **C43**(DatagramProtocol) 使用 |

---

## 八、Proactor 事件循环与传输（proactor_events.py）

### C33 — BaseProactorEventLoop

| 字段 | 内容 |
|------|------|
| **定义** | Proactor-based event loop for Windows. Uses I/O completion ports via _Proactor. |
| **继承** | extends **C08**(BaseEventLoop) |
| **关键属性** | `_proactor` (IOCP proactor object) |
| **关键方法** | Overridden: `_make_socket_transport()`, `_make_ssl_transport()`, `_make_datagram_transport()`, `add_reader()` (raise NotImplementedError), `remove_reader()` (raise NotImplementedError), `add_writer()` (raise NotImplementedError), `remove_writer()` (raise NotImplementedError) |
| **源码位置** | `proactor_events.py:~15` |
| **关联概念** | Windows 平台默认循环；不使用 selector，通过 overlapped I/O 完成通知 |

### C34 — _ProactorSocketTransport

| 字段 | 内容 |
|------|------|
| **定义** | TCP transport using proactor (overlapped I/O). |
| **关键属性** | `_sock`, `_protocol`, `_closing`, `_read_fut`, `_write_fut`, `_buffer` |
| **源码位置** | `proactor_events.py:~570` |
| **关联概念** | 使用 overlapped.recv/send；通过 `_loop_self_reading_fd` 接收完成通知 |

### C35 — _ProactorDuplexPipeTransport / _ProactorReadPipeTransport / _ProactorWritePipeTransport

| 字段 | 内容 |
|------|------|
| **定义** | Pipe transports using proactor: duplex (bidirectional), read-only, write-only. |
| **源码位置** | `proactor_events.py:~780` / `proactor_events.py:~460` / `proactor_events.py:~660` |
| **关联概念** | 用于子进程管道; 配对 **C44**(SubprocessProtocol) |

---

## 九、协议体系（protocols.py）

### C40 — BaseProtocol

| 字段 | 内容 |
|------|------|
| **定义** | Base protocol class. All methods are callbacks called by the event loop. |
| **关键方法** | `connection_made(transport)`, `connection_lost(exc)`, `pause_writing()`, `resume_writing()` |
| **源码位置** | `protocols.py:~12` |
| **关联概念** | 所有 Protocol 的基类；`connection_made` 接收 **C45**(BaseTransport) 实例 |

### C41 — Protocol(BaseProtocol)

| 字段 | 内容 |
|------|------|
| **定义** | Protocol for stream-oriented (TCP) connections. |
| **状态机** | `start → CM [→ DR*] [→ ER?] → CL → end` |
| **关键方法** | `data_received(data)`, `eof_received()` → bool |
| **源码位置** | `protocols.py:~40` |
| **关联概念** | 配对 **C48**(Transport) / **C31**(_SelectorSocketTransport); CM=connection_made, DR=data_received, ER=eof_received, CL=connection_lost |

### C42 — BufferedProtocol(BaseProtocol)

| 字段 | 内容 |
|------|------|
| **定义** | A protocol with manual buffer control. Avoids extra data copies by letting the protocol provide the buffer. |
| **关键方法** | `get_buffer(sizehint)` → bytearray-like, `buffer_updated(nbytes)` |
| **源码位置** | `protocols.py:~70` |
| **关联概念** | 用于高性能场景减少内存拷贝 |

### C43 — DatagramProtocol(BaseProtocol)

| 字段 | 内容 |
|------|------|
| **定义** | Protocol for datagram (UDP) connections. |
| **关键方法** | `datagram_received(data, addr)`, `error_received(exc)` |
| **源码位置** | `protocols.py:~100` |
| **关联概念** | 配对 **C32**(_SelectorDatagramTransport) / **C49**(DatagramTransport) |

### C44 — SubprocessProtocol(BaseProtocol)

| 字段 | 内容 |
|------|------|
| **定义** | Protocol for subprocess pipes. |
| **关键方法** | `pipe_data_received(fd, data)`, `pipe_connection_lost(fd, exc)`, `process_exited()` |
| **源码位置** | `protocols.py:~130` |
| **关联概念** | 配对 **C50**(SubprocessTransport) |

---

## 十、传输体系（transports.py）

### C45 — BaseTransport

| 字段 | 内容 |
|------|------|
| **定义** | Base class for transports. |
| **关键属性** | `_extra` (dict, extra info like peername, socket etc.) |
| **关键方法** | `get_extra_info(name, default=None)`, `is_closing()`, `close()`, `set_protocol(protocol)`, `get_protocol()` |
| **源码位置** | `transports.py:~20` |
| **关联概念** | 所有 Transport 的基类；在 `connection_made` 中传给 Protocol |

### C46 — ReadTransport(BaseTransport)

| 字段 | 内容 |
|------|------|
| **定义** | Read-only transport interface. |
| **关键方法** | `is_reading()`, `pause_reading()`, `resume_reading()` |
| **源码位置** | `transports.py:~70` |
| **关联概念** | 继承 **C45** |

### C47 — WriteTransport(BaseTransport)

| 字段 | 内容 |
|------|------|
| **定义** | Write-only transport interface. |
| **关键方法** | `write(data)`, `writelines(list_of_data)`, `write_eof()`, `can_write_eof()`, `abort()`, `set_write_buffer_limits(high, low)`, `get_write_buffer_size()` |
| **源码位置** | `transports.py:~100` |
| **关联概念** | 继承 **C45** |

### C48 — Transport(ReadTransport, WriteTransport)

| 字段 | 内容 |
|------|------|
| **定义** | Bidirectional transport, inherits both ReadTransport and WriteTransport. |
| **源码位置** | `transports.py:~140` |
| **关联概念** | 多重继承 **C46** + **C47**；TCP 连接使用此接口 |

### C49 — DatagramTransport

| 字段 | 内容 |
|------|------|
| **定义** | Datagram (UDP) transport interface. |
| **关键方法** | `sendto(data, addr=None)`, `abort()` |
| **源码位置** | `transports.py:~160` |
| **关联概念** | 继承 **C45**；配对 **C43**(DatagramProtocol) |

### C50 — SubprocessTransport

| 字段 | 内容 |
|------|------|
| **定义** | Transport for subprocess. |
| **关键方法** | `get_pid()`, `get_returncode()`, `get_pipe_transport(fd)`, `send_signal(signal)`, `terminate()`, `kill()` |
| **源码位置** | `transports.py:~195` |
| **关联概念** | 继承 **C45**；配对 **C44**(SubprocessProtocol) |

### C51 — _FlowControlMixin

| 字段 | 内容 |
|------|------|
| **定义** | Mixin for write flow control. Pauses the protocol when the write buffer exceeds the high-water mark and resumes it when it drops below the low-water mark. |
| **关键属性** | `_loop`, `_protocol_paused` (bool), `_high_water` (int, default 64KB), `_low_water` (int, default 16KB) |
| **关键方法** | `_maybe_pause_protocol()`, `_maybe_resume_protocol()` |
| **源码位置** | `transports.py:~230` |
| **关联概念** | 被 **C31**(_SelectorSocketTransport) 等继承；调用 Protocol 的 `pause_writing()`/`resume_writing()` |

---

## 十一、同步原语（locks.py）

### C60 — Lock

| 字段 | 内容 |
|------|------|
| **定义** | Primitive lock object. A Lock can be acquired only once. Not reentrant (a second acquire by the same task will deadlock). |
| **关键属性** | `_locked` (bool), `_waiters` (deque of Future) |
| **关键方法** | `acquire()` (async → bool), `release()`, `locked()` → bool |
| **支持** | `async with lock:` |
| **源码位置** | `locks.py:~15` |
| **关联概念** | **C62**(Condition) 内部持有一个 Lock |

### C61 — Event

| 字段 | 内容 |
|------|------|
| **定义** | Asynchronous equivalent of threading.Event. An Event object will wake up one or more tasks when set. |
| **关键属性** | `_value` (bool), `_waiters` (deque of Future) |
| **关键方法** | `set()`, `clear()`, `wait()` (async → bool), `is_set()` → bool |
| **源码位置** | `locks.py:~230` |
| **关联概念** | Queue 的 `_finished` 是 Event 实例 |

### C62 — Condition

| 字段 | 内容 |
|------|------|
| **定义** | Asynchronous equivalent of threading.Condition. Can be used to wait for a condition to become true. |
| **关键属性** | `_lock` (**C60** Lock), `_waiters` (deque of Future) |
| **关键方法** | `wait()` (async → bool), `notify(n=1)`, `notify_all()`, `wait_for(predicate)` (async) |
| **支持** | `async with condition:` |
| **源码位置** | `locks.py:~360` |
| **关联概念** | **C65**(Barrier) 内部使用 Condition |

### C63 — Semaphore

| 字段 | 内容 |
|------|------|
| **定义** | Asynchronous equivalent of threading.Semaphore. A semaphore manages an internal counter which is decremented by each acquire() call and incremented by each release() call. The counter can never go below zero. |
| **关键属性** | `_value` (int), `_waiters` (deque of Future) |
| **关键方法** | `acquire()` (async → bool), `release()` |
| **支持** | `async with semaphore:` |
| **源码位置** | `locks.py:~500` |
| **关联概念** | **C64**(BoundedSemaphore) 继承此类 |

### C64 — BoundedSemaphore(Semaphore)

| 字段 | 内容 |
|------|------|
| **定义** | A bounded semaphore that raises ValueError if release() would increase the counter above the initial value. |
| **额外属性** | `_bound_value` (int, = initial `_value`) |
| **源码位置** | `locks.py:~570` |
| **关联概念** | 继承 **C63** |

### C65 — Barrier

| 字段 | 内容 |
|------|------|
| **定义** | Synchronization barrier. A Barrier object waits for a fixed number of tasks (parties) before releasing them all simultaneously. New in Python 3.11. |
| **关键属性** | `_parties` (int), `_state` (`FILLING`/`DRAINING`/`RESETTING`/`BROKEN`), `_count` (int), `_cond` (**C62** Condition) |
| **关键方法** | `wait()` (async → int), `reset()`, `abort()`, `parties` (property), `n_waiting` (property), `broken` (property) |
| **源码位置** | `locks.py:~630` |
| **关联概念** | 内部使用 **C62**(Condition)；`abort()` 设置 BROKEN 状态，后续 wait 抛 **C135**(BrokenBarrierError) |

---

## 十二、队列（queues.py）

### C70 — Queue

| 字段 | 内容 |
|------|------|
| **定义** | A queue, useful for coordinating producer and consumer coroutines. |
| **关键属性** | `_maxsize` (int, 0=unlimited), `_queue` (deque), `_getters` (deque of Future, 等待 get 的协程), `_putters` (deque of (item, Future), 等待 put 的协程), `_unfinished_tasks` (int), `_finished` (**C61** Event) |
| **关键方法** | `put(item)` (async), `get()` (async), `put_nowait(item)`, `get_nowait()`, `task_done()`, `join()` (async), `qsize()`, `empty()`, `full()` |
| **源码位置** | `queues.py:~15` |
| **关联概念** | `_finished` 使用 **C61**(Event)；`task_done()`/`join()` 实现生产者-消费者同步 |

#### C70.1 — Queue 内部调度机制

```
put_nowait(item):
  若 _getters 非空：弹出第一个 getter Future, set_result(item)
  否则：_queue.append(item), _unfinished_tasks += 1

get_nowait():
  若 _putters 非空：弹出第一个 putter, putter Future set_result(True), 返回 _queue.popleft() 或 putter.item
  否则：返回 _queue.popleft()

task_done(): _unfinished_tasks -= 1; 若 == 0: _finished.set()
join(): await _finished.wait()
```

### C71 — PriorityQueue(Queue)

| 字段 | 内容 |
|------|------|
| **定义** | A subclass of Queue; entries are sorted by priority (lowest first). |
| **内部存储** | 使用 `heapq` 模块 |
| **源码位置** | `queues.py:~250` |
| **关联概念** | 继承 **C70**；仅覆盖 `_init`, `_put`, `_get` |

### C72 — LifoQueue(Queue)

| 字段 | 内容 |
|------|------|
| **定义** | A subclass of Queue; entries are retrieved in LIFO order. |
| **内部存储** | 使用 `list` (append/pop) |
| **源码位置** | `queues.py:~275` |
| **关联概念** | 继承 **C70**；仅覆盖 `_init`, `_put`, `_get` |

---

## 十三、流（streams.py）

### C80 — StreamReader

| 字段 | 内容 |
|------|------|
| **定义** | Buffered stream reader. |
| **关键属性** | `_buffer` (deque of bytes), `_limit` (int, 缓冲区低位标), `_loop`, `_eof` (bool), `_waiter` (Future|None), `_exception` |
| **关键方法** | `read(n=-1)` (async), `readline()` (async), `readexactly(n)` (async), `readuntil(separator=b'\\n')` (async), `feed_data(data)`, `feed_eof()` |
| **源码位置** | `streams.py:~40` |
| **关联概念** | 被 **C82**(StreamReaderProtocol) 填充数据；缓冲区超 `_limit` 时触发传输暂停；`readexactly()` 抛 **C133**(IncompleteReadError); `readuntil()` 抛 **C134**(LimitOverrunError) |

### C81 — StreamWriter

| 字段 | 内容 |
|------|------|
| **定义** | Wrapper for write operations on a stream. |
| **关键属性** | `_transport` (**C48** Transport), `_protocol` (Protocol), `_reader` (**C80** StreamReader|None), `_loop` |
| **关键方法** | `write(data)`, `writelines(data)`, `close()`, `drain()` (async, 等待传输缓冲区排空), `is_closing()`, `wait_closed()` (async) |
| **源码位置** | `streams.py:~250` |
| **关联概念** | `drain()` 配合 **C51**(_FlowControlMixin) 流控使用 |

### C82 — StreamReaderProtocol(Protocol)

| 字段 | 内容 |
|------|------|
| **定义** | Bridge between Protocol callbacks and StreamReader state. |
| **关键属性** | `_stream_reader` (**C80** StreamReader), `_over_ssl` (bool), `_transport` |
| **关键方法** | `connection_made(transport)` → creates Future for connection, `data_received(data)` → `_stream_reader.feed_data()`, `eof_received()` → `_stream_reader.feed_eof()`, `connection_lost(exc)` → 设置 waiter 和 reader 异常 |
| **源码位置** | `streams.py:~210` |
| **关联概念** | 继承 **C41**(Protocol)；桥接 **C80** 与 Transport 回调 |

### C83 — open_connection(host, port, ...)

| 字段 | 内容 |
|------|------|
| **定义** | A wrapper for create_connection() returning a (reader, writer) pair. |
| **源码位置** | `streams.py:~70` |
| **关联概念** | 高层便捷函数；返回 (StreamReader, StreamWriter) |

### C84 — start_server(client_connected_cb, host, port, ...)

| 字段 | 内容 |
|------|------|
| **定义** | Start a socket server, call back for each client connected. |
| **源码位置** | `streams.py:~460` |
| **关联概念** | 返回 **C09**(Server) 对象；每连接创建 (StreamReader, StreamWriter) 并调用回调 |

---

## 十四、运行器（runners.py）

### C90 — Runner

| 字段 | 内容 |
|------|------|
| **定义** | A context manager that controls the event loop lifecycle. |
| **关键属性** | `_state` (`CREATED`/`INITIALIZED`/`CLOSED`), `_loop` (AbstractEventLoop), `_context` (contextvars.Context), `_debug` (bool), `_interrupt_count` (int) |
| **关键方法** | `__enter__()`, `__exit__()`, `run(coro)`, `close()`, `get_loop()` |
| **源码位置** | `runners.py:~10` |
| **关联概念** | `run()` 内部调用 `loop.run_until_complete(coro)`；`close()` 清理 loop 和 asyncgens；处理 KeyboardInterrupt |

### C91 — run(main, *, debug=None)

| 字段 | 内容 |
|------|------|
| **定义** | Execute the coroutine and return the result. This function creates a new event loop and closes it at the end. It should be used as a main entry point for asyncio programs. |
| **行为** | 1. 创建新事件循环 2. 运行 main 协程 3. 关闭 loop（含 asyncgen shutdown、executor shutdown） |
| **源码位置** | `runners.py:~80` |
| **关联概念** | 使用 **C90**(Runner) 实现；每次调用创建新 loop（禁止嵌套调用） |

---

## 十五、任务组（taskgroups.py）

### C100 — TaskGroup

| 字段 | 内容 |
|------|------|
| **定义** | Asynchronous context manager for managing groups of tasks. |
| **关键属性** | `_entered` (bool), `_exiting` (bool), `_aborting` (bool), `_parent_task` (**C17** Task), `_tasks` (set of **C17** Task), `_errors` (list of Exception), `_on_completed_fut` (Future|None), `_base_error` (BaseException|None) |
| **关键方法** | `__aenter__()`, `__aexit__(et, exc, tb)`, `create_task(coro)` |
| **关键行为** | 任一子 Task 抛异常 → 取消所有其他子 Task → 将所有异常组合为 `ExceptionGroup` 抛出 |
| **源码位置** | `taskgroups.py:~15` |
| **关联概念** | `create_task` 调用 **C18**；`__aexit__` 收集异常组合为 `ExceptionGroup`（Python 3.11 新特性）；结构化并发（vs 非结构化的 `gather`） |

#### C100.1 — TaskGroup 生命周期

```
__aenter__:
  记录 _parent_task = current_task()
  返回 self

create_task(coro):
  调用 _parent_task 的 loop.create_task(coro)
  将 task 加入 _tasks
  注册 task 的 done_callback

__aexit__:
  1. 设置 _exiting = True
  2. 等待所有 _tasks 完成（await _on_completed_fut）
  3. 清理已完成任务的回调
  4. 若 _errors 非空：raise ExceptionGroup(...)
  5. 若 _base_error：raise _base_error
```

---

## 十六、超时（timeouts.py）

### C110 — Timeout

| 字段 | 内容 |
|------|------|
| **定义** | Asynchronous context manager for cancelling overdue coroutines. |
| **关键属性** | `_state` (`CREATED`/`ENTERED`/`EXPIRING`/`EXPIRED`/`EXITED`), `_timeout_handler` (**C02** TimerHandle|None), `_task` (**C17** Task), `_when` (float, absolute deadline) |
| **关键方法** | `__aenter__()`, `__aexit__(et, exc, tb)`, `update(new_when)`, `reschedule(new_when)` |
| **关键行为** | 过期时调用 `task.cancel()`，捕获 `CancelledError`，通过 `uncancel()` 机制转换为 `TimeoutError` |
| **源码位置** | `timeouts.py:~15` |
| **关联概念** | 使用 **C17**(Task.cancel/uncancel) 和 **C02**(TimerHandle)；**C130**(CancelledError) → **C132**(TimeoutError) 转换 |

#### C110.1 — Timeout 状态转换

```
CREATED → ENTERED:  __aenter__()
ENTERED → EXPIRING: 定时器到期, task.cancel() 被调用
ENTERED → EXITED:   __aexit__() 在超时前
EXPIRING → EXPIRED: task.__step 中 CancelledError 被捕获
EXPIRING → EXITED:  __aexit__() 处理超时（CancelledError → TimeoutError）

在任何状态下调用 update()/reschedule() 可修改 deadline
```

### C111 — timeout(delay) / timeout_at(when)

| 字段 | 内容 |
|------|------|
| **定义** | `timeout(delay)`: Create a Timeout object that expires after delay seconds. `timeout_at(when)`: Create a Timeout object that expires at an absolute time. |
| **源码位置** | `timeouts.py:~200` / `timeouts.py:~220` |
| **关联概念** | 工厂函数，返回 **C110**(Timeout) 实例 |

---

## 十七、SSL 协议（sslproto.py）

### C120 — SSLProtocol

| 字段 | 内容 |
|------|------|
| **定义** | Full SSL/TLS state machine implementing BufferedProtocol. |
| **状态机** | `_state`: `UNWRAPPED` → `DO_HANDSHAKE` → `WRAPPED` → `FLUSHING` → `SHUTDOWN` |
| **关键属性** | `_state`, `_app_state`, `_incoming` (MemoryBIO, encrypted→decrypted), `_outgoing` (MemoryBIO, decrypted→encrypted), `_sslobj` (ssl.SSLObject), `_transport` (**C48** Transport), `_app_protocol` (**C41** Protocol), `_sslcontext` (ssl.SSLContext), `_need_ssldata` (bool), `_app_reading` (bool) |
| **源码位置** | `sslproto.py:~50` |
| **关联概念** | 实现 **C42**(BufferedProtocol) 接口；在 Transport 和 app Protocol 之间做加/解密桥梁 |

#### C120.1 — SSLProtocol 数据流

```
读取方向:
  Transport → _process_incoming_ssldata() → _incoming.write(encrypted)
  → _sslobj.read() → decrypt → _app_protocol.data_received(plaintext)

写入方向:
  _app_protocol → SSLProtocol._write_appdata(plaintext)
  → _sslobj.write(plaintext) → encrypt → _outgoing.read() → _transport.write(encrypted)
```

### C121 — _SSLProtocolTransport

| 字段 | 内容 |
|------|------|
| **定义** | Transport wrapper that delegates all operations to SSLProtocol. |
| **关键方法** | `write()` → `_ssl_protocol._write_appdata()`, `close()` → `_ssl_protocol._start_shutdown()`, `pause_reading()`, `resume_reading()` |
| **源码位置** | `sslproto.py:~30` |
| **关联概念** | 对外呈现为普通 Transport，内部委托 **C120**(SSLProtocol) |

---

## 十八、异常（exceptions.py）

### C130 — CancelledError

| 字段 | 内容 |
|------|------|
| **定义** | The Future or Task was cancelled. Subclass of BaseException (not Exception) since Python 3.9. |
| **源码位置** | `exceptions.py:~10` |
| **关联概念** | Task `__step` 中特殊处理；**C110**(Timeout) 将其转换为 TimeoutError |

### C131 — InvalidStateError

| 字段 | 内容 |
|------|------|
| **定义** | Operation is not allowed in the current state. Raised by Future.set_result/set_exception when state is not PENDING. |
| **源码位置** | `exceptions.py:~20` |
| **关联概念** | 与 **C15**(Future) 状态机联动 |

### C132 — TimeoutError

| 字段 | 内容 |
|------|------|
| **定义** | Operation has timed out. (Reuses built-in TimeoutError) |
| **源码位置** | `exceptions.py:~25` |
| **关联概念** | 由 **C21**(`wait_for`) 和 **C110**(Timeout) 抛出 |

### C133 — IncompleteReadError

| 字段 | 内容 |
|------|------|
| **定义** | Incomplete read error. Attributes: `partial` (bytes read before EOF), `expected` (expected bytes or None). |
| **源码位置** | `exceptions.py:~30` |
| **关联概念** | 由 **C80**(StreamReader) 的 `readexactly()` 抛出 |

### C134 — LimitOverrunError

| 字段 | 内容 |
|------|------|
| **定义** | Buffer size exceeded during search for separator. Attributes: `consumed` (total bytes consumed), `separator`. |
| **源码位置** | `exceptions.py:~45` |
| **关联概念** | 由 **C80**(StreamReader) 的 `readuntil()` 抛出 |

### C135 — BrokenBarrierError

| 字段 | 内容 |
|------|------|
| **定义** | Barrier is broken by one of the waiting tasks. |
| **源码位置** | `exceptions.py:~55` |
| **关联概念** | 由 **C65**(Barrier) 抛出 |

### C136 — SendfileNotAvailableError

| 字段 | 内容 |
|------|------|
| **定义** | 'sendfile' syscall is not available. Raised when loop.sendfile() is called on a platform that does not support it. |
| **源码位置** | `exceptions.py:~65` |
| **关联概念** | 由 `loop.sendfile()` 抛出 |

---

## 十九、子进程（base_subprocess.py / subprocess.py）

### C140 — SubprocessTransport（实现类）

| 字段 | 内容 |
|------|------|
| **定义** | Subprocess transport implementation (not the ABC in transports.py). |
| **关键属性** | `_protocol` (**C44** SubprocessProtocol), `_loop`, `_pipes` (dict of fd→Transport), `_pending_calls`, `_returncode`, `_proc` (subprocess.Popen) |
| **关键方法** | `close()`, `_try_finish()`, `_process_exited()` |
| **源码位置** | `base_subprocess.py:~15` |
| **关联概念** | 实现 **C50**(SubprocessTransport 接口) |

### C141 — create_subprocess_exec / create_subprocess_shell

| 字段 | 内容 |
|------|------|
| **定义** | Create a subprocess. `create_subprocess_exec`: direct exec. `create_subprocess_shell`: via shell. |
| **源码位置** | `subprocess.py:~50` |
| **关联概念** | 返回 `Process` 对象（非 Transport），提供 `stdin/stdout/stderr` 的 StreamWriter/StreamReader |

---

## 二十、全局索引

### 按类别汇总

| 类别 | 概念编号 |
|------|----------|
| 事件循环接口与策略 | C01, C02, C03, C04, C05, C06, C07a, C07b, C07c |
| 事件循环实现 | C08, C09, C10, C11, C12, C13, C14 |
| Future | C15, C16 |
| Task | C17, C18, C19, C20, C21, C22, C23, C24, C25, C26 |
| 协程工具 | C27, C28, C29 |
| Selector 循环与传输 | C30, C31, C32 |
| Proactor 循环与传输 | C33, C34, C35 |
| 协议 | C40, C41, C42, C43, C44 |
| 传输 | C45, C46, C47, C48, C49, C50, C51 |
| 同步原语 | C60, C61, C62, C63, C64, C65 |
| 队列 | C70, C71, C72 |
| 流 | C80, C81, C82, C83, C84 |
| 运行器 | C90, C91 |
| 任务组 | C100 |
| 超时 | C110, C111 |
| SSL | C120, C121 |
| 异常 | C130, C131, C132, C133, C134, C135, C136 |
| 子进程 | C140, C141 |

### 核心依赖链

```
run() → Runner(C90) → loop(C08) → _run_once() → _ready(C01 Handle) / _scheduled(C02 TimerHandle)
       ↓
create_task() → Task(C17) → __step() → coro.send() → await → Future(C15) → add_done_callback → __wakeup()
       ↓
Protocol(C41) ← Transport(C48) → I/O → Selector(C30) / Proactor(C33)
       ↓
同步原语(C60-C65) / 队列(C70) / 流(C80-C84) — 均基于 Future + loop.call_soon 构建
```

### 概念间核心关系矩阵

| 源概念 | 关系类型 | 目标概念 |
|--------|----------|----------|
| C02-TimerHandle | inherits | C01-Handle |
| C08-BaseEventLoop | implements | C03-AbstractEventLoop |
| C30-BaseSelectorEventLoop | extends | C08-BaseEventLoop |
| C33-BaseProactorEventLoop | extends | C08-BaseEventLoop |
| C17-Task | extends | C15-Future |
| C48-Transport | multi-inherits | C46-ReadTransport + C47-WriteTransport |
| C64-BoundedSemaphore | extends | C63-Semaphore |
| C41-Protocol | extends | C40-BaseProtocol |
| C42-BufferedProtocol | extends | C40-BaseProtocol |
| C43-DatagramProtocol | extends | C40-BaseProtocol |
| C44-SubprocessProtocol | extends | C40-BaseProtocol |
| C31-_SelectorSocketTransport | mixes-in | C51-_FlowControlMixin |
| C82-StreamReaderProtocol | extends | C41-Protocol |
| C120-SSLProtocol | implements | C42-BufferedProtocol |
| C100-TaskGroup.create_task | delegates-to | C18-create_task |
| C110-Timeout | uses | C17-Task.cancel/uncancel |
| C110-Timeout | uses | C02-TimerHandle |

---

> **提取完成**。本清单覆盖 asyncio 核心源码中所有公开与关键内部概念，共计 48 个顶层概念 + 若干子概念。
> 后续步骤（语义建模、关系图、代码生成）均以本清单为唯一输入源。
