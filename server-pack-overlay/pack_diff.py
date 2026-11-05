#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pack_diff.py — HK1V11 服务器回传包(PACK_TAR_*.tar.gz)全量 diff 与批准覆盖工具

流程定位（server-pack-overlay skill v2 强制流程）:
  1) 回传包落地后: python pack_diff.py <pack.tar.gz> [--out report.md]
     -> 全量 md5 比对（不依赖 mtime），输出【全部】差异清单 + 建议标签（仅供人参考，不做取舍）
  2) 人看报告逐文件/逐类拍板 -> 把批准覆盖的路径写进 approved.txt
  3) python pack_diff.py <pack.tar.gz> --apply approved.txt
     -> 只覆盖批准的文件，机械执行，输出落地清单供 CHANGES 记录

差异分类（枚举全集，不抽样）:
  identical  两边 md5 相同
  eol_only   仅行尾/空白差异（归一化后相同）——覆盖与否由人定
  diff       内容差异（报告含 git 最后提交时间 + 首 hunk 摘要）
  pack_only  包内有、本地无
  local_only 本地有、包内无（合并规则=保留本地，仅列出确认）

建议标签（非约束，最终判断权在人）:
  LOG-JUNK  Verdi/会话日志类   PRISTINE clk_period.tcl(默认不覆盖)
  IPCONS    ip_cons(逐 hunk 评估)  REGGEN  生成物(建议重新生成而非覆盖)
"""
import argparse, hashlib, os, re, subprocess, sys, tarfile

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

KNOWN_ROOTS = ['DV_TCON_C', 'HDL', 'SYNTHESIS', 'VERIFICATION']
LOCAL_ROOT = r'E:/project/HK1V11'
AREA_MAP = {}   # 例 {'VERIFICATION': 'DV_TCON_C'}，--map 注入
MAX_TEXT  = 4 * 1024 * 1024    # 超过则不做文本归一化/hunk（SYNTHESIS 大 rpt 保护）
MAX_HUNK  = 512 * 1024         # 超过则不算 hunk 摘要
JUNK_RE = re.compile(r'verdiLog|novas|fsdb\.|\.log$|\.~lock|turbo\.log|tdc\.list|verdi\.cmd|\.result$')
CODE_RE = re.compile(r'\.(sv|svh|v|vh|f|pl|py|sh|tcl|c|h|csh|md|txt)$', re.I)

def md5(b): return hashlib.md5(b).hexdigest()

def rel_path(name):
    """把包内成员名归一到 <AREA>/后续相对路径；返回 (area, rel) 或 None。
    兼容三种布局：../../../project/.../HK1V11/<AREA>/...、顶层 <AREA>/...、他人区 VERIFICATION/（经 AREA_MAP 映射）。"""
    parts = name.split('/')
    for i, p in enumerate(parts):
        if p in KNOWN_ROOTS:
            area = AREA_MAP.get(p, p)
            return area, '/'.join(parts[i + 1:])
    return None

def norm_text(b):
    try:
        s = b.decode('utf-8')
    except Exception:
        return None
    return [l.rstrip() for l in s.replace('\r\n', '\n').replace('\r', '\n').split('\n')]

def first_hunk(loc_lines, srv_lines, max_lines=6):
    import difflib
    d = list(difflib.unified_diff(loc_lines, srv_lines, lineterm='', n=0))
    return d[2:2 + max_lines] if len(d) > 2 else ['(no visible text diff)']

def git_last(path):
    try:
        r = subprocess.run(['git', 'log', '-1', '--format=%ad %h %s', '--date=format:%y%m%d',
                            '--', path], cwd=LOCAL_ROOT, capture_output=True, timeout=15,
                           encoding='utf-8', errors='replace')
        out = (r.stdout or '').strip()
        return (out or '(no git history)')[:90]
    except Exception:
        return '(git n/a)'

def collect(pack):
    entries = {}   # (area, rel) -> (size, tarfile member)
    with tarfile.open(pack, 'r:gz') as t:
        for m in t:
            if not m.isfile():
                continue
            rp = rel_path(m.name)
            if not rp or not rp[1]:
                continue
            entries[rp] = m
    return entries

def tag_for(area, rel):
    tags = []
    base = rel.rsplit('/', 1)[-1]
    if JUNK_RE.search(rel): tags.append('LOG-JUNK')
    if base == 'clk_period.tcl': tags.append('PRISTINE')
    if 'ip_cons' in base: tags.append('IPCONS')
    if rel.endswith('auto_script/env_cfg.sv'): tags.append('REGGEN')
    return ' '.join(tags) if tags else ''

def do_report(pack, out_path):
    # 单次顺序流式遍历（gzip tar 随机 extractfile 是 O(n²)，禁止二次遍历/排序后取数）
    res = {'identical': [], 'eol_only': [], 'diff': [], 'pack_only': []}
    areas_in_pack = set()
    # local 枚举：优先 git ls-files（只列 tracked，天然排除 gitignore 的解压产物/大产物噪音）；失败回退 os.walk
    local_all = {}   # area -> set(rel)（仅统计包内出现过的区域，单区包不把其他区全算进来）
    def enum_local():
        try:
            r = subprocess.run(['git', 'ls-files', '--', 'DV_TCON_C', 'HDL', 'SYNTHESIS'],
                               cwd=LOCAL_ROOT, capture_output=True, timeout=120,
                               encoding='utf-8', errors='replace')
            if r.returncode == 0 and r.stdout.strip():
                for line in r.stdout.splitlines():
                    area, _, rel = line.partition('/')
                    if rel:
                        local_all.setdefault(area, set()).add(rel)
                return 'git ls-files'
        except Exception:
            pass
        for area in ['DV_TCON_C', 'HDL', 'SYNTHESIS']:
            root = os.path.join(LOCAL_ROOT, area)
            if os.path.isdir(root):
                for r2, d, fs in os.walk(root):
                    if '.git' in r2: continue
                    for f in fs:
                        p = os.path.join(r2, f)
                        local_all.setdefault(area, set()).add(os.path.relpath(p, root).replace(os.sep, '/'))
        return 'os.walk'
    enum_src = enum_local()
    local_only = []
    n_pack = 0
    with tarfile.open(pack, 'r:gz') as t:
        for m in t:                      # 顺序流，一次到底
            if not m.isfile():
                continue
            rp = rel_path(m.name)
            if not rp or not rp[1]:
                continue
            area, rel = rp
            n_pack += 1
            areas_in_pack.add(area)
            lp = os.path.join(LOCAL_ROOT, area, rel.replace('/', os.sep))
            data = t.extractfile(m).read()   # 流式顺序读，非 seek
            if not os.path.isfile(lp):
                res['pack_only'].append((area, rel, len(data)))
            else:
                lb = open(lp, 'rb').read()
                if md5(data) == md5(lb):
                    res['identical'].append((area, rel))
                else:
                    if len(data) > MAX_TEXT or os.path.getsize(lp) > MAX_TEXT:
                        res['diff'].append((area, rel, len(data), os.path.getsize(lp),
                                            git_last(os.path.join(area, rel)), ['(size>4MB, md5-only)']))
                        continue
                    a, b = norm_text(data), norm_text(lb)
                    if a is not None and b is not None and a == b:
                        res['eol_only'].append((area, rel))
                    else:
                        if a and b and len(data) <= MAX_HUNK and os.path.getsize(lp) <= MAX_HUNK:
                            hunk = first_hunk(b, a)
                        else:
                            hunk = ['(text too large for hunk summary)']
                        res['diff'].append((area, rel, len(data), os.path.getsize(lp), git_last(os.path.join(area, rel)), hunk))
            local_all.setdefault(area, set()).discard(rel)
    for area, rels in local_all.items():
        if area not in areas_in_pack:
            continue
        for rel in sorted(rels):
            local_only.append(f'{area}/{rel}')

    L = []
    A = L.append
    A(f'# pack_diff 报告: {os.path.basename(pack)}')
    A('')
    A(f'- 包内文件: {n_pack} | identical: {len(res["identical"])} | eol_only: {len(res["eol_only"])} '
      f'| **diff: {len(res["diff"])}** | pack_only: {len(res["pack_only"])} | local_only: {len(local_only)} '
      f'| local 枚举: {enum_src}' + (f' | 区映射: {AREA_MAP}' if AREA_MAP else ''))
    A('')
    A('## diff（全部列出，含建议标签；是否覆盖由人拍板）')
    for area, rel, ssz, lsz, gl, hunk in res['diff']:
        A(f'### {area}/{rel}  `{tag_for(area, rel)}`')
        A(f'- 包 {ssz}B vs 本地 {lsz}B | 本地 git: {gl}')
        for h in hunk: A(f'    {h[:200]}{"…" if len(h) > 200 else ""}')
    A('## eol_only（仅行尾差异）')
    for area, rel in res['eol_only']: A(f'- {area}/{rel} `{tag_for(area, rel)}`')
    A('## pack_only（本地缺失）')
    for area, rel, sz in res['pack_only']: A(f'- {area}/{rel} ({sz}B) `{tag_for(area, rel)}`')
    A('## local_only（本地独有=保留，仅确认）')
    for r in local_only: A(f'- {r}')

    txt = '\n'.join(L)
    print(txt[:8000])
    if out_path:
        open(out_path, 'w', encoding='utf-8').write(txt + '\n')
        print(f'\n[完整报告已写入] {out_path}')
    return res

def do_apply(pack, approved):
    want = set(l.strip() for l in open(approved, encoding='utf-8') if l.strip() and not l.startswith('#'))
    done = []
    with tarfile.open(pack, 'r:gz') as t:   # 顺序流一遍，命中即写
        for m in t:
            if not m.isfile():
                continue
            rp = rel_path(m.name)
            if not rp or not rp[1]:
                continue
            area, rel = rp
            key = f'{area}/{rel}'
            if key not in want:
                continue
            lp = os.path.join(LOCAL_ROOT, area, rel.replace('/', os.sep))
            os.makedirs(os.path.dirname(lp), exist_ok=True)
            open(lp, 'wb').write(t.extractfile(m).read())
            done.append(key)
    miss = sorted(want - set(done))
    print(f'[apply] 覆盖 {len(done)} 个文件; 未命中 {len(miss)} 个')
    for k in miss: print(f'  MISS: {k}')
    rec = approved + '.applied.txt'
    open(rec, 'w', encoding='utf-8').write('\n'.join(done) + '\n')
    print(f'[apply] 落地清单已写入 {rec}（供 CHANGES 记录）')

def main():
    global AREA_MAP
    ap = argparse.ArgumentParser(description='HK1V11 服务器回传包全量 diff 与批准覆盖（DV_TCON_C/HDL/SYNTHESIS 通用）')
    ap.add_argument('pack', help='PACK_TAR_*.tar.gz 路径')
    ap.add_argument('--out', help='报告输出路径（缺省 <pack>_diff_report.md）')
    ap.add_argument('--apply', dest='approved', help='approved.txt：每行一个要覆盖的 <AREA>/<rel> 路径')
    ap.add_argument('--map', action='append', default=[], metavar='FROM=TO',
                    help='区名映射，可多次；如 --map VERIFICATION=DV_TCON_C')
    ap.add_argument('--areas', help='只比对这些区（逗号分隔），如 --areas HDL,SYNTHESIS')
    a = ap.parse_args()
    for m in a.map:
        f, _, t = m.partition('=')
        if f and t:
            AREA_MAP[f] = t
    if a.areas:
        only = set(a.areas.split(','))
        KNOWN_ROOTS[:] = [r for r in KNOWN_ROOTS if AREA_MAP.get(r, r) in only]
    if a.approved:
        do_apply(a.pack, a.approved)
    else:
        do_report(a.pack, a.out or (os.path.splitext(a.pack)[0] + '_diff_report.md'))

if __name__ == '__main__':
    main()
# ymzhu 2026-11-05 15:52
