---
name: rtl-signal-trace
description: >-
  Static signal-path tracing and module-dependency analysis for
  Verilog/SystemVerilog projects: trace a signal from source to sink across
  module hierarchy, flag clock-domain crossings, and build module dependency
  graphs to validate file lists (file_list.f). Text-search based, no EDA or
  AST tooling required. Use when the user asks to trace a signal, analyze CDC
  risk, map module call/instantiation relationships, or check a file list.
  触发词: "检查信号", "信号追踪", "信号链路", "信号是否连通", "signal trace",
  "信号路径", "跨时钟域", "CDC 分析", "模块依赖", "调用关系", "file_list",
  "拓扑排序". Do not use as a replacement
  for real CDC/EDA signoff tools.
---

# RTL Signal Trace

在**没有 AST/EDA 工具**的条件下，用文本搜索（Grep/Read）做信号跨模块路径追踪与模块依赖分析。若项目已有 AST 工具链，可参考 `$SKILL_ROOT/references/ast_traversal_rules.md` 走 AST 路线。

## Runtime Compatibility

读取 reference 之前，先把本 `SKILL.md` 所在目录解析为 `SKILL_ROOT`（Kimi Code / Claude Code 中使用 skill 加载信息给出的绝对路径；Claude Code 可用 `${CLAUDE_SKILL_DIR}`）。下文所有 `$SKILL_ROOT/...` 均为相对本目录的路径。

## Workflow A：信号路径追踪（source → sink）

1. **定位 source**：Grep 信号声明（`wire`/`reg`/`logic`/`output`）与首次赋值点。
2. **逐跳追踪**，沿三类边向 sink 方向 DFS：
   - 赋值边：`assign`、always 块内 `LHS <= / = RHS`
   - 端口边：模块实例 `.port(sig)`——跨层时进入被实例化模块内部继续追
   - 位操作：拼接 `{a,b}` / 截位 `x[7:4]`，记录位宽变化
3. **记录每一跳**：`模块 / 信号名 / 文件:行号 / 操作类型 / 时钟域`。
4. **时钟域判断**：记录每跳所在 always 块的时钟；相邻跳时钟不同 → 标记疑似 CDC，检查路径上有无同步器（2flop sync / FIFO / handshake）。
5. **防环**：设深度上限（如 50 跳）；超限报"疑似环路"。
6. **找不到路径时**：说明断点位置与可能原因（黑盒/IP、`define 分支、generate 块、宏拼接信号名），不要硬编一条路径。

## Workflow B：模块依赖图与 file_list 校验

1. 读取项目的文件列表（如 `file_list.f` / `*.f` / 构建脚本）得到文件全集。
2. Grep 各文件中的模块实例化语句，构建"模块 → 依赖模块"有向图。
3. 拓扑排序并检查三类问题：
   - **顺序**：file_list 是否满足先定义后实例化（视工具要求）
   - **孤儿**：文件在列表中但没有任何模块被实例化
   - **缺失**：被实例化的模块不在列表中
4. 输出依赖关系与问题清单；结构有变化时更新项目的调用关系文档（保持该项目既有格式）。

## Workflow C：重定时消费者相对相位审计（打一拍/tap 移动类变更必跑）

> 出处：2026-09-29 HK1V11 G13 SHORT/LONG 打一拍双事故——静态逐信号追踪全部"连通/无绝对相位假设"，仍漏掉成对消费的相对拍差回归（DECODE 钥旋转、掩码-窗口互锁）。

触发条件：diff 中任一信号生效拍被移动（加打拍 / 数据参考后移 / 掩蔽换 tap / 输出换域）。

1. **枚举成对消费点**：对每个被重定时信号 X，grep 所有与其它信号**同拍组合消费**的位置（比较器、判决器、门控项、装载使能、掩蔽项），列出全部 (X, Y) 对，逐对标注消费模块 file:line。
2. **标注拍差**：X、Y 各自相对改动前的位移量 ΔX、ΔY；**ΔX ≠ ΔY 即红旗**（整体 +N 平移 = 所有共消费信号同 Δ 才合法）。
3. **三杀结构猎杀**（消费者侧）：
   - 同拍交叉比较判决器（`f(X)` 与 `Y` 直接同拍比较/判决，如钥旋转、相位选择）；
   - 反重触发掩蔽 lag（掩码字相对检测窗的滞后量是**行为参数**，不得随实现便利移动）；
   - 装载窗 == 首作用窗（装载值采样拍与桶形/数据窗首作用拍必须对位，错一拍 = 装错相位或丢字）。
4. **等价判定**：形状差异（任一 Δ 不同）必须逐拍对照旧版证明接受集等价（第一个分叉拍定位法）；**无对拍证据不得给 PASS**——静态"相对几何保持"推演不得单独作为结论。
5. 输出「消费者 × 拍差」总表（含每个红旗的判别波形建议）。


## 输出格式

```markdown
## 信号路径：<source> → <sink>

| 跳 | 模块 | 信号 | 位置 | 操作 | 时钟域 |
| --- | --- | --- | --- | --- | --- |
| 1 | uart_rx | rx_data | uart_rx.v:123 | assign | clk_a |
| 2 | top | rx_data | top.v:45 | .d(rx_data) | clk_a |
| 3 | fifo | wdata | fifo.v:67 | .wdata(rx_data) | clk_b |

- 跨时钟域：是（第 2→3 跳，clk_a → clk_b），⚠ 路径上未见同步器
- 备注：基于静态文本分析，未跑仿真/CDC 工具验证。
```

## 硬性规则

- **只分析不改动**；如需修改 file_list 或设计文档，经用户确认后执行。
- 结论必须标注"基于静态文本分析"——本 skill 不能替代真正的 CDC/LEC/仿真签核。
- **重定时类变更的 Workflow C 结论必须标注"待对拍/实跑佐证"**：相对相位/接受集等价不得仅凭静态推演判 PASS（2026-09-29 事故：增量静态审两轮全过，动态回归双 case 红；静态反证亦不可信，同日两次翻案）。
- 默认只分析当前版本源码；历史版本/归档目录除非用户指定否则不追。
