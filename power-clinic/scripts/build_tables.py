#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""power-clinic 第①步入口：DC 门级网表全设计底表（只读，不改网表）。

用法:
  python build_tables.py <netlist.gv> --out <ECO_HEALTH 目录> [--powercsv hier_pwr_detail.csv] [--mods M1,M2]

产出 <out>/data/:
  flops.csv             每个 flop：模块/行号/实例/cell/CK/D/复位/Q/时钟来源类别/时钟链/Q 负载数/死锥判定/D 锥叶子
  icgs.csv              每个 ICG：手写(dc 之外)/DC 自动、输入时钟、EN 网、EN 源叶子、EN 锥门数、直挂 flop 数
  clk_genealogy.csv     时钟网谱系：每 (模块, CK 网) 一行，源头类别、链上 ICG 及 EN、顶层端口、链摘要
  bare_groups.csv       裸挂 flop 按 (模块, CK, 寄存器名) 归组 + "EN 现成"启发式
  redundant_candidates.csv  冗余 FF 四形态候选（死寄存器 / 重复状态 / 直通级 / 常量 D）
  power_by_module.csv   PowerPro 叶子模块"自身"功耗（父行减去直接子行）
"""
import re, sys, os, csv, bisect, hashlib, argparse, collections

ID = r"[A-Za-z_$][\w$]*"
CONST_RE = re.compile(r"^(?:\d*'[bBdDhHoO][0-9a-fA-FxXzZ_]+|VDD|VSS|VDDO|VSSO|TIE[HhLl])$")
NET_RE = re.compile(r"^(%s)\s*(?:\[\s*(\d+)\s*(?::\s*(\d+))?\s*\])?$" % ID)
IDENT_RE = re.compile(r"(?<![\w'])(%s)\s*(?:\[\s*(\d+)\s*(?::\s*(\d+))?\s*\])?" % ID)
NONFUNC = {"APR_CDM"}          # 物理电容，不算功能负载
BUF_PRE = ("CLKBUF", "BUF", "INV", "CLKINV", "DEL")
DATA_PINS = ("D", "D1", "D2")
RST_PINS = ("RB", "SB")


def is_flop(c):
    return "DFF" in c.upper()


def is_icg(c):
    return c.upper().startswith("GCK")


def is_mux(c):
    return "MUX" in c.upper()


def is_buf(c):
    return c.upper().startswith(BUF_PRE)


def out_pins(cell, pins):
    c = cell.upper()
    if "DFF" in c:
        return {p for p in ("Q", "QB") if p in pins}
    if c.startswith("GCK"):
        return {"Q"} & set(pins)
    if c[:3] in ("FAX", "HAX") or c.startswith(("ADD", "FAD")):
        return {p for p in ("S", "CO") if p in pins}
    if "MUX2B" in c:
        return {"OB"} & set(pins)
    return {"O"} & set(pins)


def norm(e):
    """把引脚表达式归一成 (kind, base, (lo,hi)|None, raw)。kind: NET/CONST/OPEN/EXPR"""
    e = e.strip()
    if e == "":
        return ("OPEN", None, None, e)
    if CONST_RE.match(e):
        return ("CONST", e, None, e)
    m = NET_RE.match(e)
    if m:
        if m.group(2) is not None:
            lo = int(m.group(3)) if m.group(3) is not None else int(m.group(2))
            hi = int(m.group(2))
            return ("NET", m.group(1), (lo, hi), e)
        return ("NET", m.group(1), None, e)
    return ("EXPR", e, None, e)


def rng_match(rng, i):
    """负载引用区间 rng 是否覆盖第 i 位（i=None 表示整根/未知 → 全匹配）"""
    if rng is None or i is None:
        return True
    lo, hi = rng
    return lo <= i <= hi


def parse_pins(t):
    pins, i, n = {}, 0, len(t)
    while i < n:
        j = t.find(".", i)
        if j < 0:
            break
        mm = re.match(r"\.(\w+)\s*\(", t[j:])
        if not mm:
            i = j + 1
            continue
        k = j + mm.end()
        p, depth = k, 1
        while p < n and depth:
            c = t[p]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
            p += 1
        pins[mm.group(1)] = t[k:p - 1].strip()
        i = p
    return pins


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("netlist")
    ap.add_argument("--out", required=True)
    ap.add_argument("--powercsv")
    ap.add_argument("--mods", default="", help="只打印这些网表模块的摘要（逗号分隔）")
    ap.add_argument("--debug", default="", help="调试：MOD:NET;MOD:NET 打印时钟解析链")
    ap.add_argument("--cone", default="", help="取证：MOD:NET[:深度];... 打印组合扇入锥")
    ap.add_argument("--cone-head", type=int, default=80, help="每个锥最多打印多少行")
    ap.add_argument("--live", default="", help="取证：MOD:端口,端口;... 从这些输入端口出发的活输入可达组合锥")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "data"), exist_ok=True)

    raw = open(a.netlist, "rb").read()
    md5 = hashlib.md5(raw).hexdigest()
    s = raw.decode("utf-8", "replace")
    line_starts = [0] + [m.end() for m in re.finditer(r"\n", s)]

    def line_of(off):
        return bisect.bisect_right(line_starts, off)

    # ---------------- 1. 解析模块 ----------------
    mods = collections.OrderedDict()
    OTHER = []
    SUPPLIES = set()
    for m in re.finditer(r"^[ \t]*module\s+(\w+)\s*\((.*?)\);(.*?)^[ \t]*endmodule", s, re.S | re.M):
        name, bstart = m.group(1), m.start(3)
        M = dict(name=name, start=line_of(m.start()), end=line_of(m.end()), dir={}, assigns=[], insts=[])
        mods[name] = M
        for p in m.group(2).split(","):
            p = p.strip()
            if p:
                M["dir"][p] = "?"
        body = re.sub(r"//[^\n]*", "", m.group(3))
        pos = 0
        for rawst in body.split(";"):
            lead = len(rawst) - len(rawst.lstrip())
            st = rawst[lead:]
            off = bstart + pos + lead
            pos += len(rawst) + 1
            if not st:
                continue
            kw = re.match(r"^(input|output|inout|supply0|supply1|wire|tri|tri0|tri1|wand|wor)\b(.*)$", st, re.S)
            if kw:
                k, rest = kw.group(1), kw.group(2)
                for n in [x.strip() for x in re.sub(r"\[[^\]]*\]", "", rest).split(",") if x.strip()]:
                    if k in ("input", "output", "inout"):
                        M["dir"][n] = k
                    elif k.startswith("supply"):
                        SUPPLIES.add(n)
                continue
            if st.startswith("assign"):
                am = re.match(r"^assign\s+(.*?)\s*=(?!=)\s*(.*)$", st, re.S)
                if am:
                    M["assigns"].append(dict(kind="assign", lhs=norm(am.group(1)), rhs=norm(am.group(2)),
                                             line=line_of(off), text=" ".join(st.split())))
                continue
            im = re.match(r"^(\w+)\s+([^\s(]+)\s*\((.*)\)$", st, re.S)
            if im:
                M["insts"].append(dict(kind="inst", cell=im.group(1), cell0=None, inst=im.group(2),
                                       pins={p: norm(e) for p, e in parse_pins(im.group(3)).items()},
                                       line=line_of(off)))
                continue
            OTHER.append((name, line_of(off), st[:60]))
    top = [n for n in mods if not any(n in M2["insts"] and False for M2 in mods.values())]

    # ---------------- 2. 单实例包装模块拍平（库 wrapper / CG_CELLX4_N / SNPS_CG_MOD_*） ----------------
    # 判据取结构：只含 1 个原语实例、无 assign、每个端口 1:1 接到该实例引脚。
    # DC 对 RTL 模块保界（-no_autoungroup），真设计模块不会是这种形态；SDA_DLY_BUF 这类多实例模块自动排除。
    wrapper, single_design = {}, []
    for name, M in mods.items():
        if len(M["insts"]) == 1 and not M["assigns"] and (M["insts"][0]["cell"] in mods or is_flop(M["insts"][0]["cell"])):
            single_design.append(name)     # 单实例但内含层级实例/flop：真设计模块，保界不拍平
            continue
        if len(M["insts"]) != 1 or M["assigns"]:
            continue
        I = M["insts"][0]
        pmap, ok = {}, True
        for port, d in M["dir"].items():
            if d not in ("input", "output"):
                continue
            found = [p for p, e in I["pins"].items() if e[0] == "NET" and e[1] == port]
            if len(found) != 1:
                ok = False
                break
            pmap[port] = found[0]
        if ok and pmap:
            wrapper[name] = (I["cell"], pmap)
    for name, M in mods.items():
        for I in M["insts"]:
            c = I["cell"]
            if c in wrapper:
                bc, pmap = wrapper[c]
                I["cell0"] = c
                I["cell"] = bc
                I["pins"] = {pmap.get(p, p): e for p, e in I["pins"].items()}

    def icg_kind(I):
        c0 = I.get("cell0") or ""
        return "hand" if "CG_CELLX4" in c0 else ("dc" if "SNPS_CG_MOD" in c0 else "prim")

    # ---------------- 3. 驱动 / 负载 / 父实例索引 ----------------
    drv = collections.defaultdict(lambda: collections.defaultdict(list))
    loads = collections.defaultdict(lambda: collections.defaultdict(list))
    parents = collections.defaultdict(list)
    NOOUT = collections.Counter()
    NOOUT_EX = []
    for name, M in mods.items():
        for A in M["assigns"]:
            k, b, rng, raw_e = A["lhs"]
            if k == "NET":
                drv[name][b].append(dict(kind="assign", A=A, rng=rng))
            k2, b2, rng2, raw2 = A["rhs"]
            if k2 == "NET":
                loads[name][b2].append(dict(kind="assign", A=A, rng=rng2))
            elif k2 == "EXPR":
                for mm in IDENT_RE.finditer(raw2):
                    lo = int(mm.group(3)) if mm.group(3) is not None else (
                        int(mm.group(2)) if mm.group(2) is not None else None)
                    hi = int(mm.group(2)) if mm.group(2) is not None else None
                    loads[name][mm.group(1)].append(dict(kind="assign", A=A, rng=(lo, hi) if hi is not None else None))
        for I in M["insts"]:
            cell = I["cell"]
            # 层级实例（真设计模块）的输出脚 = 子模块的 output/inout 端口
            outs = ({p for p in I["pins"] if mods[cell]["dir"].get(p) in ("output", "inout")}
                    if cell in mods else out_pins(cell, set(I["pins"])))
            if not outs and cell.upper() not in NONFUNC:
                NOOUT[cell] += 1
                if len(NOOUT_EX) < 6:
                    NOOUT_EX.append((name.replace("HK1V11_digital_top_", ""), I["inst"], I.get("cell0"), sorted(I["pins"])))
            for p, e in I["pins"].items():
                if e[0] == "NET":
                    rec = dict(kind="inst", I=I, pin=p, rng=e[2])
                    if p in outs:
                        drv[name][e[1]].append(rec)
                    elif cell.upper() not in NONFUNC:
                        loads[name][e[1]].append(rec)
                elif e[0] == "EXPR" and p not in outs:
                    for mm in IDENT_RE.finditer(e[3]):
                        loads[name][mm.group(1)].append(dict(kind="inst", I=I, pin=p, rng=None))
            if I["cell"] in mods:
                parents[I["cell"]].append((name, I["inst"], I["pins"]))

    # ---------------- 4. 时钟链解析 ----------------
    ck_cache = {}

    def resolve(name, base, seen=frozenset(), depth=0):
        key = (name, base)
        if key in seen or depth > 80:
            return [[("LOOP", name, base, None)]]
        seen = seen | {key}
        out = []
        dr = drv[name].get(base, [])
        if not dr:
            d = mods[name]["dir"].get(base)
            if d in ("input", "inout", "?"):
                par = parents.get(name, [])
                if not par:
                    return [[("TOP_PORT", name, base, None)]]
                for (pm, pi, pmap) in par:
                    e = pmap.get(base)
                    if e is None:
                        out.append([("NOPORT", pm, pi + "." + base, None)])
                    elif e[0] != "NET":
                        out.append([("PORT_CONST", pm, pi + "." + base, e[3])])
                    else:
                        for p in resolve(pm, e[1], seen, depth + 1):
                            out.append([("UP", name, pi + "." + base, None)] + p)
                return out
            return [[("UNDRIVEN", name, base, None)]]
        for r in dr:
            if r["kind"] == "assign":
                A = r["A"]
                k2, b2, rng2, raw2 = A["rhs"]
                if k2 == "NET":
                    for p in resolve(name, b2, seen, depth + 1):
                        out.append([("ASSIGN", name, base + "=" + raw2, None)] + p)
                else:
                    out.append([("CONST" if k2 == "CONST" else "LOGIC", name, "assign " + base + "=" + raw2, None)])
                continue
            I = r["I"]
            cell, p = I["cell"], r["pin"]
            cu = cell.upper()
            if is_icg(cu):
                en, ck = I["pins"].get("E"), I["pins"].get("CK")
                tag = ("ICG", name, I["inst"], dict(en=en, kind=icg_kind(I), cell=cell, line=I["line"], out=base))
                if ck and ck[0] == "NET":
                    for q in resolve(name, ck[1], seen, depth + 1):
                        out.append([tag] + q)
                else:
                    out.append([tag, ("PORT_CONST", name, I["inst"], ck[3] if ck else None)])
            elif cell in mods:
                for q in resolve(cell, p, seen, depth + 1):
                    out.append([("SUB", name, I["inst"] + "." + p, None)] + q)
            elif is_flop(cu):
                out.append([("FLOP", name, I["inst"], cell)])
            elif is_mux(cu):
                s = I["pins"].get("S")
                for ip in ("I0", "I1"):
                    e = I["pins"].get(ip)
                    tag = ("MUX", name, I["inst"], dict(sel=s, inp=ip))
                    if e and e[0] == "NET":
                        for q in resolve(name, e[1], seen, depth + 1):
                            out.append([tag] + q)
                    else:
                        out.append([tag, ("PORT_CONST", name, I["inst"] + "." + ip, e[3] if e else None)])
            elif is_buf(cu):
                e = I["pins"].get("I")
                if e and e[0] == "NET":
                    for q in resolve(name, e[1], seen, depth + 1):
                        out.append([("BUF", name, I["inst"], cell)] + q)
                else:
                    out.append([("BUF", name, I["inst"], cell), ("PORT_CONST", name, I["inst"], e[3] if e else None)])
            else:
                out.append([("LOGIC", name, I["inst"] + ":" + cell, None)])
            if len(out) > 64:
                out = out[:64] + [["TRUNC"]]
                break
        return out

    def ck_info(name, base):
        """返回 dict: local_gated / all_icg / some_icg / cls / icgs(list 'mod/inst') / ens / tops / chain"""
        key = (name, base)
        if key in ck_cache:
            return ck_cache[key]
        paths = resolve(name, base)
        local, all_icg, some_icg = False, True, False
        icgs, ens, tops, leaves = [], [], set(), collections.Counter()
        for p in paths:
            has = any(st[0] == "ICG" for st in p if isinstance(st, tuple))
            some_icg = some_icg or has
            all_icg = all_icg and has
            # 本模块内经 assign/buf 直达的 ICG = 本地已门控；跨层(UP)后直达的 ICG = 上层已门控
            up = False
            for st in p:
                if isinstance(st, str) or st[0] in ("ASSIGN", "BUF", "UP"):
                    continue
                if st[0] == "ICG":
                    if st[1] == name:
                        local = True
                    else:
                        up = True
                break
            for st in p:
                if st[0] == "ICG":
                    tag = "%s/%s" % (st[1], st[2])
                    if tag not in icgs:
                        icgs.append(tag)
                    en = st[3]["en"]
                    ens.append("%s/%s<=%s" % (st[1], st[2], en[1] if en and en[0] == "NET" else (en[3] if en else "?")))
                elif st[0] in ("TOP_PORT", "UNDRIVEN", "FLOP", "LOGIC", "LOOP", "CONST", "TRUNC", "NOPORT", "PORT_CONST"):
                    leaves[st[0]] += 1
                    if st[0] == "TOP_PORT":
                        tops.add(st[2])
        if local:
            cls = "GATED_LOCAL"
        elif all_icg and up:
            cls = "GATED_UP"
        elif all_icg:
            cls = "BARE_SRC_GATED"
        elif some_icg:
            cls = "BARE_SRC_MIXED"
        elif leaves["FLOP"] or leaves["LOGIC"] or leaves["LOOP"]:
            cls = "BARE_SRC_FLOPLOGIC"
        else:
            cls = "BARE_SRC_FREE"
        chain = " <- ".join("%s:%s%s" % (st[0], st[1].replace("HK1V11_digital_top_", ""), (":" + str(st[2])) if isinstance(st[2], str) else "")
                            for st in paths[0]) if paths else ""
        info = dict(local_gated=local, all_icg=all_icg, cls=cls, icgs=icgs, ens=ens, tops=sorted(tops),
                    n_paths=len(paths), chain=chain, leaves=dict(leaves))
        ck_cache[key] = info
        return info

    # ---------------- 5. 组合锥回溯（EN 源叶子 / D 端叶子） ----------------
    def fanin(name, base, maxdepth=8, self_inst=None, _acc=None, _depth=0, _seen=None):
        """组合扇入叶子：FLOP:inst / SELF / ICG:inst / PORT:net / TOP:net / SUB:inst；返回 (leaves set, n_cells)"""
        if _acc is None:
            _acc = dict(leaves=set(), cells=0)
            _seen = set()
        if _depth > maxdepth or _acc["cells"] > 400:
            _acc["leaves"].add("LIMIT")
            return _acc
        if (name, base) in _seen:
            return _acc
        _seen.add((name, base))
        dr = drv[name].get(base, [])
        if not dr:
            d = mods[name]["dir"].get(base)
            _acc["leaves"].add(("TOP:" if not parents.get(name) else "PORT:") + base if d else "UND:" + base)
            return _acc
        for r in dr:
            if r["kind"] == "assign":
                k2, b2, rng2, raw2 = r["A"]["rhs"]
                if k2 == "NET":
                    fanin(name, b2, maxdepth, self_inst, _acc, _depth + 1, _seen)
                elif k2 == "CONST":
                    _acc["leaves"].add("CONST")
                else:
                    _acc["leaves"].add("EXPR")
                continue
            I = r["I"]
            cell = I["cell"]
            cu = cell.upper()
            if is_flop(cu):
                _acc["leaves"].add("SELF" if I["inst"] == self_inst else "FLOP:" + I["inst"].rstrip("_"))
            elif is_icg(cu):
                _acc["leaves"].add("ICG:" + I["inst"])
            elif cell in mods:
                _acc["leaves"].add("SUB:" + I["inst"])
            else:
                _acc["cells"] += 1
                outs = out_pins(cell, set(I["pins"]))
                for p, e in I["pins"].items():
                    if p in outs or e[0] != "NET":
                        continue
                    fanin(name, e[1], maxdepth, self_inst, _acc, _depth + 1, _seen)
        return _acc

    # ---------------- 6. Q 负载计数 + 死锥前向可达 ----------------
    def count_loads(name, base, i, depth=0):
        n = sum(1 for L in loads[name].get(base, []) if rng_match(L["rng"], i))
        if mods[name]["dir"].get(base) in ("output", "inout", "?") and depth < 12:
            for (pm, pi, pmap) in parents.get(name, []):
                e = pmap.get(base)
                if e and e[0] == "NET":
                    n += count_loads(pm, e[1], i, depth + 1)
        return n

    reach_memo = {}

    def reach(name, base, i, seen=frozenset(), self_inst=None):
        """Q 往前追：到达 其它状态件/层级边界/有负载的输出端口 → 返回见证串；否则 None（死锥）。
        self_inst = 起点 flop 自身：回到自己 D 端的自保持不算活。"""
        key = (name, base, i, self_inst)
        if key in seen:
            return "LOOP?"
        if key in reach_memo:
            return reach_memo[key]
        seen = seen | {key}
        res = None
        for L in loads[name].get(base, []):
            if not rng_match(L["rng"], i):
                continue
            if L["kind"] == "assign":
                k, b, r, raw = L["A"]["lhs"]
                if k == "NET":
                    res = reach(name, b, i, seen, self_inst)
                else:
                    res = "ASSIGN_EXPR:" + raw[:30]
            else:
                I, cell, p = L["I"], L["I"]["cell"], L["pin"]
                cu = cell.upper()
                if is_flop(cu):
                    if I["inst"] != self_inst:          # 自保持环不算负载
                        res = "FF:" + I["inst"].rstrip("_") + "." + p
                elif is_icg(cu):
                    res = "ICG:" + I["inst"] + "." + p
                elif cell in mods:
                    res = "HIER:" + I["inst"] + "." + p
                else:
                    # 组合门：输出若是模块端口，由 reach 的端口分支接着往上追
                    for op in out_pins(cell, set(I["pins"])):
                        e = I["pins"].get(op)
                        if e and e[0] == "NET":
                            res = res or reach(name, e[1], i, seen, self_inst)
            if res:
                break
        # 起点自身是模块输出端口 → 到父模块继续追；顶层输出 = 活
        if res is None and mods[name]["dir"].get(base) in ("output", "inout", "?"):
            par = parents.get(name, [])
            if not par:
                res = "TOP_OUT:" + base
            for (pm, pi, pmap) in par:
                pe = pmap.get(base)
                if pe and pe[0] == "NET":
                    res = res or reach(pm, pe[1], i, seen, self_inst)
        reach_memo[key] = res
        return res

    def d_src_flop(name, base, i=None, depth=0):
        """D 端经 assign/buf 直通到某个 flop 的 Q → 返回该 flop 实例名（按位匹配驱动）"""
        if depth > 4:
            return None
        dr = [r for r in drv[name].get(base, [])
              if r["rng"] is None or i is None or r["rng"][0] <= i <= r["rng"][1]]
        if len(dr) != 1:
            return None
        r = dr[0]
        if r["kind"] == "assign":
            k2, b2, _, _ = r["A"]["rhs"]
            return d_src_flop(name, b2, i, depth + 1) if k2 == "NET" else None
        I = r["I"]
        if is_flop(I["cell"]) and r["pin"] in ("Q", "QB"):
            return I["inst"].rstrip("_") + ("" if r["pin"] == "Q" else "(QB)")
        if is_buf(I["cell"]):
            e = I["pins"].get("I")
            return d_src_flop(name, e[1], e[2][0] if e[2] else None, depth + 1) if e and e[0] == "NET" else None
        return None

    # ---------------- 7. 逐 flop 建表（包装模块内部实例已拍平到父层，不重复计） ----------------
    flops, icgs = [], []
    for name, M in mods.items():
        if name in wrapper:
            continue
        for I in M["insts"]:
            cell = I["cell"]
            P = I["pins"]
            if is_icg(cell):
                en, ck, q = P.get("E"), P.get("CK"), P.get("Q")
                acc = fanin(name, en[1], maxdepth=14) if en and en[0] == "NET" else dict(leaves=set(["CONST:" + (en[3] if en else "?")]), cells=0)
                icgs.append(dict(module=name, line=I["line"], inst=I["inst"], kind=icg_kind(I), wrapper=I.get("cell0") or "",
                                 clk_in=ck[1] if ck and ck[0] == "NET" else (ck[3] if ck else ""),
                                 en=en[1] if en and en[0] == "NET" else (en[3] if en else ""),
                                 out=q[1] if q and q[0] == "NET" else "",
                                 en_leaves=" ".join(sorted(acc["leaves"])), en_cells=acc["cells"], n_out=0))
                continue
            if not is_flop(cell):
                continue
            iname = I["inst"].rstrip("_")
            mm = re.match(r"^(.*)_reg(?:_(\d+))?$", iname)
            reg, idx = (mm.group(1), int(mm.group(2)) if mm.group(2) is not None else None) if mm else (iname, None)
            ck = P.get("CK")
            ckb = ck[1] if ck and ck[0] == "NET" else ""
            ci = ck_info(name, ckb) if ckb else dict(local_gated=False, cls="NO_CK", icgs=[], ens=[], tops=[], n_paths=0, chain="", leaves={})
            q = P.get("Q", P.get("QB"))
            qb, qi = (q[1], (q[2][0] if q[2] else None)) if q and q[0] == "NET" else ("", None)
            outs = []
            for op in ("Q", "QB"):
                e = P.get(op)
                if e and e[0] == "NET":
                    outs.append((op, e[1], e[2][0] if e[2] else None))
            nload = sum(count_loads(name, b, i) for _, b, i in outs)
            wit = [reach(name, b, i, frozenset(), I["inst"]) for _, b, i in outs]
            dead = (nload == 0) or all(w is None for w in wit)
            rst = ";".join("%s=%s" % (rp, P[rp][3]) for rp in RST_PINS if rp in P)
            rst_type = ("set" if "SB" in P and "RB" not in P else ("reset" if "RB" in P and "SB" not in P else ("set+reset" if ("SB" in P or "RB" in P) else "none")))
            dsrc = [d_src_flop(name, P[dp][1], P[dp][2][0] if P[dp][2] else None) for dp in DATA_PINS if dp in P and P[dp][0] == "NET"]
            dconst = all(P[dp][0] == "CONST" for dp in DATA_PINS if dp in P) and any(dp in P for dp in DATA_PINS)
            acc = fanin(name, P["D"][1], maxdepth=6, self_inst=I["inst"]) if "D" in P and P["D"][0] == "NET" else dict(leaves=set(), cells=0)
            if "D2" in P and P["D2"][0] == "NET":
                acc2 = fanin(name, P["D2"][1], maxdepth=6, self_inst=I["inst"])
                acc["leaves"] |= acc2["leaves"]
                acc["cells"] += acc2["cells"]
            leaves = set(acc["leaves"])
            mux_en = ""
            dr = drv[name].get(P["D"][1], []) if "D" in P and P["D"][0] == "NET" else []
            if dr and dr[0]["kind"] == "inst":
                DI = dr[0]["I"]
                if is_mux(DI["cell"]):
                    qe = P.get("Q")
                    ins = [e[1] for p, e in DI["pins"].items() if p not in ("S", "O", "OB") and e[0] == "NET"]
                    if qe and qe[0] == "NET" and qe[1] in ins:
                        se = DI["pins"].get("S")
                        mux_en = se[1] if se and se[0] == "NET" else ""
            flops.append(dict(module=name, line=I["line"], inst=iname, cell=cell, reg=reg, idx=("" if idx is None else idx),
                              ck=ckb, ck_cls=ci["cls"], ck_src=" ".join(ci["icgs"]) if ci["icgs"] else " ".join(ci["tops"]),
                              ck_chain=ci["chain"],
                              d=";".join("%s=%s" % (dp, P[dp][3]) for dp in DATA_PINS if dp in P),
                              reset=rst, rst_type=rst_type, q=q[3] if q and q[0] != "OPEN" else "", q_loads=nload,
                              dead="Y" if dead else "", reach=" | ".join(str(w) for w in wit),
                              fb="Y" if "SELF" in leaves else "", mux_en=mux_en,
                              d_leaves=" ".join(sorted(leaves - {"SELF"})), d_cells=acc["cells"],
                              pass_src=" ".join(x for x in dsrc if x), const_d="Y" if dconst else ""))
    for ic in icgs:
        ic["n_out"] = sum(1 for f in flops if f["module"] == ic["module"] and f["ck"] == ic["out"])

    def wcsv(fn, rows, cols):
        p = os.path.join(a.out, "data", fn)
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return p

    F = sorted(flops, key=lambda f: (f["module"], f["line"]))
    wcsv("flops.csv", F, ["module", "line", "inst", "cell", "reg", "idx", "ck", "ck_cls", "ck_src", "reset", "rst_type", "d",
                          "q", "q_loads", "dead", "reach", "fb", "mux_en", "d_leaves", "d_cells", "pass_src", "const_d", "ck_chain"])
    I_ = sorted(icgs, key=lambda x: (x["module"], x["line"]))
    wcsv("icgs.csv", I_, ["module", "line", "inst", "kind", "wrapper", "clk_in", "en", "out", "n_out", "en_leaves", "en_cells"])

    # 时钟网谱系：每 (模块, CK 网) 一行
    clk = collections.OrderedDict()
    for f in flops:
        k = (f["module"], f["ck"])
        r = clk.setdefault(k, dict(module=f["module"], ck=f["ck"], n=0, local=0, cls=f["ck_cls"], src=f["ck_src"], n_paths=0, chain=f["ck_chain"]))
        r["n"] += 1
        r["local"] += 1 if f["ck_cls"].startswith("GATED") else 0
    for r in clk.values():
        ci = ck_cache[(r["module"], r["ck"])]
        r["ens"] = " ".join(ci["ens"])
        r["tops"] = " ".join(ci["tops"])
        r["n_paths"] = ci["n_paths"]
    CK = sorted(clk.values(), key=lambda r: (r["module"], -r["n"]))
    wcsv("clk_genealogy.csv", CK, ["module", "ck", "n", "local", "cls", "src", "ens", "tops", "n_paths", "chain"])

    # 裸挂归组 + EN 现成启发式
    grp = collections.OrderedDict()
    for f in flops:
        if f["ck_cls"].startswith("GATED"):
            continue
        k = (f["module"], f["ck"], f["reg"])
        g = grp.setdefault(k, dict(module=f["module"], ck=f["ck"], ck_cls=f["ck_cls"], reg=f["reg"], n=0, cells=set(), n_fb=0,
                                   mux_en=set(), common=None, rst=set(), idxs=[], lmin=f["line"], lmax=f["line"]))
        g["n"] += 1
        g["lmin"] = min(g["lmin"], f["line"])
        g["lmax"] = max(g["lmax"], f["line"])
        g["cells"].add(f["cell"])
        g["n_fb"] += 1 if f["fb"] else 0
        if f["mux_en"]:
            g["mux_en"].add(f["mux_en"])
        g["rst"].add(f["rst_type"])
        g["idxs"].append(f["idx"])
        ls = set(f["d_leaves"].split()) if f["d_leaves"] else set()
        g["common"] = ls if g["common"] is None else (g["common"] & ls)
    G = []
    for g in grp.values():
        g["cells"] = " ".join(sorted(g["cells"]))
        g["mux_en"] = " ".join(sorted(g["mux_en"]))
        g["rst"] = " ".join(sorted(g["rst"]))
        g["common"] = " ".join(sorted(g["common"] or set()))
        g["idxs"] = ",".join(str(x) for x in sorted(g["idxs"], key=lambda x: (x == "", x)) if x != "") if any(x != "" for x in g["idxs"]) else ""
        G.append(g)
    G.sort(key=lambda g: (g["module"], -g["n"]))
    wcsv("bare_groups.csv", G, ["module", "ck", "ck_cls", "reg", "n", "lmin", "lmax", "cells", "n_fb", "mux_en", "common", "rst", "idxs"])

    # 冗余候选（passthrough 补源 flop 的时钟，判是否同 CK）
    fidx = {(f["module"], f["inst"]): f for f in F}
    red = []
    for f in F:
        if f["dead"]:
            red.append(dict(kind="dead", module=f["module"], line=f["line"], inst=f["inst"], cell=f["cell"], ck=f["ck"], detail="q_loads=%s reach=%s" % (f["q_loads"], f["reach"])))
        if f["const_d"]:
            red.append(dict(kind="const_d", module=f["module"], line=f["line"], inst=f["inst"], cell=f["cell"], ck=f["ck"], detail="d=%s reset=%s" % (f["d"], f["reset"])))
        # 已门控 flop 的 D 直连上级 Q 是正常门控形态（保持已进 ICG），不算直通级
        for srcn in (f["pass_src"].split() if not f["ck_cls"].startswith("GATED") else []):
            sf = fidx.get((f["module"], srcn.rstrip("(QB)") if srcn.endswith("(QB)") else srcn))
            red.append(dict(kind="passthrough", module=f["module"], line=f["line"], inst=f["inst"], cell=f["cell"], ck=f["ck"],
                            detail="D<=%s | src_ck=%s | same_ck=%s | src_cell=%s" % (srcn, sf["ck"] if sf else "?", "Y" if sf and sf["ck"] == f["ck"] else "N", sf["cell"] if sf else "?")))
    dup = collections.OrderedDict()
    for f in F:
        key = (f["module"], f["cell"], f["ck"], f["d"], f["reset"])
        dup.setdefault(key, []).append(f)
    for key, fl in dup.items():
        if len(fl) > 1:
            for f in fl:
                red.append(dict(kind="duplicate", module=f["module"], line=f["line"], inst=f["inst"], cell=f["cell"], ck=f["ck"],
                                detail="same-as:" + " ".join(x["inst"] for x in fl if x is not f) + " | q=%s loads=%s" % (f["q"], f["q_loads"])))
    red.sort(key=lambda r: (r["module"], r["kind"], r["line"]))
    wcsv("redundant_candidates.csv", red, ["kind", "module", "inst", "line", "cell", "ck", "detail"])

    # PowerPro 自身功耗
    if a.powercsv and os.path.isfile(a.powercsv):
        rows = collections.OrderedDict()
        cur = None
        for line in open(a.powercsv, encoding="utf-8", errors="replace"):
            c = [x.strip() for x in line.strip().split(";")]
            if len(c) < 8:
                continue
            if c[1] == "Power Group":          # 块头行：给出本组的层级名
                cur = c[0]
                continue
            if cur is None or c[1] not in ("register", "combinational", "clock_network", "total"):
                continue
            try:
                rows[(cur, c[1])] = (int(float(c[2])), float(c[6]))
            except ValueError:
                continue
        hiers = sorted({k[0] for k in rows}, key=len)
        P = []
        for h in hiers:
            kids = [k for k in hiers if k.startswith(h + ".") and "." not in k[len(h) + 1:]]
            P.append(dict(hier=h, leaf=h.split(".")[-1],
                          **{g: round(rows.get((h, g), (0, 0.0))[1] - sum(rows.get((k, g), (0, 0.0))[1] for k in kids), 2) for g in ("register", "combinational", "clock_network", "total")},
                          reg_cnt=rows.get((h, "register"), (0, 0.0))[0] - sum(rows.get((k, "register"), (0, 0.0))[0] for k in kids)))
        P.sort(key=lambda r: -r["register"])
        wcsv("power_by_module.csv", P, ["hier", "leaf", "register", "combinational", "clock_network", "total", "reg_cnt"])

    def comb_live(name):
        """从模块输入端口出发、只穿过组合门（不穿过 flop/ICG/层级）能碰到的组合门数 = "活输入可达锥"。
        返回 (活可达组合门数, 模块组合门总数, 到达的 flop D 脚数, 到达的输出端口数)"""
        total = 0
        for I in mods[name]["insts"]:
            c = I["cell"]
            if c not in mods and not is_flop(c) and not is_icg(c) and c.upper() not in NONFUNC:
                total += 1
        seen, nd, nport = set(), set(), set()
        front = [b for b, d in mods[name]["dir"].items() if d in ("input", "inout", "?")]
        done = set(front)
        while front:
            n = front.pop()
            for L in loads[name].get(n, []):
                if L["kind"] != "inst":
                    continue
                I = L["I"]
                c = I["cell"]
                if is_flop(c):
                    if L["pin"] in DATA_PINS:
                        nd.add(I["inst"])
                    continue
                if is_icg(c) or c in mods or c.upper() in NONFUNC:
                    continue
                if id(I) in seen:
                    continue
                seen.add(id(I))
                for op in out_pins(c, set(I["pins"])):
                    e = I["pins"].get(op)
                    if e and e[0] == "NET":
                        if mods[name]["dir"].get(e[1]) in ("output", "inout"):
                            nport.add(e[1])
                        if e[1] not in done:
                            done.add(e[1])
                            front.append(e[1])
        return len(seen), total, len(nd), len(nport)

    CL = []
    for name in mods:
        if name in wrapper:
            continue
        a_, b_, c_, d_ = comb_live(name)
        if b_:
            CL.append(dict(module=name, comb_total=b_, comb_live=a_, live_pct=round(100.0 * a_ / b_), flop_d_reached=c_, out_ports_reached=d_))
    CL.sort(key=lambda r: -r["comb_live"])
    wcsv("comb_live.csv", CL, ["module", "comb_total", "comb_live", "live_pct", "flop_d_reached", "out_ports_reached"])

    # 组合锥打印（调试/取证）：--cone "MOD:NET[:深度];..."
    out = sys.stdout
    for tok in [x for x in a.cone.split(";") if x.strip()]:
        parts = tok.split(":")
        mod, net = parts[0], parts[1]
        dmax = int(parts[2]) if len(parts) > 2 else 14
        out.write("== CONE %s : %s (depth<=%d)\n" % (mod.replace("HK1V11_digital_top_", ""), net, dmax))
        rows, seen, stack = [], set(), [(net, 0)]
        while stack:
            n, d = stack.pop()
            if (n, d) in seen:
                continue
            seen.add((n, d))
            for r in drv[mod].get(n, []):
                if r["kind"] == "assign":
                    k2, b2, _, raw2 = r["A"]["rhs"]
                    rows.append((r["A"]["line"], "assign %s = %s" % (n, raw2)))
                    if k2 == "NET" and d < dmax:
                        stack.append((b2, d + 1))
                    continue
                I = r["I"]
                if is_flop(I["cell"]) or is_icg(I["cell"]) or I["cell"] in mods:
                    rows.append((I["line"], "LEAF %s %s .%s(%s)" % (I["cell"], I["inst"], r["pin"], n)))
                    continue
                ins = [p for p in I["pins"] if p not in out_pins(I["cell"], set(I["pins"]))]
                rows.append((I["line"], "%s %s ( %s )" % (I["cell"], I["inst"], ", ".join(".%s(%s)" % (p, I["pins"][p][3]) for p in sorted(ins)))))
                if d < dmax:
                    for p in ins:
                        e = I["pins"][p]
                        if e[0] == "NET":
                            stack.append((e[1], d + 1))
        for ln, t in sorted(rows)[:int(getattr(a, "cone_head", 80))]:
            out.write("   L%-6d %s\n" % (ln, t))

    # 从指定输入端口出发的"活输入可达锥"（--live "MOD:p1,p2;..."）：只穿过组合门，到 flop 为止
    for tok in [x for x in a.live.split(";") if x.strip()]:
        mod, ps = tok.split(":")
        ports = ps.split(",")
        seen, nd, nport, types = set(), collections.Counter(), set(), collections.Counter()
        front, done = list(ports), set(ports)
        while front:
            n = front.pop()
            for L in loads[mod].get(n, []):
                if L["kind"] != "inst":
                    continue
                I = L["I"]
                c = I["cell"]
                if is_flop(c):
                    if L["pin"] in DATA_PINS:
                        nd[re.sub(r"_reg.*$", "", I["inst"].rstrip("_"))] += 1
                    continue
                if is_icg(c) or c in mods or c.upper() in NONFUNC or id(I) in seen:
                    continue
                seen.add(id(I))
                types[c] += 1
                for op in out_pins(c, set(I["pins"])):
                    e = I["pins"].get(op)
                    if e and e[0] == "NET":
                        if mods[mod]["dir"].get(e[1]) in ("output", "inout"):
                            nport.add(e[1])
                        if e[1] not in done:
                            done.add(e[1])
                            front.append(e[1])
        total = sum(1 for I in mods[mod]["insts"]
                    if I["cell"] not in mods and not is_flop(I["cell"]) and not is_icg(I["cell"]) and I["cell"].upper() not in NONFUNC)
        out.write("== LIVE %s from [%s]: %d / %d comb cells (%.0f%%); flop-D groups reached: %s; out ports: %s\n" % (
            mod.replace("HK1V11_digital_top_", ""), ",".join(ports), len(seen), total, 100.0 * len(seen) / max(total, 1),
            " ".join("%s×%d" % kv for kv in nd.most_common(24)), " ".join(sorted(nport))))
        out.write("   cell types: %s\n" % ", ".join("%s %d" % kv for kv in types.most_common(12)))

    # ---------------- 8. 控制台摘要 ----------------
    out = sys.stdout
    for tok in [x for x in a.debug.split(";") if x.strip()]:
        mod, net = tok.split(":")
        out.write("== DEBUG resolve %s : %s  dir=%s\n" % (mod.replace("HK1V11_digital_top_", ""), net, mods[mod]["dir"].get(net)))
        for p in resolve(mod, net):
            out.write("   " + " <- ".join(("%s@%s:%s" % (st[0], st[1].replace("HK1V11_digital_top_", ""), st[2])) if isinstance(st, tuple) else str(st) for st in p) + "\n")
    out.write("== build_tables: %s\n== md5 %s | modules %d (库包装 %d, 单实例设计模块 %d: %s) | insts %d | OTHER stmts %d | no-output cells %s | ex %s\n" % (
        a.netlist, md5, len(mods), len(wrapper), len(single_design),
        " ".join(n.replace("HK1V11_digital_top_", "") for n in single_design),
        sum(len(M["insts"]) for M in mods.values()), len(OTHER), dict((k, v) for k, v in NOOUT.items() if "AL9" in k), NOOUT_EX))
    tot = len(flops)
    gated = sum(1 for f in flops if f["ck_cls"].startswith("GATED"))
    out.write("== flops %d | 本地已门控 %d | 裸挂 %d\n" % (tot, gated, tot - gated))
    byc = collections.Counter(f["ck_cls"] for f in flops if not f["ck_cls"].startswith("GATED"))
    out.write("== 裸挂按时钟来源类别: %s\n" % ", ".join("%s %d" % kv for kv in byc.most_common()))
    out.write("== ICG %d (dc %d / hand %d); EN 锥 >50 门的 ICG: %s\n" % (
        len(icgs), sum(1 for i in icgs if i["kind"] == "dc"), sum(1 for i in icgs if i["kind"] == "hand"),
        " ".join("%s/%s(%d)" % (i["module"].replace("HK1V11_digital_top_", ""), i["inst"], i["en_cells"]) for i in icgs if i["en_cells"] > 50)))
    redc = collections.Counter(r["kind"] for r in red)
    out.write("== 冗余候选: %s\n" % ", ".join("%s %d" % kv for kv in redc.most_common()))
    want = [w.strip() for w in a.mods.split(",") if w.strip()]
    for name in mods:
        short = name.replace("HK1V11_digital_top_", "")
        if want and not any(w.lower() in short.lower() for w in want):
            continue
        fl = [f for f in flops if f["module"] == name]
        if not fl and not want:
            continue
        b = sum(1 for f in fl if not f["ck_cls"].startswith("GATED"))
        out.write("-- %s: flops %d / 裸挂 %d / ICG %d / 冗余候选 %s\n" % (
            short, len(fl), b, sum(1 for i in icgs if i["module"] == name),
            dict(collections.Counter(r["kind"] for r in red if r["module"] == name)) or "-"))
        for r in CK:
            if r["module"] == name:
                out.write("     CK %-14s n=%-4d local=%-4d %-16s src=%s\n" % (r["ck"], r["n"], r["local"], r["cls"], r["ens"] or r["tops"]))
    for n in sorted(SUPPLIES):
        pass


if __name__ == "__main__":
    main()

# ymzhu 2026-11-24 17:05
