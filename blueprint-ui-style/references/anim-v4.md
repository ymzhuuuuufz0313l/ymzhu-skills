# 动画实战与 v4 运行时契约（切换零重载/动效质量标准/落地状态）

> 2026-11-18 从 SKILL.md 原文整体迁出（内容未改，仅落位）。本文件是被指向的参考，不读不违规、只做得不够精细。

## 站点图表动画化实战（2026-10-26 定稿；与本文件 v4 架构章冲突处，一律以 v4 为准）

把站点里"模型判定可动画"的图做成动画 SVG（hk1v11 站点 6 图实例：结构图/条形/环形/表格×3，`team-share-public/hk1v11-synthesis-postpt-practice/`）。

- **选型（两步门控）**：① 用途=传达数据进报告 → 可重绘；工具输出快照截图（CSV 报表截屏等）→ **keep 原样，重绘=伪造截图**。② 有源（数据在生成脚本里）+ 离散结构（表/条/环/框图）→ 重绘；无源（波形/照片）→ keep。
- **动画架构**：入场一次性、绝不循环（forwards、总 ≤2.5s、元素默认态=最终完整态——`from` 态只在 keyframes 内生效）；循环只给持续特效——**v4 修订：稳态"肉眼可辨"标准（列车/脉冲/扫光/生长 ≥2 族）见 v4 架构章 §3，取代旧"温和 opacity≤0.5"上限**；同图 infinite 周期互异+相位错开（禁整图同步机械脉冲）保留；特效服务可视化语义（数据流方向/峰值强调/对比对/代际演进）保留。
- **长页面下方图问题（v4 修订）**：入场动画在加载时播完、用户滚到时看不到 → **滚动重播用 `img.replaceWith(img.cloneNode())`**（重启 CSS 动画、零网络零闪跳）+ `loading="lazy"`；**禁止 `?v=Date.now()` 强制重载重播**——那是 v1–v3 切换错位的根因，2026-10-28 已全仓废除。
- **数据纪律**：数值从源脚本 **ast 逐字转录**（禁手抄），生成后双向核对（单元格数/`<text>` 节点数/扇区数逐一相等，含 −/→/— 码位）；数据表图尾零要跟 PNG 显示一致。环形图免手算弧线：`<circle pathLength="100">` + `stroke-dasharray="p 100-p"` + `dashoffset=25−cum`（12 点起顺时针）。
- **硬约束**：纯 CSS `@keyframes`（无 JS/无外部引用/无外部字体）；`@media (prefers-reduced-motion:reduce){*{animation:none!important}}`；只用站点 :root 色板；**根元素必须显式数值 `width`/`height`（=viewBox 尺寸）**——`width="100%"` 在站点 `.lb-thumb{width:fit-content}` 包裹下无固有尺寸会塌缩成 0（2026-10-26 实测）。
- **QA 双检查器**（`HK1V11/script/_chapter_viz/`）：`_svg_qa.py`（XML/无JS/无外联/reduced-motion/签名）+ `_svg_anim_qa.py`（infinite 动画含 opacity 0→1 / scale 0→1 入场语义即打回；逗号分隔多动画 shorthand 须分段解析）。
- **上下文经济学**：数据图（条形/环形）手算几何易撑爆 subagent 上下文 → 让 subagent **写生成器脚本**（ast 取数+代码算几何+内置自检）再执行，实测可复跑（`gen_donut_svg.py`）。
- **图面干净**：图内脚注**不与页面正文重复**——口径说明页面 blockquote 已有的，图里直接删；图只放"看表时此刻需要"的信息。
- **视觉验证（Windows 本机）**：Edge 无头截图 `msedge --headless=new --disable-gpu --user-data-dir=<每次新目录> --virtual-time-budget=8000 --screenshot=<png> <file:///…svg>`——**文件延迟落盘**（进程退出后 1–30s，轮询 `[ -f ]` 最多 ~40s 再判失败）；**一次工具调用只渲染一张**；中文走系统字体正常（cairosvg 无 CJK 出豆腐块，只适合结构自检）。诊断签名："直接 URL 能显示、页面里空白" = `<img>` 上下文问题（wrapper CSS/JS），先查 `.lb-thumb`/lightbox 包裹与 fit-content×百分比宽，不要疑文件本体/部署/缓存。
- **聊天分享**：聊天附件预览不支持 SVG → 用 Edge 渲染法出 PNG 快照（放站点 `png_preview/` 本地存档，不提交进站点仓库）。

- **mermaid 流程图（内联 SVG，另一条动画化路径，2026-10-26 hk1v11 站点 ch05/06/09 实例）**：
  - **先验证 fence 真的渲染了**：```mermaid 块若没引入 mermaid.min.js + 调 `run()`，页面显示的是**原始代码块**（hk1v11 站点 3 章此前就是这个状态）——"动画化"之前先确认图本体存在。
  - **启用三件套**：页面引 mermaid.min.js（site.js 前）→ site.js 把 `pre code.language-mermaid` 换成 `pre.mermaid` 交 `mermaid.run({nodes})`（theme=default + themeVariables 站点色板）→ IntersectionObserver 加 `.play` + 内联样式启动动画（纯 class/inline，**无需重渲染**，与 `<img>` SVG 的 src 重播不同）。
  - **动画配方**：节点阶梯淡入（opacity only，`g.node` 自带 transform 属性——**禁 transform 动画**，会被覆盖导致节点错位）+ 边线 dash-draw（可见边 = `path.flowchart-link`，marker 箭头在画线期间先现=标准效果）+ 节点接力柔光（infinite，8s 周期）。
  - **多动画同属性冲突（实测坑）**：CSS 多动画作用于同一属性时**列表最后一个生效**——infinite 接力动画若带 fill-mode 或其 0% 关键帧含 opacity:1，会整体覆盖一次性淡入 → **接力动画不给 fill-mode + delay 设到入场播完之后**（如 2.8s），周期要容得下全部节点按序接力。
  - **样式坑**：`.mermaid` 是 `<pre>`，会吃到站点暗色代码块样式 → 覆盖（transparent 底/无边框/去语言标签/去复制按钮）；themeVariables 在部分版本不吃 → 节点色用 CSS 直接覆盖 `g.node rect{fill/stroke}`；节点文本在 foreignObject 的 div 里（无 SVG `<text>`）。
  - **无头验证**：Edge `--virtual-time-budget` **会推进 CSS 动画并在预算时刻截帧**——小预算（300ms）可截入场中途帧验证逐现；JS 流程卡点用"状态机测试页"（把每步结果写进页面 div，截图读）。

## 动画/静态双版 SVG 站点架构（v4，2026-10-28 定稿，team-share 全仓库强制）

> 背景：team-share-public 多站点（84 页 / 8 份 fx.js 副本）采用「动画版 + 静态版」双 SVG。用户定性两条：①动效不明显、可视化差；②切换按钮点击后页面错位。根因：v1–v3 的 img.src 交换 + `?v=Date.now()` 强制重载，img 无布局锁定，重载窗口图片塌陷 → 页面跳动（git 已连修三轮表面症状）。v4 = **零重载切换 + 电影感动效**。本章是架构契约；各站实现细节（kit CSS 全文、分图分工）在站点内 `anim/MOTION_KIT.md`。

### 1. 文件契约（三层不变量）

| 文件 | 角色 | 铁律 |
|---|---|---|
| `<name>.svg`（原路径） | 静态版 = **事实源** | 人审通过的唯一版本；不含 animation/keyframes/隐藏初态 |
| `anim/<name>.svg` | 动画版（生成物） | 与静态版同 viewBox/width/height；`<text>` 多重集、坐标、配色零改动 |
| `anim/make_anim_<name>.py` | 生成器 | 确定性幂等（重跑输出字节一致）；只读静态版；零第三方依赖 |
| `anim/MOTION_KIT.md` | 站内 kit 规范 | 动效类词汇表 + 逐图分工，是该站子代理的唯一事实源 |

HTML 引用一律指向动画版（`anim/xxx.svg`）；无静态对照的单文件图两模式原样保留。

### 2. 运行时切换契约（v4 核心：零重载，治错位）

1. **布局锁定**：每张 SVG img 首次加载完成后，立即将 `naturalWidth/naturalHeight` 写入 `style.aspect-ratio` 并补 `width:100%; height:auto`。此后无论 src 如何变化，盒子尺寸恒定 → 切换零位移。
2. **预载后交换**：切模式时先 `new Image()` 预载目标版本，`onload` 后才改 `img.src`（缓存命中时即时）→ 无空白窗口。
3. **废除 `?v=Date.now()` 强刷**（v3 及之前"滚动重播"的做法）：强制重载必闪跳，一律禁止。
4. **重播用同 src 重赋值**：需重播入场动画时 `img.src = img.src`——同值赋值触发 load 管线重启 SVG 内 CSS 动画（Chromium 实测有效）、零网络、**节点不变**。**禁止 `cloneNode()+replaceWith` 重播**（2026-10-28 事故：替换节点会丢失 lightbox 等外部 addEventListener 监听 → 全站图片点不开大图）。
5. 模式优先级链：URL `?motion=static|anim` > sessionStorage(`motion-mode`) > `prefers-reduced-motion` > **anim（默认一律动画，2026-10-28 用户定稿）**。选择只在会话内记忆（关浏览器重置为动画）；localStorage 持久记忆已弃用（曾致用户点过一次静态后全站永久静态）；`html.page-static` kill 块保留。
6. fx.js 是全仓库单一事实源：**9 处副本**（仓库根 + `site-template/` + 7 个文章站点目录；tj 为临时目录待删，不参与一致性）必须字节一致；任何改动后全站 84 处引用统一 bump `?v=N+1`。
7. **切换按钮 = 放在顶部导航（2026-10-28 晚定稿，取代早先右下角方案）**：由 fx.js 注入 `#motionToggle`，挂载规则自动适配：横向 `.navbar-links` → **内联小胶囊**（链接流末尾）；纵向/下拉式 links（practice 站）→ `navbar-abs` **绝对定位于 .navbar 右缘垂直居中**（不参与 links 布局，绝不独占一行；static navbar 自动补 relative）；无 .navbar → `float-motion` 右上角固定兜底。**页面不得硬编码 motionToggle**；按钮不注入右下角。

> 为何不内联 `<svg>`：内联可让页面 CSS 直接控制动画（理论最优），但 Chromium 拦截 `file://` 下的 fetch，而本地 file:// 截图验收是本 skill 标准流程；v4 预载交换在 file:// 与 https 行为一致。

### 3. 动效质量标准（v3 kit，用户定调"不要怕炫技"）

> **单一来源声明（2026-11-02）**：本章是站点动画图规格的**唯一数值来源**（效果种类、周期、速度、颜色、目录）。`fireworks-tech-graph`「Animated SVG」章只给通用技法与不变量，两者冲突一律以本章为准。逐类配方与逐图分工见站内 `anim/MOTION_KIT.md`（范本：`hk1v11-longcode-420b-verification/anim/MOTION_KIT.md` v4.3）。

**三幕叙事**：入场（一次性，总长 ≤2.5s，讲故事）→ 稳态（持续层，必须"肉眼可辨"）。

**稳态禁用纯低幅 opacity 呼吸充当主要动效**（0.45–0.68 幅度已被用户判定"看不出动画"）。稳态至少含下述 2 类。**v4.1 口径（2026-10-28 用户验收）**：①**一切缩放类动画（transform:scale）禁止**——用户定性"抖动效果不喜欢，远不如呼吸"，pulse/wave/step 只用 opacity + drop-shadow 辉光呼吸；②**列车慢速**：flowdot/flowtail 元素级时长 **≥2.4s/程、典型 3s+**（2026-10-29 二次降速定稿，速度过快"眼花缭乱"）；③**拖尾颜色必须同链光点色**；**扫光一律改为文字光带（v4.3，2026-11-02 用户定调"琥珀色扫光带很丑，SVG 里面用光带而不是扫光"）**——白色亮峰只在文字字形内滑过（与 hero 标题同技法），峰值 ≤.65（再高会把浅底深色字洗白），**禁整块色带擦过面板、禁红棕/琥珀色亮带**；旧 v4.1"白色高亮扫过刺眼"针对的是整块白色带，不适用于文字光带；④数据图表**默认不加行进**，用户点名才加；⑤**短箭头规则（v4.3，2026-11-02）**：可见长度 < 80px 的箭头不挂 flowdot/flowtail/march/dashgrow（短线流点只剩闪烁），要表达流向改用 `.step` **方框接力点亮**（沿链路逐盒点亮，相邻 +1s）。**v4.2 数据密度硬指标（2026-10-29 用户定调）**：数据矩阵类图 **行 ≥20 且列 ≥6 = 数据密集 → 数据区（数值格/数据行/数据列）禁止一切弥漫性动效（逐格呼吸/整行行波/整列扫光）**——行列多时呼吸严重影响读数体验；仅允许 ≤3 个语义强调点（关键行 pulse）与非数据 chrome（表头/图例/边框）动效。行或列低于阈值 → 呼吸/行波照常（低密度加是很好的）。

| 类 | 效果 | 关键实现 |
|---|---|---|
| `.flowdot` 数据列车 | 主链路光点流：stroke-width 3–4 + 拖尾（拖尾同色，禁白色），速度分层（主干快/支路慢，默认 2.6s）；**仅用于 ≥80px 的箭头** | `pathLength="100"` |
| `.pulse` 节点脉冲 | 英雄节点**辉光呼吸**（opacity 0.8 + 10px 辉光，无缩放） | 类保留 `transform-box:fill-box`（校验签名）；keyframes 无 transform |
| `.sweepband` 文字光带 | 白色亮峰滑过关键文字（标题/标注/结论），只在字形内可见；每图 ≤2 区 | 给目标 `<text>` 加 id → `<clipPath>` 内 `<use href="#id"/>` 引用（不复制文字）→ 叠在内容之上的渐变 rect 平移；8s 周期；配方见 MOTION_KIT §4 |
| `.step` 步骤 / 接力点亮 | ①②③④ 步骤框循环；短箭头链路的方框逐盒点亮 | stepLit 6s，相邻盒 delay +1s |
| `.dashgrow` 链路生长 | 关键路径虚线持续生长回卷，暗示链路活性（≥80px 虚线） | dashoffset 循环 |

入场编排铁律：**先容器 → 再内容 → 最后箭头**；箭头 delay ≥ 两端面板入场完成时刻（v2 实测 0.8s 帧有"箭头悬浮在空白面板上"的缺陷，禁止再现）。
持续层 ≤4 族、同族错相位（**2026-10-28 晚放宽：用户认可呼吸辉光/慢速列车/行波/虚线生长四族，要求"再进一步增加"——可在既有几何上加密这四族，但用户点名移除的效果不回加（如 donut 行进）**）；辉光/脉冲配色一律用站点色板（琥珀 `#b45309` / 深青 `#0e7490` / 蓝 `#1d4ed8`），**文字光带亮峰用白色（唯一例外）**，禁 fireworks 自带深蓝孤岛。kit CSS 必须自带 `prefers-reduced-motion` 块（opacity 复位 + flowdot/sweepband 隐藏）。

**验证注意（2026-11-02 实测）**：无头截图 `--virtual-time-budget` 对合成层 `transform` 动画（光带平移）取帧不可靠，常截不到；验证时在诊断副本注入 `document.getAnimations().forEach(a=>{a.pause();a.currentTime=T})` 定格后截图（诊断副本不入库）。

### 5. 落地状态

| 站点 | 双版图 | 状态 |
|---|---|---|
| hk1v11-longcode-420b-verification | 10 张 | v4 首发站：fx.js v4 + kit v3（2026-10-28） |
| hk1v11-synthesis-postpt-practice | 6 张 | 已迁 /anim/ 约定；fx.js v4 自动受益；动效升级按需另开任务 |
| hk1v11-lc-cpuwr-history · synthesis-integration-flow-guide · 根站 | 若干 | fx.js v4 自动受益；既有动效口径维持用户 10-28 指示，不追改 |

<!-- ymzhu 2026-11-18 14:30 -->
