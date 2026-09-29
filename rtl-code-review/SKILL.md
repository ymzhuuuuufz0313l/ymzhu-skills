---
name: rtl-code-review
description: >-
  Adversarial, structured review of RTL (Verilog/SystemVerilog) changes:
  timing risk, maintainability, synthesis-friendliness, interface consistency,
  with severity grading and a pass/fail gate. Use when the user asks to review
  RTL changes, run a code review before commit/delivery, or do a reliability
  check on hardware code. 触发词: "检查 rtl", "检查RTL", "检查 RTL",
  "帮我检查 rtl", "rtl review", "code review", "代码评审", "对抗评审",
  "交付前 review", "可靠性检查". Do not use for running
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
| **重定时消费者审计** | **本次 diff 移动了任一信号的生效拍（打一拍/装载源换延迟域/比较器判决器换 tap/输出改吃流水版本）时触发：枚举该信号全部跨模块消费者，逐个标注所需 tap 并产出修复前后拍差表；猎杀同拍交叉比较结构（判决器/反重触发掩蔽把两个延迟域信号放同一表达式）；掩蔽窗口 lag 与"装载值窗==首作用窗"级联属校准行为参数，不得随实现移动；拍差变化且无新旧对拍等价论证 → CRITICAL（细则见 references/rtl_review_dimensions.md §6）** |
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
- **不跑项目 case 仿真**。时序/功能判断基于静态代码分析，报告中必须注明这一点。**例外**：重定时/移 tap 类变更（触发"重定时消费者审计"维度时）要求编写最小对拍 TB——新旧 RTL 同激励差分比较关键事件序列（检测/装载/find）——此类 TB 是评审证据的一部分，允许且推荐执行，不属于 case 仿真。
- **静态"相对几何保持"推演不得作为重定时变更的 pass 依据**：此类变更在无对拍等价证据时不得 pass（即使 critical==0）。历史上静态推演两次误判"几何保持"而实际掩蔽接受集已变（2026-09-29 SHORT 打一拍回归教训）。
- 问题被修复后，复审对应条目并更新报告，不要默认修复即正确。
- 找不到问题就如实说"未发现"，不要为凑数编造低风险项。
