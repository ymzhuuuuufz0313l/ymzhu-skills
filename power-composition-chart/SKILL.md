# power-composition-chart

功耗/STA 数据可视化模板：双条形对比图 + 双环组成图（matplotlib），生成 PNG 嵌入网站。适用于 PowerPro 功耗模块对比、setup/hold 违例分布、skew 对比等"两组数据按功能块对齐"或"组成占比"场景。

## 触发词

功耗图、组成图、对比图、条形图、环形图、donut chart、module comparison、power composition、可视化、画图

## 模板来源

HK1V11 项目 2026-10-19 用户确认满意的样式（`back_ppt/gen_power_composition_charts.py`）。

---

## 核心样式约定

### 颜色系
- **项目 A（主项目）**：青色系 `#1B7A8C`（深）、`#2E9B8C`（浅）
- **项目 B（对比项目）**：橙色系 `#E8913A`、`#D4600F`
- **辅助色**：`#5B8DB8` 蓝 / `#8B6BB1` 紫 / `#6BAF6B` 绿 / `#C0504D` 红 / `#999999` 灰

### 中文字体
```python
import matplotlib.font_manager as fm
for fp in fm.findSystemFonts(fontpaths=['C:/Windows/fonts']):
    if 'msyh' in fp.lower() or 'simhei' in fp.lower():
        fm.fontManager.addfont(fp); break
plt.rcParams['font.family'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
```

---

## 图 1：双条形对比图模板

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# 数据：(标签, 项目A值, 项目B值)，按项目A降序
mods = [
    ("功能块A\n模块名↔对应模块", valA, valB),
    ("功能块B\n模块名",           valA, 0),   # B无对应物填0
    ...
]
labels = [m[0] for m in mods]
vA = [m[1] for m in mods]
vB = [m[2] for m in mods]

fig, ax = plt.subplots(figsize=(14, 8))
y = np.arange(len(mods)); h = 0.38
b1 = ax.barh(y - h/2, vA, h, label='项目A (总功耗)', color='#1B7A8C', edgecolor='white', linewidth=0.5)
b2 = ax.barh(y + h/2, vB, h, label='项目B (总功耗)', color='#E8913A', edgecolor='white', linewidth=0.5)
ax.set_yticks(y); ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel('Power (µW)', fontsize=11)
ax.set_title('标题\n副标题（口径说明）', fontsize=13, fontweight='bold', pad=12)
ax.legend(fontsize=10, loc='lower right')
ax.invert_yaxis()  # 最大在顶部
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
ax.grid(axis='x', alpha=0.3, linestyle='--')
for bars in [b1, b2]:
    for bar in bars:
        w = bar.get_width()
        if w > 0:
            ax.text(w + offset, bar.get_y() + bar.get_height()/2, f'{w:.0f}', va='center', fontsize=8, color='#333')
plt.tight_layout()
plt.savefig('output.png', dpi=200, bbox_inches='tight')
```

## 图 2：双环组成图模板

```python
fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5))
# 左环：项目A
groups_A = [("标签1", val), ("标签2", val), ...]
colors_A = ['#1B7A8C', '#2E9B8C', '#E8913A', '#D4600F', '#5B8DB8', '#8B6BB1', '#6BAF6B', '#C0504D', '#999999']
wedges, texts, autotexts = ax1.pie([g[1] for g in groups_A], labels=[g[0] for g in groups_A],
    colors=colors_A, autopct='%1.1f%%', startangle=90, pctdistance=0.78,
    wedgeprops=dict(width=0.42, edgecolor='white', linewidth=1.5))  # width=环形宽度，0.42=标准环
for t in autotexts: t.set_fontsize(8); t.set_color('white'); t.set_fontweight('bold')
for t in texts: t.set_fontsize(9)
ax1.text(0, 0, '项目A\nXX.XX mW\n@频率', ha='center', va='center', fontsize=12, fontweight='bold')
# 右环同理，用 ax2
fig2.suptitle('总标题', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('output2.png', dpi=200, bbox_inches='tight')
```

---

## 工作流程

1. 准备数据数组（从 csv/report 提取，功能块配对）
2. 复制模板改数组 → `python script.py` 生成 PNG
3. 复制 PNG 到网站目录（team-share-public）
4. 在 ch08 等 html 中嵌入 `![标题](./filename.png)`
5. 双仓 commit + push
6. Pages `?v=<commit>` 验证

## 注意事项

- `matplotlib.use('Agg')` 必须在 import pyplot 之前
- 中文标签需要 `\n` 换行控制宽度
- B 项目无对应物的模块填 `0`，值标签跳过 `if w > 0`
- `dpi=200` 适合网站展示（清晰度够、文件 <300KB）
- 数据量 >12 组时饼图会拥挤，考虑合并小项为"其他"

## 参考实例

- HK1V11 vs 1V22 功耗对比：`E:\project\HK1V11\back_ppt\gen_power_composition_charts.py`
- 网站嵌入效果：ch08-powerpro.html §4.5「功耗组成可视化」
- commit：team-share-public `3ee6ba2`、HK1V11 `6ccf96d1`

---

<!-- ymzhu 2026-10-19 16:35 -->
