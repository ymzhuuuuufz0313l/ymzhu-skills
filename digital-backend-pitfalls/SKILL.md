# digital-backend-pitfalls

数字后端经验与坑：cell 引用稳定性（post-route 探针/约束）、不同工具喂不同 SDC、ICG 复位机制与两大坑。适用于 PT/DC 脚本编写、skew/setup/hold 报表探针、跨代际约束维护、时钟门控设计。

## 触发词

探针失效、999 哨兵、cell 改名、write_sdc 找不到、SEL-005、No pin objects matched、PTE-139、set_sense、ICG、时钟门控、gating check、stop_propagation

---

## 一、Cell 引用稳定性：约束/探针写到"实例/引脚"，绝不带 cell 型号子层

PR 会给 cell 改名/拍平/换型号，"实例/cell型号/引脚"三段式路径 PR 后必断。

| 场景 | ✗ 不要 | ✓ 要 |
|---|---|---|
| 引用实例引脚 | `实例/CLKMUX2X2/S`、`实例/MUX2X2/O` | `实例/S`、`实例/O` |
| -from/-to 用钟 | 引用生成钟的 cell 子层 | `-from [get_clocks ...]`（钟对象可序列化、跨代际）|
| 探针挂钟结构 | 引 PR 自动插的 cell 子层 | 引 RTL 手动例化实例（`u_gate_*` 前缀，实例名跨代际稳定）|

**案例（HK1V11 2026-10）**：skew 探针 `u_gate_MUX_DPLC_CLK/MUX2X2/O` 失效——PR 把 cell 改名 `HK1V11_digital_top_CLKMUX2X2_2`、引脚拍平为裸 `O` → SEL-005 空报告 → 解析哨兵（$min=1000）→ csv 出现 −99x "999"行。修复：去 cell 型号段 → `u_gate_MUX_DPLC_CLK/O`。

**加固选项（按需）**：关键时钟结构（时钟 mux/ICG）RTL 手动例化（实例名稳定）+ `set_dont_touch [get_cells 实例]`——防 cell 改名/换型号/被优化，时钟结构代价≈0。数据路径普通单元禁止滥用。不防 RTL 层级本身重构。

**约束形态的工具识别矩阵（蓝路/红路，知乎·芯思维）**：一条 timing path 工具算两段时间——蓝色=数据路径（`-from DFF1/CK -to DFF2/D`），红色=capture 时钟路径（`-through M -to DFF2/CK`）。**DC/PT 两色都认；Innovus/ICC 只认蓝色（数据路径），红色（capture 时钟路径上的点，如 -through 钟 mux 腿的 pin）不认、照常分析**。后果=幻觉分裂：只看 PT 的以为 PR 也不修，实际 PR 在花大代价修（往钟腿塞延时单元）；只看 PR 的以为约束没生效。**规则：跨工具统一的豁免/约束一律写成蓝色形态（钟对象组、数据路径 -from/-to），禁止红色形态（-through capture 时钟腿上的 pin 点）**——PR/PT 分裂、约束失效两大事故的根源。蓝色难写时（CG 命名漂移）用"手动例化+dont_touch"稳定引用点。

---

## 二、不同工具喂不同 SDC：同一文件类型，吃它的工具不同，文件就要跟着变

一颗芯片必然存在多份 SDC——DC/ICC/Innovus/PT 对 SDC 的理解逻辑不同：

| 工具 | 对时钟约束的理解 | 对 SDC 的要求 |
|---|---|---|
| **DC（综合）** | 直观：自动穿透 mux、分频直接写 div；未被 set_case_analysis 选中的路径不分析 | 简单直观 |
| **ICC/Innovus（PR）** | 严苛：mux 输入须显式声明；只声明需要的 path——多声明会让 CTS 树加长；多 mux 共享 sel 时声明一点仍可能双路径都分析 | 更详细更具体 |
| **PT（签核）** | CTS 已结束，需**取消部分 case_analysis 让工具都分析**，否则 SDC 膨胀 | 与 PR 又不同 |

**write_sdc 序列化差异（HK1V11 实测）**：`set_sense` DC 的 write_sdc **不带**、PT 的 write_sdc **带**。跨 stage 想要的命令必须确认"目标 stage 读的文件里有它"（HK1V11 案例：post-PT 读 `design.set` 的 SDC_PATH 指向的 to_APR/latest 产物，而 set_sense 加在 ip_cons——post-PT 永远看不到；且 read_design.tcl 还指向过期的 0922 网表）。

推论：约束跨 stage 传递必须显式管理（stage 矩阵：每个 stage 读哪个文件、哪条命令能存活），不能默认一份 SDC 通吃。

---

## 三、ICG 复位机制与两大坑

ICG（集成时钟门控）本质 = 低电平敏感锁存器（抓 enable）+ 与门。**没有复位脚——靠输入时钟走到低电平来完成"复位"**。由此两个反直觉的坑（作者芯思维曾栽在坑①，靠 ECO 挽救）：

**坑 ①：输入钟停在 1 电平 → ICG 输出 X**
"使能关了输出就恒定"是错误理解——复位靠时钟低电平，钟停在 1 复不了位，输出不定态 → 下游全 X。
**HK1V11 场景**：`DPLC_CLK` 族只在 DPLC 模式翻转，非 DPLC 运行长期静止——确认其静态电平；任何"停钟"操作（set_case_analysis 锁模式、test/scan 停钟、set_sense 实验停传播）**先查被停钟网络下游 ICG 的停驻电平：停 0 安全，停 1 = X 灾难**。

**坑 ②：使能=0 也挡不住 ps 级毛刺 → 亚稳**
锁存器复位有 **recovery 要求**。使能=0 期间输入钟上 ps 级毛刺若违反 recovery，ICG 输出亚稳。
**这正是 PT clock gating check 在查的东西**（gating setup/hold，如本项目 G15 的门控 setup 1.0ns、DTCTL gating hold −5.08）——所以 **gating 检查不能用 clock_groups 断、不能随便 mc/waiver**，机理依据。
**HK1V11 场景**：时钟 mux（WCK1_ASEL 等）sel 切换瞬间的毛刺/短脉冲若混进下游 ICG 钟输入即触发坑 ②——本项目 mux 均为配置期静态切换（运行期不切）+ 切换发生在消隐期，风险被兜住；**"运行期不切"必须作为设计约束保持**。

---

## 详细案例存档（HK1V11 仓库）

CHANGES.md 2026-10-08/09 各条；`script/_audit_pt_report_tcl_k3.md`（pt_report 排除失败根因）；`script/_syn_1008_skew_说明.md`（999/哨兵/判读窗）；`script/_review_bkdu_sync_k3.md`/`_qwen.md`（BKDU_SYNC 评审，含 gating recovery 机理引用）；网站 ch11 §12（时钟豁免列表配对方法论）、ch18 §4.2（set_sense 闭环）。

---

<!-- ymzhu 2026-10-12 16:45 -->