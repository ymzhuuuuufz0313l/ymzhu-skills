# 站点图生成管线参考模板（figure pipeline）

> 2026-11-18 从 team-share 四站审计沉淀。配合 `SKILL.md` 的「§验证门 5–8」与「§图版生命周期规则 6–9」使用。
> 一句话：**图 = 生成器 + 数据源 + 单一写入出口 + 有牙的校验门**，四件事缺一件就会在下一轮返工。

## 1. 目录与职责（单向，不许回写）

```
<站点>/
├── images/
│   ├── <name>.svg                 # 当前采纳版（静态，生成器输出）
│   ├── anim/<name>.svg            # 动画版（同源骨架 + kit）
│   ├── archive/<YYYYMMDD>/        # 只追加的快照
│   └── tools/gen_<name>.py        # 生成器（脚本头写清"生成哪几张图"）
└── <page>.html                    # 只引用主名 + ?v=<版本串>
```

数据源放在**上游仓库**（如 `E:/project/HK1V11/script/_chapter_viz/_power_data.py` 或 `power1117b_data.json`），
站点生成器**只读**它，绝不反向写。站点内不允许再存一份数字。

## 2. 生成器 CLI 契约（每个生成器都必须有）

```python
# gen_<name>.py —— 契约：默认幂等；--out 可重定向；--check 只判不写；DRIFT 拒写
# 用法：
#   python gen_<name>.py                 # 幂等写站点，内容没变则打印 SKIPPED
#   python gen_<name>.py --out DIR       # 从零重生（可复现性验证用）
#   python gen_<name>.py --check         # 只比对，漂移则 exit 1（CI 用）
#   python gen_<name>.py --allow-drift   # 显式越权覆盖漂移文件（事故恢复用）
```

三条硬性行为，缺一条不算合格：

1. **默认幂等**：内容逐字节相同 → 打印 `SKIPPED <path>`，不写盘、不改 mtime。
2. **`--out` 可重定向**：同一份输入跑两次到两个空目录，md5 必须相同（这是"从零可复现"的唯一证据）。
3. **漂移态拒写**：目标文件存在且其内嵌指纹 ≠ 本生成器预期指纹 → 打印 `DRIFT <path>` 并 `exit 2`；
   只有 `--allow-drift` 才写。**防止"改了代码顺手覆盖掉别人的线上图"**。

## 3. 单一写入出口 `_siteio.py`（站点必备）

```python
from pathlib import Path
import hashlib, shutil

def write_text_lf(path: Path, text: str) -> bool:
    """强制 LF 写入；内容相同则跳过。返回是否真的写了。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = text.replace("\r\n", "\n")
    if path.exists():
        cur = path.read_bytes()
        if cur == data.encode("utf-8"):
            print(f"SKIPPED {path}")
            return False
    # newline="" 是关键：否则 Windows 会把 \n 写成 \r\n
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(data)
    print(f"WRITTEN {path}")
    return True

def archive_snapshot(src: Path, archive_dir: Path, tag: str) -> Path:
    """快照只追加，同名已存在则加指纹后缀，绝不覆盖。"""
    archive_dir.mkdir(parents=True, exist_ok=True)
    stem, suf = src.stem, src.suffix
    dst = archive_dir / f"{stem}_{tag}{suf}"
    if dst.exists():
        h = hashlib.md5(src.read_bytes()).hexdigest()[:8]
        dst = archive_dir / f"{stem}_{tag}_{h}{suf}"
        if dst.exists():
            print(f"SKIPPED {dst}")
            return dst
    shutil.copy2(src, dst)
    print(f"ARCHIVED {dst}")
    return dst

def strip_tail_sigs(text: str) -> str:
    """只在写盘前调用：去掉末尾的 ymzhu 签名注释，保证"生成内容"可逐字节复现。"""
    import re
    return re.sub(r"\n?<!--\s*ymzhu \d{4}-\d{2}-\d{2} \d{2}:\d{2}\s*-->\s*$", "", text)
```

**签名与可复现的关系**：生成器产出内容不含签名 → 落盘后再统一追加一行尾签名（`write_page_one_sig`）。
这样 `--out` 结果与线上文件的差异只允许"尾签名那一行"，其余必须 `cmp` 一致。

## 4. 数据层校验（放在数据源脚本里，不放在站点）

```python
# 组成图：Σ片 必须等于中心值，百分比分母 = 中心值
total = sum(v for _, v in slices)
center = data["total_uw"]
assert abs(total - center) < 1e-6, f"slice sum {total} != center {center}"
assert abs(sum(p for _, p in pcts) - 100.0) < 0.05, "percentages must sum to 100.0"

# 口径变更护栏：残差片必须显式登记，且不许为负
residual = center - sum(registered)
if residual < 0:
    raise SystemExit(f"negative residual {residual}: 数据源口径不一致")
```

## 5. 校验门的"有牙"三连（写完门脚本必须自测）

```text
① 注入真实错误 → 必须红（exit != 0）
② 空输入 / 空扫描集 → 必须 FAIL，不许 PASS
③ 只改一处 → 错误定位必须指到那一处，不许"全绿/全红"
```

带 N=0 自证的扫描门骨架：

```python
scanned = 0
for p in root.rglob("*.svg"):
    scanned += 1
    ...
print(f"scanned {scanned} files")
if scanned == 0:
    print("RESULT: FAIL (scanned 0 files — path wrong or tree empty)")
    sys.exit(1)
```

## 6. 落地顺序（改图的固定流程）

1. 读数据源，确认数字口径与目标值（谁是大盘、谁是分片）。
2. 跑生成器 `--out` 到临时目录，与线上 `cmp` → 得到"是否已漂移"的基线结论。
3. 改生成器（不改产物），再 `--out` ×2 比 md5。
4. 写站点（幂等 → `SKIPPED`）。
5. 归档旧版（只追加）。
6. bump 页面引用 `?v=`；若站点有搜索索引，重生成索引并 `--check`。
7. 跑图门 `_svg_qa.py` / `_svg_anim_qa.py` + 站点 `validate_kit_v4.py` / `qa_site.py`。
8. 交付前走 `hk1v11-delivery-gate`（preflight → add → commit → push → ls-remote 核对）。

<!-- ymzhu 2026-11-18 10:43 -->
