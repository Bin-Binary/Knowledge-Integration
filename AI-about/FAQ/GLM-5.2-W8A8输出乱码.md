## 部署信息
> 8 台机器每台 8 张 64G NPU A2 卡，采用4P4D分离部署，P节点 4DP 8TP，1个容器1个节点1个实例，D节点 8DP 4TP，1个容器1个节点2个实例
>
> 注：经核查 `glm52_pd_oneclick.sh` 启动脚本，实际为 **4P8D** 部署（4个Prefill节点 + 4个Decode节点，每D节点2实例=8个Decode实例），与文档原描述的 4P4D 不符。

| 节点类型 | 节点数量 | 显卡类型 | 显卡数量 | DP | TP | 实例数 |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Prefill | 4 | NPU A2 64G | 4*8 | 4 | 8 | 1节点1实例 |
| Decode | 4 | NPU A2 64G | 4*8 | 8 | 4 | 1节点2实例 |

### 节点 IP 清单
| 角色 | 节点 | IP | 容器名 |
| :---- | :---- | :---- | :---- |
| Prefill | P0 (master) | 85.25.15.101 | glm-5.2-sky-pr45915 |
| Prefill | P1 | 85.25.20.101 | glm-5.2-sky-pr45915 |
| Prefill | P2 | 85.25.20.103 | glm-5.2-sky-pr45915 |
| Prefill | P3 | 85.25.20.107 | glm-5.2-sky-pr45915 |
| Decode | D0 (master) | 85.25.9.4 | glm-5.2-sky-pr45915 |
| Decode | D1 | 85.25.9.2 | glm-5.2-sky-pr45915 |
| Decode | D2 | 85.25.1.5 | glm-5.2-sky-pr45915 |
| Decode | D3 | 85.25.0.110 | glm-5.2-sky-pr45915 |

### 路由层
- 非标准 LiteLLM，实际为 vllm-ascend 提供的示例负载均衡代理：`/vllm-workspace/vllm-ascend/examples/disaggregated_prefill_v1/load_balance_proxy_server_example.py`
- 监听端口：13400，运行于 P0 节点宿主机（pid 935801）
- 路由逻辑：请求先发往 Prefiller 做 prefill（max_tokens=1），获取 `kv_transfer_params` 后再选 Decoder 做 decode 并流式返回
- 负载均衡：基于 `active_tokens + active_kv_cache*0.3`（P）和 `active_tokens`（D）的最小堆轮询
- 日志路径：`/home/gandalf/images/glm5.2-8pd-logs/proxy-*.log`（proxy 日志仅记录 HTTP 状态码，无业务错误）

## 现象

### 故障请求样本
- 请求 ID：`chatcmpl-fd88bcfb-372b-4a46-9545-c19af485655f`
- 发生时间：2026-08-06 10:11:45 ~ 10:13:31（耗时 105.984s，TTFT 103.585s）
- Prompt tokens：52,689，Completion tokens：85
- 模型输出大量乱码（多语言混杂、无意义token拼接），例如：
  ```
  syscall1, allowing6. ... Null Point1 Sampling Resources2! ... Shemale Review5 Personal C游 Byoo Lazy ...
  ```

### 关键现象
1. **同一会话多次请求中，部分请求输出正常中文（如"您好，我无法理解您的请求"），部分请求输出乱码** —— 表明问题非模型权重/量化本身的静态错误，而是运行时偶发
2. **TTFT 异常高（103.585s）** —— 正常 PD 分离部署 TTFT 应在秒级，此处近 2 分钟，提示 prefill→decode 阶段存在严重阻塞
3. **proxy 日志全为 200 OK** —— HTTP 层无错误，问题隐藏在后端 vLLM 引擎层
4. **乱码内容含多语言碎片、专有名词、代码符号** —— 典型的 KV Cache 未对齐导致的 attention 错位特征（query 与错误的 key/value 做注意力计算）

## 关键日志信息

### 1. Mooncake KV 传输大面积失败（根因证据）

日志文件：`vllm-glm5.2-8pd-d0-rank0-85.25.9.4-20260806_095730.log`（D0 节点，rank0）

请求 `chatcmpl-fd88bcfb` 发生前后的 10:06 ~ 10:13 时段，D0 节点 4 个 TP worker（TP0~TP3）持续报错：

```
E0806 10:11:18.470886 10729 ascend_direct_transport.cpp:831] Transfer timeout to: 85.25.20.101:20296, ...
I0806 10:11:18.470988 10729 ascend_direct_transport.cpp:843] transfer failed and disconnect to:85.25.20.101:20296
(Worker_DP0_TP3_EP3 pid=1057) ERROR 08-06 10:11:18 [mooncake_connector.py:774] Mooncake transfer failed for request. remote_request_id=chatcmpl-d1fbbd73-...-b935cdf9, ret=-1.
(Worker_DP0_TP3_EP3 pid=1057) ERROR 08-06 10:11:18 [mooncake_connector.py:558] Error in KVCacheTransferThread. error=unhashable type: 'list'.
```

错误特征：
- **Transfer timeout**：到 P1(85.25.20.101)、P2(85.25.20.103)、P3(85.25.20.107) 的 ascend_direct 传输超时
- **Mooncake transfer failed ... ret=-1**：KV 传输失败，D 节点拿不到 P 节点计算的 KV Cache
- **Error in KVCacheTransferThread. error=unhashable type: 'list'**：KV 传输线程异常，疑似 Mooncake Connector 在处理某数据结构时将 list 用作 dict key
- 同一请求的 4 个 TP worker 全部失败，偶有部分 worker 成功（`KV cache transfer for request ... took 176.49 ms`）—— **TP 维度 KV 部分缺失**

### 2. 投机解码完全失效（放大效应证据）

D 节点日志 `SpecDecoding metrics` 显示投机解码接受率近乎为 0：

```
(APIServer pid=271) INFO 08-06 11:39:25 [metrics.py:101] SpecDecoding metrics: Mean acceptance length: 1.00, Accepted throughput: 0.00 tokens/s, Drafted throughput: 40.20 tokens/s, Accepted: 0 tokens, Drafted: 402 tokens, Per-position acceptance rate: 0.000, 0.000, 0.000, Avg Draft acceptance rate: 0.0%
```

- `Avg Draft acceptance rate: 0.0%`（正常应 >50%）
- `Per-position acceptance rate: 0.000, 0.000, 0.000`（3 个猜测位置全拒）
- `External prefix cache hit rate: 100.0%`（KV 全部"命中"外部缓存——实为 PD 传输过来的 KV，但其中部分为错误/缺失数据）

启动时相关 WARNING：
```
(APIServer pid=271) WARNING 08-06 09:57:49 [speculative.py:668] Enabling num_speculative_tokens > 1 will run multiple times of forward on same MTP layer,which may result in lower acceptance rate
```

### 3. P 节点侧表现

P0 日志 `vllm-glm5.2-8pd-p0-rank0-85.25.15.101-20260806_095703.log`：
- prefill 请求均返回 200 OK
- `Avg generation throughput: 0.1 tokens/s` —— 符合 P 节点只做 prefill（max_tokens=1）的预期
- 仅有 `Delaying free of 1 blocks for request ...` 的 Mooncake 延迟释放日志，无 ERROR
- **P 侧无错误，KV 传输失败发生在 D 侧接收端**

### 4. 其他相关 WARNING
- `mlapo only supports W8A8 quantization in SFA scenario on non-A5 devices. Some layers in your model are not quantized with W8A8, thus mlapo is disabled for these layers.` —— MLAPO 部分层禁用，非乱码主因
- `min_p and logit_bias parameters won't work with speculative decoding.` —— 采样参数与投机解码冲突，可能影响采样质量
- `Default vLLM sampling parameters have been overridden by the model's generation_config.json: {'temperature': 1.0, 'top_p': 0.95}` —— 温度 1.0 较高，在 KV 错位时会放大乱码概率

## 初步结论（未验证）

### 根因判断
**D 节点 Mooncake KV 传输大面积超时失败，导致 Decode 阶段使用错误/缺失的 KV Cache 进行注意力计算，是输出乱码的直接根因。**

### 因果链
1. Prefill 节点正常计算 KV 并通过 Mooncake/ascend_direct 发送
2. Decode 节点接收时，到 P1/P2/P3 的 ascend_direct 传输超时（`Transfer timeout`），`ret=-1`，KV 未到达
3. `Error in KVCacheTransferThread. error=unhashable type: 'list'` 表明 Mooncake Connector 的 KV 传输线程存在 bug（list 被用作 hash key），进一步导致传输线程异常
4. D 节点在 KV 缺失/部分 TP 缺失的情况下仍继续 decode（`kv_load_failure_policy='fail'` 理论上应失败，但实际因线程异常未被正确捕获）
5. 错误的 KV 导致 attention 计算错位，logits 分布异常
6. 投机解码 MTP 头基于错误上下文猜测的 token 全部被拒（acceptance rate 0%），主模型在错误 KV 上自回归生成 → 多语言碎片乱码
7. temperature=1.0 + top_p=0.95 的高采样温度进一步放大了错误 logits 下的乱码表现

### 为何偶发（部分请求正常）
- KV 传输失败是**超时驱动**的（`ASCEND_TRANSFER_TIMEOUT=120`），在网络抖动或 P 节点繁忙时偶发
- 当 4 个 TP worker 的 KV 全部成功传输时，输出正常（如"您好，我无法理解您的请求"）
- 当部分 TP worker KV 传输失败时，输出乱码

### 待验证项
1. **`unhashable type: 'list'` 的具体触发点**：需查 `mooncake_connector.py:558` 附近代码，确认是 Mooncake 自身 bug 还是 vllm-ascend 传入数据结构问题
2. **`kv_load_failure_policy='fail'` 是否生效**：理论上 KV 加载失败应终止请求，但实际请求仍返回 200，需确认 fail 策略是否覆盖传输超时场景
3. **网络链路质量**：P1/P2/P3 到 D0 的 RDMA/ascend_direct 链路是否存在拥塞或配置问题（可查 `ibstat`、`hccn_tool` 等）
4. **`ASCEND_TRANSFER_TIMEOUT=120` 是否足够**：当前 120s 仍超时，可能是 P 节点 KV 发送端阻塞而非纯网络问题

### 建议排查方向
1. **优先修复 Mooncake `unhashable type: 'list'` bug**：定位 `mooncake_connector.py:558` 的 KVCacheTransferThread 异常，这是传输线程崩溃的直接原因
2. **验证 KV 传输失败时是否应终止请求**：检查 `kv_load_failure_policy` 实现，确保 KV 缺失时不产出 token 而非输出乱码
3. **降低投机解码风险**：可临时关闭投机解码（移除 `--speculative-config`）验证乱码是否消失，以隔离问题
4. **降低采样温度**：临时设置 `--generation-config vllm` 或请求侧 temperature=0.7，减少乱码可见度（治标）
5. **网络排查**：对 P1/P2/P3 → D0 的 ascend_direct 链路做带宽和延迟测试

## 参考日志路径

| 节点 | 日志文件 | 说明 |
| :---- | :---- | :---- |
| P0 | `/home/gandalf/images/glm5.2-8pd-logs/vllm-glm5.2-8pd-p0-rank0-85.25.15.101-20260806_095703.log` | P0 prefill 日志，无错误 |
| D0 | `/home/gandalf/images/glm5.2-8pd-logs/vllm-glm5.2-8pd-d0-rank0-85.25.9.4-20260806_095730.log` | D0 decode 日志，含 KV 传输失败错误 |
| Proxy | `/home/gandalf/images/glm5.2-8pd-logs/proxy-20260806_100335.log` | 负载均衡代理日志，仅 HTTP 状态 |
| 启动脚本 | `/home/gandalf/glm52_pd_oneclick.sh` | 4P8D 一键启动脚本 |
| 路由代码 | 容器内 `/vllm-workspace/vllm-ascend/examples/disaggregated_prefill_v1/load_balance_proxy_server_example.py` | PD 路由代理实现 |

## 故障链路示意图

```
                        ┌─────────────────────────────────────────────────────────────────────────┐
                        │                   PD 负载均衡代理 (85.25.15.101:13400)                    │
                        │  load_balance_proxy_server_example.py (pid 935801)                       │
                        │  流程: ① select_prefiller → ② send_request (max_tokens=1)               │
                        │        → ③ 获取 kv_transfer_params → ④ select_decoder                  │
                        │        → ⑤ stream_service (decode) → ⑥ 流式返回                         │
                        └─────┬──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┘
                              │          │          │          │          │          │
              ┌───────────────┘          │          │          │          │          └───────────────┐
              ▼                          ▼          ▼          ▼          ▼                          ▼
      ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
      │  P0 (Prefill) │  │  P1 (Prefill) │  │  P2 (Prefill) │  │  P3 (Prefill) │
      │ 85.25.15.101  │  │ 85.25.20.101  │  │ 85.25.20.103  │  │ 85.25.20.107  │
      │ DP=4, TP=8    │  │ DP=4, TP=8    │  │ DP=4, TP=8    │  │ DP=4, TP=8    │
      │ mooncake_port │  │ mooncake_port │  │ mooncake_port │  │ mooncake_port │
      │ =30000        │  │ =30000        │  │ =30000        │  │ =30000        │
      └──────┬───────-┘  └──────┬────────-┘  └──────┬───────-┘  └──────┬───────-┘
             │                  │                    │                  │
             │      Mooncake KV Cache 传输 (ascend_direct)
             │      ┌─────────────────────────────────────┐
             │      │  ⚠  ⚠  ⚠  故障链路  ⚠  ⚠  ⚠          │
             │      │  P1/P2/P3 → D0 传输大面积超时失败    │
             │      │  · Transfer timeout (120s timeout)    │
             │      │  · Mooncake transfer failed (ret=-1)  │
             │      │  · Error in KVCacheTransferThread     │
             │      │    ("unhashable type: 'list'")        │
             │      │                                      │
             │      │  偶有成功：P0 ↔ D0 传输正常            │
             │      └─────────────────────────────────────┘
             │                  │                    │                  │
             ▼                  ▼                    ▼                  ▼
      ┌──────────────────────────────────────────────────────────────────────────────────────┐
      │                       Decode 节点组 (4节点 × 2实例 = 8实例)                           │
      │                                                                                       │
      │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
      │  │ D0 (85.25.9.4) │  │ D1 (85.25.9.2) │  │ D2 (85.25.1.5) │  │ D3 (85.25.0.110)│       │
      │  │ DP=8, TP=4     │  │ DP=8, TP=4     │  │ DP=8, TP=4     │  │ DP=8, TP=4     │       │
      │  │ inst0:9081     │  │ inst0:9081     │  │ inst0:9081     │  │ inst0:9081     │       │
      │  │ inst1:9082     │  │ inst1:9082     │  │ inst1:9082     │  │ inst1:9082     │       │
      │  └────────────────┘  └────────────────┘  └────────────────┘  └────────────────┘       │
      │                                                                                       │
      │  Decode 阶段（在错误/缺失的 KV Cache 上执行）:                                         │
      │  ① D 节点未收到正确 KV → 用错误/空 KV 做 attention                                   │
      │  ② logits 分布异常 → 采样输出多语言碎片乱码                                           │
      │  ③ 投机解码 MTP head 全拒 (acceptance rate 0%)                                       │
      └──────────────────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
      ┌────────────────────────────────────────────────────┐
      │              客户端收到响应                               │
      │  · 部分请求正确 (KV传输成功): 正常中文回复                │
      │  · 部分请求乱码 (KV传输失败): 多语言混杂无意义文本        │
      └────────────────────────────────────────────────────┘
```

## 记录信息

- **记录时间**：2026-08-06
- **记录人**：AI agent（上下文持续集成云上 Agent）
- **信息来源**：
  - 日志路径见参考日志表（P0、D0 节点日志 + Proxy 日志）
  - 节点信息可通过 `C:\Users\l60130933\.ssh\config` SSH 配置查看
  - 其他 PD 节点日志可通过相同方式从对应 IP 获取

---

## 🔬 实际环境验证记录

> 本节记录问题排查建议的验证状态与实际观测结果。详细操作过程见 [../Model%20Deploy/实践记录.md](../Model%20Deploy/实践记录.md)

### 验证项 1：Mooncake `unhashable type: 'list'` bug 定位

**状态**：⚠️ 待定位（需查看源码）

**实际观测**：
- 日志证据：`Error in KVCacheTransferThread. error=unhashable type: 'list'` (mooncake_connector.py:558)
- 推测：Mooncake Connector 在处理 KV Cache 数据结构时，将 list 用作了 dict 的 key（Python 不允许）

**下一步行动**：
```bash
# 需在 vLLM 容器内查看源码（仅读操作）
kubectl exec -it <vllm-pod-name> -- cat /vllm-workspace/vllm-ascend/vllm/ascend/kv_transfer/mooncake_connector.py | grep -A 10 -B 10 "line 558"
```

### 验证项 2：`kv_load_failure_policy='fail'` 是否生效

**状态**：⚠️ 未生效（KV 缺失时仍返回 200 OK，而非拒绝请求）

**实际观测**：
- 现象：KV 传输失败时，D 节点继续输出乱码 Token，而非报错
- 推测：`kv_load_failure_policy` 可能未覆盖 Mooncake 传输超时场景

**下一步行动**：
```bash
# 查询 vLLM 启动参数（仅读操作）
ps aux | grep vllm | grep -o "kv_load_failure_policy=[^ ]*"
```

### 验证项 3：网络链路质量（P 节点 → D 节点）

**状态**：✅ 可通过 ping 验证（但当前 SSH 认证问题，暂未实测）

**下一步行动**：
```bash
# 在 D0 节点执行
ssh root@85.25.9.4
ping -c 5 85.25.15.101  # P0
ping -c 5 85.25.20.101  # P1
ping -c 5 85.25.20.103  # P2
ping -c 5 85.25.20.107  # P3

# 检查 RDMA/HCCS 链路（华为 NPU）
hccn_tool -i npu_0 -link -g
```

### 验证项 4：`ASCEND_TRANSFER_TIMEOUT=120` 是否足够

**状态**：⚠️ 当前 120s 仍超时，需判断是网络问题还是 P 节点阻塞

**实际观测**：
- 日志证据：`Transfer timeout` 在 120s 后触发
- 推测：可能是 P 节点 KV 发送端阻塞（而非单纯网络延迟）

**下一步行动**：
```bash
# 检查 P 节点的 Mooncake 发送队列（仅读操作）
ssh root@85.25.15.101  # P0
grep "Mooncake.*queue\|kv_transfer" /path/to/vllm.log | tail -50
```

### 验证项 5：关闭投机解码验证乱码是否消失（临时验证）

**状态**：⚠️ 待验证

**推测**：关闭投机解码后，若乱码消失，则说明问题出在 MTP head；若仍乱码，则确认是 KV Cache 根因

**下一步行动**：
```bash
# 需修改启动脚本（写操作），在生产环境谨慎操作
# 建议在测试环境先验证：移除 --speculative-config 参数后重启 vLLM
```

### 当前验证结论

- ✅ **根因明确**：Mooncake KV 传输大面积失败 → D 节点使用错误 KV → attention 错位 → 乱码
- ⚠️ **待定位**：Mooncake Connector 的 `unhashable type: 'list'` 具体触发点（需源码审计）
- ⚠️ **策略失效**：`kv_load_failure_policy='fail'` 未在传输超时场景生效
- ⚠️ **临时规避**：降低采样温度（temperature=0.7）可减少乱码可见度，但治标不治本

---

## 建议修复方案（待确认）

### 短期规避（生产环境可立即实施）

1. **降低采样温度**（减少乱码可见度）
   ```bash
   # 在 LiteLLM 请求中设置 temperature=0.7
   # 或修改模型 generation_config.json
   ```

2. **关闭投机解码**（如 MTP head 对 KV 错误敏感）
   ```bash
   # 移除 --speculative-config 参数（需重启 vLLM，谨慎操作）
   ```

3. **增加 KV 传输超时阈值**（临时缓解）
   ```bash
   export ASCEND_TRANSFER_TIMEOUT=300  # 从 120s 增加到 300s
   ```

### 中期修复（需代码/配置变更）

1. **修复 Mooncake Connector bug**
   - 定位 `mooncake_connector.py:558` 的 list-as-dict-key 问题
   - 提交 bug fix 到 vllm-ascend 社区

2. **强化 `kv_load_failure_policy='fail'`**
   - 确保传输超时、部分 TP 缺失等场景都触发 failure
   - 避免 D 节点在错误状态下继续输出

3. **PD 分离健康检查**
   - 在路由层（proxy）增加 P→D 的 KV 传输健康检查
   - 传输失败时直接返回错误，而非让 D 节点盲算

### 长期优化

1. **Mooncake 传输监控**
   - 在 Prometheus 中增加 Mooncake 传输成功率、延迟的 metrics
   - 设置告警：传输失败率 > 阈值时告警

2. **网络链路优化**
   - 铺测 P1/P2/P3 → D0 的 RDMA/HCCS 带宽和延迟
   - 排查是否存在链路拥塞或配置问题

---

*快照更新时间：2026-08-06*
