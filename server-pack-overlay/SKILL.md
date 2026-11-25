---
name: server-pack-overlay
description: 服务器回传压缩包（PACK_TAR_xxx.tar.gz）搬回本机的提取与合并式覆盖规则。触发词："服务器包"、"PACK_TAR"、"回传包"、"解压覆盖"、"同步服务器包"、"搬回本机"。适用于 HK1V11（可推广到同结构项目）：SYNTHESIS/HDL/DV_TCON_C 三类包的合并口径。
---

# 服务器回传包提取与合并式覆盖规则

> 从服务器搬回本机的三类包（SYNTHESIS / RTL-HDL / DV_TCON_C）处理手册。沉淀自 0921V3/V4/V5、0920 系列与 2026-09-23 规则修订、2026-11-05 diff-first 修订（1105 事故：1028 包 BIT_SWAP 补丁漏采 → KCODE 找不到）、2026-11-17 whole_session 硬规则（永不覆盖永不入库）与 Downloads 预解压形态说明。
> **核心原则：合并式覆盖——同名文件覆盖、新增文件添加、本地独有文件保留；禁止暴力文件夹整替**（本地可能有只在本机用的脚本，整替会误删）。
> **diff-first（2026-11-05 起强制）：覆盖哪些文件由人拍板，agent 只跑脚本、报全集、执行批准清单，不得自行取舍。**
> **覆盖后必过 overlay 校验（2026-11-16 起）：`pack_diff.py --apply` 只保证"没多覆盖"，不保证"没漏提交"。提交前后各跑一次 `script/gates/overlay_check.py`，A/D/R 一律 FAIL，详见 §0B。**
> **交付级 = L0/L1（见 hk1v11-delivery-gate）：包 overlay 不跑 L2 对抗评审、不跑 L3 信号追踪，也不生成 REVIEW.md；但签名 + CHANGES + 提交且推送三条不可省。**

## 0A. diff-first 强制流程（v2，2026-11-05 起取代"agent 自行选文件"）

> **只报不同，不分析原因（2026-11-23 ymzhu 指令；优先级高于本节其余条目与一切旧习惯）**：回传包的 diff-first 只回答两件事——**哪里不同**（`diff`：文件 + 首 hunk）、**哪里新增**（`pack_only`）。**不做**「为什么不同 / 是不是回归 / 谁新谁旧 / 功能影响 / 该不该覆盖」的分析，不预判、不给覆盖建议。用户看过清单、**明确要求分析之后才分析**。用户一句话拍板（如「新增/变更无条件入库」「功能没问题就直接覆盖」）= 批准完成，直接走第 4~5 步并提交推送，**中途不再插入核对数字、验证报告等额外环节**。用户只点名某个文件问「功能有没有问题」时，只回答那个文件。

1. **回传包落地后第一动作**：跑 `python ~/.dsh/skills/server-pack-overlay/pack_diff.py <pack.tar.gz> --out <report.md>`
   （脚本随 skill 分发、进 ymzhu-skills 仓库，**skill 版为准**；HK1V11 项目内 `script/pack_diff.py` 为同步副本，改 skill 版后必须覆盖过去。2026-11-17 核对并同步：HK1V11 项目副本已与 skill 正本一致（补齐 `--root` 参数）；比对其它项目（如 HV1V22A1）前仍先核对版本，落后即用 skill 正本覆盖过去）
   - **DV_TCON_C / HDL(RTL) / SYNTHESIS 三类包通用**（自动识别 `../../../project/.../<AREA>/` 与顶层 `<AREA>/` 两种布局）；他人区布局用 `--map VERIFICATION=DV_TCON_C` 映射；只比对部分区用 `--areas HDL,SYNTHESIS`；>4MB 大文件自动 md5-only（SYNTHESIS 大 rpt 保护）；local 侧用 `git ls-files` 枚举（天然排除 gitignore 解压产物噪音）
   - 全量 md5 比对（不依赖 mtime、不抽样、不排除目录），产出五桶全集：`identical / eol_only / diff / pack_only / local_only`
   - 每个 diff 附：包/本地大小、本地 git 最后提交、首 hunk 摘要、建议标签（`LOG-JUNK`/`PRISTINE`/`IPCONS`/`REGGEN`——**仅提示，无约束力**）
2. **反馈**：把报告完整交给用户（diff 桶逐文件、其余桶可汇总计数+清单）。**不做任何"这个该覆盖/那个不该"的替用户决定**——历史教训：1028 overlay 的 changed-list 不完整，isptx_driver.sv 的 BIT_SWAP 分支与 boe_test/user_def.sv 的 `define BIT_SWAP` 双双漏采，本地一直缺补丁，直接引发 KCODE 找不到排查。
3. **拍板**：用户逐文件/逐类批准 → 批准路径写入 `approved.txt`（含 `REGGEN` 类时提醒"覆盖生成物 ≠ 重新生成，寄存器类 env_cfg 建议走 update_env_cfg.py 重生成"即可，仍由用户定）。
4. **执行**：`python pack_diff.py <pack.tar.gz> --apply approved.txt` → 机械覆盖、仅覆盖批准项，产出 `<approved>.applied.txt` 落地清单。
   - **批准清单从报告机械生成，不手敲、不逐个看**：`diff` 桶每条 = `### <路径>` + 可选「空白+反引号」标签（标签有无两种形态，按正则 `\s+`` 切，**不要按两个反引号切**——2026-11-23 因此漏了 322 条带 `LOG-JUNK` 标签的条目）；`pack_only` 桶每条 = `- <路径> (<字节数>B)`。「无条件入库」= `diff` ∪ `pack_only` 再去掉 `whole_session`。
   - 落地后先对账：`覆盖 + 跳过 + 未命中 == 清单条数`；对不上就是清单解析错了，补跑差额（`--apply` 幂等）。
   - 含 `::` 等 Windows 非法名的路径会被 `--apply` 记入 `<approved>.skipped.txt`（物理无法落地），汇报条数即可。
5. **记录**：applied 清单进 `修改记录/CHANGES.md` + 中间版本说明，条目里写明交付级 `L0/L1`；RTL 三关仍不适用于包覆盖。
6. 大包（数百 MB）跑 pack_diff 用后台任务执行，避免前台超时中断。

## 0B. 覆盖后的 overlay 校验与提交自检（2026-11-16 起强制）

**为什么要有这一节**：`pack_diff.py --apply` 保证的是"没多覆盖"（批准清单之外一个字节不动），它**不保证"没漏提交"**。1113 三轮包（V1/V2/V3）覆盖后手工 `git add` 只加了部分路径，`TOP/HK1V11_digital_top.v` 等漏加，commit 里少文件、push 之后服务器拿到的还是旧版——排查了半天才发现是本地漏提交，不是推送失败。

1. **覆盖前打 baseline**（本包范围内须干净；范围外的脏文件只告警不拦——2026-11-23 起）：
   ```bash
   python script/gates/overlay_check.py pre --package SYNTHESIS   # 或 HDL / DV_TCON_C
   ```
   写出 `script/gates/overlay_baseline.json`（commit + 范围 + 文件树快照）。
2. **覆盖后复核**：`--paths` 给实际覆盖的目录/文件
   ```bash
   python script/gates/overlay_check.py post --package SYNTHESIS --paths SYNTHESIS/
   ```
   校验口径：
   - 与 baseline 比对，**D/R（删除 / 改名）一律 FAIL；新增（已 `git add` 的 A，以及范围内尚未 `git add` 的未跟踪新文件）必须在 `--approved-adds <清单>` 内**——清单外的任何新增与未跟踪残留一律 FAIL。新增只能来自用户明确批准的 `pack_only` 桶；删除/改名视为异常，先问人。用法：
     ```bash
     python script/gates/overlay_check.py post --package SYNTHESIS --paths SYNTHESIS/ --approved-adds script/approved_adds_<ver>.txt
     ```
     （`approved_adds_<ver>.txt` = 报告 `pack_only` 桶，每行一个 `<AREA>/<rel>`。）
   - 跑 `script/gates/probes.json` 里的**版本代际探针**（如 `LONG_ENCODING_ALIGN.v` 的 `I_INDATA_D4==0`、`SHORT_ENCODING_ALIGN.v` 的 `_TYP1_M>0`），确认真拿到了新代数值而不是旧文件原地未动；
   - 打印建议命令 **`git add -A -- <paths>`** —— 用 `-A` + 显式路径，不要 `git add <file1> <file2>` 手敲（漏加就是这么来的，见 server-pack-overlay 1113 事故）。
3. **提交后自检**（overlay_check 内置）：带 `--commit` 时它会 `git add -A -- <paths>` + commit，并**只按文件名**复核「提交文件数 == 暂存数」；不一致就是漏加，`git commit --amend` 补。**一次 overlay 一笔提交，不按目录拆笔**（2026-11-23 ymzhu 指令）。
4. 解压产物目录（`script\_syn_*` / `_rtl_*` / `_dv_*`）靠 `.gitignore` 排除；若 overlay_check 把解压目录报成未跟踪杂散，说明 gitignore 漏了，补一行而不是 `git add` 进去。

## 0C. 落位硬规则（2026-11-24 起以 project-control skill 为准；2026-11-18 版见文末备注）

**仓库根目录禁止新增任何文件。** 白名单与各区规则见 project-control skill，机器判据是 `python script/gates/pc.py check`。与回传相关的落位：

| 产物 | 落位 |
|---|---|
| pack_diff 五桶报告 / approved(.applied) 清单 / overlay 审计与基线 / 中间版本说明 `README_中间版本说明_<ver>.md` | `script/`（闸门与回传流程的机器产物，文件名模式固定） |
| 回传包里的回传内容 | 五个回传目录之一：`HDL/` `SYNTHESIS/` `DV_TCON_C/` `FPGA/` `APR/` |
| 包内 `designer/<组>/<人>/HK1V11/…` 这类个人目录的内容 | 不落到本地根目录：FPGA 工程副本只留源文件进 `FPGA/server_<版本>/`，模拟端交付进 `APR/analog_release/`（样例：`FPGA/server_1022V5/`、`APR/`） |
| 一次性分析报告、审计、评审 | `内部分享/YYYYMMDD/NN.中文说明/readme.md` |
| 功耗/对比图等成套图产物 | `GITHUB/PPT/back_ppt/` 等生成器同目录 |
| 长期规则文档 | `docs/`（只放规则类；分析文档已对外发布的删、未发布的进内部分享） |

执行纪律：agent 落盘前对照 project-control §4 的落位表，或直接跑 check；白名单外即违规。2026-11-24 目录整理之前的历史遗留不追溯。

FPGA、APR 两类回传目录沿用本 skill 的同一套纪律（PACK_TAR、diff-first、overlay 校验）；包内结构的判定规则等第一个真实包样例到了再补，`overlay_check.py` 的 `--package FPGA/APR` 同步跟进。

## 0. 包定位与目录映射

1. **远端操作默认禁用（2026-11-06 ymzhu 指令，取代旧"agent 自己拉取"规则）**：回传包一律由**用户手动下载**到 `C:\Users\zhuyanming\Downloads\`（包源通常是内网工作站，与 IC_EDA VM 无关），agent 从 Downloads 起步。未经用户**当次会话明确授权**，agent 不得对任何 ssh 远端主机（IC_EDA VM、内网工作站或其他一切主机）执行 ssh_exec / ssh_upload / ssh_download / ssh_tunnel / ssh_cluster 操作——包括 ls 探查等"只读"命令一律禁止（2026-11-06 教训：agent 依据旧规则自行 ssh 探查 VM 被叫停；回传源头是内网工作站，与 VM 无关）。
   - 仅当用户在当前对话明确点名某主机并说"去上面××"时才可动用对应 ssh 工具，且该授权**不延续**到后续轮次/后续会话。
   - 包已在 Downloads（用户已下载）则直接进解压/比对。
   - Downloads 下可能并存用户**已预解压**的 `PACK_TAR_*` 目录与 `PACK_TAR_*.tar.gz` 原包：**pack_diff 一律以 tar.gz 原包为比对/覆盖源**，预解压目录仅作人读对照，不作为 diff 或覆盖输入。
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
- 包内结构形如 `XXW_PRJ01/HK1V11/designer/<组>/<人>/HK1V11/...`（编号↔内容的判定见 §0 第 2 条）。

## 2. SYNTHESIS 包

合并式覆盖，量大可用 robocopy（排除 gitignore 的解压目录）：

| 对象 | 动作 |
|---|---|
| `top/sta/` 各 corner `latest/` 报告（log/rpt/summary/run_summary）、`sdc_pr/`、rpt/sdc 类产物 | **覆盖**（服务器 run 产物同步的正主）；仍须进 `approved.txt`，走 diff-first 拍板，不得自行批量覆盖 |
| 服务器改过的脚本（pt_setup.tcl / read_design.tcl / run_pt / design.set / deploy 脚本） | **先 diff，有差异才覆盖**，并记录差异内容 |
| `SYNTHESIS\common\ip_cons\<top>.tcl` | **先 diff 约束差异，逐条评估同不同意——同意的采纳（覆盖/合并进本地），不同意的保留本地并写明理由**。同时判定服务器 run 吃到的约束版本（找本代标记：`cpuwr_reg_grp`、10 分区排除清单、`-to RX_CLK` 的 UTC 行、`U_DPLC_DATA_GEN/*/D*`），用于解读这批报表 |
| `common\clk_period.tcl` | **不动**（要求 pristine），有变化只汇报 |

> **whole_session 硬规则（2026-11-17 用户指令，永久生效，优先级高于上表与一切包内容）**：`whole_session/` 目录（各 corner 的 `latest/` 与 `history/` 下均有，PT 会话存档，单 corner 数百 MB）**永不覆盖、永不入库**：
> 1. **pack_diff 批准清单一律排除**——`whole_session` 路径不得进入 `approved.txt`（diff 报告里出现也只作计数汇报，不参与拍板批准）；
> 2. **overlay 无视**——覆盖执行时该目录不是覆盖对象，任何包来源都不写它；
> 3. **.gitignore 常备** `whole_session/`（或等效 `**/whole_session/` 行），缺则当场补上；
> 4. **仓库已有跟踪路径的，用 `git rm -r --cached` 清除**（解除跟踪、磁盘文件保留），单独提交，不混进包覆盖提交。

用户要求时才出的验证数字（**默认不出**，2026-11-23 ymzhu 指令；用于确认上一轮修复是否被服务器吃到）：
1. setup/hold 各 corner 总数与 worst（`summary/latest/report_setup.csv` / `report_hold.csv` 的 setup.rpt / hold.rpt 行）
2. `read_cons.log` 搜 `SEL-004` 计数、搜 `/D1` `/D2` 计数（已知遗留项是否仍丢）
3. `report_exceptions.rpt` 关键 applied 行（如 `* RX_CLK cycles=2(start)`）在不在
4. 违例 startpoint 分布：近期排除/注释的分区**回单周期后冒不冒新违例**（收窄/注释修改后最关心的一笔）

覆盖后 git：先按 §0B 跑 `overlay_check.py post`，再 `git add -A -- SYNTHESIS/`（显式路径 + `-A`；解压目录靠 gitignore），commit 注明"<ver> 服务器 run 产物同步（L1）"，提交后用 `git log --stat` 复核文件数，push。**推送策略（1116 实战修订，取代旧的 http.version/postBuffer 单条重试）**：

- **GB 级大包禁止单次全量 push**——必被代理/TUN 掐断（`send-pack: unexpected disconnect while reading sideband packet` / `broken pipe`）。默认**不拆笔**（一次 overlay 一笔提交，2026-11-23 ymzhu 指令），被掐就走重试循环或切 ssh 443，确实推不上去再问用户是否拆笔；单笔仍断就逐 commit 增量推：`git push origin <sha>:refs/heads/main`（oldest 先）。
- **断连是间歇性的**：写带重试的循环（每 15~20s 一次，`git rev-list --count origin/main..main` 判停），网络恢复窗口一次能推齐多笔；commit 先落本地永远安全，等窗口即可，不要反复杀进程重来。
- **双通道互备（2026-11-16 起）**：默认 HTTPS + gh 凭据免密（`gh auth setup-git` 已接管）；被掐时切 ssh 443：`git remote set-url --push origin ssh://git@ssh.github.com:443/<owner>/<repo>.git`，fetch 仍走 HTTPS 互不影响。
- **坑：代理配置与实际监听端口脱节**——2026-11-16 实测本机系统代理是 `127.0.0.1:12450`（旧的 7890 记录已作废），而 `git`/`gh` **都是 Go/自管 HTTP 客户端，不读 Windows 的 IE 代理设置**，只认 `HTTPS_PROXY` / `HTTP_PROXY` 环境变量。症状是"浏览器能开 github、git 却超时"，报错像网络不通。排查顺序：`curl -x http://127.0.0.1:<port> https://github.com` 先验代理活 → 再确认环境变量。TUN/系统代理模式下没有可用的 HTTP 代理端口时，直接 `git config --global --unset http.proxy`。
- 旧招留档：`git config http.version HTTP/1.1` + `http.postBuffer 524288000`（HTTP/2 层面问题时用）。
- **超大目录不入库**：whole_session 按上方「whole_session 硬规则」处理（永不覆盖、永不入库）；历史 run 产物（log_/rpt_）逐笔推。

## 3. RTL（HDL）包

**合并式覆盖到本地 `HDL\`**（与 DV_TCON_C 同一套规则）：同名文件覆盖、新增文件添加（影响 file_list 就同步 `.f`）、本地独有文件保留。

- 覆盖是**同步动作，不做 check/评审**——只记录覆盖/新增/保留了哪些文件，写进 `script/README_中间版本说明_<ver>.md`（快照来源 + diff 摘要 + 文件清单），文末签名。
- **寄存器相关模块特别 diff（2026-11-06 ymzhu 要求）**：HDL 包内 LC_CPUWR / LC_REG_MAPPING / LC_REG* / R_REG* 体系等寄存器相关文件必须从普通 diff 清单中**单列呈报**（完整差异，不并入汇总）；批准覆盖后按 version-archive 规则维护 `LC_CPUWR_history/`（固定文件名+文件头版本号、目录内 CHANGES.md 与根级修改记录双轨、README 版本速查表），并登记 `back3.HK1V11_changelist.xlsx` Register Change 表。
- RTL 三关（iverilog / rtl-code-review / rtl-signal-trace）**不适用**于包覆盖：那是"本地自行修改 RTL 功能并发布新版本"时才走的流程；服务器回传包是权威交付物的搬运，交付级记 **L1**（签名 + CHANGES + 提交推送）。
- 同一次交付里既有包覆盖、又有本地改 RTL 功能时，那一轮按**更高**的级走（改功能 → L2，涉及时序/编码变更 → L3），不要用"包里带来的"当豁免理由。

## 4. DV_TCON_C 包

**合并式覆盖到本地 `DV_TCON_C\`**（与 RTL 同一套规则）：同名 case/env/checker 文件覆盖、新增 case 添加、本地独有文件保留；覆盖/新增/保留清单照常记录。

- **ppm 等大仿真文件不会随包下载**：在解压目录对应位置用 `mklink /J`（junction，不需管理员）链到本地现有 ppm 文件夹（如 `DV_TCON_C\top\tests\ppm_mix_*`）；路径结构不明确就写 `PPM_链接说明.md` 说明缺什么、链到哪。
- env/checker 类差异若涉及 cfg_frame 解析，注意 `%b` 二进制口径一致性。

## 5. 通用纪律

- 所有说明类 md 文末签名 `<!-- ymzhu YYYY-MM-DD HH:MM -->`（实际时间）。
- **汇报模板**（默认只报这些，2026-11-23 ymzhu 指令）：① **哪里不同**（`diff` 文件数 + 报告路径）、**哪里新增**（`pack_only` 文件数/体积 + 报告路径），以及 whole_session / 被仓库 `.gitignore` 忽略 / Windows 非法名无法落地的各多少；② overlay 校验结论（修改 / 新增 / 删除 / 改名数，新增是否全在批准清单内）+ 交付级 L0/L1；③ commit hash、提交自检文件数、push 结果。**验证数字（SEL-004 / D1D2 / exceptions / setup+hold 总账）、服务器约束代际判定、RTL 功能差异分析，一律等用户要求再做。**
- 时间线意识：服务器 run 的时间戳可能**早于本地最新约束修改**——汇报时明确"服务器吃到了哪一代，哪些没吃到"。

## 6. 服务器 EDA 工具启动（dsh-ssh 插件执行，2026-09-30 dc_shell 实测，2026-10-22 修订）

> **⚠️ 默认禁用（2026-11-06 ymzhu 指令）**：本节全部远端操作（bsub / dc_shell / pt_shell / 远端文件操作）仅在用户**当次会话明确授权**后执行；未授权时 agent 一律不碰任何远端主机（含 IC_EDA VM），以下命令模板只作参考存档。

**服务器操作一律走 dsh-ssh 插件**：alias=IC_EDA（root@192.168.206.128，key 免密，tags `[eda, hk1v11]`），先 `ssh_list` 确认再执行。路径约定：服务器项目根 `/home/ICer/work/HK1V11/`（与本地 `E:\project\HK1V11` 同构）；**本机（dsh host）的文件/命令用本地工具，ssh_* 只针对远端**，两类路径勿混。

**铁律：EDA 工具（dc_shell/pt_shell 等）不能在登录节点直接跑**——license 只对 bsub 分配的计算节点使能，直接跑报 `Fatal: Design Compiler is not enabled. (DCSH-1)`，或静默卡住等一个等不到的 license。所有 EDA 命令必须经 bsub 到计算节点执行。

**三种执行模式（按任务时长选）**：

| 模式 | ssh_exec 命令 | 适用 |
|---|---|---|
| ① 批量作业 | `cd <工作目录> && bsub < job.sh` | 长任务（小时级综合/PT）：提交即返回，`bjobs` 轮询状态 |
| ② 非交互计算节点执行 | `cd <工作目录> && bsub -I 'source /eda/env/syn1709.cshrc && dc_shell -f run.tcl'` | 短中任务（分钟级）：输出同会话完整返回，`timeoutMs` 设大（最大 600000） |
| ③ 交互探针（命令管道） | `printf 'source /eda/env/syn1709.cshrc\ndc_shell -f probe.tcl\n' \| bsub -Ip csh` | 节点上 what-if 探针；探针 tcl 先 `ssh_upload`（或 heredoc）写入服务器再执行 |

泛化：
- 其他 Synopsys 工具同模式（pt_shell / formality 等，换最后一步的启动命令）；
- 项目 wrapper 脚本（如 `run_dc`）= "source 环境文件 + 启动工具" 的封装——交互调试时拆开：先 bsub 内 source 环境，再敲工具命令，便于逐条验证；
- Web 终端（GUI「SSH」入口）是给**人**用的全交互 shell；agent 一律用 ssh_exec，上述三档覆盖绝大多数 EDA 场景。

**启动慢 ≠ 卡死**：license checkout/初始化可等 1-3 分钟（黑屏光标闪 = 还在等）。超 3-5 分钟另开会话 ssh_exec：
`ps -ef | grep dc_shell | grep -v grep`——查残留进程占 license，kill 后重进。
**license 锁节点**：默认节点报 not enabled 时，指定到跑过综合的节点重试：`bsub -I -m node043 'source /eda/env/syn1709.cshrc && dc_shell -f run.tcl'`（dc_shell 0930 实测 node043 可用）。

**交互探针必须复刻完整 setup 链（0930 探针污染教训）**：在 bsub 节点上做增量精修/what-if 实验时，只 source design.set + clk_period + ip_cons **不够**——必须补齐 `dont_use_all.tcl`（流程禁用 *SFF*/*X05* 等单元族；漏 source 会导致 DC 自由使用禁用单元，实验数字成为"放宽规则的上界"，不代表生产环境）。完整链：design.set → clk_period.tcl → ip_cons → **dont_use_all.tcl** → 目标库 target/link_library 设置 → read_ddc/网表 → 实验。库限制在 `SYNTHESIS/common/tcl_dir/dc/dont_use_all.tcl`。
<!-- ymzhu 2026-11-24 16:52 -->
