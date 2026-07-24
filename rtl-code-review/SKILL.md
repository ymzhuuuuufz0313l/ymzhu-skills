---
name: rtl-code-review
description: >-
  Adversarial, structured review of RTL (Verilog/SystemVerilog) changes:
  timing risk, maintainability, synthesis-friendliness, interface consistency,
  with severity grading and a pass/fail gate. Use when the user asks to review
  RTL changes, run a code review before commit/delivery, or do a reliability
  check on hardware code. 触发词: "rtl review", "code review", "代码评审",
  "对抗评审", "交付前 review", "可靠性检查". Do not use for running
  simulations, debugging testbenches, or reviewing non-RTL code.
---

# RTL Code Review

对 RTL 变更做对抗性结构化评审：分维度检查 + severity 分级 + pass/fail 门禁。评审由当前 Agent 直接执行，不依赖任何外部工具或子进程。

## Runtime Compatibility

读取 reference 之前，先把本 `SKILL.md` 所在目录解析为 `SKILL_ROOT`。不要假设当前工作目录就是 skill 目录，也不要假设某个 shell 调用里设置的变量会保留到下一个。

- 在 Kimi Code / Claude Code 中：使用 skill 加载信息中给出的本 skill 绝对路径（Claude Code 可用 `${CLAUDE_SKILL_DIR}`）。
- 下文所有 `$SKILL_ROOT/...` 均为相对本目录的路径。

## 角色

| 角色 | 风格 | 适用场景 |
| --- | --- | --- |
| `ruthless`（默认） | 无赞美只挑刺，找出每一个缺陷 | 重大改动前的压力测试 |
| `linus` | 直接尖锐，技术导向 | 风格/架构决策评审 |
| `balanced` | 承认优点 + 给出建议 | 常规评审 |

角色详细提示词见 `$SKILL_ROOT/references/role_personas.md`。

## Workflow

1. **收集评审对象**：本次变更的 diff（`git diff`）或用户指定的 RTL 文件；同时读取相关接口文档与上层实例化文件。
2. **加载维度定义**：读取 `$SKILL_ROOT/references/rtl_review_dimensions.md`，按其中的检查项执行。
3. **按维度逐项审查**，每个问题标注 severity：`[CRITICAL]` / `[HIGH]` / `[MEDIUM]` / `[LOW]`，并给出文件:行号 与修复方向。
4. **pass 判定**：`pass = (critical == 0 && high <= 1)`。
5. **输出报告**：格式见下文。默认直接回复用户；用户要求时再落盘。

## 评审维度

| 维度 | 检查点 |
| --- | --- |
| 语法/风格 | 语法正确；命名与周边代码一致；注释与实际行为同步（改代码必须顺手改注释） |
| 时序风险 | 新增长组合路径；该 pipeline 未 pipeline；跨时钟域信号无同步处理 |
| 可维护性 | 过深嵌套；模块膨胀；魔法数字（应用 parameter/localparam） |
| 综合友好 | 不可综合语法；latch 推断；不完整敏感列表 |
| 接口一致性 | 端口/位宽变化是否同步更新上层实例化、文件列表（如 `file_list.f`）、接口文档 |
| 验证影响 | 行为变化是否影响现有 testbench/checker/coverage（只静态分析，不跑仿真） |
| 可追溯性（可选） | 若项目使用 `@requirement` / REQ_ID 体系：变更代码是否有对应需求标注，标注是否仍有效 |

## 输出格式

```markdown
## RTL Review 报告（<日期>，角色: ruthless）

### 评审对象
- <文件列表 / diff 范围>

### 问题清单
1. [HIGH] <文件:行号> <问题描述> → 建议：<修复方向>
2. [MEDIUM] ...

### 维度小结
- 时序风险：<n 项 / 无>
- 接口一致性：<n 项 / 无>
- ...

### 判定
- severity 统计：critical=X, high=X, medium=X, low=X
- pass: true / false
```

## 硬性规则

- **只评审、只报告**。修复动作经用户确认后再执行，不在评审过程中顺手改代码。
- **不跑仿真**。时序/功能判断基于静态代码分析，报告中必须注明这一点。
- 问题被修复后，复审对应条目并更新报告，不要默认修复即正确。
- 找不到问题就如实说"未发现"，不要为凑数编造低风险项。
