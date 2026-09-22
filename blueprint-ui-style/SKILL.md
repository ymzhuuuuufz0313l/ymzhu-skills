---
name: blueprint-ui-style
description: 用户偏好的网页/UI 画风（蓝图工程风 blueprint engineering aesthetic），做网站、HTML 报告、页面美化、前端界面时优先使用。触发词："画风"、"用我喜欢的风格"、"蓝图风"、"之前的网站风格"、"blueprint"。构建任何网页/UI/报告站点时都应先加载本 skill，并在过程中提示用户确认效果。
---

# Blueprint UI Style（蓝图工程风）—— 用户首选画风

> 起源：2026-09-07 team-share-public `hk1v11-lc-cpuwr-history` 首页重构，用户确认"这个画风不错，优先用这个画风"。
> 参考实现：`E:\project\team-share-public\hk1v11-lc-cpuwr-history\index.html`（可直接打开查看/复制片段）。

## 使用规则（重要）

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
| 次要 muted | `#667180` | `#9aa4b5` |
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

## 反模式（避免）

- ❌ 多版本变更堆成一长段文字（用户明确批评过："简介内容太多太多了"）
- ❌ 通用 AI 风：Inter/Roboto、紫渐变、千篇一律卡片
- ❌ teal/slate 旧配色（本站 2026-09-07 前的样子）
