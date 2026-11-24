#!/usr/bin/env python3
"""power-eco 第①步：DC 优化体检——全设计 flop 门控覆盖率逐模块统计。
用法: python netlist_health.py <netlist.gv> [--min-flops 20] [--top 30]
输出 ≤30 行模块表（按裸挂数降序）+ 全设计汇总。只读网表。
"""
import re, sys, io, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("netlist")
    ap.add_argument("--min-flops", type=int, default=20)
    ap.add_argument("--top", type=int, default=30)
    a = ap.parse_args()
    s = io.open(a.netlist, encoding="utf-8", errors="replace").read()

    mods = [(m.start(), m.group(1)) for m in re.finditer(r"^module (\w+) \(", s, re.M)]
    FLOP = re.compile(r"^\s+[A-Z0-9]*DFF[A-Z0-9]*\s+(\S+_reg\S*)\s*\((.*?)\);", re.S | re.M)
    CK_GATED = re.compile(r"\.CK\(\s*(net\d+|ECG_[A-Z_]+)\s*\)")
    CK_BARE = re.compile(r"\.CK\(\s*([A-Z][A-Z0-9_]+)\s*\)")

    rows = []; tot = gated = 0; by_clk = {}
    for i, (p, name) in enumerate(mods):
        e = mods[i+1][0] if i+1 < len(mods) else len(s)
        seg = s[p:e]
        if "SNPS_CG_MOD" in name or "CG_CELLX4" in name:
            continue
        flops = list(FLOP.finditer(seg))
        if not flops:
            continue
        icg = len(re.findall(r"SNPS_CG_CELL", seg))
        g = 0; bare = 0
        for m in flops:
            if CK_GATED.search(m.group(2)):
                g += 1
            else:
                mb = CK_BARE.search(m.group(2))
                if mb:
                    bare += 1
                    by_clk[mb.group(1)] = by_clk.get(mb.group(1), 0) + 1
        tot += len(flops); gated += g
        if len(flops) >= a.min_flops:
            rows.append((name, len(flops), icg, bare, len(flops) - g - bare))

    rows.sort(key=lambda r: -r[3])
    print(f"== DC 优化体检: {a.netlist}")
    print(f"== flop 总数 {tot} | CK 接 ICG {gated} ({100*gated/tot:.0f}%) | 裸挂 {tot-gated} ({100*(tot-gated)/tot:.0f}%)")
    print(f"{'module':<44}{'flops':>6}{'ICG':>5}{'bare':>6}{'bare%':>7}  初判")
    for n, f, c, b, o in rows[:a.top]:
        pct = 100 * b / f
        tag = "主战场" if (pct > 50 and f >= 50) else ("看EN现成否" if pct >= 20 else "DC已做透")
        print(f"{n:<44}{f:>6}{c:>5}{b:>6}{pct:>6.0f}%  {tag}")
    print("== 裸挂按时钟网:", ", ".join(f"{k} {v}" for k, v in sorted(by_clk.items(), key=lambda x: -x[1])))

if __name__ == "__main__":
    main()

# ymzhu 2026-11-24 10:05
