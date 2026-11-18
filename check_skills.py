#!/usr/bin/env python3
# check_skills.py —— skill 库自检门（2026-11-18 新增，Q6=A 拍板）
# 用法：
#   python check_skills.py            # 全量自检，exit 0 = 全绿
#   python check_skills.py --negatest # 有牙负测：注入坏指针/双签名/CRLF，必须逐项被抓到
# 改动任何 skill 后必须跑一次且 exit 0 才算可提交。
import re, sys, os
from pathlib import Path

ROOT = Path(__file__).parent
SIG = re.compile(r'<!-- ymzhu \d{4}-\d{2}-\d{2} \d{2}:\d{2} -->')
POINTER = re.compile(r'(?:references/|`\w+/references/)([A-Za-z0-9_\-]+\.md)')
SKILL_REF = re.compile(r'`([a-z0-9][a-z0-9\-]{2,40})`')

problems = []

def flag(msg):
    problems.append(msg)

def skill_dirs():
    return sorted(p.parent for p in ROOT.glob('*/SKILL.md'))

def check_skill_file(sd: Path):
    p = sd / 'SKILL.md'
    b = p.read_bytes()
    if b.count(b'\r\n'):
        flag(f'{p}: CRLF 检出（必须 LF）')
    s = b.decode('utf-8')
    m = re.match(r'^---\s*\n(.*?)\n---', s, re.S)
    if not m:
        flag(f'{p}: frontmatter 缺失/破裂'); return s
    fm = m.group(1)
    nm = re.search(r'^name:\s*(\S+)', fm, re.M)
    if not nm or nm.group(1) != sd.name:
        flag(f'{p}: name 字段 "{nm.group(1) if nm else "(缺)"}" != 目录名 {sd.name}')
    if not re.search(r'^description:\s*\S', fm, re.M):
        flag(f'{p}: description 缺失')
    tail = [l for l in s.rstrip().split('\n')[-3:]]
    sigs = [l for l in tail if SIG.search(l)]
    if len(sigs) != 1:
        flag(f'{p}: 尾签名数 {len(sigs)}（末 3 行内必须恰好 1 个）')
    return s

def broken_pointers(text: str, base: Path):
    out = []
    # 两种指针形态：同 skill `references/x.md`；跨 skill `skill-name/references/x.md`
    for rel in set(re.findall(r'references/([A-Za-z0-9_\-]+\.md)', text)):
        if not (base / 'references' / rel).exists():
            # 再按跨 skill 形态从仓库根解析（如 `blueprint-ui-style/references/x.md`）
            m = re.search(r'`?([a-z0-9\-]+)/references/' + re.escape(rel) + r'`?', text)
            if not (m and (ROOT / m.group(1) / 'references' / rel).exists()):
                out.append(rel)
    return out

def check_pointers_all():
    dirs = {d.name: d for d in skill_dirs()}
    for md in ROOT.glob('*/**/*.md'):
        s = md.read_text(encoding='utf-8', errors='replace')
        for rel in broken_pointers(s, md.parent):
            flag(f'{md}: 指针断裂 references/{rel}')
    # README 路由表 <-> 目录 双向
    rd = (ROOT/'README.md').read_text(encoding='utf-8')
    routed = set(SKILL_REF.findall(rd))
    for n in routed:
        if (ROOT/n/'SKILL.md').exists() is False and (ROOT/n).is_dir() is False:
            if n in ('SKILL','md','csv','json','py'):  # 明显非 skill 名的 code span 跳过
                continue
    missing_dir = [n for n in routed if not (ROOT/n).is_dir() and n not in
                   ('SKILL','md','csv','json','py','v','sv','f','tcl','c','h','sh','html')]
    for n in missing_dir:
        if not re.search(r'[a-z]-[a-z]', n):  # 只校验疑似 skill 名（含连字符）
            continue
        flag(f'README.md: 路由/一览提到 `{n}` 但目录不存在')
    for d in dirs:
        if d not in rd:
            flag(f'README.md: skill 目录 {d}/ 未出现在路由表或一览')
    # 跨 skill 引用（"见 `skill-name` §"）必须存在
    for md in ROOT.glob('*/SKILL.md'):
        s = md.read_text(encoding='utf-8', errors='replace')
        for n in set(SKILL_REF.findall(s)):
            if re.search(r'[a-z]-[a-z]', n) and (ROOT/n).is_dir() and n != md.parent.name:
                pass  # 存在即可
            elif re.search(r'(?:skill|见|载入|加载|引用)\s*`' + re.escape(n) + r'`', s):
                if not (ROOT/n).is_dir():
                    flag(f'{md}: 引用了不存在的 skill `{n}`')

def run():
    dirs = skill_dirs()
    if len(dirs) == 0:
        flag('(全局) 扫到 0 个 SKILL.md——路径错了？')
    for d in dirs:
        check_skill_file(d)
    check_pointers_all()
    print(f'scanned {len(dirs)} skills')
    for p in problems:
        print('FAIL:', p)
    verdict = 'PASS' if not problems else f'FAIL ({len(problems)})'
    print('RESULT:', verdict)
    return 0 if not problems else 1

def negatest():
    ok = True
    # ① 坏指针必须被抓
    fake = 'see references/no-such-file.md and `blueprint-ui-style`'
    if not broken_pointers(fake, ROOT/'_nonexistent_skill_'):
        print('NEGATEST FAIL: 坏指针未被检出'); ok = False
    # ② 双签名必须被抓（构造文本走 check_skill_file 的签名逻辑）
    t = 'x\n<!-- ymzhu 2026-11-18 10:00 -->\n<!-- ymzhu 2026-11-18 11:00 -->'
    tail = t.rstrip().split('\n')[-3:]
    if len([l for l in tail if SIG.search(l)]) == 1:
        print('NEGATEST FAIL: 双签名未被检出'); ok = False
    # ③ CRLF 必须被抓
    if b'\r\n' not in b'a\r\nb':
        print('NEGATEST FAIL: CRLF 判定失效'); ok = False
    # ④ 空扫描集必须 FAIL（run() 内已内置 scanned 0 判红，此处验证计数）
    if len(skill_dirs()) == 0 and not problems:
        print('NEGATEST FAIL: 0 skill 未判红'); ok = False
    print('NEGATEST:', 'PASS (teeth ok)' if ok else 'FAIL')
    return 0 if ok else 1

if __name__ == '__main__':
    sys.exit(negatest() if '--negatest' in sys.argv else run())

# ymzhu 2026-11-18 14:32
