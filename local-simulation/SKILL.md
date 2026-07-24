---
name: local-simulation
description: 当用户想用 Windows 本机开源工具链（Icarus Verilog + GTKWave / Yosys）跑 Verilog/SystemVerilog 模块、不依赖 VCS/UVM/cmodel 时触发。触发词包括“本机仿真”、“本地仿真”、“用 iverilog 跑”、“用开源工具跑 case”、“本地验证”、“不用 VCS 跑”、“通用本机仿真方案”。
---

# Local Simulation Workflow（本机仿真方案）

本 Skill 提供一套通用流程：在 Windows 本地用开源工具链（Icarus Verilog + GTKWave，可选 Yosys）跑通原本依赖 VCS/UVM/cmodel 的 Verilog/SystemVerilog 模块或 case。

## 1. 什么时候用这个流程

- 本地没有 VCS/Questa，只有 Icarus Verilog
- 原 case 依赖 UVM、Linux cmodel 或完整 DUT（含模拟/IO/STD 库），无法直接跑
- 只想快速验证某个模块的功能行为，不需要跑完整 SOC/case
- 想生成 VCD 用 GTKWave 看波形
- 想用 Yosys 对独立模块做快速综合/网表分析

## 2. 核心原则

1. **缩小范围**：只抽取目标模块，不要跑完整 DUT。
2. **剥离 UVM**：把 sequence/driver/monitor 的激励逻辑改写成纯 Verilog `task`/`initial`。
3. **替换 cmodel**：Linux 二进制在 Windows 跑不了，用手写固定 pattern、预生成数据文件或直接跳过。
4. **补齐依赖**：给 foundry 专用单元（如 `CLKINVX4AL9`）提供行为级 stub。
5. **直接驱动端口**：testbench 直接驱动 DUT 端口，不再通过 virtual interface/UVM config_db。
6. **文档跟项目走**：所有记录放在**当前工作目录**下的 `本地仿真方案/` 或 `local_sim/` 文件夹，不指定固定绝对路径。
7. **真实验证，不隐瞒错误**：本机仿真的目的是验证 HDL code 对不对。如果结果 FAIL，必须如实报告；不能为了让仿真“跑通”而修改 DUT 来迎合 testbench，也不能掩盖或粉饰错误。只有在明确确认是 DUT bug 时，才可以修改 HDL。

## 3. 前置检查：工具链是否已安装

在每次触发本 Skill 时，先检查以下工具是否已安装：

```powershell
iverilog -V
yosys -V
gtkwave --version
```

如果任意一个命令报错或找不到，**必须立即停止**，并明确告知用户：

> 本机仿真需要以下工具，但当前环境缺少：{列出缺失工具}。  
> 请先安装：Icarus Verilog、Yosys、GTKWave，然后再继续。

只有三个工具都可用时，才进入改造步骤。

## 4. 通用改造步骤

### 步骤 1：确定核心模块

问自己：这个 case 到底在验证什么？

- 例：某个 checksum case 的核心是 `LC_CPUWR` 的 Seg1 checksum 逻辑。
- 不要试图跑完整 DUT + PHY + 外部接口 + cmodel。

### 步骤 2：创建独立 sandbox 目录

在当前工作目录下创建：

```powershell
New-Item -ItemType Directory -Path .\本地仿真方案\rtl -Force
New-Item -ItemType Directory -Path .\本地仿真方案\tb -Force
New-Item -ItemType Directory -Path .\本地仿真方案\sim -Force
New-Item -ItemType Directory -Path .\本地仿真方案\wave -Force
New-Item -ItemType Directory -Path .\本地仿真方案\ref -Force
```

> 如果当前目录已有项目上下文（如 HK1V11），也可以命名为 `local_sim/` 或 `<feature>_sim/`，以不冲突为准。

### 步骤 3：复制目标模块和依赖

从当前工作目录的 HDL 源码树复制需要的模块。例如：

```powershell
Copy-Item .\HDL\HK1V11_digital_top\HDL_define.v .\本地仿真方案\rtl\HDL_define.v
Copy-Item .\HDL\HK1V11_digital_top\seperated_code\LC_CPUWR.v .\本地仿真方案\rtl\LC_CPUWR.v
```

### 步骤 4：补齐 foundry 单元 stub

如果模块实例化了专用单元（如 ECO placeholder），创建 `rtl/dummy_cells.v`：

```verilog
module CLKINVX4AL9 (input I, output O);
    assign O = ~I;
endmodule
```

### 步骤 5：加 `timescale`

在 filelist 第一个文件（如 `HDL_define.v`）顶部加：

```verilog
`timescale 1ns / 1ps
```

### 步骤 6：剥离 UVM，编写 testbench

- 用 `module tb_top` 替代 UVM test
- 用 `initial` 产生复位和时钟
- 用 `task` 封装激励序列
- 用 `$dumpfile` / `$dumpvars` 生成 VCD
- 用层次引用访问内部信号（如 `u_dut.shadow_06_F`）

### 步骤 7：替换 cmodel

根据场景选择：

- 手写固定 pattern（如递增数据、color bar）
- Python 预生成 `.txt` / `.hex`，testbench 用 `$fopen` / `$fscanf` 读取
- 只验证控制帧/寄存器，跳过图像数据

### 步骤 8：创建 filelist 并编译

`本地仿真方案/rtl/filelist.f`：

```text
rtl/HDL_define.v
rtl/LC_CPUWR.v
rtl/dummy_cells.v
tb/tb_top.v
```

编译：

```powershell
cd .\本地仿真方案
iverilog -g2012 -DCHKSUM_A_EN -c rtl\filelist.f -o sim\tb.out
```

常用选项：
- `-g2012`：SystemVerilog-2012
- `-D<MACRO>`：定义宏
- `-c filelist.f`：从 filelist 读文件列表
- `-o`：指定输出

### 步骤 9：运行并调试

```powershell
vvp sim\tb.out
```

常见问题：
- `Unknown module type` → 补 stub
- `uvm_macros.svh not found` → UVM 没剥离干净
- `timescale warning` → 加 `timescale`
- 端口不存在/位宽不匹配 → 对照 DUT 端口声明

### 步骤 10：查看波形

```powershell
gtkwave wave\tb.vcd wave\tb.gtkw
```

## 5. 输出要求

完成改造后，向用户汇报：

1. sandbox 目录位置（当前工作目录下的 `本地仿真方案/`）
2. 核心验证模块
3. 编译/运行命令
4. **结果摘要（必须如实）**：明确给出 PASS 或 FAIL，列出关键信号观测、错误数量和具体错误。如果 FAIL，要说明失败原因和排查方向，不能隐瞒或美化。
5. 记录文档放在当前目录的 `本地仿真方案/README.md` 和 `本地仿真方案/CHANGELOG.md`

## 6. 参考案例

已跑通案例：HK1V11 项目 `t_8b1lane_checksum_pwrc_n2_longtest` 的 checksum 核心链路。

- 参考 Sandbox：`E:\sandbox_t_8b1lane`
- 参考文档：`E:\project\HK1V11\本机仿真方案\通用本机仿真方案.md`
- 参考工具链指南：`E:\project\HK1V11\本机仿真方案\HK1V11_open_source_toolflow.md`
- 参考示例脚本：`E:\project\HK1V11\本机仿真方案\examples\run_iverilog.bat`

> 以上路径仅作为参考示例，通用流程中应把 `本地仿真方案/` 放在当前工作目录下。

## 7. 如何交付给同事

本 Skill 以单个 Markdown 文件形式存在，交付时只需让同事把 `SKILL.md` 放到对应目录即可：

```text
Windows:
  C:\Users\<用户名>\.config\opencode\skills\local-simulation\SKILL.md
  C:\Users\<用户名>\.claude\skills\local-simulation\SKILL.md
```

交付步骤：

1. 复制你本地以下两个文件：
   - `C:\Users\zhuyanming\.config\opencode\skills\local-simulation\SKILL.md`
   - `C:\Users\zhuyanming\.claude\skills\local-simulation\SKILL.md`
2. 打包或发到共享盘。
3. 同事收到后，在各自机器上创建 `local-simulation/` 目录，放到上述路径。
4. 重启 OpenCode/Claude 客户端，或重新加载 skills 后即可生效。

注意：
- 不需要把项目文档库（如 `E:\project\HK1V11\本机仿真方案`）一起交付，因为通用流程会在同事当前工作目录自动生成。
- 如果同事的 OpenCode 只读取 `~/.config/opencode/skills/`，则只需放一份；如果同时用 Claude，两份都放。

## 8. 注意事项

- 本机仿真只能验证**功能行为**，不能替代 VCS 的完整 case 回归、覆盖率、SDF 后仿等。
- **验证的目的是找 bug，不是跑通**。如果仿真结果与预期不符，必须如实报告；不能通过改 DUT 来“凑”结果，也不能删除检查项来让仿真看起来通过。
- 如果目标模块依赖大量标准单元或模拟宏，需要更多 stub 工作或无法直接剥离。
- 每次改造后，把步骤和坑记录到当前目录 `本地仿真方案/` 下的 Markdown，方便后续复用。
- 不要把记录文件写死到某个绝对路径（如 `E:\project\HK1V11\...`），要跟当前项目走。
