---
name: blueprint-ui-style
description: 用户偏好的网页/UI 画风（蓝图工程风 blueprint engineering aesthetic），做网站、HTML 报告、页面美化、前端界面时优先使用。触发词："画风"、"用我喜欢的风格"、"蓝图风"、"之前的网站风格"、"blueprint"。构建任何网页/UI/报告站点时都应先加载本 skill，并在过程中提示用户确认效果。
---

# Blueprint UI Style（蓝图工程风）—— 用户首选画风

> 起源：2026-09-07 team-share-public `hk1v11-lc-cpuwr-history` 首页重构，用户确认"这个画风不错，优先用这个画风"。
> 参考实现：`E:\project\team-share-public\hk1v11-lc-cpuwr-history\index.html`（可直接打开查看/复制片段）。
> 组件完整版参考（2026-10-21 全站升级）：`E:\project\team-share-public\hk1v11-synthesis-postpt-practice\`（导航/表格/图片/卡片全组件，见下方"站点组件模板"章）。

## 使用规则（重要）

0. **做网站时的 skill 分工与优先级（2026-10-21 审查定稿）**——本 skill 是**视觉语言与组件的唯一权威**（用户明确偏好 = 最高优先级来源）：
   - `frontend-design`（host 内建，不可改）：同时被触发时**只作工程质量清单**（可读性/可达性/代码质量），**不得**引入新配色/新字体/新视觉方向——创意发散以本 skill 的 token 与组件为边界；两者矛盾时一律按本 skill。
   - `fireworks-tech-graph`：给本画风站点画内嵌图时，**必须改用站点 `:root` 色板**（纸底 `#f4f1ea`/墨 `#1c2534`/琥珀 `#b45309`/深青 `#0e7490`），禁用其自带 Style 3 深蓝（delay_skew v1 教训）；仅独立交付的图才用 skill 自带样式。
   - `sta-csv-table-png`：目标是本画风站点（如 practice 站）→ 用 paper 色板 fork 模式（模板 `E:\project\HK1V11\back_ppt\gen_power_compare_hk11_site.py`，数据行逐行照抄）；目标是 2M23 指南站 → 保持 teal 同款不冲突。
   - `gpt-image-2-style-library`：位图插画与本工程画风无关，做网站默认不调用。
1. **任何网页/UI/HTML 报告任务，默认优先采用本画风**，除非用户明确要求其他风格。
2. **过程中必须提示用户确认**：
   - 动手前先一句话说明将采用蓝图工程风（若任务大，可先给设计要点再确认）；
   - **截图是可选项，不是必经流程（2026-09-11 用户定稿，取代 09-09 强制版）**：重要改动完成后，**先问用户一句"要不要截图验收？"**——要，才走第 3 条截图流程；不要，就直接结束回答，不截图、不阻塞、不把截图当提交前置条件。
3. 截图验证流程（**仅当用户选择要截图时执行**；Windows，2026-09-09 定稿「单弹窗 + HTML 查看器」模式）：
   - 同一批验收截图统一放进一个专用文件夹（如 `$env:TEMP\dsh_shots\<任务名>\`，开批前清空），按 `01_`/`02_`… 序号命名；
   - **全部截完后用 HTML 查看器弹给用户**：把本 skill 目录下的 `review-template.html` 拷进 shotdir 改名 `review.html`，把 `imgs` 数组填成本批文件名清单，再 `Start-Process msedge "file:///.../review.html"` 打开——页面内 ←/→ 方向键切换、Home/End 首末、数字键直达；
   - **禁止 `Invoke-Item` 弹照片应用**（方向键实测不可用，2026-09-09 用户痛点），也禁止每张截图各弹一个窗口。
   ```powershell
   $shotdir = "$env:TEMP\dsh_shots\my-task"
   if (Test-Path $shotdir) { Remove-Item "$shotdir\*" -Force } else { New-Item -ItemType Directory $shotdir | Out-Null }
   & 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' --headless --disable-gpu --window-size=1440,900 --screenshot="$shotdir\01_page.png" "file:///<绝对路径>.html"
   # ...其余页面依次 02_、03_...
   # 拷 review-template.html -> $shotdir\review.html，imgs 数组填入本批文件名清单
   Start-Process 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' -ArgumentList "file:///$($env:TEMP -replace '\\','/')/dsh_shots/my-task/review.html"
   ```
4. **编码红线**：批量读写 HTML/MD 文件时，PowerShell 5.1 的 `Get-Content` 会把 UTF-8 无 BOM 按 GBK 误读成乱码。必须用 `[System.IO.File]::ReadAllText/WriteAllText` 显式 UTF-8（无 BOM），或用 read/edit 文件工具。改完自查无乱码再提交（读文件检查即可，无需截图）。

## 设计系统（Design Tokens）

### 配色（暖纸 + 墨蓝 + 琥珀）

| 角色 | 浅色 | 深色（prefers-color-scheme） |
|------|------|------|
| 页面底 bg | `#f4f1ea` 暖纸 | `#0e1420` |
| 卡片 surface | `#fffdf7` | `#161f31` |
| 正文 text | `#1c2534` | `#e9e5d9` |
| 次要 muted | `#5b6675`（10-21 提对比至 5.2:1） | `#9aa4b5` |
| 强调 accent（琥珀） | `#b45309` | `#f0a137` |
| 柔和强调 accent-soft | `#f7e8d4` | `#3a2f1a` |
| 边线 line | `#ddd6c8` | `#2b3852` |
| hero 深底 ink | `#0d1526` → `#131f38` 渐变 | 同左 |
| 阴影 | `0 12px 32px rgba(28,37,52,0.10)` | `rgba(0,0,0,0.45)` |

### 字体

```html
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Noto+Serif+SC:wght@600;900&display=swap" rel="stylesheet">
```

- **展示标题**：`"Noto Serif SC", serif`，900 粗，大字号 clamp(34px, 5.2vw, 56px)
- **标签/数字/代码**：`"IBM Plex Mono", monospace`（kicker 加 `letter-spacing: 0.2em` 大写）
- **正文**：系统 CJK 栈（PingFang SC / Microsoft YaHei）

### 标志性组件

1. **深色蓝图 hero**：墨蓝渐变底 + 细网格纹理（`repeating-linear-gradient` 56px 网格 + 琥珀径向光晕）；琥珀 kicker（短横线 + 大写 mono）；超大衬线标题（关键词用琥珀色 `.thin`）；一句话导语；mono meta 行（AUTHOR/SPAN/ARCHIVE）；右上角超大版本号水印（如 `0903v1`）。
2. **LATEST 悬浮卡片**：`margin-top: -58px` 压在 hero 下缘；左 4px 琥珀边；版本 badge（chip 底 mono）；只列当前版本 1-3 条要点 + 「全部演进 →」链接。
3. **统计条**：4 格白卡，mono 大数字 + muted 小标签。
4. **hero 提示胶囊**：琥珀描边 + 10% 琥珀底，放首屏关键引导语（⭐ 推荐阅读顺序等）。
5. **章节卡片**：mono 编号（01/02…）+ 粗标题 + muted 描述；hover 上浮 3px + 左侧琥珀条淡入 + 琥珀边框。
6. **节标题**：mono 小字大写 + `::after` 延伸细线。
7. **代码 chip**：`--chip` 底 + 琥珀文字 + IBM Plex Mono。

## 内容原则（用户明确偏好）

- **低文字密度**：简介/导语一句话说清；版本流水账、细节数据收进专属子页面，首页只留入口链接（「全部版本演进 →」）。
- **关键信息首屏可见**：阅读引导、当前版本等必须在第一屏（hero 区）出现。
- 导航条：sticky、mono 品牌字、active 项琥珀底白字。

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
- **动画 SVG**：纯 CSS 动画 SVG（`fireworks-tech-graph`「Animated SVG」条款）在 `<img>`/lightbox 内正常播放；站点配图若判定可动画（寄存器大图/拍重组网格等），静态版保留为 fallback，`<img>` 指向 `anim/` 子目录动画版（2026-10-26）。
- **图表配色 = 站点色板**（消灭白底 matplotlib 孤岛）：
```python
PAPER='#f4f1ea'; INK='#1c2534'; MUTED='#5b6675'; C_A='#0e7490'; C_B='#b45309'
plt.rcParams.update({'text.color':INK,'figure.facecolor':PAPER,'axes.facecolor':PAPER,
  'savefig.facecolor':PAPER,'xtick.color':MUTED,'axes.edgecolor':'#c9bfa8'})
# savefig(..., facecolor=PAPER)；楔形边 SURFACE #fffdf7；网格 #ddd6c8
```
- PIL 表格图：fork 共享渲染函数仅换色板（墨头条+纸底+语义行底：焦点行 `#e8edfb` 淡蓝、次焦点 `#f7e8d4` 柔琥珀、关键列 `#065f70` 深绿加粗），**数据行逐行照抄禁改**，超采样 `S=4` 防缩放糊（字体=size×S，等效字号=字带px×显示宽/图宽）。
- 暗色主题：纸底 PNG 加 surface 框线过渡（`.lb-thumb` 暗色 padding+border+圆角）。

### 站点图表动画化（2026-10-26 定稿，观赏性加分项）

把站点里"模型判定可动画"的图做成动画 SVG（hk1v11 站点 6 图实例：结构图/条形/环形/表格×3，`team-share-public/hk1v11-synthesis-postpt-practice/`）。

- **选型（两步门控）**：① 用途=传达数据进报告 → 可重绘；工具输出快照截图（CSV 报表截屏等）→ **keep 原样，重绘=伪造截图**。② 有源（数据在生成脚本里）+ 离散结构（表/条/环/框图）→ 重绘；无源（波形/照片）→ keep。
- **动画架构（用户口径 2026-10-26）**：
  - **入场一次性、绝不循环**（forwards、总 ≤2.5s、元素默认态=最终完整态——`from` 态只在 keyframes 内生效）；
  - **循环只给持续特效**：每图 3–6 个 infinite，周期 2.4/3.2/4/5.2/6/7s **互异+相位错开**（禁整图同步机械脉冲），温和（峰值 opacity≤0.5、内容元素位移≤2–4px、scale≤1.03；扫光带等纯装饰光效可长位移）；
  - 特效优先服务可视化：数据流方向（行进虚线）、峰值/关键值（柔光脉冲）、对比对（扫光带限定 clip）、代际演进（时间轴进度带逐段填充）。
- **长页面下方图问题（关键）**：入场动画在加载时播完、用户滚到时看不到 → site.js 加 **IntersectionObserver 滚动重播**：首屏外 `img[src$=".svg"]` 首进视口前 240px 时 `img.src = base + '?v=' + Date.now()`（query 强制 `<img>` 内 SVG 重渲染=重播）+ `loading="lazy"`；首屏内图不重播。
- **数据纪律**：数值从源脚本 **ast 逐字转录**（禁手抄），生成后双向核对（单元格数/`<text>` 节点数/扇区数逐一相等，含 −/→/— 码位）；数据表图尾零要跟 PNG 显示一致（`fmt_num` 去尾零口径）。环形图免手算弧线：`<circle pathLength="100">` + `stroke-dasharray="p 100-p"` + `dashoffset=25−cum`（12 点起顺时针）。
- **硬约束**：纯 CSS `@keyframes`（无 JS/无外部引用/无外部字体）；`@media (prefers-reduced-motion:reduce){*{animation:none!important}}`；只用站点 :root 色板；**根元素必须显式数值 `width`/`height`（=viewBox 尺寸）**——`width="100%"` 在站点 `.lb-thumb{width:fit-content}` 包裹下无固有尺寸会塌缩成 0（图不显示，2026-10-26 实测）；显式像素 + 全局 `max-width:100%` 仍响应式；原 PNG 保留不删（引用切 .svg）。
- **QA 双检查器**（`HK1V11/script/_chapter_viz/`）：`_svg_qa.py`（XML/无JS/无外联/reduced-motion/签名）+ `_svg_anim_qa.py`（**infinite 动画含 opacity 0→1 / scale 0→1 入场语义即打回**；逗号分隔多动画 shorthand 须分段解析——`infinite` 只属于它所在段）。
- **上下文经济学**：数据图（条形/环形）手算几何易撑爆 subagent 上下文 → 让 subagent **写生成器脚本**（ast 取数+代码算几何+内置自检）再执行，实测可复跑（`gen_donut_svg.py`）。
- **图面干净**：图内脚注**不与页面正文重复**——口径说明页面 blockquote 已有的，图里直接删（2026-10-26 功耗对比图删 4 行脚注 + 画布收紧 457→400）；图只放"看表时此刻需要"的信息。
- **视觉验证（Windows 本机，subagent 沙箱跑不了时的正路）**：
  - **Edge 无头截图**：`msedge --headless --disable-gpu --user-data-dir=<每跑一个新目录> --window-size=<W>,<H> --virtual-time-budget=8000 --screenshot=<png> <file:///…svg>`——**文件延迟落盘**（进程退出后 1–30s 才写出，必须轮询 `[ -f ]` 最多 ~40s 再判失败）；**一次工具调用只渲染一张**（连续批量易静默失败）；中文走系统字体正常（cairosvg 无 CJK 出豆腐块，只适合结构自检）。
  - **诊断签名**："直接 URL 能显示、页面里空白" = **`<img>` 上下文问题**（wrapper CSS/JS），先查 `.lb-thumb`/lightbox 包裹与 fit-content×百分比宽，**不要**疑文件本体、部署或缓存；硬刷新解决不了这种问题。
- **聊天分享**：聊天附件预览**不支持 SVG**（只认位图）→ 图需要发聊天时，用上面的 Edge 渲染法出 PNG 快照（放站点 `png_preview/` 本地存档，不提交进站点仓库——站点继续用 SVG 动画版）。

### 卡片系统（组件类收敛，禁 inline 泛滥）

- `chapter-card` 基类 + `.card-span`（通栏）/`.card-hero`（大数卡，`.title` 32px）/`.card-center`/`.card-mini`（`.title` 20px）；**非链接卡 `:not(a):hover` 不升起**（升起误导点击）。
- **badge 方向语义**：纯百分比 delta 加箭头（改善 `▼ −97.6%` badge-ok），**比值（×1.35）不加箭头**；带文字标签（"hold −96.8%"）不加。
- tag 语义变体：`.tag-warn/.tag-bad/.tag-info/.tag-muted`（中性标签不占用琥珀强调色）。
- 学习路径/入口页：8 步 `card-mini` 网格（STEP N + 标题 + 一句话），锚点跳详情。

## 反模式（避免）

- ❌ 多版本变更堆成一长段文字（用户明确批评过："简介内容太多太多了"）
- ❌ 通用 AI 风：Inter/Roboto、紫渐变、千篇一律卡片
- ❌ teal/slate 旧配色（本站 2026-09-07 前的样子）
- ❌ 列表型卡片墙（镜像 TOC 无增量信息，用户否决过 ch10 21 则卡墙）
- ❌ 点击图片本体即关闭 lightbox（应为缩放平移，点空白才关）
- ❌ 白底 matplotlib 图直接嵌暖纸站（视觉孤岛，必须换站色板）

<!-- ymzhu 2026-10-26 18:20 -->
