# 请求-响应完整生命周期

> 从Micro视角追踪一个HTTP请求如何穿透AI基础设施各层，与Macro视角的基础设施生命周期对照

---

## 主线脉络（鸟瞰）

![请求-响应主线脉络](./RR-Overview.svg)

**请求流**：H4(我有个问题) → H3(请进分发 → 验身指路 → 持证穿越) → H2(化问为答) → H1(算力就位)

**响应流**：H1 → H2 → H3 → H4（Token流逐层返回）

---

## 视角区分

| 视角 | 文档 | 关注点 | 时间尺度 |
|:----|:----|:----|:----|
| **Macro** | AI Infrastructure Graph.md | 基础设施建设：规划→部署→运维→演进 | 月~年 |
| **Micro** | 本文档 | 单次请求：发起→路由→推理→响应 | 毫秒~秒 |

**映射关系**：Macro定义的H1-H4架构分层，是Micro请求流经的载体；模型/数据为横切资源

---

## 架构分层实现映射

| 架构层 | Graph.md定义 | Manual.md中的具体实现组件 |
|:----|:----|:----|
| **H4 顶层应用** | 业务功能封装、用户交互 | 客户端应用（SDK/业务系统），发起HTTP请求至VIP入口 |
| **H3 平台与调度** | 请求路由、负载均衡、资源编排、监控 | K8s集群 + HAProxy + Keepalived + LiteLLM网关（路由调度） + Prometheus |
| **H2 推理服务** | 模型加载、推理执行、API服务 | vLLM推理引擎（多地域GPU服务器上直接运行） |
| **H1 硬件** | GPU/NPU、存储、网络 | ARM服务器双节点（16 CPU/64Gi）+ GPU集群（多地域A2/A3/V100/G5500） |
| _横切资源_ | _模型/数据（非独立架构层）_ | _模型权重文件（GLM-V5.1/Qwen3等），被H2加载、H1承载_ |

> **H2与H3的划分依据**：vLLM引擎直接在GPU上执行推理（H2），LiteLLM网关+K8s+HAProxy负责路由调度（H3）。请求流：H4→H3调度→H2推理→H1算力。

---

## 场景设定

**示例请求**：
```http
POST http://***:***/v1/chat/completions
Headers:
  Authorization: Bearer ***
  Content-Type: application/json
Body:
{
  "model": "GLM-V5.1",
  "messages": [{"role": "user", "content": "解释量子纠缠"}],
  "stream": true
}
```

**选型**：请求指定模型 `GLM-V5.1`，LiteLLM根据路由配置选择后端

---

## 初始快照 — 待命

![初始快照](./RR-S00-Initial.svg)

**系统稳态基准线（请求到来前）**：
- **H4**：用户界面空白，等待输入
- **H3**：HAProxy监听VIP:32400 (连接数:0)、LiteLLM Pod空闲 (路由表已加载)、header_proxy监听933x端口 (无活跃转发)
- **H2**：vLLM引擎模型权重已加载GPU显存，空闲等待请求
- **H1**：GPU集群就绪，显存已占用（模型权重），计算单元空闲，KV Cache: 0%
- **横切资源**：GLM-V5.1权重常驻GPU显存，不随请求装卸

**路由表已就绪（GLM-V5.1）**：HIS AITeam(w:26)、上海绿区A3(w:50)、西安绿区A3(w:20)、苏州A2(w:20) — 全部healthy，max_parallel_requests未达上限

---

## 快照1 — 我有个问题

![快照1](./RR-S01-Client.svg)

| 维度 | 状态 |
|:----|:----|
| **层级** | H4 顶层应用 |
| **组件** | 客户端应用 |
| **初始状态** | 输入框空白，等待用户 |
| **触发操作** | 用户输入"解释量子纠缠" |
| **变化结果** | 输入框填充，生成按钮点亮 |
| **耗时** | ~1ms（构造+发送） |
| **核心职责** | 用户意图的入口 |

---

## 快照2 — 请进分发

![快照2](./RR-S02-HAProxy.svg)

| 维度 | 状态 |
|:----|:----|
| **层级** | H3 平台与调度 |
| **组件** | Keepalived VIP（***） + HAProxy |
| **初始状态** | VIP监听:32400，连接数:0 |
| **触发操作** | 请求到达VIP，HAProxy根据`leastconn`策略选择后端 |
| **变化结果** | 请求分发至node-0或node-1的NodePort 31937 |
| **耗时** | ~0.5ms（HAProxy代理） |
| **核心职责** | 请求入口与负载均衡 |

**HAProxy配置**：
```
frontend litellm
  bind ***:32400
  mode tcp
  default_backend litellm_nodes

backend litellm_nodes
  mode tcp
  balance leastconn
  option httpchk GET /health/readiness
  server node0 ***:31937 check
  server node1 ***:31937 check
```

---

## 快照3 — 转发到位

![快照3](./RR-S03-K8s.svg)

| 维度 | 状态 |
|:----|:----|
| **层级** | H3 平台与调度 |
| **组件** | K8s Service (NodePort 31937) + kube-proxy |
| **初始状态** | 请求到达NodePort 31937 |
| **触发操作** | kube-proxy通过iptables/IPVS转发至LiteLLM Pod |
| **变化结果** | 请求到达LiteLLM Pod（node-0或node-1） |
| **耗时** | ~0.5ms（iptables转发） |
| **核心职责** | K8s Service路由 |

**K8s资源**：
```
Service: litellm-litellm-stack-litellm
  Type: NodePort
  NodePort: 31937
  ClusterIP: <cluster-ip>
  Selector: app.kubernetes.io/component=litellm
```

---

## 快照4 — 验身指路

![快照4](./RR-S04-LiteLLM.svg)

| 维度 | 状态 |
|:----|:----|
| **层级** | H3 平台与调度 |
| **组件** | LiteLLM Pod（容器内Python进程） |
| **初始状态** | HTTP Request到达Pod 4000端口 |
| **操作① 验身** | 鉴权：验证 `Authorization: Bearer ***` 是否匹配Master Key → 通过 |
| **操作② 查路由表** | 解析Body，提取model="GLM-V5.1" → 找到4个候选后端 |
| **操作③ 决策** | simple-shuffle(weight) → 选中：上海绿区A3 (w:50) |
| **变化结果** | 选定后端：api_base :9333/v1 |
| **耗时** | ~5ms（鉴权+路由决策） |
| **核心职责** | 鉴权准入 → 路由查询 → 后端决策 |

**并发控制**：max_parallel_requests = 50 (当前后端)，当前并发: 12/50 → 未达上限，允许转发

**路由表（GLM-V5.1）**：
| 后端ID | api_base | weight | max_parallel_requests | 说明 |
|:----|:----|:----|:----|:----|
| prod-aiteam-glm5.1 | http://***.../v1 | 26 | 26 | HIS AITeam（主） |
| green-shanghai-A3-glm5.1 | http://***:9333/v1 | 50 | 50 | 上海绿区A3 ← 选中 |
| green-xian-A3-glm5.1 | http://***:9334/v1 | 20 | 30 | 西安绿区A3 |
| green-suzhou-A2-111-glm5.1 | http://***:9335/v1 | 20 | 30 | 苏州绿区A2 |

---

## 快照5 — 持证穿越

![快照5](./RR-S05-Network.svg)

| 维度 | 状态 |
|:----|:----|
| **层级** | H3 平台与调度（网络层） |
| **当前场景** | 场景B：上海绿区A3（header_proxy:9333） |
| **操作①** | header_proxy拦截请求 |
| **操作②** | 注入静态API Key：`***` |
| **操作③** | 设置环境变量`HTTP_PROXY=***:3128`（华为网关） |
| **操作④** | 穿越网络隔离，到达vLLM服务器：`***:8000` |
| **变化结果** | 请求到达上海绿区A3 vLLM实例（H2推理服务） |
| **耗时** | ~20ms（header_proxy + 网关代理 + RTT） |
| **核心职责** | 注入认证凭证 → 穿越网络隔离 → 到达推理引擎 |

**三种网络场景对比**：
| 场景 | 后端 | header_proxy端口 | 认证方式 | 网络 | 耗时 |
|:----|:----|:----|:----|:----|:----|
| A | HIS AITeam | 9332 | OAuth2动态Token | 直连 | ~10ms |
| **B** | **上海绿区A3** | **9333** | **静态API Key** | **HTTP_PROXY网关** | **~20ms** |
| C | 内网Pod | — | DUMMY_API_KEY | Pod内网直连 | ~5ms |

---

## 快照6 — 化问为答

![快照6](./RR-S06-vLLM.svg)

| 维度 | 状态 |
|:----|:----|
| **层级** | H2 推理服务（运行在H1硬件上） |
| **组件** | vLLM进程 + GPU（A3） |
| **横切资源** | 模型权重GLM-V5.1（已加载在GPU显存中） |
| **输入** | prompt："解释量子纠缠" |
| **操作①** | vLLM解析请求，验证模型已加载 |
| **操作②** | 启动流式推理引擎（stream=true） |
| **操作③** | 执行前向计算，逐Token生成 |
| **操作④** | 每生成一个Token立即flush SSE事件 |
| **输出** | SSE流：`data: {"choices":[{"delta":{"content":"量"}}]} ...` → "量" "子" "纠" "缠" ... |
| **耗时** | 首Token耗时：TTFT ~100-300ms；后续Token：~20-50ms/token |
| **核心职责** | 问题输入 → GPU推理 → 答案输出 |

**GPU状态**：计算单元执行推理 · 显存占用：模型权重 + KV Cache (增长中) · 利用率: 80%

**vLLM核心指标**：
- `vllm:num_requests_running`：当前运行请求数
- `vllm:time_to_first_token_seconds`：首Token延迟
- `vllm:generation_time_seconds`：总生成时间
- `vllm:kv_cache_usage_ratio`：KV Cache使用率

---

## 快照7 — 逐字回流

![快照7](./RR-S07-Response.svg)

| 维度 | 状态 |
|:----|:----|
| **层级** | H1 → H2 → H3 → H4（逐层返回） |
| **数据流** | SSE Stream逐Token向上传递 |
| **操作①** | vLLM生成Token → flush SSE |
| **操作②** | 经header_proxy透传（计数器+1） |
| **操作③** | 到达LiteLLM → 透传至客户端（LiteLLM不缓冲stream，记录延迟、Token数） |
| **操作④** | 经HAProxy → 到达客户端 |
| **输出** | 用户界面逐字显示答案："量" "子" "纠" "缠" ... |
| **耗时** | 每Token RTT：~1-5ms（网络） |
| **核心职责** | Token沿H1→H2→H3→H4逆向逐层返回 |

---

## 最终快照 — 归位留痕

![最终快照](./RR-S08-Final.svg)

**稳态回归 + 增量变化（对比初始快照）**：

| 组件 | 初始状态 | 最终状态 | 变化？ |
|:----|:----|:----|:----|
| **用户界面(H4)** | 输入框空白，响应区空 | 输入框"解释量子纠缠"，答案已展示 | **变了** |
| **HAProxy(H3)** | 监听:32400，连接数:0 | 监听:32400，连接数:0 | 不变 |
| **LiteLLM Pod(H3)** | 空闲，路由表就绪 | 空闲，**已记录指标** | **变了** |
| **header_proxy(H3)** | 监听933x，无活跃转发 | 监听933x，无活跃转发 | 不变 |
| **vLLM引擎(H2)** | 模型已加载GPU，空闲 | 模型仍在GPU，KV Cache已释放，空闲 | 不变（模型不装卸） |
| **模型权重(横切)** | 常驻GPU显存 | 仍在GPU显存 | 不变 |
| **GPU(H1)** | 就绪，显存已占用，计算单元空闲 | 就绪，显存已占用，计算单元空闲 | 不变 |

**指标增量（请求留下的痕迹）**：
- `litellm_requests_total` +1
- `duration`: ~500ms
- `tokens`: 10 (prompt+completion)
- PostgreSQL日志 +1
- Prometheus下次scrape可见 · Grafana仪表盘更新

**核心观察**：
- **不变的** = 基础设施的稳定性（模型权重不随请求装卸、路由表不因单次请求改变）
- **变化的** = 请求的痕迹（可观测性的来源：指标、日志、用户界面状态）

---

## 快照8：监控数据采集（异步）

| 维度 | 状态 |
|:----|:----|
| **层级** | H3 平台与调度 |
| **组件** | LiteLLM /metrics + Prometheus + Grafana |
| **触发** | Prometheus每15s scrape LiteLLM Pod的`/metrics/`端点 |
| **操作①** | LiteLLM暴露指标：`litellm_requests_total`, `litellm_request_duration_seconds` |
| **操作②** | Prometheus拉取并存储时序数据 |
| **操作③** | 若触发告警规则（如后端unhealthy），记录Alert |
| **输出** | 指标写入Prometheus TSDB，告警规则评估 |
| **耗时** | scrape耗时~10-50ms |

**Prometheus监控目标**：
- LiteLLM Pod（`/metrics/`）
- vLLM实例（经header_proxy端口：9333/9334/9335/9340/9341 或直连）

**告警规则**：
- `VllmScrapeTargetDown`：vLLM不可达持续2m → critical
- `LiteLLMDeploymentUnhealthy`：路由后端unhealthy持续3m → warning

---

## 完整时间线

```
T+0ms     客户端发起请求（H4） — 我有个问题
T+1ms     VIP + HAProxy负载均衡（H3） — 请进分发
T+1.5ms   K8s Service转发至Pod（H3） — 转发到位
T+2ms     LiteLLM收到请求，开始鉴权（H3） — 验身指路(验身)
T+7ms     LiteLLM路由决策完成，选择后端（H3） — 验身指路(指路)
T+17ms    header_proxy转发至vLLM（H3→H2） — 持证穿越
T+117ms   vLLM首Token生成完成（H2 on H1） — 化问为答（TTFT~100ms）
T+117-120ms 首Token逐层返回至客户端（H2→H3→H4） — 逐字回流
T+120-500ms  后续Token流式生成与返回（~20-50ms/token）
T+500ms   客户端收到完整响应（假设输出10 tokens） — 归位留痕
T+515s    Prometheus周期性scrape指标（L3监控） — 异步采集
```

**总耗时**：~500ms（首Token+生成时间+网络），不含排队时间

---

## 生命周期映射

| 请求阶段 | 架构层 | 核心标签 | 对应Macro生命周期阶段 |
|:----|:----|:----|:----|
| 初始状态 | 全系统 | **待命** | L3 运行与观测（稳态基准线） |
| 发起请求 | H4 顶层应用 | **我有个问题** | L3 运行与观测（业务运行） |
| 负载均衡 | H3 平台与调度 | **请进分发** | L3 运行与观测（服务稳定） |
| K8s转发 | H3 平台与调度 | **转发到位** | L3 运行与观测（服务稳定） |
| 鉴权路由 | H3 平台与调度 | **验身指路** | L3 运行与观测（服务稳定） |
| 网络穿越 | H3 平台与调度 | **持证穿越** | L2 部署与搭建（网络配置） + L3运行与观测 |
| 推理执行 | H2 推理服务 | **化问为答** | L3 运行与观测（推理服务） |
| 响应返回 | 全程 | **逐字回流** | L3 运行与观测（服务稳定） |
| 最终状态 | 全系统 | **归位留痕** | L3 运行与观测（稳态回归+增量变化） |
| 模型加载 | _横切资源_ | — | L2 部署与搭建（模型落位） + L4优化与演进（版本迭代） |
| 指标采集 | H3 平台与调度 | — | L3 运行与观测（采集指标） |

**核心观察**：
- **单次请求**主要运行在 **L3 运行与观测** 阶段（稳态运行）
- H3调度层承载了请求流中大部分转发/路由/监控职责
- H2推理层专注GPU推理执行，直接依赖H1算力
- **部署配置**（header_proxy端口、路由表）在 **L2 部署与搭建** 阶段固化
- **性能优化**（weight、并发、模型迭代）属于 **L4 优化与演进**
- **模型/数据**作为横切资源，在L2(加载)和L4(迭代)被H2推理服务消费

---

## 关键组件状态快照对比

| 组件 | 所属层 | 请求前状态 | 请求中状态 | 请求后状态 |
|:----|:----|:----|:----|:----|
| **HAProxy** | H3 | 监听VIP:32400 | 转发请求 | 回到监听态 |
| **LiteLLM Pod** | H3 | 空闲 | 并发+1，路由决策 | 并发-1，指标更新 |
| **LiteLLM路由表** | H3 | ConfigMap+DB路由 | 读取路由 | 保持不变 |
| **Redis** | H3 | RPM/TPM计数 | 更新计数 | 持久化 |
| **header_proxy** | H3 | 监听933x端口 | 注入Header，转发 | 回到监听态 |
| **vLLM** | H2 | 模型已加载GPU | GPU推理中，KV Cache增长 | KV Cache释放 |
| **模型权重** | _横切_ | 常驻GPU显存 | 被推理引擎读取 | 保持在显存 |
| **Prometheus** | H3 | 定期scrape | 无交互（异步） | 下次scrape获取新指标 |
| **PostgreSQL** | H3 | 存储日志 | 写入请求日志 | 日志持久化 |

---

## 异常路径快照

### 异常1：后端不可达（vLLM宕机）

| 快照点 | 状态变化 |
|:----|:----|
| LiteLLM路由(H3) | 选中后端A3，发起请求 |
| header_proxy(H3) | 连接超时/拒绝（后端vLLM宕机） |
| LiteLLM容错(H3) | 根据num_retries=3重试，切换其他GLM-V5.1后端（如西安A3） |
| 最终结果 | 请求成功（降级到其他后端）或全部失败返回错误 |

**对应告警**：`VllmScrapeTargetDown`触发 → Prometheus记录 → Grafana显示

---

### 异常2：并发超限（max_parallel_requests耗尽）

| 快照点 | 状态变化 |
|:----|:----|
| LiteLLM路由(H3) | 检查后端并发计数，已达max_parallel_requests上限 |
| 拒绝策略 | 返回HTTP 429 Too Many Requests 或排队等待 |
| 客户端(H4) | 需重试或降级到其他模型 |

**注意**：max_parallel_requests是**密钥级**限制（asyncio Semaphore），不跨Pod共享，双Pod实际总并发=单Pod配置×2

---

### 异常3：OAuth2 Token过期（HIS AITeam）

| 快照点 | 状态变化 |
|:----|:----|
| header_proxy 9332(H3) | 向HIS AITeam发请求，返回401 Unauthorized |
| Token刷新 | header_proxy检测Token过期，触发OAuth2刷新流程 |
| 重试 | 使用新Token重新发起请求 |
| 最终结果 | 请求成功（自动刷新） |

**Token刷新策略**：每1500s自动刷新，提前于过期时间

---

## 运维操作视角

| 操作 | 触发时机 | 影响的快照点 | 影响范围 |
|:----|:----|:----|:----|
| **调整路由weight** | L4优化与演进 | 快照4路由选择概率 | 后续请求 |
| **修改max_parallel_requests** | L4优化与演进 | 快照4并发限制 | 后续请求 |
| **新增vLLM后端** | L2部署与搭建 | 快照4路由表 | 后续请求 |
| **header_proxy配置变更** | L2部署与搭建 | 快照5网络路径 | 后续请求 |
| **模型版本更新/量化** | L4优化与演进 | 快照6模型权重 | 后续请求推理结果 |
| **LiteLLM Pod滚动重启** | L3运行与观测 | 短暂不可用（maxUnavailable=0） | 重启期间分发到其他Pod |
| **Prometheus热重载配置** | L3运行与观测 | 快照8监控目标 | 异步采集 |

---

## 总结

**从请求到响应的生命周期**是架构分层（H1-H4）上的数据流：

1. **H4**：业务发起请求（我有个问题）
2. **H3**：调度层负载均衡（请进分发）+鉴权路由（验身指路）+网络穿越（持证穿越）
3. **H2**：推理层GPU执行（化问为答）——消费横切资源：模型权重
4. **H1**：硬件层提供算力
5. **H2→H3→H4**：响应逐层返回（逐字回流）
6. **H3**：指标采集+告警（异步）

**初始快照 vs 最终快照**：
- **初始**：系统稳态基准线（模型常驻GPU、路由表就绪、组件监听）—— 一切就绪，只差一个请求
- **最终**：稳态回归 + 增量变化（模型仍在GPU、路由表不变 —— 但指标+1、日志多一条、用户看到了答案）
- **对比之下，直观学到**：不变的=基础设施稳定性；变化的=请求痕迹（可观测性来源）

**与Macro生命周期的关系**：
- 请求生命周期运行在 **L3运行与观测** 的稳态阶段
- H3调度层承载请求转发、路由决策、监控采集；H2推理层专注GPU推理
- 配置（路由、代理、模型加载）来自 **L2部署与搭建** 的固化工件
- 调优（weight、并发、模型迭代）驱动 **L4优化与演进**
- **模型/数据**作为横切资源贯穿L2(加载)和L4(迭代)，被H2推理服务消费

**Observability**：每层的关键状态变化均通过Prometheus指标、日志、告警可观测
