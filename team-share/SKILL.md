---
name: team-share
description: Maintain the team-share VitePress knowledge base and publish standalone public articles. Trigger on: "team-share", "添加文章", "更新知识库", "发布文章", "分享文章", "公开分享", "导出单页", "add article", "new article", "share article", "publish to public".
---

# Team Share Skill

## Trigger

When the user wants to add/update an article in the `team-share` VitePress knowledge base, or publish a standalone public article.

Trigger phrases include:
- "team-share", "添加文章", "更新知识库", "发布文章", "add article", "new article" → add to main knowledge base
- "分享文章", "公开分享", "导出单页", "share article", "publish to public", "独立页面" → publish standalone public article

## Workflow A: Add/update article in main knowledge base

1. **Identify article metadata**: Extract title, slug, and content from the user's request.
2. **Create/update Markdown file** at `E:\project\team-share\docs\<slug>.md`.
3. **Update sidebar** in `E:\project\team-share\docs\.vitepress\config.js`.
4. **Commit and push**:
   - `cd "E:\project\team-share"`
   - `git add .`
   - `git commit -m "add/update article: <slug>"`
   - `git push origin main`
5. **Report**: public URL `https://ymzhuuuuufz0313l.github.io/team-share/<slug>.html`

## Workflow B: Publish a standalone public article

Use this when the user explicitly asks to share a single article publicly without exposing the main knowledge base.

Each article gets its own directory so multiple shared articles can coexist.

1. **Identify article metadata**: Extract title, slug, content, and any images from the user's request.
2. **Check prerequisites**:
   - Public repository `team-share-public` must exist on GitHub at `https://github.com/ymzhuuuuufz0313l/team-share-public`
   - Local path: `E:\project\team-share-public\`
   - If the local directory does not exist, create it.
   - If the repository does not exist, instruct the user to create it first.
3. **Create article directory** at `E:\project\team-share-public\<slug>\`.
4. **Choose page structure**:
   - **Single-page** (default for short articles): one `index.html` with a floating TOC.
   - **Multi-page** (recommended when the article is long or the user wants an overview landing page): `index.html` landing page + one HTML file per major chapter.
5. **Generate standalone HTML**:
   - **视觉风格（强制，2026-09-09 用户定稿）：一律使用蓝图工程风（blueprint engineering aesthetic）**，完整设计令牌与组件规范见 `blueprint-ui-style` skill（生成页面前必须先加载它）。参考实现：`fusion-compiler-migration/`（共享 style.css 多页结构）与 `hk1v11-lc-cpuwr-history/`（自包含单页结构）。禁止紫色玻璃拟态/紫渐变/霓虹光晕（旧画风，已废弃）。
   - 每页 `<head>` 必须带 Google Fonts：`IBM Plex Mono:wght@400;500;600` + `Noto+Serif+SC:wght@600;900`（两个 preconnect + 一条 css2 link）。数字/代码/标签用 IBM Plex Mono，展示大标题用 Noto Serif SC 900。
   - 核心令牌（浅色 / 深色 prefers-color-scheme）：bg `#f4f1ea`/`#0e1420`、surface `#fffdf7`/`#161f31`、text `#1c2534`/`#e9e5d9`、muted `#667180`/`#9aa4b5`、accent（琥珀）`#b45309`/`#f0a137`、accent-strong `#92400e`/`#f6b95c`、accent-soft `#f7e8d4`/`#3a2f1a`、line `#ddd6c8`/`#2b3852`、chip `#efe9db`/`#1e2a44`、ink 渐变 `#0d1526→#131f38`、阴影 `0 12px 32px rgba(28,37,52,.10)`。
   - Embed Markdown content **without the VitePress frontmatter block** (`--- title: ... ---`).
   - Put the Markdown source inside a `<script type="text/template" id="md">` block, then read it via `document.getElementById('md').textContent`. Do NOT put Markdown inside a JS template literal, because backslashes in code snippets (e.g., `\`, `\p`, `\H`) cause syntax errors.
   - Copy required images to the same directory.
   - **配图决策（先判断是否需要图，再决定怎么画）**:
     - **不需要画图**：纯文字、代码、表格就能讲清的内容，不配图，不调用任何绘图 skill。
     - **简单图**（几步的线性流程、简单状态/进展、简单对比）：直接用下方「Rich Visualization Components」中的 flow / timeline / badge / statbar / pcard 等 HTML 组件表达，**不调用** `fireworks-tech-graph`。
     - **复杂技术图**（架构图、数据流图、时序图、寄存器/地址映射、多层级结构等）：根据图类型选择工具：
       - **流程图/调用关系图/层次结构图**：优先用 **Graphviz** 自动布局（见下方「Graphviz 使用方式」），避免手写 SVG 坐标错位。
       - **架构图/数据流图/时序图/UML 图**：优先调用 `fireworks-tech-graph` skill 生成 SVG（见下方「fireworks-tech-graph 使用方式」），引用为 `./<name>.svg`。SVG 优先于 PNG。
     - 无论哪种方式，图和组件都服务于读者体验：层次清晰、配色克制、重点突出，宁缺毋滥，不为配图而配图。
   **Graphviz 使用方式**

   当绘制流程图、调用关系图、层次结构图时，优先使用 Graphviz 自动布局。

   1. **安装**：`winget install graphviz`
   2. **编写 DOT 文件**：定义节点、边、分组（cluster），如 `scripts/script_flow.dot`
   3. **生成 SVG**：`dot -Tsvg input.dot -o output.svg`
   4. **引用**：`./output.svg`

   优点：自动布局，箭头、节点、标签规整，不需要手写坐标。

   **fireworks-tech-graph 使用方式**

   当绘制架构图、数据流图、时序图、UML 图时，调用 `fireworks-tech-graph` skill。

   工作流：
   1. 分类图类型
   2. 提取结构（节点、边、层次）
   3. 规划布局
   4. 加载样式（默认 style-1-flat-icon）
   5. 生成 SVG（Python list 方法或 `generate-from-template.py`）
   6. 验证（`validate-svg.sh`）
   7. 导出 PNG（`generate-diagram.sh` 或 `cairosvg`）
   8. 视觉检查（读取 PNG 确认无重叠）

   优点：精细控制每个元素的位置和样式，支持 8 种视觉风格。

   - Add cache-control meta tags to reduce browser caching:
     ```html
     <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
     <meta http-equiv="Pragma" content="no-cache">
     <meta http-equiv="Expires" content="0">
     ```

   **SVG register/address map conventions**

   For register or address space diagrams (e.g., checksum coverage, register byte mapping), when an address has a special cross-cutting property—such as one address containing fields for two different `chip_sel` values—use the following highlight style:

   - **Left colored accent bar + light tinted background band**: Draw a vertical bar on the left edge of the address block and a semi-transparent rounded rectangle behind the whole address block.
   - **One color per special address**: Use a distinct accent color for each address so readers can visually group the rows.
   - **Colored address label**: Change the address label text to the same accent color and make it bold.
   - **Caption note**: Add a line in the caption explaining what the colored bars mean.

   Example SVG snippet:
   ```xml
   <!-- Highlight for a dual-chip_sel address (e.g., 0x02) -->
   <rect x="90" y="308" width="810" height="122" fill="#ef4444" opacity="0.08" rx="8"/>
   <rect x="90" y="308" width="6" height="122" fill="#ef4444" rx="3"/>
   <text x="170" y="328" text-anchor="end" font-size="14" font-weight="700" fill="#ef4444">0x02 (2)</text>
   ```

   Use this style only when the property is at the **address level**. For per-field differences (e.g., `LC_REG_MAPPING` 回拼字段 in `chip_sel=1` maps), continue using per-field markers such as red borders or star icons instead.

   For **single-page** articles:
   - Include a **floating table of contents (TOC)** on the left side (desktop) or a collapsible drawer (mobile):
     - Generate TOC automatically from rendered `h2`/`h3` headings.
     - Add anchor IDs to each heading.
     - Highlight the current section while scrolling (scroll spy).
     - Smooth-scroll to section when a TOC item is clicked.
     - **必须**支持 h2 分组折叠：带 h3 子项的 h2 条目前有箭头可展开/收起子项，实现见文末「TOC 折叠交互（每页必须包含）」。
   - **必须**包含图片 lightbox（点击放大 / 滚轮缩放 / 拖拽移动），完整实现见文末「图片 Lightbox（每页必须包含）」，不得省略。

   For **multi-page** articles, use the following layout (preferred by the user):
   - **Landing page** (`E:\project\team-share-public\<slug>\index.html`):
     - Hero: title, author line (ask user for attribution), one-sentence summary.
     - Show the overall framework/structure diagrams first.
     - Provide a grid of chapter cards; each card links to its chapter page.
   - **Chapter pages** (`E:\project\team-share-public\<slug>\<chapter>.html`):
     - Each page renders **one chapter** of Markdown.
     - Structure the chapter content with numbered `h2`/`h3` headings — this is **mandatory**: `## 1. ...`, `## 2. ...` for h2 and `### 1.1 ...`, `### 1.2 ...` for h3 (numbering follows the parent h2), so the TOC shows a clear numbered hierarchy.
     - **必须**包含同一个图片 lightbox（见文末「图片 Lightbox（每页必须包含）」），landing 页和每个 chapter 页都要有。
     - Chapter file names should be short and in kebab-case or pinyin (e.g., `architecture.html`, `frame.html`, `encoding.html`).
   - **Persistent top navbar** on every page (landing + all chapters):
     - Sticky at the top, visible while scrolling.
     - Links to the landing page and every chapter.
     - Highlight the current page.
     - On mobile, allow horizontal scroll for overflow items.
     - **数量上限（强制，2026-09-09 用户定稿）：导航条最多放 首页 + 9 个 sheet**；第 10 个起的 sheet 不进导航（只从首页章节卡进入），防止导航拥挤/溢出截断（synthesis-integration-flow-guide 12 页实测教训）。
     - **尺寸统一（强制）：全站所有页面（含 landing）导航使用同一组度量**——landing 导航 max-width 1120px、**sheet 页导航 max-width 1288px（用户指定 +15%）** / padding 10px 24px / flex-wrap:wrap 换行兜底；品牌 14px；链接 13.5px、padding 5px 10px；搜索按钮 margin-left:auto 钉最右。禁止某几页私改度量（2026-09-09 首页 vs 子页不统一教训）。
   - **Left-side TOC** on every chapter page (desktop only):
     - Show the current page title (`h1`) and its in-page `h2`/`h3` headings only. **Do not** show cross-page chapter links here (those belong in the top navbar).
     - Keep the TOC sticky and always visible while scrolling the right-side content:
       - The TOC wrapper must stretch to the full height of the content container (`align-self: stretch`).
       - The TOC itself is sticky at a position below the top navbar.
     - Highlight the current heading while scrolling (scroll spy).
     - Smooth-scroll to the heading when a TOC item is clicked.
     - **必须**支持 h2 分组折叠：带 h3 子项的 h2 条目前有箭头可展开/收起子项，实现见文末「TOC 折叠交互（每页必须包含）」。
   - **Bottom page navigation** on every chapter page:
     - Previous / next chapter links.
6. **Ensure root placeholder**: If `E:\project\team-share-public\index.html` does not exist, create a simple placeholder page.
7. **Update README.md** with the article URL.
8. **Commit and push**:
   - `cd "E:\project\team-share-public"`
   - `git add .`
   - `git commit -m "Add shared article: <slug>"`
   - `git push origin main`
   - If push fails because the remote repository does not exist, ask the user to create `team-share-public` on GitHub first.
9. **Configure GitHub Pages** (instruct user if not done):
   - Repository `team-share-public` → Settings → Pages
   - Source: **Deploy from a branch**
   - Branch: `main`, folder: `/ (root)`
10. **Report**: public URL `https://ymzhuuuuufz0313l.github.io/team-share-public/<slug>/`

## Important Rules

- Main knowledge base: `E:\project\team-share\`, URL `https://ymzhuuuuufz0313l.github.io/team-share/`
- Public standalone articles: `E:\project\team-share-public\<slug>\`, URL `https://ymzhuuuuufz0313l.github.io/team-share-public/<slug>/`
- Use kebab-case or pinyin for slugs and chapter file names.
- Each shared article must be in its own directory so multiple articles can coexist.
- Do not include links back to the main knowledge base in standalone articles.
- If the user only provides a topic without content, ask for the content before creating the file.
- When an article grows too long for a single page, proactively propose the multi-page landing + chapters structure.
- **标题编号（强制）**：正文标题必须带编号——h2 用 `## 1. xxx`、`## 2. xxx` 顺序编号，h3 用 `### 1.1 xxx`、`### 1.2 xxx`、`### 2.1 xxx` 跟随所属 h2 编号。TOC 直接取自标题文本，因此 TOC 里也必须能看到 `1.` / `1.1` 这样的编号。
- **标题级别一致性（强制，2026-09-09 用户补充）**：语义同级的标题必须用同一 heading 级别——不能让同级标题有的 h2 有的 h3（TOC 里会看起来层级错乱）。每个 sheet 内编号独立从 1 开始。**Sheet 自身的序号用中文数字**（一/二/三/四/五），不用 01/02 阿拉伯编号。
- **多页主题标题体系（强制，2026-09-09 用户定稿，范本 hk1v11-lc-cpuwr-history）**：
  - 每页 h1 = Sheet 标题，带中文数字前缀（`# 一、XXX`）；正文一律从 h2 `## 1.` 起编，h3 `### 1.1`，h4 `#### 1.1.1`。
  - **一篇长文档拆成多 sheet 时，必须重新起编**——禁止把原文档的连续编号带进子页（否则出现 sheet 内顶端就是 `## 1.1`、sheet 2 从 `## 2.1` 开始的错乱）；原 `## X.Y` → `## Y.`、`### X.Y.Z` → `### Y.Z`，无编号的小节标题（如 `### 证据 ①`）补父级.序号。
  - **编号必须连续，禁止"插队号"**——后插章节不许用 `## 1.5` 这种号（LC_CPUWR regmap 页实测问题），要么插入后全节顺延重编，要么排到末尾。
  - 重编号后必须同步正文交叉引用（"见 3.2 节"等）与 page-nav 文字。
  - TOC 缩进规范：h2 条目 `padding-left: 24px`（预留箭头槽位，无折叠箭头的主题也预留，保持全站一致），h3 `padding-left: 38px`。
- 配图规则（两个 workflow 通用）：复杂技术图优先调用 `fireworks-tech-graph` skill 生成 SVG；简单图示直接用本文末尾的 Rich Visualization HTML 组件；能不画图就不画。一切以读者的阅读体验为先——层次清晰、配色克制、重点突出。
- **图片交互规则（强制）**：任何包含图片的独立 HTML 页面（single-page、landing、chapter 都算）都必须实现文末「图片 Lightbox」的完整交互——点击放大、滚轮缩放、拖拽移动、Esc/点击关闭。缺了 lightbox 视为页面未完成；更新已有页面时如果发现没有，要顺手补上。

## Rich Visualization Components（推荐样式，用户确认 0717）

页面内容较丰富时（问题追踪/调试实录/进展报告类），在 markdown 中嵌入以下 HTML 组件增强可视化。范例页面：`hk1v11-longcode-420b-verification/debug-log.html`。

**配色体系（2026-09-09 起）：以下组件全部继承蓝图工程风令牌**（`var(--accent)` 琥珀、`var(--accent-soft)`、`var(--chip)` 等，定义见上文「视觉风格（强制）」）；数字/编号/日期类元素（`.num`、`.tdate`、`.k`）字体一律 IBM Plex Mono。

**使用规则**：
- 组件 CSS 统一放在该页 `<style>` 末尾，必须含暗色模式变体（`@media (prefers-color-scheme: dark)`）。
- `##`/`###` 标题保持 markdown 写法（左侧 TOC 依赖 h2/h3 生成）；HTML 组件块内部用纯 HTML 标签（`<b>/<code>/<span>`），不要再写 markdown 语法（marked 默认不解析块级 HTML 内部）。
- 表格单元格内可以放 `<span class="badge">` 等内联 HTML，正常渲染。

### 1. 状态/侧别徽章 badge

```html
<span class="badge badge-fixed">🔵 已解决</span>
<span class="badge badge-pending">🟡 待跟进</span>
<span class="badge badge-rtl">RTL 侧</span>   <!-- 红 -->
<span class="badge badge-tx">TX 侧</span>     <!-- 蓝 -->
<span class="badge badge-dv">DV 侧</span>     <!-- 紫 -->
```

```css
.badge { display: inline-block; padding: 2px 12px; border-radius: 999px; font-size: 13px; font-weight: 600; line-height: 1.6; white-space: nowrap; }
.badge-fixed   { background: #dcfce7; color: #166534; }
.badge-pending { background: #fef9c3; color: #854d0e; }
.badge-rtl     { background: #fee2e2; color: #991b1b; }
.badge-tx      { background: #dbeafe; color: #1e40af; }
.badge-dv      { background: #f3e8ff; color: #6b21a8; }
@media (prefers-color-scheme: dark) {
  .badge-fixed   { background: #14532d; color: #86efac; }
  .badge-pending { background: #713f12; color: #fde047; }
  .badge-rtl     { background: #7f1d1d; color: #fca5a5; }
  .badge-tx      { background: #1e3a8a; color: #93c5fd; }
  .badge-dv      { background: #581c87; color: #d8b4fe; }
}
```

### 2. 统计条 statbar

```html
<div class="statbar">
  <div class="stat"><div class="num">8</div><div class="lbl">定位问题总数</div></div>
  <div class="stat"><div class="num ok">6</div><div class="lbl">🔵 已解决</div></div>
  <div class="stat"><div class="num warn">2</div><div class="lbl">🟡 待跟进</div></div>
</div>
```

```css
.statbar { display: flex; gap: 16px; flex-wrap: wrap; margin: 24px 0 8px; }
.stat { flex: 1; min-width: 130px; text-align: center; border: 1px solid var(--line); border-radius: 14px; padding: 14px 8px; background: var(--surface); }
.stat .num { font-family: "IBM Plex Mono", Consolas, monospace; font-size: 30px; font-weight: 600; color: var(--accent); line-height: 1.2; }
.stat .num.ok { color: #16a34a; }
.stat .num.warn { color: #eab308; }
.stat .lbl { font-size: 13px; color: var(--muted); margin-top: 4px; }
```

### 3. 步骤流程图 flow

```html
<div class="flow">
  <div class="fbox"><b>① 步骤名</b><br/>说明文字<br/><code>产出文件</code></div>
  <div class="farrow">→</div>
  <div class="fbox"><b>② 步骤名</b><br/>...</div>
</div>
```

```css
.flow { display: flex; gap: 10px; align-items: stretch; flex-wrap: wrap; margin: 18px 0; }
.fbox { flex: 1; min-width: 210px; border: 1.5px solid var(--accent); border-radius: 12px; padding: 14px 16px; background: var(--accent-soft); font-size: 14.5px; }
.fbox b { color: var(--accent); }
.farrow { align-self: center; font-size: 26px; color: var(--accent); font-weight: 800; }
```

### 4. 时间线 timeline

```html
<div class="timeline">
  <div class="titem"><span class="tdate">07/15</span>事件描述 🔵</div>
  <div class="titem"><span class="tdate">07/17</span>事件描述 ✅</div>
</div>
```

```css
.timeline { border-left: 3px solid var(--accent); margin: 16px 0 8px 14px; padding-left: 22px; }
.titem { position: relative; margin-bottom: 14px; font-size: 15px; }
.titem::before { content: ''; position: absolute; left: -29px; top: 7px; width: 11px; height: 11px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
.tdate { font-weight: 700; color: var(--accent); margin-right: 8px; }
```

### 5. 问题卡片 pcard（现象/定位/解决分行）

```html
<div class="pcard">           <!-- 待跟进用 <div class="pcard pending"> -->
<div class="prow"><span class="k">状态</span><span><span class="badge badge-fixed">🔵 已解决</span> <span class="badge badge-tx">TX 侧</span> <span class="badge">07/17</span></span></div>
<div class="prow"><span class="k">现象</span><span>...</span></div>
<div class="prow"><span class="k">定位</span><span>...</span></div>
<div class="prow"><span class="k">解决</span><span>...</span></div>
</div>
```

```css
.pcard { border: 1px solid var(--line); border-left: 5px solid #16a34a; border-radius: 12px; padding: 14px 20px; margin: 14px 0 26px; background: var(--surface); }
.pcard.pending { border-left-color: #eab308; }
.prow { display: grid; grid-template-columns: 52px 1fr; gap: 10px; margin: 7px 0; font-size: 15px; }
.prow .k { font-weight: 700; color: var(--accent); }
.prow code { font-size: 13px; }
```

## 图片 Lightbox（每页必须包含）

任何含图片的独立 HTML 页面都必须带以下 lightbox，读者点击图片后可放大、滚轮缩放、拖拽移动。参考实现：`hk1v11-longcode-420b-verification/debug-log.html`。

**1. 正文图片样式**（`cursor: zoom-in` 提示可点击）：

```css
img {
  max-width: 100%;
  border-radius: 10px;
  border: 1px solid var(--line);
  cursor: zoom-in;
  display: block;
  margin: 28px auto;
  transition: box-shadow 0.2s ease;
}
img:hover { box-shadow: 0 8px 30px rgba(0,0,0,0.12); }
```

**2. Lightbox CSS**：

```css
.lightbox {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.25s ease, visibility 0.25s ease;
  cursor: grab;
}
.lightbox.active { opacity: 1; visibility: visible; }
.lightbox img {
  max-width: none;
  max-height: none;
  border: none;
  border-radius: 4px;
  cursor: grab;
  transform-origin: center center;
  transition: none;
  margin: 0;
}
.lightbox img.grabbing { cursor: grabbing; }
.lightbox .hint {
  position: absolute;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255,255,255,0.7);
  font-size: 13px;
  pointer-events: none;
  user-select: none;
  background: rgba(0,0,0,0.4);
  padding: 6px 14px;
  border-radius: 20px;
}
.lightbox .close {
  position: absolute;
  top: 20px;
  right: 24px;
  color: rgba(255,255,255,0.8);
  font-size: 32px;
  line-height: 1;
  cursor: pointer;
  user-select: none;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s;
}
.lightbox .close:hover { background: rgba(255,255,255,0.15); color: #fff; }
```

**3. Lightbox HTML**（放在 `</body>` 前）：

```html
<div class="lightbox" id="lightbox">
  <span class="close" id="lightbox-close">&times;</span>
  <img id="lightbox-img" src="" alt="">
  <div class="hint">滚轮缩放 · 拖拽移动 · Esc 或点击空白处关闭</div>
</div>
```

**4. Lightbox JS**（放在渲染 markdown 的 `marked.parse(...)` 之后；`.article img` 选择器要与正文容器实际 class 一致）：

```html
<script>
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightbox-img');
  const lightboxClose = document.getElementById('lightbox-close');
  let scale = 1, translateX = 0, translateY = 0;
  let isDragging = false, startX = 0, startY = 0, initialTranslateX = 0, initialTranslateY = 0;
  function updateTransform() { lightboxImg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`; }
  function resetTransform() { scale = 1; translateX = 0; translateY = 0; updateTransform(); }
  function openLightbox(src) { lightboxImg.src = src; resetTransform(); lightbox.classList.add('active'); document.body.style.overflow = 'hidden'; }
  function closeLightbox() { lightbox.classList.remove('active'); document.body.style.overflow = ''; setTimeout(() => { lightboxImg.src = ''; }, 250); }
  document.querySelectorAll('.article img').forEach(img => img.addEventListener('click', () => openLightbox(img.src)));
  lightboxClose.addEventListener('click', (e) => { e.stopPropagation(); closeLightbox(); });
  lightbox.addEventListener('click', (e) => { if (e.target === lightbox) closeLightbox(); });
  lightbox.addEventListener('wheel', (e) => { e.preventDefault(); scale = Math.min(Math.max(0.5, scale + (e.deltaY > 0 ? -0.15 : 0.15)), 5); updateTransform(); }, { passive: false });
  lightboxImg.addEventListener('mousedown', (e) => { e.preventDefault(); isDragging = true; lightboxImg.classList.add('grabbing'); startX = e.clientX; startY = e.clientY; initialTranslateX = translateX; initialTranslateY = translateY; });
  window.addEventListener('mousemove', (e) => { if (!isDragging) return; translateX = initialTranslateX + (e.clientX - startX); translateY = initialTranslateY + (e.clientY - startY); updateTransform(); });
  window.addEventListener('mouseup', () => { isDragging = false; lightboxImg.classList.remove('grabbing'); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox(); });
</script>
```

**自查清单**（生成/更新页面后逐项确认）：
1. 正文每张图片点击后能打开 lightbox（注意 JS 选择器要覆盖正文容器内所有 `img`，含 SVG 引用图）。
2. 滚轮可缩放（0.5x–5x）、按住可拖拽、Esc 和点击遮罩可关闭。
3. lightbox 打开时正文禁止滚动（`body overflow: hidden`），关闭后恢复。

## TOC 折叠交互（每页必须包含）

左侧 TOC 中，带 `h3` 子项的 `h2` 条目（`.toc-h2`）前面必须有一个箭头，点击可展开/收起对应的 `h3` 子项，方便读者只看一级结构再逐组展开。默认全部展开。

**1. CSS**：

```css
.toc a.toc-h2 { position: relative; padding-left: 24px; } /* 所有 h2 统一预留箭头槽位，无子项的 h2 也与有子项的视觉对齐（2026-09-09 用户要求） */
/* h3 子项缩进：文字起始位置必须明显在 h2 父项文字之后（父项 padding-left 24px，子项在此基础上再缩进） */
.toc a.toc-h3 { padding-left: 38px; font-size: 13px; }
.toc a.toc-parent { position: relative; }
.toc .toc-arrow {
  position: absolute;
  left: 6px;
  top: 50%;
  transform: translateY(-50%) rotate(90deg); /* 展开时箭头朝下 */
  font-size: 11px;
  color: var(--muted);
  cursor: pointer;
  user-select: none;
  padding: 2px 4px;
  transition: transform 0.15s ease;
}
.toc a.collapsed .toc-arrow { transform: translateY(-50%) rotate(0deg); } /* 收起时箭头朝右 */
.toc .toc-arrow:hover { color: var(--accent); }
```

**2. JS**（放在 TOC 生成代码之后、scroll spy 之前）：

```js
// Collapsible TOC groups: h2 entries with h3 children get a toggle arrow
const tocLinksAll = Array.from(toc.querySelectorAll('a'));
tocLinksAll.forEach((link, i) => {
  if (!link.classList.contains('toc-h2')) return;
  const children = [];
  for (let j = i + 1; j < tocLinksAll.length && tocLinksAll[j].classList.contains('toc-h3'); j++) {
    children.push(tocLinksAll[j]);
  }
  if (!children.length) return;
  link.classList.add('toc-parent');
  const arrow = document.createElement('span');
  arrow.className = 'toc-arrow';
  arrow.textContent = '▸';
  link.prepend(arrow);
  children.forEach(c => { c.parentLink = link; });
  arrow.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const collapsed = link.classList.toggle('collapsed');
    children.forEach(c => { c.style.display = collapsed ? 'none' : ''; });
  });
});
```

**3. Scroll spy 调整（关键）**：当前小节是被隐藏的 h3 时，高亮要落到它的父级 h2 上，否则 TOC 里看不到任何高亮。在原来"给 active 链接加高亮"的位置改成：

```js
if (current) {
  let active = tocLinks.find(a => a.getAttribute('href') === '#' + current);
  if (active && active.style.display === 'none' && active.parentLink) {
    active = active.parentLink; // 子项被折叠时，高亮父级 h2
  }
  if (active) active.classList.add('active');
}
```

**自查清单**：
1. 有 h3 子项的 h2 条目左侧有箭头；无子项的 h2 没有箭头。
2. 点箭头只折叠/展开，不触发跳转；点条目文字仍正常跳转。
3. 子项被折叠时，滚动到该组内任意 h3，高亮显示在父级 h2 上。
4. 默认状态为全部展开。
5. h3 条目（如 `1.1`）的文字起始位置必须明显缩进在 h2 条目（如 `1.`）文字之后，不能对齐或反超。
6. TOC 中 h2 条目必须带编号（`1.` `2.` `3.`…），h3 条目必须带子编号（`1.1` `1.2` `2.1`…）；编号来自正文标题本身（见 Important Rules 的标题编号规则）。

---

## 图表文字渲染规范（PIL 表格图，如 PowerPro 六组图 / 对比图）

做 PIL 表格图（`render_table` / 自写 renderer，teal 表头风格）时，文字渲染必须遵守以下规则（本规范来自 2026-08-27 PowerPro 0826 六组图多轮评审沉淀）：

### 1. 字体选择：同一元素内字体必须一致，不同元素可以不同字体

- **同一元素**（一个标题条 / 一个表头单元格 / 一个数据单元格）内的全部字符必须使用**同一个字体对象**整串渲染（`draw.text(pos, whole_string, font=f)` 一次画完），**禁止**在元素内部按字符切换字体（不要用逐字符 `draw_mixed` 中英混排——两字体 ascent/baseline 不同必然导致元素内字符上下错位"不在一行"）。
- **不同元素之间**允许不同字体（标题行与数据部分不需要同字体）：
  - 标题条 / 表头 → CJK 粗体（中文为主）
  - 数据单元格 → 沿用该图已认可的字体体系即可（如 msyh 常规/粗体）；如需数字列更整齐，可对纯英文/数字单元格改用等宽字体——但**必须先给用户确认**，不要擅自改变整体字体风格。
- ⚠️ 教训：不要为了"统一"擅自更换全图字体（NotoSansSC/Deng 等线都试过）——用户对已认可的视觉密度很敏感，任何全局字体更换都会被判"不如之前"；只修对齐问题，不动字体风格。

### 2. 基线对齐：每格整串渲染后按字体 ascent 垂直居中

- 不要用 `(cell_h - font.size)//2` 近似居中——不同字体的 `size` 与 `ascent` 关系不同。
- 用 `font.getmetrics()[0]` 取 ascent，`y_text = cell_y + (cell_h - ascent) // 2` 计算绘制起点。
- 同一行内所有单元格共用同一 `cell_y` → 全行字符上沿/下沿齐平。

### 3. 标题/表头

- 标题条（teal 底）用 CJK 粗体整串渲染；文字过长时**先量宽度**（`font.getlength(title)`）确认不超过画布，超宽要压缩文案而不是依赖自动截断；副标题放不下就省略（渲染器会把放不下的副标题静默丢弃，不要留悬念）。
- 表头同标题：CJK 粗体整串 + ascent 居中。

### 4. 评审迭代避坑记录（PowerPro 0826 六组图实测）

- **用户要的是"字体平行"（基线对齐），不是"字体统一"**——曾三次尝试全局换字体（NotoSansSC / Deng / 数据格等宽化）全部被否："回到之前的图""反而非常难看"。正确做法：保持已认可视觉的一切不变，只把混排改成整串渲染。
- 行高亮/单元格高亮：0826 行只高亮**指定列的单格**（teal 字 + 浅青底），不要整行背景；其余行列保持默认（INK + 白/斑马）。
- 数值精度：Total 等数值统一 2 位小数四舍五入（`.2f`），不同来源（报告 / Excel 汇总）要一致。
- 造图脚本必须可重跑（数据源硬编码 CSV 路径 + 脚本注释数据来源），禁止手改 PNG。

<!-- ymzhu 2026-09-20 11:04 -->
