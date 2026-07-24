---
name: rtl-signal-trace
description: >-
  Static signal-path tracing and module-dependency analysis for
  Verilog/SystemVerilog projects: trace a signal from source to sink across
  module hierarchy, flag clock-domain crossings, and build module dependency
  graphs to validate file lists (file_list.f). Text-search based, no EDA or
  AST tooling required. Use when the user asks to trace a signal, analyze CDC
  risk, map module call/instantiation relationships, or check a file list.
  触发词: "信号追踪", "signal trace", "信号路径", "跨时钟域", "CDC 分析",
  "模块依赖", "调用关系", "file_list", "拓扑排序". Do not use as a replacement
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
- 默认只分析当前版本源码；历史版本/归档目录除非用户指定否则不追。
