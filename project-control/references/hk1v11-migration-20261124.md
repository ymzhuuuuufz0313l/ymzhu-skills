# 2026-11-24 目录迁移清单（一次性）

> 状态：**草稿，待 ymzhu 确认后执行**。规则正文在 [`../SKILL.md`](../SKILL.md)。

## 0. 执行原则

- 已入库的用 git mv，未入库的直接 mv；历史全程保留。
- 顺序：先建骨架（新目录 + README）→ 再迁内容 → 再改引用 → 最后才删空目录；中途任何一步可停，已迁的内容不影响未迁的。
- 每一步落一份清单到 `script/gates/reports/`，迁移完成后一次性走 L0 闸门（签名 + CHANGES + 提交推送）。

## 1. 逐项映射

| 旧位置 | 新位置 | 方式 | 备注 |
|---|---|---|---|
| `power_saving/` | `内部分享/power_saving/` | mv（259 个文件未入库）→ 源文件补入库（md/py/v/ys），.vvp、日志、大网表加 ignore | README 顶部加"原位于…"一行 |
| `rtl_power_opt_1118/` | `内部分享/power_saving/rtl_power_opt_1118/` | mv（未入库）→ 补入库 | 修基线引用：power_saving/20261119/README.md、v0_original/README.md |
| `longcode_ver/` | `内部分享/longcode_ver/` | git mv（已入库 405 个） | 加 README.md；0713v2.rar 不动 |
| `register_research/` | `内部分享/register_research/` | git mv（已入库 28 个） | 加 README.md |
| `simulation/` | `local_simulation/` | git mv 改名 | local-simulation skill 改路径；入库状态不变 |
| `back_ppt/` | `GITHUB/PPT/back_ppt/` | git mv（已入库 70 个） | pil-table-render、server-pack-overlay、站点工具改路径 |
| `DataBase/Analog/APR_CDM_TOAPR/` | `APR/lib_cdm/` | git mv | |
| `DataBase/Analog/VERILOG/`、`DataBase/Digital/Release/` | `APR/lib_models/` | git mv | DataBase 目录消失 |
| `designer/AD/hmnie/release/` | `APR/analog_release/` | mv + git mv（12 个文件，198MB） | |
| `designer/DD/chengli/HK1V11/FPGA/VU440_FPGA/` | `FPGA/server_1022V5/`：只留源文件（.v/.xdc/.xci/.tcl/.md 等） | 源文件 git mv；.db/.sdb/.txt 等 2.1GB 生成物 `git rm --cached` 后删本地 | 7427 个已入库文件 |
| `designer/DD/chengli/README_1022V5说明.md` | `FPGA/server_1022V5/README_1022V5说明.md` | git mv | designer 目录消失 |
| `docs/` 下已发布到 team-share-public 的 29 篇 md | 删除 | git rm；**删前逐篇比对正文**（§2 的命中是按标题做的） | |
| `docs/` 未发布的 4 篇 + 根目录 3 个 md | `内部分享/<日期>/NN.中文说明/` | 见 §5 待定项 Q27 | |
| `docs/agents/` | 留在 docs/ | — | |
| `docs/` 的配图与数据目录 | 站点已有的删；被站点工具读取的（to_signoff_1104v2 等）见 §5 | — | |
| `.claude/`、`.claudeignore` | 删除 | git rm | |
| `.venv_xlsx/` | 删除 | rm；AGENTS.md §2 去掉该行 | |
| `script/` 六项缓存 | 删除 | rm（本来未入库） | pack_0828_extract、pack_0909_extract、_1117_extract、_r4_diag、_review_inject、__pycache__ |
| docs/images → GITHUB/IMAGE/project_diagrams（README 配图与生成脚本；目录树图已按新结构重生成） | git mv | README 链接同步 |
| 新建 | `APR/README.md`、`GITHUB/README.md`、`GITHUB/PPT/README.md`、`GITHUB/IMAGE/README.md`、`GITHUB/ISSUE/README.md`、`内部分享/README.md`、`外部分享/README.md` | — | 内容取自 SKILL.md 对应小节 |

## 2. docs 已发布清单（29 篇，命中站点目录按标题匹配）

- 根下 8 篇：HK1V11_1p_dplc_5G3G_analysis_20261019、HK1V11_2M23_content_audit_20261019、HK1V11_full_audit_verdict_20261019、HK1V11_longcode_420b_delta_audit_20261105、HK1V11_skew_explainer_20261019、HK1V11_skew_probe_audit_20261028、HK1V11_后端综合集成流程_学习笔记、HK1V11_流程准备评估报告_PACK_TAR_0909V2 → 站点 hk1v11-synthesis-postpt-practice、hk1v11-longcode-420b-verification
- boe_kcode_debug_1105/ 下 20 篇（m_captain_bitrev_cancel、m_glm53a、m_glm53flash_b、m_qwen_c … m_qwen_i2）→ hk1v11-longcode-420b-verification
- to_signoff_1104v2/README.md

未发布 4 篇：VU440_FPGA工程盘点_20261023、VU440_XDC约束审查_20261023、VU440_器件仿真与验证报告_20261023、boe_kcode_debug_1105/kcode_positions_table。

## 3. 需要同步修改的 skill 与工具

| # | 对象 | 改什么 |
|---|---|---|
| 1 | power-clinic（整理当天由 power-eco 改名） | 产物路径 `power_saving/<日期>/ECO_<名>/` → `内部分享/power_saving/<日期>/ECO_<名>/` |
| 2 | feature-sandbox | longcode_ver 的路径 |
| 3 | local-simulation | `simulation/` → `local_simulation/` |
| 4 | pil-table-render | `back_ppt` → `GITHUB/PPT/back_ppt` |
| 5 | server-pack-overlay | §0C 落位表改为指向本 skill；包类型加 FPGA、APR 的规则；designer、back_ppt、docs 的引用 |
| 6 | hk1v11-delivery-gate | preflight 接入 `script/gates/repo_layout_check.py`（根目录白名单、GITHUB 根、分享目录命名）与 script/README 自动索引 |
| 7 | xilinx-suite | 核对 10 处 FPGA/docs 引用，涉及路径的改 |
| 8 | team-share-public 的工具脚本 | 改来源路径；修掉 `designer/DD/ymzhu/…` 那批坏路径 |
| 9 | AGENTS.md | §2 目录结构重写、§2 去掉 .venv_xlsx、§5 文档索引改链接（已发布的 docs 条目移除）、§7.1 加本 skill 路由行、§8 落位规则指向本 skill |
| 10 | README.md | 目录结构同步 |
| — | project-init | 模板只泛指 docs/ 和 修改记录/，不改 |
| — | ~/.dsh/skills/README.md 任务路由表 | 加本 skill 一行 |

## 4. 验证

1. `python script/gates/preflight.py --level L0` verdict=pass。
2. `python script/gates/repo_layout_check.py` 全绿。
3. 链接检查：AGENTS.md、README.md、docs 索引里的相对链接逐个打开。
4. skill 冒烟：`内部分享/power_saving/20261119/ECO_HEALTH/tools/build_tables.py` 可复跑；local-simulation、pil-table-render 的新路径存在。
5. 推送后 `git log --stat -1` 自检文件数。

## 5. 待定项

- **Q27**：未发布的 4 篇 docs 与根目录 3 个 md 的落点；docs 的配图/数据目录（to_signoff_1104v2、delay_skew、skew_probe_audit_1028、chpi_spec_pages、chpi_codec_pages、images）哪些删、哪些留。
- **第二阶段**：power_saving/20261119 下已有 35 个条目的 `NN.中文说明` 编号映射（先出表，过目后再改）。

## 6. 执行顺序

建骨架 → 回传类（APR 三目录、FPGA/server_1022V5）→ 分享类（内部分享四项、GITHUB/PPT/back_ppt）→ local_simulation 改名 → docs 与根文件 → 隐藏目录与 script 清理 → 改 skill 与工具引用 → 自检脚本接入 preflight → L0 闸门、CHANGES、提交推送。
<!-- ymzhu 2026-11-24 17:15 -->
