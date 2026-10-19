---
name: xilinx-suite
description: Xilinx(AMD) FPGA/MPSoC 全工具链参考——Vivado XDC 约束、Tcl 命令、纯 FPGA 流程、综合实现与报告分析、CDC/时序例外。触发词："xdc"、"约束"、"vivado"、"tcl"、"fpga"、"时钟域"、"false_path"、"multicycle"、"create_clock"、"set_property"、"set_clock_groups"、"set_max_delay"、"report_timing"、"report_cdc"、"report_clock_interaction"、"综合"、"实现"、"比特流"、"ILA"、"VU440"、"ultrascale"、"versal"、"zynq"。适用于 HK1V11（VU440 FPGA XDC），可推广到同族 UltraScale+/UltraScale/7 系列与 MPSoC。
---

# Xilinx 全工具链 Skill（DSH 版）

> Xilinx(AMD) FPGA/MPSoC 设计参考手册。源自 QingquanYao/xilinx-skill（MIT），按 DSH + HK1V11（VU440 FPGA XDC）场景改编；`references/` 为原始参考文档库。
> **核心原则**：① XDC 约束顺序 **时钟定义 → IO 约束 → 时序例外**，缺一不可；② 判定约束"生效/冲突/丢失"只看**落地证据链**（read_cons.log 的 SEL-004、report_exceptions.rpt 的 applied 标志、report_timing 的 capture 边沿数），**不看源码猜**。

## 0. 参考文档路由（按需加载）

| 任务 | 加载参考 |
|---|---|
| IO 引脚 / 时序约束 / XDC 语法 | `references/xdc_constraints.md`（与 `xdc_guide.md` 同内容）|
| Vivado Tcl 命令 / 报告命令 | `references/tcl_commands.md` |
| 纯 FPGA（无 PS）工程流程、SLR、GT 时钟 | `references/vu9p_guide.md` |
| Block Design / PS 配置（MPSoC）| `references/vivado_guide.md` + `references/mpsoc_ps_config.md` |
| JESD204B→C 高速串行迁移 | `references/jesd204b_to_c_migration.md` |
| 官方文档编号（UG/PG/DS/XAPP）| `references/official-docs/index.md` |

> 生成任何脚本 / 约束前**先读对应参考文件**，不要凭记忆写 Tcl/XDC（不同 Vivado 版本 API 有差异）。

## 1. XDC 约束要点（核心）

约束顺序：**时钟 → IO → 时序例外**。完整语法见 `references/xdc_constraints.md`。

- **主时钟**：`create_clock -period <ns> -name <clk> [get_ports <pin>]`；差分只约束正端（`_p`，`_n` 自动关联）。
- **生成时钟**：`create_generated_clock -source [get_pins ...] -multiply_by/-divide_by N [get_pins ...]`；Clock Wizard IP 通常已自动约束，检查报告避免重复定义。
- **IO**：`set_property PACKAGE_PIN <pin>` + `set_property IOSTANDARD <std>`（**必须同时设**）；同 Bank 电平组统一（VCCIO），混用报 DRC。
- **输入/输出延迟**：`set_input_delay/-output_delay -clock <clk> -max/-min <ns> [get_ports ...]`（与外部芯片通信时用）。
- **false path**：`set_false_path -from [get_clocks A] -to [get_clocks B]`（异步对要双向）。
- **异步时钟组**（更清晰，推荐）：`set_clock_groups -asynchronous -group [get_clocks A] -group [get_clocks B]`。
- **multicycle**：`set_multicycle_path -setup 2 -from ... -to ...` **必须配对** `set_multicycle_path -hold 1 ...`（否则 hold 过严）。
- **max delay（CDC 同步器）**：`set_max_delay -datapath_only <ns> -from <src_ff> -to <sync_ff1>`。
- **综合后**：`report_clock_interaction` 检查所有 CDC 路径是否都有约束。

## 2. 纯 FPGA 流程（VU440 / UltraScale+ 同族）

详见 `references/vu9p_guide.md`：`create_project -part <part>` → `add_files`（HDL + IP）→ `add_files -fileset constrs_1 <xdc>` → `set_property top <top>` → `launch_runs synth_1 -jobs N` / `launch_runs impl_1 -to_step write_bitstream`。**无 BD、不导 XSA**，直接用 `.bit`。
- SLR 跨区时序（大器件）：`set_property USER_SLR_ASSIGNMENT SLRn [get_cells ...]` + 实现策略 `Performance_ExplorePostRoutePhysOpt`。
- GT 收发器 / PCIe 硬核时钟：引脚由 IP 自动约束，一般不手写 IOSTANDARD。

## 3. Tcl 命令速查

详见 `references/tcl_commands.md`：工程管理 / 文件管理 / 综合实现（`synth_design`/`place_design`/`route_design`/`write_bitstream` + `-directive` 选项）/ 报告（`report_timing_summary`/`report_timing`/`report_clock_interaction`/`report_cdc`/`report_drc`/`report_power`/`report_io`）/ 调试（ILA/VIO）/ 查询（`get_cells`/`get_pins`/`report_property`）。

## 4. HK1V11 项目集成（VU440 FPGA XDC 场景）

本 skill 在 HK1V11 主要用于 **FPGA XDC 约束（七月基线 → 当前版本 delta）+ 约束生效验证**，配合项目既有纪律：

### 4.1 XDC delta 工作流
1. 先读项目 `HK1V11_HDL_analysis_*.md`（顶层端口 / 时钟域 / CDC 异步对清单，§10 delta 核对项）。
2. 对照七月基线 XDC 逐条核对：`create_clock`（含 `clk_lane` 这种**数据脚当时钟**——来自 `VU440_FPGA_RX_BUS_I[201]`）/ 输出时钟（`WCK_fpga`）/ `false_path` / `max_delay` / 新增删端口 / pin 分配 / ILA 探针。
3. 三模型（GLM-5.3 / Qwen / Kimi K3）各自独立产出 → 交叉验证仲裁出最终版（模型路由见 `subagent-dispatch`；Qwen 256K 只给目标+文件路径让它自读）。

### 4.2 约束生效判定纪律（铁律，不看源码猜）
判定"生效 / 冲突 / 丢失"只看落地证据链：
- ① `read_cons.log` 的 `SEL-004` 警告与落地产物形态；
- ② `report_exceptions.rpt` 的 applied 标志（o=被覆盖 / p=路径不存在 / po）；
- ③ `report_timing` 的 capture 边沿数。
"两条约束冲突"看落地后对象集合是否相交；"N 条路径靠 mc 活着"必须核对 startpoint 是否真被 pattern 匹配（0922 曾把 D1/SHORT 分支路径误归给 G13）。

### 4.3 跨网表（DC→APR）纪律
- `-from <寄存器>` 被 write_sdc 落成 /CK 脚（稳定）；`-to <寄存器>` 落成数据脚——DC 普通 DFF=/D、AND2DFFRBQX=/D1+/D2，APR 网表常为 /D → **SEL-004 静默丢弃**（UTC_FRM_CNT −0.369、G9 各踩过）。
- 规则：`-to` 用时钟对象；层级 `-to X/*` 会罩内部节点（max_delay 伪违例 −3.8 教训），`/*/D*` 才是寄存器 D 脚；**from-only（无 -to）= 全端点无边界放宽，B 类位禁用**；**新造时钟必须加进 false_path / 异步豁免清单**（CDR_2X hold −1.67 假违例教训）。

### 4.4 工具命名
- dc_shell elaborate 阶段触发器名是 `reg[n]` 方括号，映射后网表才是 `_reg_n_` 下划线——ip_cons 跨工具 pattern 用 `reg*`（不带下划线）两种通吃；**bit-exact 精确名只放 pt_shell 分支**（否则 DC 报 CMD-036 Can't find objects）。`R_REG48_F_reg*` 这类"前缀+reg*"两种通吃。

### 4.5 与其他 skill / 数据率口径
- 服务器包 ip_cons 覆盖 → 走 `server-pack-overlay`（diff 逐条评估同不同意才采纳，clk_period.tcl 保持 pristine）。
- 信号 / CDC 静态追踪 → `rtl-signal-trace`；RTL 对抗评审 → `rtl-code-review`。
- **数据率口径**：`data_rate(G) = RX_CLK(MHz) × 20 / 1000`（20bit RX 通路，LINK_LOGIC.v INDATA[19:0]，非颜色深度），**不乘 1.05**（1.05 是 2M23 clk_period.tcl 的 STA 周期 5% margin，是设计约束约定，非数据率↔时钟物理因子）。
- RTL 注释一律英文（文档/CHANGES 仍中文）；`.xdc`/`.tcl` 文末签名 `# ymzhu YYYY-MM-DD HH:MM`（实际时间），`.md` 用 `<!-- ymzhu ... -->`。

## 5. 常见陷阱
1. `[get_ports xxx]` 返回空 → 顶层端口名大小写 / 拼写与 HDL 不一致。
2. 同 Bank 混用 IOSTANDARD → DRC 报错，查 VCCIO 设计。
3. multicycle setup 不配 hold → hold 过严假违例。
4. 生成时钟重复定义（Clock Wizard 已自动生成）。
5. **数据脚当时钟（clk_lane）漏 create_clock** → 该域无时钟、路径全 unconstrained。
6. **新时钟没进 false_path / 异步豁免** → 跨域假违例。

<!-- ymzhu 2026-10-16 15:34 -->
