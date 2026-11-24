#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小查询器：按列过滤打印 data/*.csv（只读）。用法:
  python q.py <csv> [--where 列=子串 ...] [--sort 列] [--desc] [--cols 列,列] [--head N] [--width W]
未给 --cols 时打印全部列（每格按 --width 截断）。"""
import sys, csv, argparse, os

ap = argparse.ArgumentParser()
ap.add_argument("csv")
ap.add_argument("--where", action="append", default=[])
ap.add_argument("--sort")
ap.add_argument("--desc", action="store_true")
ap.add_argument("--cols", default="")
ap.add_argument("--head", type=int, default=60)
ap.add_argument("--width", type=int, default=40)
a = ap.parse_args()
p = a.csv if os.path.isabs(a.csv) or os.path.exists(a.csv) else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", a.csv)
rows = list(csv.DictReader(open(p, encoding="utf-8")))
for w in a.where:
    k, v = w.split("=", 1)
    rows = [r for r in rows if v.lower() in (r.get(k) or "").lower()]
cols = [c for c in a.cols.split(",") if c] or list(rows[0].keys()) if rows else []
if a.sort:
    def key(r):
        x = r.get(a.sort, "")
        try:
            return float(x)
        except ValueError:
            return x
    rows.sort(key=key, reverse=a.desc)
print("%d rows" % len(rows))
for r in rows[:a.head]:
    print(" | ".join(("%-*s" % (a.width, (r.get(c) or "")[:a.width].replace("HK1V11_digital_top_", ""))) for c in cols))

# ymzhu 2026-11-24 11:20
