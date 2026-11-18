# ymzhu-skills

ymzhu（HK1V11 芯片数字后端）的 Agent Skill 库。每个目录一个 skill（`SKILL.md` 为入口），供 OpenCode / DeepSeek Harness / Kimi 等 Agent 按触发词自动加载，沉淀日常芯片后端 + 工程工作流中反复用到的规则和模板。

## 任务路由表（2026-11-18 加；接手任务先查这张表，命中就走对应 skill，不要凭记忆开工）

| 你会怎么说 / 任务长什么样 | 走哪个 skill | 进去后第一件事 |
|---|---|---|
| 「做个网站 / 新站 / 加一个站点 / 用我喜欢的风格」 | `blueprint-ui-style` | 读 §新站搭建强制流程 §0 强制读取链，复制 `site-template/` |
| 「改一下站点 / 页面美化 / 改组件」 | `blueprint-ui-style` | 读 §使用规则 0.5 路由表 → §设计系统 + §站点组件模板 |
| 「加动画版 / 动效 / 静动双版」 | `blueprint-ui-style` | 读 v4 架构章 1→4 + `anim/MOTION_KIT.md` |
| 「改图 / 重生成图 / 图里数字不对 / 图跟正文不一致 / 环形图加起来不对 / 归档旧图」 | `blueprint-ui-style`（图规则）+ `anim-svg-site-audit`（先体检） | 跑生成器 `--out` 与线上 `cmp`，别先手改 SVG |
| 「审计站点 / 全站核对 / 扫一遍这些图 / 图体检」 | `anim-svg-site-audit` | A0–A9 逐项，只读，报告落 `修改记录/` |
| 「跑闸门 / preflight / 能不能交付 / 改完图要交付 / 推送前检查」 | `hk1v11-delivery-gate` | preflight → git add（显式路径）→ commit → push → ls-remote |
| 「用 AgentTeams / 并行拆线 / 多站审计」 | `agent-teams-router` | 判断能否拆线 → 站点审计编排模板 |
| 「派子代理 / 分发 subagent / 上下文爆了 / 成员死了」 | `subagent-dispatch` | 选模型 + 上下文纪律五条 + 并发纪律 |
| 「记录变更 / 更新 CHANGES / 生成 REVIEW / 签名规则」 | `workflow-maintainer` | CHANGES 追加式 + 双签名例外 |
| 「做表格图 / 条形图 / 环形图 / donut / PowerPro 图」 | `pil-table-render` | 选第一节还是第二节，禁逐行几何覆盖 |
| 「team-share 加文章 / 发布文章 / 更新知识库」 | `team-share` | 自查清单 1–9 |

> 路由失效的典型症状：**没加载 skill 就开始手改站点/图**。凡任务里出现"站点 / 页面 / 图 / donut / 归档 / 推送 / 审计"任一词，先回到本表。



## 使用方式

- 把本目录整体放到 Agent 的全局 skills 目录（本机镜像：`C:\Users\zhuyanming\.dsh\skills`、`~/.config/opencode/skills`、`~/.kimi/skills`）。
- 不需要手动调用：说对应触发词（如"检查 RTL"、"写日报"、"服务器包"）即命中；每个 `SKILL.md` 头部都列了触发词。
- 新增 skill 时：独立目录 + `SKILL.md`，职责尽量合并进已有 skill，避免拆太碎；**新增后必须回填上面「任务路由表」**（否则以后的任务找不到入口）。

## Skill 一览（27 个）

### 芯片设计 / RTL

| Skill | 做什么 |
|---|---|
| `chip-design-supervisor` | 扮演资深芯片设计主管：设计评审、架构反馈、RTL 走查、技术讨论 |
| `rtl-code-review` | RTL 变更对抗性评审：时序风险/可维护性/综合友好度/接口一致性，severity 分级 + pass/fail 门禁 |
| `rtl-signal-trace` | 信号跨模块路径追踪（文本搜索）+ CDC 风险标记 + 模块依赖图/file_list 校验 |
| `regmap-pipeline` | 寄存器单一事实源：`regmap.md` → 寄存器文档（MD + CMSIS-SVD）+ SVA 断言 + RTL↔表一致性检查 |
| `spec-traceability` | spec↔code 轻量追溯：REQ_ID 分配/唯一性、spec hash 漂移检测、版本一致性审计 |
| `digital-backend-pitfalls` | 数字后端经验坑集：cell 引用稳定性（post-route 探针/999 哨兵）、跨工具 SDC、ICG 复位机制、蓝/红路径约束矩阵（DC/PT vs Innovus/ICC） |
| `netlist-metal-eco` | 网表级金属层 ECO：死锥分析找可复用门（`&~`/AND2B1/NAND2B1）+ 三步金属层重接线 + 极性判定 + 驱动/时序/功能风险闸门；判断"只改走线可不可行" |
| `local-simulation` | Windows 本机开源工具链（Icarus Verilog + GTKWave / Yosys）跑 Verilog/SV 模块，不依赖 VCS/UVM |
| `xilinx-suite` | Xilinx(AMD) FPGA/MPSoC 全工具链参考：Vivado XDC 约束、Tcl、综合实现、报告分析、CDC/时序例外（源自 MIT 开源库，按 HK1V11 VU440 场景改编） |
| `server-pack-overlay` | 服务器回传包（PACK_TAR_*.tar.gz）提取 + 合并式覆盖规则（SYNTHESIS/HDL/DV_TCON_C 三类包口径） |
| `version-archive` | 多版本归档目录维护规则：目录内 CHANGES.md 总览 + README 版本速查表 + 双轨记录 |
| `pil-table-render` | PIL 表格图渲染规范（两节）：一、PowerPro / teal 表头表格图（字体一致性/基线对齐/评审避坑）；二、STA csv 表格图（PT summary csv → to-signoff 同款表格图）+ 功耗/违例对比条形图 + 组成环形图（matplotlib） |
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
| `subagent-dispatch` | 派发 subagent 前的模型选择与确认协议（多模型分工：QWEN/GLM 等） |

### 可视化 / UI

| Skill | 做什么 |
|---|---|
| `blueprint-ui-style` | 用户首选的蓝图工程风（blueprint engineering aesthetic）：网站、HTML 报告、页面美化统一画风 |
| `anim-svg-site-audit` | 已建双版 SVG 站点的只读审计：图内数字↔正文↔数据源同源、Σ片=中心值、双版成对、?v=/索引同源、归档可追溯；A0–A9 报告模板 |
| `fireworks-tech-graph` | 技术图（架构/数据流/时序/状态机/ER/拓扑/时间线）生成并导出 SVG+PNG |
| `gpt-image-2-style-library` | GPT-Image2 风格库 + 工业级 prompt 模板（分类/风格标签/坑位/案例） |

### 工具 / 杂项

| Skill | 做什么 |
|---|---|
| `office-com-reader` | 读取加密/受保护的 Office（xlsx/docx/pptx）与 PDF：原生 COM API + pypdf + Acrobat COM 兜底，兼容企业 DLP 透明加密 |
| `colleague-skill`（distilly） | 把同事/关系/名人素材蒸馏成可复用的 Person Profile |

<!-- ymzhu 2026-11-02 18:05 -->
