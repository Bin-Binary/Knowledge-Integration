# LLM 平台实践操作记录

> 本文档侧重实操步骤与验证方法。

---

### Agent免密ssh到远端
```powershell
#1. 生成密钥对
ssh-keygen -t rsa -b 4096 -f "C:\Users\l60130933\.ssh\id_rsa" \
-N '""' -C "l60130933@huawei.com"

#2. 上传公钥到远端
type C:\Users\l60130933\.ssh\id_rsa.pub | ssh ${USER_NAME}$@${IP}$ \
"mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

---
### 查看systemd日志
```bash
# 实时输出
journalctl -u opencode-api -f 

# 最近一个小时日志
journalctl -u opencode-api --since "1 hour ago" --no-pager 
```

### 验证K8s集群状态

```bash
#1. 连接 K8s master 节点
ssh root@

#2. 检查集群节点状态
kubectl get nodes -o wide

# 步骤 3：查看控制面组件健康状态
kubectl get cs

# 步骤 4：检查命名空间
kubectl get ns
```

### 预期结果快照（运维手册 §1）

```
NAME           STATUS   ROLES           AGE   VERSION   INTERNAL-IP
x.x.x.x        Ready    control-plane   XXd   v1.31.1   x.x.x.x
x.x.x.x        Ready    <none>          XXd   v1.31.1   x.x.x.x
```

### 验证要点

- ✅ 两个节点状态均为 `Ready`
- ✅ 版本号应为 `v1.31.1`
- ✅ master 节点 ROLES 包含 `control-plane`

---

### 检查LiteLLM服务状态

```bash
# 步骤 1：查看LiteLLM Pod状态
kubectl get pods -n litellm -o wide

# 步骤 2：查看 LiteLLM Service
kubectl get svc -n litellm

# 步骤 3：检查 LiteLLM 日志（最近 50 行）
kubectl logs -n litellm -l app.kubernetes.io/component=litellm --tail=50

# 步骤 4：验证 Pod 环境变量（检查密钥注入）
POD=$(kubectl get pods -n litellm -l app.kubernetes.io/component=litellm --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')
kubectl exec -n litellm $POD -- env | grep -E 'KEY|BASE' | sort
```

### 预期结果快照（运维手册 §5）

**Pod 状态**：
```
NAME                                          READY   STATUS    RESTARTS   AGE   IP            NODE
litellm-litellm-stack-litellm-xxx-yyy         1/1     Running   0          XXh   10.244.x.x    x.x.x.x
litellm-litellm-stack-litellm-xxx-zzz         1/1     Running   0          XXh   10.244.x.x    x.x.x.x
litellm-litellm-stack-postgres-xxx            1/1     Running   0          XXh   10.244.x.x    x.x.x.x
litellm-litellm-stack-redis-xxx               1/1     Running   0          XXh   10.244.x.x    x.x.x.x
```

**Service 配置**：
```
NAME                                  TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
litellm-litellm-stack-litellm         NodePort    10.96.x.x       <none>        ?:31937/TCP   XXd
litellm-litellm-stack-postgres        ClusterIP   10.96.x.x       <none>        ?/TCP         XXd
litellm-litellm-stack-redis           ClusterIP   10.96.x.x       <none>        ?/TCP         XXd
```

### 验证要点

- ✅ LiteLLM Pod 运行 2 个副本（双节点）
- ✅ PostgreSQL 和 Redis 运行在 node-1 (x.x.x.x)
- ✅ NodePort 为 ?（生产入口）
- ✅ 环境变量应包含 `LITELLM_MASTER_KEY`、`DATABASE_URL`、`REDIS_HOST` 等

---

### 查询模型路由配置

```bash
# 步骤 1：查询 LiteLLM 路由表（API 方式）
curl -sf -H 'Authorization: Bearer sk-2274cb53dfe7ece2c4c1c8200e9d4a7b' \
  'http://x.x.x.x:?/model/info' | python3 -c '
import json,sys
d=json.load(sys.stdin)
for m in d.get("data",[]):
    p=m.get("litellm_params",{})
    print(f"{m["model_name"]:30s} {p.get("api_base","N/A"):40s} {m.get("model_info",{}).get("id","N/A")}")'

# 步骤 2：查看 ConfigMap 中的路由配置
kubectl get configmap litellm-litellm-stack-config -n litellm -o jsonpath='{.data.config\.yaml}'

# 步骤 3：查看数据库中的动态路由
# (需通过 LiteLLM UI 或直接查询 PostgreSQL)
```

### 预期结果快照（运维手册 §6）

**ConfigMap 路由（2026-06-26 快照参考）**：

| model_name | litellm_params.model | model_info.id | weight | 说明 |
|:---|:---|:---|:---|:---|
| GLM-V5.1 | openai/GLM-V5.1 | prod-aiteam-glm5.1 | 26 | HIS AITeam |
| GLM-V5.1-Green | openai/GLM-V5.1 | green-shanghai-A3-glm5.1 | 50 | 上海绿区 A3 |
| Qwen3-30B-A3B-Instruct | openai/qwen3 | yellow-shanghai-A2-0-qwen3-30b | 50 | 上海黄区 A2-0 |

### 验证要点

- ✅ 路由表包含 ConfigMap + DB 动态路由两部分
- ✅ GLM-V5.1 至少有 4 个后端（AITeam + 上海/西安/苏州绿区）
- ✅ weight 总和应在合理范围（反映流量分配）

---


### 检查Prometheus监控目标

```bash
# 步骤 1：查看 Prometheus Service
kubectl get svc -n monitoring

# 步骤 2：获取 Prometheus ClusterIP
PROM_IP=$(kubectl get svc -n monitoring llm-monitoring-llm-monitoring-prometheus -o jsonpath="{.spec.clusterIP}")

# 步骤 3：查询监控目标健康状态
curl -s http://$PROM_IP:9090/api/v1/targets | python3 -c '
import json,sys
d=json.load(sys.stdin)
for t in d["data"]["activeTargets"]:
    print(f"{t["labels"]["job"]:30s} {t["health"]:10s} {t["scrapeUrl"]}")'

# 步骤 4：查看告警规则
kubectl get configmap llm-monitoring-llm-monitoring-prometheus-config -n monitoring -o yaml | grep -A 20 "alert_rules.yml"
```

### 预期结果快照（运维手册 §7）

**监控目标状态**：

```
job                            health     scrapeUrl
prometheus                     up         http://localhost:9090/metrics
litellm                        up         http://litellm-litellm-stack-litellm.litellm.svc.cluster.local:4000/metrics/
green-shA3-via-proxy          up         http://x.x.x.x:?/metrics/
green-xA3-via-proxy           up         http://x.x.x.x:?/metrics/
yellow-szA2-112-glm52         up         http://x.x.x.x:?/metrics/
```

### 验证要点

- ✅ 所有 scrape 目标 `health` 应为 `up`
- ✅ header_proxy 端口（9333/9334/9335/9340/9341）可达
- ✅ vLLM 内网直连地址（10.246.x.x、100.102.x.x）可达
- ✅ metrics_path 应为 `/metrics/`（带尾斜杠，避免 307 重定向）

---


### 测试请求生命周期（端到端）

```bash
# 步骤 1：构造测试请求
curl -X POST http://x.x.x.x:?/v1/chat/completions \
  -H "Authorization: ??? \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-V5.1",
    "messages": [{"role": "user", "content": "解释Transformer架构"}],
    "stream": false,
    "max_tokens": 50
  }'

# 步骤 2：流式请求测试
curl -X POST http://x.x.x.x:?/v1/chat/completions \
  -H "Authorization: ???" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "GLM-V5.1",
    "messages": [{"role": "user", "content": "什么是KV Cache"}],
    "stream": true,
    "max_tokens": 100
  }'

# 步骤 3：检查响应延迟（使用 time 命令）
time curl -X POST http://x.x.x.x:?/v1/chat/completions \
  -H "Authorization: ???" \
  -H "Content-Type: application/json" \
  -d '{"model": "GLM-V5.1", "messages": [{"role": "user", "content": "测试"}], "max_tokens": 10}'
```

### 预期结果快照

**正常响应示例**：
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1722964800,
  "model": "GLM-V5.1",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Transformer架构是一种基于自注意力机制..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 50,
    "total_tokens": 65
  }
}
```

### 验证要点

- ✅ HTTP 状态码应为 `200 OK`
- ✅ `object` 字段为 `chat.completion`（非流式）或 `chat.completion.chunk`（流式）
- ✅ TTFT（首 Token 时间）应在秒级（<2s）
- ✅ 响应体包含 `usage.prompt_tokens` 和 `usage.completion_tokens`
- ✅ 流式响应应逐 Token 返回，无明显卡顿

---

### 调试 vLLM 推理引擎（远程服务器）

```bash
# 步骤 1：连接 vLLM 服务器（示例：上海绿区 A3）
ssh root@x.x.x.x

# 步骤 2：检查 vLLM 进程
ps aux | grep vllm

# 步骤 3：查看 GPU/NPU 显存占用
# NVIDIA GPU:
nvidia-smi

# 华为 NPU:
npu-smi info

# 步骤 4：检查 vLLM 日志
tail -f /path/to/vllm.log | grep -E "TTFT|tokens|KV Cache"

# 步骤 5：查询 vLLM metrics（如果暴露）
curl http://localhost:8000/metrics/ | grep -E "vllm:num_requests_running|vllm:time_to_first_token_seconds|vllm:kv_cache_usage_ratio"
```

### 预期结果快照

**nvidia-smi 输出示例**：
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.104.05   Driver Version: 535.104.05   CUDA Version: 12.2     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Ev|   Memory-Usage      | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA A100-SXM...  On   | 00000000:00:04.0 Off |                    0 |
| N/A   35C    P0    60W / 400W |  68234MiB / 81920MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

**vLLM metrics 关键指标**：
```
vllm:num_requests_running 0
vllm:time_to_first_token_seconds_sum 15.2
vllm:kv_cache_usage_ratio 0.45
```

### 验证要点

- ✅ vLLM 进程运行中，端口监听（默认 8000）
- ✅ 显存占用 = 模型权重 + KV Cache（通常 60-80GB）
- ✅ GPU-Util 在有请求时应 >0%
- ✅ KV Cache usage ratio < 1.0（否则 OOM）
- ✅ TTFT 指标应在合理范围（<1s）

---

### 排查 KV Cache 传输失败（GLM-5.2 PD 分离）

```bash
# 步骤 1：连接 Decode 节点（D0）
ssh root@x.x.x.x

# 步骤 2：查看 Mooncake 传输日志
grep -E "Transfer timeout|Mooncake transfer failed|KVCacheTransferThread" /home/gandalf/images/glm5.2-8pd-logs/vllm-glm5.2-8pd-d0-rank0-*.log

# 步骤 3：检查网络连通性（P 节点 → D 节点）
ping -c 5 

# 步骤 4：检查 RDMA/HCCS 链路（华为 NPU）
hccn_tool -i npu_0 -link -g

# 步骤 5：查看投机解码指标
grep "SpecDecoding metrics" /path/to/vllm.log | tail -5
```

### 预期结果快照（正常场景）

**KV 传输成功**：
```
I0806 10:11:18 [mooncake_connector.py:XXX] KV cache transfer for request chatcmpl-xxx took 176.49 ms
```

**投机解码正常**：
```
SpecDecoding metrics: Mean acceptance length: 2.50, Accepted throughput: 40.20 tokens/s, Avg Draft acceptance rate: 60.0%
```

### 异常快照（Issue 文档案例）

**KV 传输失败**：
```
E0806 10:11:18 [ascend_direct_transport.cpp:831] Transfer timeout to: x.x.x.x:?
E0806 10:11:18 [mooncake_connector.py:774] Mooncake transfer failed for request. ret=-1
E0806 10:11:18 [mooncake_connector.py:558] Error in KVCacheTransferThread. error=unhashable type: 'list'
```

**投机解码失效**：
```
SpecDecoding metrics: Mean acceptance length: 1.00, Accepted: 0 tokens, Avg Draft acceptance rate: 0.0%
```

### 验证要点

- ✅ KV 传输延迟应在百毫秒级（<500ms）
- ✅ 无 `Transfer timeout` 或 `Mooncake transfer failed` 错误
- ✅ 投机解码 acceptance rate 应 >50%
- ✅ P 节点到 D 节点网络 ping 延迟 <1ms

---


### 查看KV Cache显存计算公式

```bash
# 场景：验证 Llama 3 70B 的显存计算

# 步骤 1：确认模型参数
# 参数量：70B = 70 × 10^9
# 层数 L：80 (Llama 3 70B)
# KV Heads H_kv：8 (GQA)
# Head Dim d_h：128
# 精度 P：2 bytes (FP16)

# 步骤 2：计算权重显存
# INT8 量化权重：70B × 1 byte = 70 GB
python3 -c "print(f'权重显存(INT8): {70e9 * 1 / 1e9:.2f} GB')"

# 步骤 3：计算 KV Cache 显存（128k 序列长度）
python3 << 'EOF'
L = 80  # 层数
H_kv = 8  # KV heads
d_h = 128  # head dim
S = 128000  # 序列长度
P = 2  # FP16 = 2 bytes

kv_cache = 2 * L * H_kv * d_h * S * P
print(f'KV Cache 显存: {kv_cache / 1e9:.2f} GB')
print(f'模型权重(INT8) + KV Cache: {70 + kv_cache/1e9:.2f} GB')
EOF

# 查询实际显存占用（从 vLLM metrics）
curl http://vllm-server:8000/metrics/ | grep kv_cache_usage_ratio
```

### 预期结果快照

**理论计算结果**：
```
权重显存(INT8): 70.00 GB
KV Cache 显存: 20.97 GB
模型权重(INT8) + KV Cache: 90.97 GB
```

### 验证要点

- ✅ 理论计算与实际显存占用相差应在 10% 以内
- ✅ 128k 序列的 KV Cache 约 21GB（符合运维手册的"32000 tokens => 10GB"估算）
- ✅ 单张 80GB 显卡无法承载 70B 模型 + 长上下文 KV Cache（需 2 张以上）

---

## 快速诊断命令速查

### LiteLLM 相关
```bash
# 查看 Pod 状态
kubectl get pods -n litellm -o wide

# 查看最近日志
kubectl logs -n litellm -l app.kubernetes.io/component=litellm --tail=100

# 查看环境变量
kubectl exec -n litellm <pod-name> -- env | grep -E 'KEY|PASSWORD'

# 查看路由表
curl -H "Authorization: Bearer sk-xxx" http://7.212.76.8:31937/model/info

# 测试推理请求
curl -X POST http://x.x.x.x:?/v1/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"GLM-V5.1","messages":[{"role":"user","content":"测试"}],"max_tokens":10}'
```

### Prometheus 相关
```bash
# 查看监控目标
kubectl port-forward -n monitoring svc/llm-monitoring-llm-monitoring-prometheus 9090:9090
curl http://localhost:9090/api/v1/targets

# 查看告警规则
curl http://localhost:9090/api/v1/rules
```

### vLLM 相关
```bash
# 查看 GPU 显存
nvidia-smi  # NVIDIA
npu-smi info  # 华为

# 查看 vLLM metrics
curl http://localhost:8000/metrics/

# 查看进程
ps aux | grep vllm
```

### 网络排查
```bash
# 检查节点连通性
ping -c 5 <node-ip>

# 检查端口监听
ss -tlnp | grep <port>

# 查看 header_proxy 端口
ssh root@x.x.x.x:? "ss -tlnp | grep python3 | grep -E '933[0-9]|934[0-9]'"
```

---

