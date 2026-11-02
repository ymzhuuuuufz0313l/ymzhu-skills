---
name: team-share
description: Maintain the team-share VitePress knowledge base and publish standalone public articles. Trigger on: "team-share", "添加文章", "更新知识库", "发布文章", "分享文章", "公开分享", "导出单页", "add article", "new article", "share article", "publish to public".
---

# Team Share Skill

> 2026-11-02 精简版（563 → 约 190 行）：组件/lightbox/TOC 代码已迁入 `site-template/` 文件，PIL 表格图规范迁入 `pil-table-render` skill。迁移台账：`E:\project\team-share-public\SKILL_TRIM_LEDGER_20261102.md`；旧版备份 `SKILL.md.bak-20261102`。
> **原则：本文件只留"必须/禁止"；"怎么做"的细节放在被指向的文件或 skill 里。被指向的东西不读也不会违规，只会做得不够精细。**

## Trigger

- "team-share", "添加文章", "更新知识库", "发布文章", "add article", "new article" → Workflow A（主知识库）
- "分享文章", "公开分享", "导出单页", "share article", "publish to public", "独立页面" → Workflow B（独立公开文章）

## Workflow A: Add/update article in main knowledge base

1. 从用户请求提取 title、slug、正文。
2. 写 `E:\project\team-share\docs\<slug>.md`。
3. 更新侧边栏 `E:\project\team-share\docs\.vitepress\config.js`。
4. `cd "E:\project\team-share"` → `git add .` → `git commit -m "add/update article: <slug>"` → `git push origin main`。
5. 报告 URL：`https://ymzhuuuuufz0313l.github.io/team-share/<slug>.html`

## Workflow B: Publish a standalone public article

用户明确要把单篇文章公开分享、且不暴露主知识库时使用。每篇文章一个独立目录。

1. **提取元数据**：title、slug、正文、图片。只给了主题没给内容 → 先向用户要内容。
2. **前置检查**：GitHub 仓库 `https://github.com/ymzhuuuuufz0313l/team-share-public` 必须存在（不存在 → 让用户先建）；本地 `E:\project\team-share-public\`。
3. **复制骨架（强制，第一动作）**：`cp -r E:\project\team-share-public\site-template E:\project\team-share-public\<slug>`。
   - **禁止从零手写页面骨架**。骨架、文件集、head 引用顺序、导航、TOC、lightbox、fx 引擎全部来自模板，逐字使用。
   - 只改模板 `README.md`「内容槽」一节列出的槽位；固定文件清单与禁止清单也以该 README 为准。
   - 上位规范：`blueprint-ui-style` skill「新站搭建强制流程」章、「动画/静态双版 SVG 站点架构」章（v4）。
4. **选页面结构**：
   - **单页**（短文默认）：用 `page.html` 改名为 `index.html`，左侧 TOC 由 site.js 自动生成；`page-nav` 留空即可。
   - **多页**（长文，或用户要总览页）：`index.html` = landing（hero：标题 + 署名行〔向用户确认署名〕+ 一句话摘要；先放总体框架图；再放章节卡片网格）；每章一个 `page.html` 副本，文件名短、kebab-case 或拼音（`architecture.html`、`frame.html`）。
   - 文章过长时主动提议拆多页。
5. **填内容**：
   - 导航只改 `js/site.js` 顶部 `NAV` 数组；**最多 首页 + 9 个 sheet**，第 10 个起不进导航，只从首页章节卡进入。
   - 正文 Markdown 放进 `<script type="text/template" id="md">`（**不要**放进 JS 模板字符串，反斜杠会导致语法错误）；去掉 VitePress frontmatter（`--- title: ... ---`）。
   - 标题编号与级别规则见 Important Rules。
   - 组件只用模板 `css/style.css` 已有的，见下方「组件速查表」；**要新组件 → 先向用户提案，批准后写进模板，不许页面内私造**。
   - 图片复制到文章目录；配图规则见「配图决策」。
6. **fx 特效引擎**：骨架 `index.html` / `page.html` 已自带 `fx.css` / `fx.js` 双 tag，**禁止删除、禁止改引擎文件**；`?v=` 取全仓库当前统一值。规范见仓库根级 `PAGE_FX.md`。
7. **根占位页**：`E:\project\team-share-public\index.html` 不存在则建一个简单占位页；并在根导航登记新文章入口。
8. **更新** `README.md`，加上文章 URL。
9. **发布前门禁（强制）**：`python E:\project\team-share-public\scripts\check_article.py <slug>`，**必须 exit 0 才能提交**。门禁失败 → 修页面，不许绕过。
10. **提交推送**：`cd "E:\project\team-share-public"` → `git add .` → `git commit -m "Add shared article: <slug>"` → `git push origin main`。push 失败且原因是远程仓库不存在 → 让用户先建仓库。
11. **GitHub Pages**（未配置时指导用户）：仓库 Settings → Pages → Source: Deploy from a branch → `main` / `/ (root)`。
12. **报告 URL**：`https://ymzhuuuuufz0313l.github.io/team-share-public/<slug>/`

## Important Rules

- 主知识库：`E:\project\team-share\`，URL `https://ymzhuuuuufz0313l.github.io/team-share/`
- 独立文章：`E:\project\team-share-public\<slug>\`，URL `https://ymzhuuuuufz0313l.github.io/team-share-public/<slug>/`
- slug 与章节文件名用 kebab-case 或拼音；每篇文章独立目录；独立文章内**不要**链接回主知识库。
- **视觉风格（强制，2026-09-09 定稿）**：一律蓝图工程风；令牌、字体、组件以 `site-template/css/style.css` 为准（色值不一致时以该文件为准），设计说明见 `blueprint-ui-style` skill「设计系统（Design Tokens）」章。**禁止紫色玻璃拟态 / 紫渐变 / 霓虹光晕**（旧画风，已废弃）。
- **标题编号（强制）**：h2 `## 1. xxx`，h3 `### 1.1 xxx`，h4 `#### 1.1.1`，跟随父级编号；TOC 取自标题文本，所以 TOC 里也要看得到编号。
- **标题级别一致（强制）**：语义同级的标题必须同一 heading 级别；每个 sheet 内编号独立从 1 开始。
- **多页主题标题体系（强制，范本 `hk1v11-lc-cpuwr-history`）**：
  - 每页 h1 = Sheet 标题，带中文数字前缀（`# 一、XXX`），**不用** 01/02；正文从 `## 1.` 起编。
  - 长文档拆多 sheet 必须**重新起编**：原 `## X.Y` → `## Y.`、`### X.Y.Z` → `### Y.Z`；无编号小节补父级.序号。
  - 编号必须连续，**禁止插队号**（如 `## 1.5`）；后插章节要么全节顺延重编，要么排到末尾。
  - 重编号后同步正文交叉引用（"见 3.2 节"）与 page-nav 文字。
- **TOC（强制）**：左侧只显示本页 h1 + 页内 h2/h3，不放跨页链接（跨页在顶部导航）；sticky 常驻；scroll spy；点击平滑滚动；带 h3 的 h2 可折叠——以上由模板 `js/site.js` 实现，不要另写。
- **导航度量统一（强制）**：全站同一组度量，由模板 `style.css` 定死，禁止某几页私改。
- **图片 lightbox（强制）**：每个含图页面必须能 点击放大 / 滚轮缩放 / 拖拽 / Esc 与点遮罩关闭——由模板 `js/lightbox.js` 提供；缺了视为页面未完成，更新旧页面发现没有要顺手补上。
- **fx 双 tag（强制）**：每个页面必须带 `fx.css` / `fx.js` 双 tag（骨架已带）；缺失 = 特效层和动/静切换静默丢失，视为页面未完成。
- 防缓存 meta（骨架已带，不要删）：`Cache-Control: no-cache, no-store, must-revalidate` / `Pragma: no-cache` / `Expires: 0`。

## 组件速查表（实现全部在 `site-template/css/style.css`，只用类名，不复制 CSS）

| 组件 | 类名 | 用途 |
|---|---|---|
| 状态徽章 | `.badge` + `.badge-ok`（已解决）/ `.badge-warn`（待跟进）/ `.badge-bad` / `.badge-info` / `.badge-reco` | 状态标记，可放表格单元格内 |
| 侧别徽章 | `.badge` + `.badge-rtl` / `.badge-tx` / `.badge-dv` | 问题归属侧 |
| 统计条 | `.statbar > .stat > .num + .lbl` | 关键数字总览 |
| 步骤流程 | `.flow > .fbox` + `.farrow` | 几步的线性流程 |
| 时间线 | `.timeline > .titem > .tdate` | 事件进展 |
| 问题卡片 | `.pcard`（`.warn` 待跟进 / `.danger`）`> .prow > .k` | 现象 / 定位 / 解决分行 |
| 状态跟踪总账 | `.st-details > details > summary + .st-body`，日期 `.st-date` | 简单展示 + 复杂细节分离 |

- 旧页面里的旧类名 = 同义：`badge-fixed`→`badge-ok`、`badge-pending`→`badge-warn`、`pcard.pending`→`pcard.warn`。新页面用新名。
- 组件块内部写纯 HTML（`<b>/<code>/<span>`），不要写 markdown 语法（marked 不解析块级 HTML 内部）；`##`/`###` 标题保持 markdown 写法（TOC 依赖它）。
- **状态跟踪总账规则**：展示层（时间线 / 摘要）每条只写一句话 `<b>标题</b>——结论`，不许出现 commit 号 / 判据 / 证据链；细节放页面最底部（footer 前）的 `.st-details`，每主题一个 `<details>`，**块序严格时间倒序**（最新置顶），同主题多次更新用 `<br><br>` 追加、不删历史；最新/进行中主题加 `open`。范例：`hk1v11-synthesis-postpt-practice/index.html`。

## 配图决策（先判断要不要图，再决定怎么画）

- **不画**：文字、代码、表格能讲清的，不配图。宁缺毋滥，不为配图而配图。
- **简单图**（几步线性流程、简单进展、简单对比）：用速查表里的 flow / timeline / badge / statbar / pcard 组件，**不调用** `fireworks-tech-graph`。
- **流程图 / 调用关系 / 层次结构**：优先 **Graphviz** 自动布局（避免手写 SVG 坐标错位）——`winget install graphviz`；写 DOT（可用 cluster 分组，范例 `team-share-public/scripts/script_flow.dot`）；`dot -Tsvg in.dot -o out.svg`；引用 `./out.svg`。
- **架构图 / 数据流图 / 时序图 / UML**：调用 `fireworks-tech-graph` skill，按其「Workflow (Always Follow This Order)」章执行，产出 SVG（优先于 PNG）。
- **寄存器 / 地址映射图**：地址级特殊属性（如一个地址同时含两个 `chip_sel` 的字段）用「左侧色条 + 浅色背景带」：每个特殊地址一种强调色；地址标签同色加粗；caption 说明色条含义。仅限地址级；字段级差异（如 `LC_REG_MAPPING` 回拼字段）用红框或星标。示例：
  ```xml
  <rect x="90" y="308" width="810" height="122" fill="#ef4444" opacity="0.08" rx="8"/>
  <rect x="90" y="308" width="6" height="122" fill="#ef4444" rx="3"/>
  <text x="170" y="328" text-anchor="end" font-size="14" font-weight="700" fill="#ef4444">0x02 (2)</text>
  ```
- **动画 SVG（2026-10-26 定稿）**：适合动画的图（有自上而下阅读顺序、有明确高亮点；寄存器大图、拍重组网格、多阶段流程 / 时序图）除静态 SVG 外**必须**再产出动画版。硬约束：
  1. 纯 CSS、无 script、零数据改动、终态 = 静态图；静态版是事实源并保留为 fallback，页面 `<img>` 指向动画版（`anim/<name>.svg`）。
  2. **必须有常驻循环特效**（图常在页面下半部，一次性入场等用户滚到时已播完）；入场效果一律一次性、不循环。
  3. **用文字光带，不用扫光带**：光只在文字字形内滑过（与首页标题同技法），亮峰白色，**禁红棕/琥珀色亮带、禁整块色带擦过面板**；**短箭头（可见长度 < 80px）不加走线 / 流点特效**，要表达流向改用方框接力点亮（2026-11-02 定稿，见根级 `PAGE_FX.md` §3）。
  4. 规格唯一来源：**`blueprint-ui-style`「动画/静态双版 SVG 站点架构」章（v4）**——效果种类、周期、速度、颜色、目录都以它为准（如禁止缩放类动画、目录用 `anim/`）；配方见站内 `anim/MOTION_KIT.md` §4，通用技法见 `fireworks-tech-graph`「Animated SVG (for web-facing diagrams)」章。
- PIL 生成的表格图（teal 表头 / PowerPro 对比图类）：按 `pil-table-render` skill 执行。

## 自查清单（生成 / 更新页面后逐项确认）

1. `check_article.py <slug>` exit 0（自动覆盖：fx 双 tag 各 1 次、lightbox、TOC 折叠、标题编号、导航 ≤ 首页 + 9、尾签名）。
2. lightbox：正文每张图（含 SVG 引用图）点开能放大；滚轮缩放 0.5x–12x（以模板 js/lightbox.js 实际钳制为准）；可拖拽；Esc 与点遮罩关闭；打开时正文不滚动、关闭后恢复。
3. TOC：有 h3 子项的 h2 有箭头、无子项的没有；点箭头只折叠不跳转；子项折叠时滚到组内 h3，高亮落在父级 h2；默认全展开；h3 文字明显缩进在 h2 之后；TOC 里能看到 `1.` / `1.1` 编号。
4. 导航：当前页高亮；移动端可横向滚动；全站度量一致。
5. 动/静切换按钮在顶部导航（由 fx.js 注入，页面不得硬编码 `#motionToggle`）；`?motion=static` 下内容完整、无半透明残留。

<!-- ymzhu 2026-11-02 19:25 -->
