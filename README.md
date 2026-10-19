# ymzhu-skills

ymzhu（HK1V11 芯片数字后端）的 Agent Skill 库。每个目录一个 skill（`SKILL.md` 为入口），供 OpenCode / DeepSeek Harness / Kimi 等 Agent 按触发词自动加载，沉淀日常芯片后端 + 工程工作流中反复用到的规则和模板。

## 使用方式

- 把本目录整体放到 Agent 的全局 skills 目录（本机镜像：`C:\Users\zhuyanming\.dsh\skills`、`~/.config/opencode/skills`、`~/.kimi/skills`）。
- 不需要手动调用：说对应触发词（如"检查 RTL"、"写日报"、"服务器包"）即命中；每个 `SKILL.md` 头部都列了触发词。
- 新增 skill 时：独立目录 + `SKILL.md`，职责尽量合并进已有 skill，避免拆太碎。

## Skill 一览（25 个）

### 芯片设计 / RTL

| Skill | 做什么 |
|---|---|
| `chip-design-supervisor` | 扮演资深芯片设计主管：设计评审、架构反馈、RTL 走查、技术讨论 |
| `rtl-code-review` | RTL 变更对抗性评审：时序风险/可维护性/综合友好度/接口一致性，severity 分级 + pass/fail 门禁 |
| `rtl-signal-trace` | 信号跨模块路径追踪（文本搜索）+ CDC 风险标记 + 模块依赖图/file_list 校验 |
| `regmap-pipeline` | 寄存器单一事实源：`regmap.md` → 寄存器文档（MD + CMSIS-SVD）+ SVA 断言 + RTL↔表一致性检查 |
| `spec-traceability` | spec↔code 轻量追溯：REQ_ID 分配/唯一性、spec hash 漂移检测、版本一致性审计 |
| `digital-backend-pitfalls` | 数字后端经验坑集：cell 引用稳定性（post-route 探针/999 哨兵）、跨工具 SDC、ICG 复位机制、蓝/红路径约束矩阵（DC/PT vs Innovus/ICC） |
| `local-simulation` | Windows 本机开源工具链（Icarus Verilog + GTKWave / Yosys）跑 Verilog/SV 模块，不依赖 VCS/UVM |
| `xilinx-suite` | Xilinx(AMD) FPGA/MPSoC 全工具链参考：Vivado XDC 约束、Tcl、综合实现、报告分析、CDC/时序例外（源自 MIT 开源库，按 HK1V11 VU440 场景改编） |
| `server-pack-overlay` | 服务器回传包（PACK_TAR_*.tar.gz）提取 + 合并式覆盖规则（SYNTHESIS/HDL/DV_TCON_C 三类包口径） |
| `version-archive` | 多版本归档目录维护规则：目录内 CHANGES.md 总览 + README 版本速查表 + 双轨记录 |
| `sta-csv-table-png` | 芯片分析数据 → 网站 PNG：① PT summary csv → to-signoff 同款表格图 ② 功耗/违例对比条形图 + 组成环形图（matplotlib） |
| `team-share` | team-share VitePress 知识库维护 + 独立公开文章发布 |

### 工作流 / 记录

| Skill | 做什么 |
|---|---|
| `daily-report` | 把当天对话/工作整理进 `E:\每日记录\` 的日报/周报/遗留问题体系 |
| `workflow-maintainer` | 维护工作流偏好、变更日志（CHANGES.md）、服务器回传清单（REVIEW.md） |
| `report-organizer` | 整理 Markdown 报告并按规则移入 `E:/report` |
| `project-init` | 新开空目录时初始化整套 AGENTS.md 项目上下文体系（根级/.kimi/子模块 + README） |
| `dated-plan-mode` | 计划模式 + 钩子自动同步计划文件到 `{workdir}/plan/MMDD_pN_{slug}.md` |
| `feature-sandbox` | 为新增独立功能/模块建隔离开发工作区，不污染主项目 changelog |

### 多智能体协作

| Skill | 做什么 |
|---|---|
| `agent-teams-router` | 判断任务是否适合启用 Agent Teams 多智能体模式，给激活方式与成本控制 |
| `subagent-dispatch` | 派发 subagent 前的模型选择与确认协议（多模型分工：K3/QWEN/GLM 等） |

### 可视化 / UI

| Skill | 做什么 |
|---|---|
| `blueprint-ui-style` | 用户首选的蓝图工程风（blueprint engineering aesthetic）：网站、HTML 报告、页面美化统一画风 |
| `fireworks-tech-graph` | 技术图（架构/数据流/时序/状态机/ER/拓扑/时间线）生成并导出 SVG+PNG |
| `gpt-image-2-style-library` | GPT-Image2 风格库 + 工业级 prompt 模板（分类/风格标签/坑位/案例） |

### 工具 / 杂项

| Skill | 做什么 |
|---|---|
| `office-com-reader` | 读取加密/受保护的 Office（xlsx/docx/pptx）与 PDF：原生 COM API + pypdf + Acrobat COM 兜底，兼容企业 DLP 透明加密 |
| `colleague-skill`（distilly） | 把同事/关系/名人素材蒸馏成可复用的 Person Profile |

<!-- ymzhu 2026-10-19 16:48 -->
