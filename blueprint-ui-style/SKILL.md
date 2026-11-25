---
name: blueprint-ui-style
description: 用户偏好的网页/UI 画风（蓝图工程风 blueprint engineering aesthetic），做网站、HTML 报告、页面美化、前端界面时优先使用；含「动画/静态双版 SVG 站点架构 v4」「新站搭建强制流程」「图版生命周期与归档标准」「图生成管线契约」与「站点图审计协议 A0–A9（references/site-audit.md）」。触发词："画风"、"用我喜欢的风格"、"蓝图风"、"之前的网站风格"、"blueprint"、"动画svg"、"动效"、"静态版"、"切换动画"、"新网站"、"新站"、"建站"、"做一个网站"、"改站点"、"更新站点"、"改图"、"重生成图"、"图不对"、"图跟正文不一致"、"归档旧图"、"站点审计"、"审计站点"、"全站核对"、"扫一遍站点"、"图体检"、"环形图加起来不对"、"双版图对不对"、"audit site"。构建任何网页/UI/报告站点、改动已建站点的图/页面、或审计站点图时都必须先加载本 skill。
---

# Blueprint UI Style（蓝图工程风）—— 用户首选画风

> 起源：2026-09-07 team-share-public `hk1v11-lc-cpuwr-history` 首页重构，用户确认"这个画风不错，优先用这个画风"。
> 参考实现：`E:\project\team-share-public\hk1v11-lc-cpuwr-history\index.html`；组件完整版 `hk1v11-synthesis-postpt-practice\`。

## 使用规则（重要）

-0. **改完必审（2026-11-18 ymzhu 指令，强制闸）**：凡按本 skill 产出的图（表格图/对比图/双版 SVG）与站点页面改动，完成后**必须经独立审查**——图=数字↔源数据逐格 + Σ片=中心值 + 双版配对；站点=A0–A9 + 站点校验门（check_article / check_anim_pairs / check_fx_clip / generate_search_index）。审查报告落盘、verdict=PASS 才算完成、才准进入邮件/交付汇报；**审查者不得是制作者本人**。与 -0.5 的分工表互补：改图前先体检（§验证门/图版生命周期），改完必审查（A0–A9），两头都是硬的。
0. **与其他 skill 的分工**（矛盾时一律按本 skill）：
   - `frontend-design` 同时触发时只作工程质量清单，不得引入新配色/字体/视觉方向；
   - `fireworks-tech-graph` 给本画风站点画内嵌图必须改用站点 `:root` 色板；
   - `pil-table-render` 目标是本画风站点时走其 paper fork 模式；2M23 指南站保持 teal；
0.5 **命中后先按任务类型定位必读章节**（2026-11-18 定）：

   | 任务长相 | 必读 | references |
   |---|---|---|
   | 建新站 / 骨架改造 | 本文§新站 + | `references/sitebuild.md` |
   | 页面美化 / 改组件 | 本文§设计系统指针 + | `references/design-tokens.md` `references/components.md` |
   | 加动画版 / 改动效 | 本文§v4 核心契约 + | `references/anim-v4.md` |
   | **改已建站点的图 / 数字** | 本文§验证门 + §图版生命周期 | `references/figure-pipeline.md` |
   | 审计站点 / 图体检 | | `references/site-audit.md`（A0–A9 唯一判据源） |

   **凡是"改图"，第一动作 = 跑生成器 `--out` 到临时目录 + 与线上 `cmp`，不是手改 SVG。**
1. 任何网页/UI/HTML 报告任务默认采用本画风，除非用户明确要求其他风格；动手前一句话说明将采用蓝图工程风。
2. 截图验收是可选项：完成后先问用户"要不要截图验收？"，要才走流程（流程细节见 `references/components.md` 末节：单弹窗 HTML 查看器模式，禁 `Invoke-Item`）。
3. **编码红线**：批量读写 HTML/MD 必须显式 UTF-8 无 BOM（read/edit 文件工具或 `[System.IO.File]`）；改完自查无乱码。
4. 写文件一律 LF（`newline=""`），禁裸 `Path.write_text`（Windows 会整文件 CRLF → "status M 但 diff 空"假改动）。

## 设计系统（指针）

完整 tokens（配色全表/字体/标志性组件）与组件模板（导航/表格/图片 lightbox/卡片）在 `references/design-tokens.md` 与 `references/components.md`——**只取其中 token，禁临时调色、禁引入新字体新框架（零依赖）**。核心六值：纸底 `#f4f1ea` / 卡面 `#fffdf7` / 正文 `#1c2534` / 琥珀 `#b45309` / 深青 `#0e7490` / 边线 `#ddd6c8`；深色模式对照表见 tokens 文件。

## 内容原则（用户明确偏好）

简介不堆长文（"简介内容太多太多了"）；镜像 TOC 的列表卡墙无增量信息（用户否决过）；变更记录展示层一句话结论、细节折叠置底、时间倒序。

## 动画/静态双版 SVG 架构（v4，team-share 全仓库强制）

**文件契约**：每图三层——`images/<name>.svg`（静态=事实源）+ `images/anim/<name>.svg`（动画版，HTML 只引用它，带 `?v=`）+ `anim/make_anim_<name>.py`（生成脚本）。运行时切换契约（零重载、`aspect-ratio` 锁位、重播同 src 重赋值）与动效质量标准（≥2 类稳态可见动效、四族持续层、入场先容器→内容→箭头）详见 `references/anim-v4.md`。

## 验证门（改完必过，不过不交付；数据类 5–8 为 2026-11-18 新增）

1. **成对完整性**：每个 `anim/*.svg` 存在同名静态版（脚本扫描，禁 404）。
2. **切换零位移**：切换前后各图 `getBoundingClientRect` 一致。
3. **稳态可辨**：稳态帧动效痕迹肉眼可指认，截图交用户验收。
4. **生成物零漂移**：XML 合法 + `<text>` 多重集与静态版一致 + 生成器重跑字节一致。
5. **门不许说谎**：自检脚本必须——注入真实错误→红；空输入/空集→FAIL（`all(())` 恒真是假绿）；扫描类打印"扫了 N 个"，N=0 判红；判定文本与退出码同源。
6. **图内数字与正文同一事实源**：图里每个数在生成器输入里指名；同一量只允许一种表示；**组成图断言 Σ片 == 中心值**，百分比分母 == 中心值。
7. **缓存串与索引同源**：改图/页 → `?v=` 同一提交内 bump；`search-index.json`+`.js` 由同一脚本产出 + `--check` 守漂移。
8. **从零可复现**：`--out` 空目录两次 md5 相同 + 与线上 `cmp` 一致 + 默认运行 `SKIPPED`；无生成器的历史图先补生成器，禁继续正则补丁线上 blob。

## 新站搭建（站点 = 固定模块组装，强约束）

完整流程（触发读取链、核心框架定死、站点模块清单、内容即模块、强约束声明）在 `references/sitebuild.md`——骨架唯一来源 `site-template/`，固定文件逐字禁改，模型只填内容槽。交付门 checklist：目录契约齐 / fx.js·fx.css md5 与他站一致 / `check_anim_pairs.py` 过 / 验证门 1–8 全过 / 根导航登记 + file:// 与构建预览正常。

## 图版生命周期与归档标准（2026-11-04 用户拍板；6–9 为 2026-11-18 新增）

1. **主名即当前采纳版**：图主文件名固定＝当前版，HTML 引用主名，换版不断链。
2. **换版必快照、任何图永不删除**：被替换整套图（静态+动画+PNG）进 `images/archive/<内容日YYYYMMDD>/`，文件名带版本标签。
3. **位图只进日期夹**（豁免：无 SVG 源的站点主配图可占主名位）；QA 截图进 `archive/qa/<日期>/`；站根/仓库根不落裸图。
4. **生成脚本归 `images/tools/`**，脚本头标注生成哪组图。
5. 归档目录只增不改不删；发现被改判红重做。
6. **快照只追加永不覆盖**：目标名已存在则加指纹后缀再写；裸 `cp` 盖同名快照 = 吞历史。
7. **单一写入出口**：站点所有落盘统一走 `_siteio.py` 式工具（模板见 `references/figure-pipeline.md`）。
8. **生成器可判漂移**：内嵌指纹，DRIFT 态拒写（仅 `--allow-drift` 越权），默认幂等 `SKIPPED`。
9. **单源分层**：数据源→生成器→图→页面引用四层单向；上层不重复存下层数字（禁 `*_display_uw` 双口径字段）。

## 反模式（避免）

- ❌ 多版本变更堆长段文字 / 通用 AI 风（Inter/Roboto、紫渐变）/ teal·slate 旧配色 / 镜像 TOC 卡墙
- ❌ 点击图片本体关 lightbox（应缩放平移，点空白才关）；lightbox 用 `transform:scale()` 放大 SVG（布局尺寸放大，v4.3）
- ❌ 白底 matplotlib 图直嵌暖纸站（换站色板）；img 换 src 不锁 `aspect-ratio`；`?v=Date.now()` 强制重载或 `cloneNode+replaceWith` 重播（同 src 重赋值）
- ❌ SVG scale 抖动动画（一律 opacity+辉光呼吸）；稳态只有 0.45–0.68 opacity 呼吸（≥2 类可见动效）
- ❌ 手改线上 SVG（正则补丁 blob）——图必须是生成器输出，补丁下次重生成即丢
- ❌ 生成器逐行几何/文案覆盖（`_BAR_W_OVERRIDE`/`_LABEL_OVERRIDE`）——改数据就出现 30px vs 公式 28px 的非单调结果；一律通用函数从数据推导
- ❌ 扫描脚本相对 cwd 拼路径（cwd 一换扫 0 文件还 PASS）；空集 `all()` 后直接 PASS；`print` 与 `sys.exit` 两处结论
- ❌ 同一数字正文/图/表三处手写互不校验（18969/18969、18068/18069 事故）；环图百分比分母用"分组和"而非中心值
- ❌ 换版不 bump `?v=`；归档同名覆盖；裸 `Path.write_text`（CRLF 假改动）

<!-- ymzhu 2026-11-18 14:30 -->
