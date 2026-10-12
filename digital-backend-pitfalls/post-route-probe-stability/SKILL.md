# post-route-probe-stability

post-route 网表下 STA 约束/报表探针的引用稳定性规则与案例。适用于 PT/DC 脚本编写、skew/setup/hold 报表探针、跨代际约束维护。

## 触发词

探针失效、999 哨兵、cell 改名、write_sdc 找不到、约束引用 cell 名、SEL-005、No pin objects matched、PTE-139

## 原理背景：为什么 DC/PR/PT 要喂不同的 SDC（同一文件类型，工具不同文件就要变）

每个工具对 SDC 的理解逻辑不同（知乎·芯思维）：
- **DC**：直观理解时钟树，自动穿透 mux/分频；未 set_case_analysis 选中的路径不分析 → 综合 SDC 简单
- **ICC/Innovus**：理解严苛，mux 输入须显式声明，只声明需要的 path（多声明会让 CTS 树加长；多 mux 共享 sel 时声明一点仍可能双路径都分析）→ 后端 SDC 更详细
- **PT**：CTS 已结束，需**取消部分 case_analysis 让工具都分析**，否则 SDC 膨胀
- **write_sdc 序列化差异**：同一条命令不同工具的 write_sdc 行为不同（HK1V11 实测：set_sense DC 的 write_sdc 不带、PT 的带）
推论：一颗芯片必然存在多份 SDC；约束跨 stage 传递必须显式管理（哪个 stage 读哪个文件、哪条命令能存活），不能默认一份通吃。

---

## 三条铁律

1. **约束/探针引用一律写到"实例/引脚"为止，绝不引用 cell 型号子层。**
   ✗ `实例/CLKMUX2X2/S`、`实例/MUX2X2/O`（PR 会给 cell 改名/拍平，子层必断）
   ✓ `实例/S`、`实例/O`
2. **tcl 报表/约束改动必须真实 pre-PT/post-PT 重跑验证后才算完成**，纸面语法推演不可上服务器。
3. **DC 与 PT 行为差异必须分别实测**（如 set_sense 进不进 write_sdc：DC 不带、PT 带），不许从一个工具推断另一个。

## 症状 → 根因速查

| 症状 | 根因 |
|---|---|
| `SEL-005 Nothing matched` / 空报告 / 报表体积骤减（如 60KB→0.05KB）| 探针 pattern 匹配 0 对象——多为 cell 子层/旧引脚名失效 |
| csv 出现哨兵值（解析脚本 $max=0/$min=1000 类 → margin −99x/+4x）| **哨兵是"探针失效报警"，不是时序数据**，勿当真实 margin 判读 |
| SDC 里找不到某命令（如 set_sense）| 该命令不被 write_sdc 序列化，或 read 链读的是旧文件——先查 design.set 的 SDC_PATH 与 read_design.tcl 指向 |
| 命令返回 1 + `PTE-139 Invalidating logical update` | 命令已生效；**必须 update_timing 后再读报表** |
| 回滚/恢复脚本后工具跑不起来 | 查文件编码（PowerShell `>` 重定向会写 UTF-16LE BOM，PT/DC 不认）|

## 写法对照表

| 场景 | ✗ 不要 | ✓ 要 |
|---|---|---|
| 引用实例引脚 | `实例/CELL型号/引脚` | `实例/引脚` |
| -from/-to 用钟 | 引用生成钟的 cell 子层 | `-from [get_clocks ...]`（钟对象可序列化、跨代际）|
| set_sense 持久化 | 裸行放被 DC 也 source 的 tcl | `if {$synopsys_program_name == "pt_shell"} { ... }` 守卫（DC 分支省略并写明理由）|
| 寄存器 pattern | DC 方括号名 / PT 下划线名硬编码 | `reg*` 前缀通吃（两种形态通吃）|
| 探针挂钟结构 | 引 PR 自动插的 cell 子层 | 引 RTL 手动例化实例（`u_gate_*` 前缀）|

## 关键案例（HK1V11 2026-10）

**① skew 探针 999 哨兵**
探针 `u_gate_MUX_DPLC_CLK/MUX2X2/O`——PR 把 cell 改名 `HK1V11_digital_top_CLKMUX2X2_2`、引脚拍平为裸 `O` → SEL-005 空报告（0.05KB）→ 解析脚本哨兵（$min=1000）→ csv 出现 −99x "999"行。
修复：去 cell 型号段 → `u_gate_MUX_DPLC_CLK/O`。

**② set_sense 路径失配与持久化**
`.../u_gate_MUX_WCK1_ASEL/CLKMUX2X2/S` 在 post-route 网表存在且 pt_shell 实测生效（返回 1+PTE-139）——**同一网表内不同实例层级形态可并存**（另一实例已拍平），路径必须按各自网表实核。持久化：放 `pt_shell` 守卫内（DC 分支省略——dc_shell 的 set_sense 为 DFT 导向命令、行为未验证），write_sdc 会带（PT 版）。

**③ 报表脚本排除失败回滚**
`pt_report.tcl` 用 `remove_from_collection` + `report_clock_timing -clock` 过滤钟名单——纸面推演正确、真实 run 失败已回滚。教训见铁律 2；根因分析存档于审计报告。

## 加固选项（按需）

关键时钟结构（时钟 mux/ICG）RTL 手动例化（`u_gate_*` 前缀）+ `set_dont_touch [get_cells 实例]`：防 cell 改名/换型号/被优化，时钟结构代价≈0。数据路径普通单元禁止滥用。不防 RTL 层级本身重构（结构性重构仍需人工同步探针）。

## 详细案例存档（HK1V11 仓库）

CHANGES.md 2026-10-08/09 各条、`script/_audit_pt_report_tcl_k3.md`、`script/_syn_1008_skew_说明.md`、`script/_review_bkdu_sync_*.md`。

---

<!-- ymzhu 2026-10-12 15:45 -->
