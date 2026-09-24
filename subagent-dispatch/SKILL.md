---
name: subagent-dispatch
description: 派发/拆分 subagent 前的模型选择与确认协议。触发词："分发 subagent"、"拆分 subagent"、"派子代理"、"启动子代理"、"并行子代理"、"delegate subagent"、"spawn subagent"。凡准备用 subagent/subagent_fork/agent_teams 成员分派任务前都应先载入本 skill。
disable-model-invocation: false
---

# Subagent 派发协议（模型分工 + 确认）

派发子代理前，按下面的分工选模型，并在需要时先让用户确认，再派。
本策略针对**本桌面已授权的子代理模型**（见 DSH 设置「Subagent」页）。

## 模型分工（本桌面已授权）

| 模型 | 用途 |
|---|---|
| GLM-5.3 | 框架 / 高强度推理（强） |
| Kimi K3-256K | 架构 / 高强度（强但慢） |
| GLM-5.3-flash | 快 / 省档；大规模任务也用它 |
| Qwen3.8-27B | 大规模任务（免费） |
| Kimi For Coding HighSpeed | 特别认真：同一件事并行派多个子代理（跨模型冗余核对） |

## 派发协议

1. **选模型**：按上表把每个子任务映射到合适的模型。
2. **高强度档**（框架/架构）：列「GLM-5.3 vs Kimi K3-256K」让用户二选一（K3 更强但更慢）。
3. **大规模档**：列「Qwen3.8-27B vs GLM-5.3-flash」让用户二选一（Qwen 免费、flash 快）。
4. **需要确认时**（多子代理 / 严谨模式 / 要覆盖默认模型 / KIMI 并行同任务）：把「任务 → 模型」列给用户确认后再派。
5. **单个简单子代理**：按档直派，不逐次打断。
6. **收尾**：一次性子代理拿回结果即弃；要留给其他会话 / agent 的结论，**显式存进 dsh-mnemon**（Document / 记忆），别指望子代理记得。
