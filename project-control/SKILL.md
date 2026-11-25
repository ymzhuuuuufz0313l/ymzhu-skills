---
name: project-control
description: 工程目录控制——统一的目录骨架、命名与落位规则。新工程一键 init（回传目录 + GITHUB/内部分享/外部分享 + script/修改记录/docs），老工程按根目录白名单整理并自检；日期文件夹 YYYYMMDD，条目 NN.中文说明 + readme.md。触发词："project-control"、"建目录骨架"、"初始化目录"、"init 目录"、"目录整理"、"根目录"、"放哪"、"落位"、"内部分享"、"外部分享"、"GITHUB"、"白名单"、"目录乱了"。
---

# 工程目录控制（project-control）

> 一句话：**根目录只有白名单里的东西；每类产物只有一个家；落盘前先查落位表。** 规则对所有工程通用，工程自己的目录名放在配置文件里。

## 1. 先判断你要做哪件事

| 情况 | 去处 |
|---|---|
| 新开一个工程目录，要把基本文件夹建好 | §2 init |
| 老工程目录乱了，要整理 | §3 整理 |
| 只是想知道一个文件该放哪，或落盘前自检 | §4 落位表、§5 规则，然后跑 check |

## 2. init（新工程）

在工程根目录执行，脚本只建缺失的目录和 README、写配置，**不移动、不删除任何既有文件**。

1. 运行 `python <skill目录>/scripts/pc.py init --roundtree …`（参数见下表）。完成标准：命令以 exit 0 结束，并打印"check 通过"。
2. 打开生成的 `script/gates/repo_layout.json` 核对一遍。完成标准：白名单里的每一项都是你认可的目录名。
3. 之后每次回传、写报告，按 §4 的落位表放；提交前跑 `python script/gates/pc.py check`。

| 参数 | 含义 | 默认 |
|---|---|---|
| `--roundtrip A,B,C` | 回传目录名（服务器回传内容，每个一个目录） | 无，必填 |
| `--exceptions X,Y` | 特例目录（保持原状、不按本规则管） | 无 |
| `--tools a,b,c` | 工具与记录目录 | script、修改记录、docs、plan |
| `--projects a,b` | 内部分享里已有的项目文件夹 | 无 |
| `--site 路径或URL` | 对外网站的仓库位置，写进 GITHUB/README | 无 |

init 会建的东西：回传目录（各带 README）、`GITHUB/`（README + PPT、IMAGE、ISSUE）、`内部分享/README.md`、`外部分享/README.md`、`script/README.md`、`修改记录/CHANGES.md`、`docs/README.md`，并把自检脚本同步一份到 `script/gates/pc.py`。

## 3. 整理（老工程）

1. **先盘点事实**：列出根目录每一项的类型、文件数、体积、是否入库、最后修改，以及哪些 skill、闸门脚本、外部工具写死了这些路径。完成标准：每个根目录条目都有一行，没有"不知道是什么"的项。
2. **出映射表给用户确认**：旧位置 → 新位置 → 方式（git mv / mv / 删除）→ 备注，外加要同步修改的 skill 与工具清单、清理清单。完成标准：用户逐项确认。HK1V11 的样例见 [`references/hk1v11-migration-20261124.md`](references/hk1v11-migration-20261124.md)。
3. **分批执行**：先建骨架 → 回传类 → 分享类 → 工具与记录 → 清理；已入库的用 git mv，未入库的直接 mv；删除的每一项都在用户批准的清单上。完成标准：每一批做完 `git status` 里只有预期内的改动。
4. **改引用**：skill、闸门脚本、外部工具、AGENTS.md、README 里会执行的路径全部改到新位置；历史文档里的旧路径字样保持原样。完成标准：§6 的验证清单全过。
5. **闸门**：按 L0 走（签名 + CHANGES + 提交推送）。

## 4. 目录形态与落位表

| 类别 | 条目 | 说明 |
|---|---|---|
| 回传 | 配置里的 roundtrip | 服务器回传内容，进出纪律走 server-pack-overlay |
| 分享 | `GITHUB/` `内部分享/` `外部分享/` | §5 |
| 工具与记录 | 配置里的 tools（script、修改记录、docs、plan 等） | §5 |
| 特例 | 配置里的 exceptions | 保持原状 |
| 根文件 | AGENTS.md、README.md、REVIEW.md | REVIEW.md 只由 preflight 生成 |
| 隐藏项 | 配置里的 hidden | .git、.gitignore、.gitattributes，以及工具自管目录 |

| 产物 | 落位 |
|---|---|
| 回传包的解压、覆盖、校验 | 对应的回传目录 |
| 一次性分析报告、体检、审计、评审 | `内部分享/YYYYMMDD/NN.中文说明/readme.md` |
| 多篇相关、带工具或数据的项目 | `内部分享/<项目名>/` |
| subagent、agent 之间的交接与问答记录 | `内部分享/YYYYMMDD/NN.中文说明/` |
| 发给同事的 md | `外部分享/YYYYMMDD/NN.中文说明/readme.md` |
| 对外发布物（PPT、图、issue 汇总） | `GITHUB/PPT/`、`GITHUB/IMAGE/`、`GITHUB/ISSUE/` |
| 变更记录 | `修改记录/` |
| 闸门代码、回传包机器产物、还会再跑的脚本 | `script/` |
| 规则类长期文档（agent 规则、ADR、术语表） | `docs/` |
| 计划文件 | `plan/` |

## 5. 各区规则

**内部分享**（三层边界）

| 层 | 只允许 | 说明 |
|---|---|---|
| 顶层 | md 文件、日期文件夹、项目文件夹 | 顶层 md 是跨项目的零散交接 |
| 日期文件夹 `YYYYMMDD/` | `NN.中文说明/` 目录 | 每个目录必须有 readme.md；图、数据等附件放在该目录内 |
| 项目文件夹 `<小写_下划线>/` | 不限类型 | 必须有 README.md；生成物（.vvp、.pyc、大网表、日志）按 .gitignore 不入库 |

- `NN` 两位补零（01、02、…、10），`中文说明` 用中文写清这是什么内容的报告，如 `01.DC再优化体检`。
- readme.md 第一行写结论，然后是背景、方法、证据路径。
- 迁入的项目在 README 顶部加一行"本目录原位于 `<旧路径>`，<日期> 迁入"。

**外部分享**：README.md 是台账（日期 / 主题 / 收件人 / 对应的内部分享链接）；下面只有 `YYYYMMDD/NN.中文说明/readme.md`，内容全是 md；图片用外链或放 `GITHUB/IMAGE/`。

**GITHUB**：对外发布物的暂存区。根上只有 README.md 和文件夹（PPT、IMAGE、ISSUE），每个文件夹用自己的 README.md 说明用途（空文件夹靠 README 占位）。网站本体在站点仓库，发布走 team-share skill；GITHUB 里不建站点副本。

**script**：工具写入区——人和 agent 都不往根上手工放报告，只允许四类：闸门代码；回传包机器产物（固定文件名模式，如 PACK_TAR_*_diff_report.md、approved_*.txt、overlay_baseline.json、README_中间版本说明_*.md）；还会再跑的一次性脚本；自动生成的 README.md 索引。新报告去内部分享。未入库的解压、截图缓存删除前先列清单并标出被引用的项，经用户批准再删。

**docs**：只放规则类长期文档（agent 规则、ADR、术语表）。分析类文档：已对外发布的直接删，未发布的进内部分享的日期文件夹。

**plan**：计划文件目录，.gitignore 忽略 `plan/*.md`（dated-plan-mode 自动同步）。

## 6. 自检与验证

- `python script/gates/pc.py check`：根目录白名单、GITHUB 根只许 README + 文件夹、内部分享与外部分享的日期文件夹只许 `NN.中文说明/` 且含 readme.md、外部分享只含 md、项目文件夹含 README.md。任何一项不满足即 exit 1。preflight 调用它。
- 整理后的验证清单：preflight L0 verdict=pass；check 全绿；AGENTS.md、README、docs 索引里的相对链接逐个打开；受影响的 skill 各做一次冒烟（路径存在、脚本可跑）；推送后 `git log --stat -1` 文件数与暂存数一致。

## 7. 工程档案

每个工程一份档案，写它的回传目录名、特例目录、内部分享里已有的项目、站点仓库、隐藏目录：

- HK1V11：[`references/hk1v11-profile.md`](references/hk1v11-profile.md)

## 8. 相关 skill

- server-pack-overlay：回传目录的进出纪律
- hk1v11-delivery-gate：闸门；preflight 调用本 skill 的 check
- team-share：对外发布
- project-init：生成 AGENTS.md 等上下文文档。新工程的顺序是先 project-control init 建目录，再 project-init 写文档
- version-archive、local-simulation、dated-plan-mode：各自管理特例目录、仿真目录、计划目录

<!-- ymzhu 2026-11-24 16:30 -->
