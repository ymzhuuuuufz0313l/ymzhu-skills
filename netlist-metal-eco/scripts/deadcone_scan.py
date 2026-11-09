#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
deadcone_scan.py — 网表"死锥"扫描 + 可复用 `&~` 门清单（金属层 ECO 找零件）

背景（见 SKILL.md 一、2）：金属层 ECO（base 冻结，只能改 metal/via）能不能做一个
功能，取决于有没有"可重新接线的现存逻辑门"。而找"可复用门"的判据**不是**"输出网 0 负载"
（那个只能抓完全无扇出的网，抓不到"输出喂进死锥"的门）。本脚本演示严格判据：

  (a) 粗筛：输出网负载 == 0 的驱动（完全无扇出）
  (b) 迭代死锥收敛：删掉"输出网负载==0 的实例"后，把它每个输入网的负载 -1，反复直到收敛
      —— 抓住 "输出有负载、但整条下游锥是死锥" 的链
  (c) 对命中的网名，跨模块逐字 grep 追到最下游，确认无真实消费点（人工，见 SKILL.md）
  (d) 用 RTL 侧"常量化残骸"佐证（optional）

本脚本是**骨架/教学模板**，按 Cadence Innovus `saveNetlist ... -excludeLeafCell` 的
层级网表格式编写（实例引脚列表常跨多行）。够跑通 HV1V22 这类网表；不同库/格式请按需扩展。

重要局限（骨架，务必读）：
  1. **net 名是模块内局部的**（如 `n47` 在许多模块各自定义）。本骨架**未做模块作用域隔离**，
     同名网会跨模块"串味"→ load 计数偏大、死锥结果不可信。真实用法必须**逐模块作用域**
     统计负载（每个 module 独立一份 net→load），或先做完整层级扁平化。
  2. 不做完整层级扁平化（端口绑定/位选/整总线拼接 `{}`/assign union-find）。
  3. 排除物理单元的 `PHYS_PREFIX` 只是常见前缀，必须按实际库核对。
  4. 层级端口负载盲区会让少数"其实是 port"的网被误判为死。
  ===> 所以脚本**只给线索**（结构统计是准的：本仓 HV1V22 得到 153/9470/152/9622），
       **判死 / 选定候选门必须人工逐字 grep 确认**（见 SKILL.md 一、2 步骤 c）。

用法:
    python deadcone_scan.py <netlist.v>
输出:
    1) 结构统计 (module / leaf / sub / inst 语句)
    2) 可复用 `&~` 门清单 (AND2B1*/AND2B2*/NAND2B1*/NAND2B2*)，附其输出网负载
    3) (a) 粗筛 load==0 的驱动网
    4) (b) 迭代死锥收敛后"死掉"的输出网
"""

import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# 可配置
# ---------------------------------------------------------------------------
POWER_PINS = {"VCCK", "GNDK", "VDDD", "VSSD", "VPW", "VNW",
              "VDD", "VSS", "VCC", "GND"}
# 输出引脚启发式（cell 输出脚常见名）；ICG 的 ENCLK 也是输出
OUTPUT_PINS = {"O", "Z", "Q", "QB", "QN", "OB", "CO", "TIE0", "TIE1", "ENCLK"}
AND2B_PREFIX = ("AND2B1", "AND2B2", "NAND2B1", "NAND2B2")
# 物理/常量单元前缀（不可当逻辑门；统计时排除）
PHYS_PREFIX = ("FILLER", "TAP", "ANTENNA", "DECAP", "BOUNDARY")


# ---------------------------------------------------------------------------
# 轻量解析（骨架：按 ; 切句，正确处理跨行实例）
# ---------------------------------------------------------------------------
def strip_comments(text):
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return text


def parse_modules(text):
    """返回 {module_name: [(cell, inst, {pin:net}), ...]}"""
    modules = {}
    for m in re.finditer(
        r"\bmodule\s+([A-Za-z_][A-Za-z_0-9]*)\s*(?:\((.*?)\))?\s*;(.*?)\bendmodule\b",
        text, flags=re.S):
        name, body = m.group(1), m.group(3)
        instances = []
        for stmt in body.split(";"):
            st = stmt.strip()
            if not st:
                continue
            if re.match(r"^(input|output|inout|wire|reg|tri|supply\d?|specify|"
                        r"parameter|localparam|integer|genvar|assign|defparam)\b", st):
                continue
            im = re.match(
                r"^([A-Za-z_][A-Za-z_0-9]*)\s+([A-Za-z_][A-Za-z_0-9]*)\s*\((.*)\)$",
                st, flags=re.S)
            if not im:
                continue
            cell, iname, pins = im.group(1), im.group(2), im.group(3)
            pin_map = {}
            for p in re.finditer(r"\.([A-Za-z_][A-Za-z_0-9]*)\s*\(([^()]*)\)", pins):
                pin_map[p.group(1)] = p.group(2).strip()
            if pin_map:
                instances.append((cell, iname, pin_map))
        modules[name] = instances
    return modules


def is_output_pin(pin, cell):
    if pin in OUTPUT_PINS:
        return True
    if pin == "S" and cell.startswith(("FA", "HA", "AD")):
        return True
    return False


def is_physical(cell):
    return cell.startswith(PHYS_PREFIX)


# ---------------------------------------------------------------------------
# 建模：每实例 -> (output_net, [input_nets]); 全局 load_count
# ---------------------------------------------------------------------------
def build_instances(modules):
    """返回 (inst_list, load_count)。inst_list = [(cell, inst, out_net, [in_nets])]"""
    inst_list = []
    load_count = defaultdict(int)
    for mname, insts in modules.items():
        for cell, iname, pin_map in insts:
            out_net = None
            in_nets = []
            for pin, net in pin_map.items():
                net = net.strip()
                if not net or net in POWER_PINS:
                    continue
                # 拼接/表达式（含 { } , 或 & |）不当单一网处理
                if any(ch in net for ch in "{}"):
                    continue
                if is_output_pin(pin, cell):
                    if out_net is None:
                        out_net = net
                else:
                    in_nets.append(net)
            if is_physical(cell):
                continue
            inst_list.append((cell, iname, out_net, in_nets))
    for cell, iname, out_net, in_nets in inst_list:
        for n in in_nets:
            load_count[n] += 1
    return inst_list, load_count


def deadcone_iterate(inst_list, load_count):
    """迭代死锥收敛。返回 {out_net: (cell, inst)} 死掉的实例输出网。"""
    lc = defaultdict(int, dict(load_count))
    alive = list(range(len(inst_list)))
    dead = {}
    changed = True
    while changed:
        changed = False
        still = []
        for idx in alive:
            cell, iname, out_net, in_nets = inst_list[idx]
            if out_net is not None and lc.get(out_net, 0) == 0:
                # 该实例输出无人消费 → 整锥死
                dead[out_net] = (cell, iname)
                for n in in_nets:
                    lc[n] -= 1   # 它不再是一个工作的消费者
                changed = True
            else:
                still.append(idx)
        alive = still
    return dead


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    fname = sys.argv[1]
    with open(fname, "r", encoding="utf-8", errors="ignore") as f:
        text = strip_comments(f.read())
    modules = parse_modules(text)
    mods = set(modules.keys())
    leaf = sum(1 for M in modules.values() for (c, i, p) in M if c not in mods)
    sub = sum(1 for M in modules.values() for (c, i, p) in M if c in mods)
    print(f"modules={len(modules)}  leaf_inst={leaf}  hier_inst={sub}  "
          f"total_inst={leaf + sub}\n")

    inst_list, load_count = build_instances(modules)

    # 1) `&~` 能力门清单
    print("=== `&~` 能力门 (AND2B1/AND2B2/NAND2B1/NAND2B2) ===")
    n_and = 0
    for mname, insts in modules.items():
        for cell, iname, pin_map in insts:
            if any(cell.startswith(p) for p in AND2B_PREFIX):
                onet = ""
                for pin, net in pin_map.items():
                    if is_output_pin(pin, cell):
                        onet = net
                        break
                print(f"  {mname}  {cell}  {iname}  .O({onet})  loads={load_count.get(onet, 0)}")
                n_and += 1
    print(f"  (共 {n_and} 个)\n")

    # 2) (a) 粗筛：输出网 load==0
    print("=== (a) 粗筛：输出网负载==0（第 1 步，仅完全无扇出） ===")
    n0 = 0
    for cell, iname, out_net, in_nets in inst_list:
        if out_net is not None and load_count.get(out_net, 0) == 0:
            print(f"  {out_net}  ({cell} {iname})  loads=0")
            n0 += 1
    print(f"  (共 {n0} 个)\n")

    # 3) (b) 迭代死锥收敛
    print("=== (b) 迭代死锥收敛后'死掉'的输出网（含死锥，比粗筛更多） ===")
    dead = deadcone_iterate(inst_list, load_count)
    for net, (cell, iname) in dead.items():
        print(f"  {net}  ({cell} {iname})")
    print(f"  (共 {len(dead)} 个) —— 这些是候选；跨模块消费点须人工 grep 确认")


if __name__ == "__main__":
    main()
