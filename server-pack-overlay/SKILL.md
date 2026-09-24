---
name: server-pack-overlay
description: 服务器回传压缩包（PACK_TAR_xxx.tar.gz）搬回本机的提取与合并式覆盖规则。触发词："服务器包"、"PACK_TAR"、"回传包"、"解压覆盖"、"同步服务器包"、"搬回本机"。适用于 HK1V11（可推广到同结构项目）：SYNTHESIS/HDL/DV_TCON_C 三类包的合并口径。
---

# 服务器回传包提取与合并式覆盖规则

> 从服务器搬回本机的三类包（SYNTHESIS / RTL-HDL / DV_TCON_C）处理手册。沉淀自 0921V3/V4/V5、0920 系列与 0923 规则修订。
> **核心原则：合并式覆盖——同名文件覆盖、新增文件添加、本地独有文件保留；禁止暴力文件夹整替**（本地可能有只在本机用的脚本，整替会误删）。个别敏感对象（约束/公共时钟文件）先评估再动。

## 0. 包定位与目录映射

1. 压缩包通常在 `C:\Users\zhuyanming\Downloads\`，不在项目根——先找到。
2. **编号与内容的对应以包内实际路径自证**（解开后看包内是 `SYNTHESIS/`、`HDL/` 还是 `DV_TCON_C/`），不要凭编号顺序猜。
3. 解压目标（历史惯例命名，放 `E:\project\HK1V11\script\` 下）：
   - SYNTHESIS → `script\_syn_<ver>\`（如 `_syn_0924v2`）
   - RTL/HDL → `script\_rtl_<ver>\`
   - DV_TCON_C → `script\_dv_<ver>\`
4. 确认 `.gitignore` 已忽略这些解压目录（不进 git；缺则补一行）。
5. **解压/覆盖前先 `git status` 快照**，确认起点干净。

## 1. 解压规则

- 包内路径带 `../../../` 前缀、含 `::` 等非法字符、超长路径 → **Windows tar 解不了，用 python tarfile 剥离 `../` 解出**。
- 无法解析的 symlink（指向包外/他人目录）跳过并记录，不强解。
- 包实际位置常在 Downloads，包内结构形如 `XXW_PRJ01/HK1V11/designer/<组>/<人>/HK1V11/...`。

## 2. SYNTHESIS 包

合并式覆盖，量大可用 robocopy（排除 gitignore 的解压目录）：

| 对象 | 动作 |
|---|---|
| `top/sta/` 各 corner `latest/` 报告（log/rpt/summary/run_summary）、`sdc_pr/`、rpt/sdc 类产物 | **覆盖**（服务器 run 产物同步的正主；可先评估再覆盖，一般不必问） |
| 服务器改过的脚本（pt_setup.tcl / read_design.tcl / run_pt / design.set / deploy 脚本） | **先 diff，有差异才覆盖**，并记录差异内容 |
| `SYNTHESIS\common\ip_cons\<top>.tcl` | **先 diff 约束差异，逐条评估同不同意——同意的采纳（覆盖/合并进本地），不同意的保留本地并写明理由**。同时判定服务器 run 吃到的约束版本（找本代标记：`cpuwr_reg_grp`、10 分区排除清单、`-to RX_CLK` 的 UTC 行、`U_DPLC_DATA_GEN/*/D*`），用于解读这批报表 |
| `common\clk_period.tcl` | **不动**（要求 pristine），有变化只汇报 |

覆盖后必出的验证数字（确认上一轮修复是否被服务器吃到）：
1. setup/hold 各 corner 总数与 worst（`summary/latest/report_setup.csv` / `report_hold.csv` 的 setup.rpt / hold.rpt 行）
2. `read_cons.log` 搜 `SEL-004` 计数、搜 `/D1` `/D2` 计数（已知遗留项是否仍丢）
3. `report_exceptions.rpt` 关键 applied 行（如 `* RX_CLK cycles=2(start)`）在不在
4. 违例 startpoint 分布：近期排除/注释的分区**回单周期后冒不冒新违例**（收窄/注释修改后最关心的一笔）

覆盖后 git：只 `git add SYNTHESIS`（解压目录靠 gitignore），commit 注明"<ver> 服务器 run 产物同步"，push（失败先 `git config http.version HTTP/1.1` + `git config http.postBuffer 524288000` 再重试）。

## 3. RTL（HDL）包

**合并式覆盖到本地 `HDL\`**：同名文件覆盖、新增文件添加、**本地独有文件保留**（可能是只在本机用的脚本/配置，禁止整目录替换误删）。

- 同名文件：diff 后逐个覆盖（重点看近期改动模块：LONG_ENCODING_ALIGN / SHORT_ENCODING_OUTPUT / SHORT_ENCODING_ALIGN 等）。
- 新增文件：直接添加进 `HDL\`；若影响 file_list，同步更新 `.f`。
- 本地独有文件：保留，列出清单说明。
- 仍写 `README_中间版本说明.md`（快照来源 + diff 摘要 + 采纳/保留决策），文末签名。
- RTL 功能性修改采纳后走 RTL 三关（iverilog → rtl-code-review → rtl-signal-trace）+ 修改记录双轨；版本头按 version-archive 规则更新。

## 4. DV_TCON_C 包

**合并式覆盖到本地 `DV_TCON_C\`**：同名 case/env/checker 文件覆盖、新增 case 添加、本地独有文件保留。

- **ppm 等大仿真文件不会随包下载**：在解压目录对应位置用 `mklink /J`（junction，不需管理员）链到本地现有 ppm 文件夹（如 `DV_TCON_C\top\tests\ppm_mix_*`）；路径结构不明确就写 `PPM_链接说明.md` 说明缺什么、链到哪。
- diff 清单照常产出留档（覆盖了什么/新增了什么/本地独有什么），但**不必停下来等确认**——按合并规则直接执行，汇报里带清单。
- env/checker 类差异若涉及 cfg_frame 解析，注意 `%b` 二进制口径一致性。

## 5. 通用纪律

- 所有说明类 md 文末签名 `<!-- ymzhu YYYY-MM-DD HH:MM -->`（实际时间）。
- **汇报模板**：① 各包解压到哪、覆盖/新增/保留文件数；② SYNTHESIS 验证数字（SEL-004 / D1D2 / exceptions 关键行 / setup+hold 总账）；③ 服务器约束版本判定（吃到哪一代修复）；④ RTL/DV 合并摘要（覆盖/新增/保留各多少）；⑤ commit hash 与 push 结果。
- 时间线意识：服务器 run 的时间戳可能**早于本地最新约束修改**——汇报时明确"服务器吃到了哪一代，哪些没吃到"。
