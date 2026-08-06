# 平台调度层 · 总览

> 请求 = 5 跳到达 GPU。每跳单一职责，可独立容错。

```
  用户 → HAProxy → K8s → LiteLLM → header_proxy → vLLM
          VIP均衡   容器转发  鉴权+路由    凭证+穿透      GPU推理
```

| 跳 | 组件 | 职责 | 故障时 |
|----|------|------|--------|
| ① | HAProxy | VIP 入口，leastconn 选节点 | Keepalived 漂移 VIP |
| ② | K8s | NodePort → Pod 转发 | 滚动更新，切另一副本 |
| ③ | LiteLLM | 鉴权 + weight 路由 + 并发控制 | num_retries=3，自动切后端 |
| ④ | header_proxy | 注入凭证，穿越网络隔离 | Token 过期自动刷新 |
| ⑤ | vLLM | Prefill → Decode → SSE Stream | 上游重试其他候选 |

> [LLM-Platform-Practice.md](./docs/LLM-Platform-Practice.md) — 运维命令 + 验证标准。
