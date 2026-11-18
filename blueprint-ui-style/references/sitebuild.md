# 新站搭建强制流程（触发读取链/核心框架定死/模块清单/内容即模块/强约束）

> 2026-11-18 从 SKILL.md 原文整体迁出（内容未改，仅落位）。本文件是被指向的参考，不读不违规、只做得不够精细。

## 新站搭建强制流程（站点 = 固定模块组装，强约束，2026-10-28 用户定调）

> 用户口径：**"当我做一个新网站时，读定死的 skill，按我定死的架构做，强限制；所有内容都只是模块化的内容。"**
> 含义：新站点不是"创作"，是**从固定模块库组装**。除内容数据与章节结构外的一切（色板/字体/组件/引擎/目录/动效管线/验证门）均为固定模块，**禁止自创**；任何偏离须先获用户明示批准。

### 0. 触发与强制读取链（顺序不可省）

用户要求"做新网站 / 新站点 / 加一个站"（team-share-public 内或独立蓝图风站点）时，动手前**依次读完**：

1. **本 skill 全文**（视觉 tokens、组件模板、动画实战章、v4 架构章、本章）；
2. **站点骨架模板**：`E:\project\team-share-public\site-template\`（README + index.html/page.html 骨架 + 引擎/组件逐字副本）——**建新站的第一动作就是复制这个目录**；
3. **组件模板源码（活模板）**：`E:\project\team-share-public\hk1v11-synthesis-postpt-practice\` 的 `css/style.css`（组件唯一事实源）、`js/site.js`、`js/lightbox.js`、`fx.css`、`fx.js`（v4 引擎）；
4. **参考站的动效事实源**：`hk1v11-longcode-420b-verification/anim/MOTION_KIT.md`（v4 kit）。

> **活模板路径兜底**：上列 `E:\project\...` 活模板均指本机当前实际位置；若某路径失效（目录被移动/删除/改名），先在 `team-share-public` 仓库内按目录名重新定位，定位不到再向用户确认新路径——**禁止凭失效路径硬做或凭空重建骨架/模板**。

### 0.5 核心框架定死（2026-10-28 用户定调："不然模型会放飞自我"）

**骨架、目录、文件集、技术栈、引用顺序全部定死，模型只填内容槽，不写结构。** 唯一骨架来源 = `site-template/`（禁止从零手写页面骨架）；固定文件（css/style.css、js/site.js 除 NAV 数组、js/lightbox.js、js/marked.min.js、fx.js、fx.css、页面骨架的 head/导航/容器/脚本顺序）逐字使用禁改；内容槽清单与禁止清单见 `site-template/README.md`（新框架/新依赖/新组件/新目录层级/第二套按钮/绕过双版管线，一律 ❌）。

### 1. 站点模块清单（目录契约，新站只允许由这些模块组成）

| 模块 | 来源 | 规则 |
|---|---|---|
| `index.html` + 子页面 | 复制 `site-template/index.html` + `page.html` 骨架 | 只改内容（标题/章节/数据/链接）；导航结构、head 引用、组件类名不动 |
| `css/style.css` | `site-template/` 逐字副本（源于 practice 站） | **token 与组件禁改**；只允许追加站点专属内容类（须最小化） |
| `js/site.js` · `js/lightbox.js` | `site-template/` 逐字副本（源于 practice 站） | site.js 唯一内容槽 = 顶部 NAV 数组，其余禁改 |
| `fx.css` · `fx.js` | `site-template/` 逐字副本（= 全仓库引擎，9 处一致） | **禁改**；引用统一带 `?v=N`，引擎升级由全仓库统一 bump |
| `<name>.svg`（静态）+ `anim/<name>.svg` + `anim/make_anim_<name>.py` | v4 双版管线 | 按 v4 架构章 + MOTION_KIT v4；HTML 只引用动画版 |
| `anim/MOTION_KIT.md` | 从 longcode 站复制 | 改"路径"与"分图规格"两节为本站实际；kit CSS 与铁律禁改 |
| `images/` 骨架（`archive/` + `tools/`） | 建站时新建空目录 | **建站即建** `images/archive/`（含 `qa/`）与 `images/tools/` 骨架；换版归档按「图版生命周期与归档标准」章执行 |
| 根导航登记 | team-share-public 根 `index.html` | 新站入口登记进站点列表 |

### 2. 内容即模块

页面内容只允许使用「站点组件模板」章定义的既有组件组装：hero / chapter-card 系 / 表格（table-wrap 自动增强）/ 图组（lb-thumb + lightbox + 双版 SVG）/ TOC / page-nav。**不发明新组件**；确需新组件 → 先向用户提案获批，批后写回本 skill 组件章（模块库唯一增长途径）。

### 3. 强约束声明

- 色板/字体/圆角/阴影/动效时序：只取本 skill tokens，禁临时调色、禁引入新字体新框架（零依赖原则：原生 HTML/CSS/JS）。
- frontend-design 同时被触发时仅作质量清单（规则 0）；fireworks 画嵌站图必须换站点色板。
- 双版 SVG 走 v4 管线与验证门（§4 四条，一项不过不交付）。
- 完成动作固定：本地 file:// 预览 → 问用户"要不要截图验收" → 更新站点 `anim/MOTION_KIT.md` 分图规格 → git 提交信息按站点惯例（改什么/为什么/验证结果）。

### 4. 新站交付门（checklist，全勾才交付）

- [ ] 目录契约齐（上表模块一个不少，无多余自创文件）
- [ ] `md5` 校验 fx.js/fx.css 与仓库其他副本一致
- [ ] 成对完整性扫描过（`scripts/check_anim_pairs.py`，无孤儿动画版）
- [ ] v4 验证门四条全过（成对完整/切换零位移/稳态可辨/生成物零漂移）
- [ ] 根导航已登记；页面在 file:// 与构建预览下均正常

<!-- ymzhu 2026-11-18 14:30 -->
