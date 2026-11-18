# 设计系统 Tokens（配色/字体/标志性组件）

> 2026-11-18 从 SKILL.md 原文整体迁出（内容未改，仅落位）。本文件是被指向的参考，不读不违规、只做得不够精细。

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

<!-- ymzhu 2026-11-18 14:30 -->
