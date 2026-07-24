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
   - Include clean modern styles (light/dark mode support).
   - Embed Markdown content **without the VitePress frontmatter block** (`--- title: ... ---`).
   - Put the Markdown source inside a `<script type="text/template" id="md">` block, then read it via `document.getElementById('md').textContent`. Do NOT put Markdown inside a JS template literal, because backslashes in code snippets (e.g., `\`, `\p`, `\H`) cause syntax errors.
   - Copy required images to the same directory.
   - **配图决策（先判断是否需要图，再决定怎么画）**:
     - **不需要画图**：纯文字、代码、表格就能讲清的内容，不配图，不调用任何绘图 skill。
     - **简单图**（几步的线性流程、简单状态/进展、简单对比）：直接用下方「Rich Visualization Components」中的 flow / timeline / badge / statbar / pcard 等 HTML 组件表达，**不调用** `fireworks-tech-graph`。
     - **复杂技术图**（架构图、数据流图、时序图、寄存器/地址映射、多层级结构等）：**优先调用 `fireworks-tech-graph` skill** 生成 SVG，引用为 `./<name>.svg`。SVG 优先于 PNG。
     - 无论哪种方式，图和组件都服务于读者体验：层次清晰、配色克制、重点突出，宁缺毋滥，不为配图而配图。
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
   - Include a custom image lightbox supporting click-to-zoom, mouse-wheel zoom, and drag pan.

   For **multi-page** articles, use the following layout (preferred by the user):
   - **Landing page** (`E:\project\team-share-public\<slug>\index.html`):
     - Hero: title, author line (ask user for attribution), one-sentence summary.
     - Show the overall framework/structure diagrams first.
     - Provide a grid of chapter cards; each card links to its chapter page.
   - **Chapter pages** (`E:\project\team-share-public\<slug>\<chapter>.html`):
     - Each page renders **one chapter** of Markdown.
     - Structure the chapter content with numbered `h2`/`h3` headings (e.g., `## 1. ...`, `### 1.1 ...`) so the TOC can display a clear hierarchy.
     - Include the same custom image lightbox.
     - Chapter file names should be short and in kebab-case or pinyin (e.g., `architecture.html`, `frame.html`, `encoding.html`).
   - **Persistent top navbar** on every page (landing + all chapters):
     - Sticky at the top, visible while scrolling.
     - Links to the landing page and every chapter.
     - Highlight the current page.
     - On mobile, allow horizontal scroll for overflow items.
   - **Left-side TOC** on every chapter page (desktop only):
     - Show the current page title (`h1`) and its in-page `h2`/`h3` headings only. **Do not** show cross-page chapter links here (those belong in the top navbar).
     - Keep the TOC sticky and always visible while scrolling the right-side content:
       - The TOC wrapper must stretch to the full height of the content container (`align-self: stretch`).
       - The TOC itself is sticky at a position below the top navbar.
     - Highlight the current heading while scrolling (scroll spy).
     - Smooth-scroll to the heading when a TOC item is clicked.
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
- 配图规则（两个 workflow 通用）：复杂技术图优先调用 `fireworks-tech-graph` skill 生成 SVG；简单图示直接用本文末尾的 Rich Visualization HTML 组件；能不画图就不画。一切以读者的阅读体验为先——层次清晰、配色克制、重点突出。

## Rich Visualization Components（推荐样式，用户确认 0717）

页面内容较丰富时（问题追踪/调试实录/进展报告类），在 markdown 中嵌入以下 HTML 组件增强可视化。范例页面：`hk1v11-longcode-420b-verification/debug-log.html`。

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
.stat .num { font-size: 30px; font-weight: 800; color: var(--accent); line-height: 1.2; }
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
