# 站点组件模板（Token 增补/导航/表格/图片/卡片）+ 截图验收流程

> 2026-11-18 从 SKILL.md 原文整体迁出（内容未改，仅落位）。本文件是被指向的参考，不读不违规、只做得不够精细。

## 站点组件模板（2026-10-21 全站升级定稿，加分项）

> 参考实现（活模板，可直接抄）：`E:\project\team-share-public\hk1v11-synthesis-postpt-practice\`
> `css/style.css`（组件唯一事实源）· `js/site.js`（导航/TOC/表格/代码块增强）· `js/lightbox.js`（图片查看器）。
> 以下组件经 8 成员 UI 审查 3 轮对账验证（24 份底稿在 HK1V11/script/_chapter_viz/uireview*.md）。

### Token 增补（在原配色表之上）

- `--muted` 浅色改 `#5b6675`（对比度 5.2:1 过 AA）；`--warn` 从 accent 拆出：浅 `#8a5305` / 深 `#eab308`（警告≠强调，避免琥珀泛滥）。
- 动效时序三档：`--t-fast: .12s / --t-med: .18s / --t-slow: .28s`，全站 transition 统一引用。
- `body { font-variant-numeric: tabular-nums }` 全局表格数字对齐；`.article > p { max-width: 46em }`（CJK ≈46 字/行）。

### 顶部导航（两行 + 混合下拉 + 抽屉）

- **两行结构**：行 1 = 主流程平铺链接 + 搜索（右，`margin-left:auto`）；行 2 = 下拉组（实战复盘 ▾ / 学习路径 ▾）+ GitHub（右）。`flex-direction: column`，行 2 与行 1 同字号同色（不做次级灰小字——实测显乱）。
- **混合下拉**（比纯 hover 好，触屏可用的主流做法）：CSS `:hover/:focus-within` 即开 + **caret ▾ 单独 click 置顶**（`.open` 类钉住）；label 点击仍导航；Esc/点外关闭；`aria-expanded`。
- **移动端（≤768px）**：hamburger 三线钮（边框 `--muted`）→ 全导航抽屉（absolute 于 sticky navbar 下、`body.nav-open` 切换）；抽屉内下拉组静态展开；**与 TOC 抽屉互斥**；点链接/点外自动收。
- TOC 侧栏：sticky + IntersectionObserver scrollspy 高亮 + **当前项自动滚入**（用户手滚目录后 4s 内让路：程序滚动打 `__progMark` 标记区分）；移动端右下角"☰ 本页目录" FAB 唤出浮层。

### 表格（数据站核心加分项）

```js
// 渲染后统一后处理（site.js）：滚动容器 + 长表 sticky + 数字列右对齐
art.querySelectorAll('table').forEach(t => {
  const rows = t.querySelectorAll('tr');
  const wrap = document.createElement('div');
  wrap.className = 'table-wrap' + (rows.length > 40 ? ' table-tall' : '');
  t.parentNode.insertBefore(wrap, t); wrap.appendChild(t);
  // 纯数字列（≥80% 单元格命中）→ th/td 加 .num（右对齐 + mono）
  const NUM = /^[-−+]?[\d,.]+\s*(?:%|MHz|GHz|ns|ps|ms|µs|µW|nW|mW|kW|W|µm²|µm|nm|KB|MB|GB|TB|G|M|k)?$/;
});
```
```css
.table-wrap { overflow-x: auto; }                       /* 宽表横滚，窄表满宽不受影响 */
.table-wrap > table { margin: 0; min-width: 100%; width: auto; }
.table-wrap.table-tall { max-height: 68vh; overflow: auto; }   /* >40 行：内部滚动 */
.table-wrap.table-tall thead th { position: sticky; top: 0; background: var(--chip); box-shadow: 0 1px 0 var(--line); }
th.num, td.num { text-align: right; font-family: var(--font-mono); font-size: 13.5px; }
/* 横线化：去竖线留横线 + 斑马 0.035（比全边框网格更现代，Stripe 风） */
th, td { border: none; border-top: 1px solid var(--line); }
th { border-top: none; border-bottom: 2px solid var(--line); }
```
- **代码块**：`pre[data-lang]::before` 右上角语言标签（读 `code.language-*`）；` ```text/log ` 加 `.log-view`（浅纸底 + muted 字）与真代码（深墨底）区分；右下角 hover 浮现 **copy 按钮**（Clipboard API + `execCommand` 降级，失败诚实显示"复制失败"）；行高 1.5。

### 图片（lightbox 查看器 + 纸色图表，双加分项）

- **lightbox v2**：点击全屏 → **滚轮以光标为锚缩放**（0.5–12×，`offsetLeft/Top` 是布局值不受 transform 影响）+ **拖动平移** + **双指捏合**（增量中点锚定，复用同一 `zoomAt(cx,cy,f)`）+ 双击/`0` 复位 + ←/→ 换图 + ESC/×/点空白关（**点图片本体不关**——点击即关是反模式）。`show()/hide()` 必须清指针状态（防幽灵捏合）。正文图 hover 显示 **🔍 角标**（JS 包 `.lb-thumb` span，img 是 replaced element 不能挂伪元素）。
- **v4.3 清晰缩放（铁律，2026-10-29）**：lightbox 放大 SVG **禁止 `transform: scale()`**，必须改真实布局尺寸——`width/height = 基准×s`（缩放期间解除 `max-width/height` 钳制，`s===1` 时清空），transform 只写 `translate`。依据：Chromium 按「布局尺寸×DPR」重栅格化 `<img>` 里的 SVG，布局尺寸放大在高 DPR 屏（Windows 125%/150%）必走矢量重栅格；transform 缩放在高 DPR 有"先按布局尺寸光栅化再拉伸位图纹理"路径 → 发糊（DPR=1 实测两法逐像素等价，均为矢量级清晰；但用户屏普遍 DPR>1）。实现模板（三处硬性细节）：① 基准尺寸懒捕获 `baseW = clientWidth || naturalWidth`；② **baseW 为 0（图未加载完）不得设 width/height**（否则 0px 图片消失）；③ `reset()/换图` 必须清零 `baseW/baseH`（否则沿用上一张图的基准）。活模板：practice 站 `js/lightbox.js` 与 52 个内联页（`updateTransform` 形态），参考实现 `hk1v11-longcode-420b-verification/index.html`。
- **动画 SVG（双版架构）**：站点配图一律走「动画/静态双版 SVG 站点架构（v4）」章——静态版为事实源，`<img>` 指向 `anim/` 动画版，切换零重载（2026-10-28 定稿）。
- **图表配色 = 站点色板**（消灭白底 matplotlib 孤岛）：
```python
PAPER='#f4f1ea'; INK='#1c2534'; MUTED='#5b6675'; C_A='#0e7490'; C_B='#b45309'
plt.rcParams.update({'text.color':INK,'figure.facecolor':PAPER,'axes.facecolor':PAPER,
  'savefig.facecolor':PAPER,'xtick.color':MUTED,'axes.edgecolor':'#c9bfa8'})
# savefig(..., facecolor=PAPER)；楔形边 SURFACE #fffdf7；网格 #ddd6c8
```
- PIL 表格图：fork 共享渲染函数仅换色板（墨头条+纸底+语义行底：焦点行 `#e8edfb` 淡蓝、次焦点 `#f7e8d4` 柔琥珀、关键列 `#065f70` 深绿加粗），**数据行逐行照抄禁改**，超采样 `S=4` 防缩放糊（字体=size×S，等效字号=字带px×显示宽/图宽）。
- 暗色主题：纸底 PNG 加 surface 框线过渡（`.lb-thumb` 暗色 padding+border+圆角）。

### 卡片系统（组件类收敛，禁 inline 泛滥）

- `chapter-card` 基类 + `.card-span`（通栏）/`.card-hero`（大数卡，`.title` 32px）/`.card-center`/`.card-mini`（`.title` 20px）；**非链接卡 `:not(a):hover` 不升起**（升起误导点击）。
- **badge 方向语义**：纯百分比 delta 加箭头（改善 `▼ −97.6%` badge-ok），**比值（×1.35）不加箭头**；带文字标签（"hold −96.8%"）不加。
- tag 语义变体：`.tag-warn/.tag-bad/.tag-info/.tag-muted`（中性标签不占用琥珀强调色）。
- 学习路径/入口页：8 步 `card-mini` 网格（STEP N + 标题 + 一句话），锚点跳详情。

<!-- ymzhu 2026-11-18 14:30 -->
