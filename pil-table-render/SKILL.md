---
name: pil-table-render
description: PIL（Pillow）表格图 / 对比图渲染规范，含两套规范——一、PowerPro / teal 表头表格图（字体一致性、基线对齐、标题表头、评审避坑）；二、STA csv 表格图（PT summary csv → 2M23 to-signoff 同款表格图）+ 功耗/违例模块对比条形图与组成环形图（matplotlib）。触发词："PIL"、"表格图"、"render_table"、"PowerPro"、"六组图"、"对比图渲染"、"表格 PNG"、"文字对齐"、"基线对齐"、"抄作业图"、"to-signoff 样式图"、"csv 转表格图"、"setup/hold 结果图"、"skew 表格图"、"功耗图"、"组成图"、"对比图"、"条形图"、"环形图"、"donut"。
---

# PIL 表格图渲染规范

> 本文件含**两套互不混用**的表格图规范：做 PowerPro / teal 表头表格图看「一、」，做 STA csv 表格图（2M23 to-signoff 风格）或 matplotlib 组成图/对比图看「二、」。两套规范冲突时（如逐字符 `draw_mixed` 混排、数值精度），**按所做的图属于哪一类选对应小节**，不要跨节混用规则。

## 一、PowerPro / teal 表头表格图

> 2026-11-02 从 `team-share` skill 原文整体迁出（内容逐字未改）。来源：2026-08-27 PowerPro 0826 六组图多轮评审沉淀。
> 注意：「二、STA csv 表格图（2M23 to-signoff 风格）」是另一套规范，二者冲突时（如逐字符 `draw_mixed` 混排、数值精度）**做 PowerPro/teal 表格图以本节为准**。

### 图表文字渲染规范（PIL 表格图，如 PowerPro 六组图 / 对比图）

做 PIL 表格图（`render_table` / 自写 renderer，teal 表头风格）时，文字渲染必须遵守以下规则（本规范来自 2026-08-27 PowerPro 0826 六组图多轮评审沉淀）：

#### 1. 字体选择：同一元素内字体必须一致，不同元素可以不同字体

- **同一元素**（一个标题条 / 一个表头单元格 / 一个数据单元格）内的全部字符必须使用**同一个字体对象**整串渲染（`draw.text(pos, whole_string, font=f)` 一次画完），**禁止**在元素内部按字符切换字体（不要用逐字符 `draw_mixed` 中英混排——两字体 ascent/baseline 不同必然导致元素内字符上下错位"不在一行"）。
- **不同元素之间**允许不同字体（标题行与数据部分不需要同字体）：
  - 标题条 / 表头 → CJK 粗体（中文为主）
  - 数据单元格 → 沿用该图已认可的字体体系即可（如 msyh 常规/粗体）；如需数字列更整齐，可对纯英文/数字单元格改用等宽字体——但**必须先给用户确认**，不要擅自改变整体字体风格。
- ⚠️ 教训：不要为了"统一"擅自更换全图字体（NotoSansSC/Deng 等线都试过）——用户对已认可的视觉密度很敏感，任何全局字体更换都会被判"不如之前"；只修对齐问题，不动字体风格。

#### 2. 基线对齐：每格整串渲染后按字体 ascent 垂直居中

- 不要用 `(cell_h - font.size)//2` 近似居中——不同字体的 `size` 与 `ascent` 关系不同。
- 用 `font.getmetrics()[0]` 取 ascent，`y_text = cell_y + (cell_h - ascent) // 2` 计算绘制起点。
- 同一行内所有单元格共用同一 `cell_y` → 全行字符上沿/下沿齐平。

#### 3. 标题/表头

- 标题条（teal 底）用 CJK 粗体整串渲染；文字过长时**先量宽度**（`font.getlength(title)`）确认不超过画布，超宽要压缩文案而不是依赖自动截断；副标题放不下就省略（渲染器会把放不下的副标题静默丢弃，不要留悬念）。
- 表头同标题：CJK 粗体整串 + ascent 居中。

#### 4. 评审迭代避坑记录（PowerPro 0826 六组图实测）

- **用户要的是"字体平行"（基线对齐），不是"字体统一"**——曾三次尝试全局换字体（NotoSansSC / Deng / 数据格等宽化）全部被否："回到之前的图""反而非常难看"。正确做法：保持已认可视觉的一切不变，只把混排改成整串渲染。
- 行高亮/单元格高亮：0826 行只高亮**指定列的单格**（teal 字 + 浅青底），不要整行背景；其余行列保持默认（INK + 白/斑马）。
- 数值精度：Total 等数值统一 2 位小数四舍五入（`.2f`），不同来源（报告 / Excel 汇总）要一致。
- 造图脚本必须可重跑（数据源硬编码 CSV 路径 + 脚本注释数据来源），禁止手改 PNG。

## 二、STA csv 表格图（2M23 to-signoff 风格）

### 目标（先做目标站点分流，2026-10-21）

**目标站点决定色板**：
- 图进 **2M23 指南站**（synthesis-integration-flow-guide）→ 走本 skill 主流程（teal 同款）。
- 图进 **暖纸站点**（blueprint-ui-style 画风，如 hk1v11-synthesis-postpt-practice）→ **改用 paper 色板 fork 模式**：表格图模板 `E:\project\HK1V11\back_ppt\gen_power_compare_hk11_site.py`（复用 `_gen_be_review_images.py` 的字体/混排助手但本地渲染：墨头条+纸底+语义行底），**数据行逐行照抄禁改**；matplotlib 组成图参考 `back_ppt/gen_power_composition_charts.py` v2 的 rcParams 站点色板。禁止把 teal 同款图直接嵌入暖纸站（视觉孤岛）。

把 `report_setup.csv` / `report_hold.csv` / `report_sd_busskew.csv` 等 PT summary csv
渲染成与 team-share-public `synthesis-integration-flow-guide` 网站
（to-signoff.html 的 30/31/33/34_postpt_*.png）**完全同款**的高清表格图，
零分析零加工，1:1 抄作业。

### 模板脚本（直接改路径重跑，不要重写）

- **主脚本模板**：`E:\project\HK1V11\back_ppt\gen_1008v3_csv2png_k3.py`
- **样式函数库**（import 复用，勿复制）：`E:\project\team-share-public\synthesis-integration-flow-guide\script\_gen_be_review_images.py`
  （G.TEAL/G.INK/G.RED_TX/G.RED_BG/G.ZEBRA/G.GRID、title_bar、draw_mixed、F_MONO/F_CJK 字体）
- **Python**：`E:\project\team-share-public\synthesis-integration-flow-guide\script\.venv\Scripts\python.exe`（PIL+numpy 已装）
- 超采样 **G.S=4**（防 PPT 缩放糊）。

### 样式规范（2M23 原版，ymzhu 2026-10-08 定稿）

- 顶部深青标题条：左白字文件名（等宽粗体）+ 右白字副标注（规格窗/说明）。
- 表头深青底白字；两层表头（corner 跨 violation number / biggest violation）时层间细线 (71,155,142)。
- 行标签列原样（csv 文本不做改写；skew 行标签带 ` : [lo:hi]` 规格窗）。
- **配色（照抄 2M23 style_violation，勿再发明）**：
  - 正值 = 深墨 INK(33,37,41)（不是绿！淡绿显淡被 ymzhu 打回过）
  - 0 = 绿 GREEN_TX(30,132,73)
  - 负值/违例 = 红 RED_TX(192,0,0) **加粗 + 红底 RED_BG(253,226,226) 整格**
  - skew 出窗判色模式：行标签解析 `[lo:hi]`，窗内深墨、**出窗才红加粗+红底**
- **数值统一保留 5 位小数**（去尾零），ymzhu 指定。
- 斑马纹浅底 (244,248,247)、细网格 (208,216,214)、等宽 Consolas + 中文 msyh 混排基线对齐。
- 空行 = 半高分隔缝（skew 族与族之间）。

### 硬性防错（历史踩坑）

1. **列宽按内容动态计算**（表头+全单元格取最大+padding）——防"宽度被裁剪"老错误。
2. 渲染后 **numpy 四边环带自检**：外框 3px 环带无文字像素、右侧内缘竖带只允许底色；
   **allow 色表必须含红底/红字**（负值整格填充会触边，否则自检假 FAIL）。
3. 大图 >8192px 无法直接 read_image 目检：先 thumbnail 到 2000px 出 `_preview_*.png` 再看，看完删。
4. 出窗判色正则要写 `(-?\+?[\d.]+)`——**"+3.5" 有前导加号**，漏了会 TypeError: cannot unpack None。
5. csv 长尾小数（如 `0.514888999999999`）是全精度真值，优先取 csv 而非截图截断值；
   截图里带 `…` 的格子是截断，无 csv 依据时暂取可见位数并登记待复核。
6. 脚本文件尾必须更新签名注释 `# ymzhu <日期> <时分>`。
7. 变更记录追加到 `E:\project\HK1V11\修改记录\CHANGES.md`（与 back_ppt 交付同条目）。

### 流程

1. 读 csv（`utf-8`/`utf-8-sig`），两层表头 csv 用 load_paired 对齐 corner 组。
2. 改模板脚本的 `V3` 数据目录与输出文件名（版本后缀如 `_k3`）。
3. 跑：`& "...script\.venv\Scripts\python.exe" "<脚本>.py"`，确认 ALL PASS。
4. thumbnail 目检三边完整与配色，交付 `back_ppt/*.png`。

---

### 二、组成图/对比图模板（matplotlib 条形图+环形图，2026-10-19 新增）

适用于功耗模块对比、违例分布、skew 对比等"两组数据按功能块对齐"或"组成占比"场景。

**模板脚本**：`E:\project\HK1V11\back_ppt\gen_power_composition_charts.py`（直接改数组重跑）
**参考效果**：ch08-powerpro.html §4.5「功耗组成可视化」

#### 颜色系

- **项目 A（主项目）**：青色系 `#1B7A8C`（深）、`#2E9B8C`（浅）
- **项目 B（对比项目）**：橙色系 `#E8913A`、`#D4600F`
- **辅助**：`#5B8DB8` 蓝 / `#8B6BB1` 紫 / `#6BAF6B` 绿 / `#C0504D` 红 / `#999999` 灰

#### 中文字体

```python
import matplotlib.font_manager as fm
for fp in fm.findSystemFonts(fontpaths=['C:/Windows/fonts']):
    if 'msyh' in fp.lower() or 'simhei' in fp.lower():
        fm.fontManager.addfont(fp); break
plt.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
```

#### 图 1：双条形对比图（项目 A vs B 按功能块并排横条）

- `barh` 双色并排（`y±h/2`），青/橙，值标注右侧，B 无对应物填 0 跳过标注
- `invert_yaxis()` 最大在顶部，去 top/right spine，`grid(axis='x', alpha=0.3)`
- `dpi=200, bbox_inches='tight'`，figsize≈(14, 8)

#### 图 2：双环组成图（donut 并排）

- `wedgeprops=dict(width=0.42)` 标准环宽，`pctdistance=0.78`
- `autopct='%1.1f%%'` 白色加粗 8pt，标签 9pt
- **中空标注总功耗**：`ax.text(0, 0, '项目\nXX.XX mW\n@频率', ha='center', fontsize=12, fontweight='bold')`
- >12 组时合并小项为"其他"；figsize≈(14, 6.5) 两环并排

#### 注意

- `matplotlib.use('Agg')` 在 import pyplot 之前
- 中文标签用 `\n` 控制宽度
- 需要安装 matplotlib：`pip install matplotlib`

<!-- ymzhu 2026-11-02 18:03 -->
