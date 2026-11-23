#!/usr/bin/env python3
"""服务器回传包 overlay 校验（三类包：SYNTHESIS / HDL / DV_TCON_C）。

两段式：

    # 覆盖前：确认干净、记基线
    python script/gates/overlay_check.py pre --package HDL

    # 覆盖后：比对清单、跑代际探针、给提交命令并自检
    python script/gates/overlay_check.py post --package HDL --paths HDL/

`post` 默认只检查并打印建议命令；加 --commit 才真正 `git add -A --` + commit + 自检。
有用户批准的新增（pack_diff 的 pack_only 桶）时：清单内的新增（含尚未 git add 的未跟踪新文件）放行，
清单外的新增与任何未跟踪残留仍 FAIL
    python script/gates/overlay_check.py post --package SYNTHESIS --paths SYNTHESIS/ --approved-adds script/approved_adds.txt

探针表机器可读副本：script/gates/probes.json
    {"probes": [{"version": "0929", "file": "HDL/.../LONG_ENCODING_ALIGN.v",
                 "pattern": "I_INDATA_D4", "expect": "==0"}]}
expect 支持 ==0 / >0 / ==N。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASELINE = Path("script/gates/overlay_baseline.json")
PROBES = Path("script/gates/probes.json")
PACKAGE_SCOPE = {
    "SYNTHESIS": ["SYNTHESIS/"],
    "HDL": ["HDL/"],
    "DV_TCON_C": ["DV_TCON_C/"],
}


def run(cmd, cwd, timeout=300):
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def repo_root() -> Path:
    p = run(["git", "rev-parse", "--show-toplevel"], Path.cwd())
    if p.returncode != 0:
        sys.exit("不是 git 仓库，无法校验")
    return Path(p.stdout.strip())


def is_clean(root: Path, scope: list[str] | None = None) -> tuple[bool, str]:
    """基线可信只要求「本包范围内」没有未提交改动：基线取自 HEAD 与已跟踪清单，
    范围外的脏文件既不进基线，也不会被 `git add -A -- <scope>` 卷进 overlay 提交，
    所以只告警不拦（2026-11-23 改；此前要求全仓干净，本仓 script/、docs/ 长期有与本包
    无关的未提交改动，pre 实际永远 FAIL）。不给 scope 时保持全仓口径。"""
    p = run(["git", "status", "--porcelain"] + (scope or []), root)
    dirty = [l for l in p.stdout.splitlines() if l.strip()]
    if dirty:
        return False, "工作区不干净：" + "; ".join(dirty[:8])
    if not scope:
        return True, "工作区干净"
    a = run(["git", "status", "--porcelain"], root)
    outside = len([l for l in a.stdout.splitlines() if l.strip()])
    if outside:
        print(f"[WARN] 本包范围外有 {outside} 项未提交改动（不进基线、不进本次 overlay 提交）")
    return True, "本包范围干净：" + " ".join(scope)


def cmd_pre(root: Path, package: str) -> int:
    ok, detail = is_clean(root, PACKAGE_SCOPE.get(package))
    print(f"[{'OK ' if ok else 'FAIL'}] {detail}")
    if not ok:
        print("\n覆盖前必须先提交或 stash，否则基线不可信。")
        return 1
    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    baseline = {
        "package": package,
        "commit": head,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scope": PACKAGE_SCOPE.get(package, [package.rstrip('/') + "/"]),
        "tree": run(["git", "ls-files"] + PACKAGE_SCOPE.get(package, []), root).stdout.splitlines(),
    }
    p = root / BASELINE
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK ] 基线已记录 {head[:8]}（{package}，{len(baseline['tree'])} 个文件）")
    print(f"      {BASELINE.as_posix()}")
    print("\n现在可以去服务器取包并覆盖。完成后运行：")
    print(f"  python script/gates/overlay_check.py post --package {package} --paths <覆盖路径>")
    return 0


def load_probes(root: Path) -> list[dict]:
    p = root / PROBES
    if not p.is_file():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("probes", [])
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] probes.json 不可解析：{exc}")
        return []


def eval_expect(actual: int, expect: str) -> bool:
    if m := re.fullmatch(r"==\s*(\d+)", expect):
        return actual == int(m.group(1))
    if expect.strip() == ">0":
        return actual > 0
    if m := re.fullmatch(r">=\s*(\d+)", expect):
        return actual >= int(m.group(1))
    return False


def run_probes(root: Path, package: str) -> list[tuple[str, bool, str]]:
    probes = [p for p in load_probes(root) if p.get("package", package) == package]
    out = []
    for pr in probes:
        path = root / pr["file"]
        if not path.is_file():
            out.append((pr["file"], False, "文件不存在"))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        n = len(re.findall(pr["pattern"], text))
        ok = eval_expect(n, pr.get("expect", ">0"))
        out.append((f"{pr['file']} :: /{pr['pattern']}/ {pr.get('expect')}", ok, f"实际 {n}"))
    return out


def cmd_post(root: Path, package: str, paths: list[str], do_commit: bool, message: str | None,
             approved_adds: list[str] | None = None) -> int:
    bl_path = root / BASELINE
    if not bl_path.is_file():
        print("[FAIL] 没有基线，先跑 pre")
        return 1
    baseline = json.loads(bl_path.read_text(encoding="utf-8"))
    if baseline.get("package") != package:
        print(f"[WARN] 基线记录的是 {baseline.get('package')}，本次是 {package}")

    base_commit = baseline["commit"]
    p = run(["git", "diff", "--name-status", base_commit, "--"] + (paths or baseline["scope"]), root)
    changes = [l for l in p.stdout.splitlines() if l.strip()]
    added = [l for l in changes if l.startswith("A")]
    deleted = [l for l in changes if l.startswith("D")]
    renamed = [l for l in changes if l.startswith("R")]
    modified = [l for l in changes if l.startswith("M")]

    # 新增只在「用户明确批准的 pack_only 清单」内放行（server-pack-overlay §0B）；清单外的新增与 D/R 仍 FAIL
    approved = set(approved_adds or [])

    # 已跟踪侧的新增（git add 之后才会出现在 name-status 的 A 里）
    added_bad = [l for l in added if l.split("\t", 1)[-1].strip('"') not in approved]
    # 刚落地、尚未 git add 的新文件不在 A 里，只出现在未跟踪清单中：同样按批准清单判定。
    # 否则 post 会报「新增 0」而放行任何新文件（2026-11-23 PACK_TAR_1123V0 覆盖后实测到的盲区）。
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"] + (paths or []), root)
    untracked_all = [l for l in untracked.stdout.splitlines() if l.strip()]
    new_ok = [l for l in untracked_all if l.strip('"') in approved]
    strays = [l for l in untracked_all if l.strip('"') not in approved]

    n_new = len(added) + len(untracked_all)
    n_new_bad = len(added_bad) + len(strays)
    print(f"== overlay post {package} == 基线 {base_commit[:8]} → 工作区")
    print(f"   修改 {len(modified)} | 新增 {n_new}（已批准 {n_new - n_new_bad} / 未批准 {n_new_bad}）"
          f" | 删除 {len(deleted)} | 改名 {len(renamed)}")

    bad = bool(added_bad or strays or deleted or renamed)
    if bad:
        print("\n[FAIL] 合并式覆盖规则要求「只改不增删改名」，新增须在 --approved-adds 清单内。发现：")
        for l in (added_bad + [f"??\t{u}" for u in strays] + deleted + renamed)[:20]:
            print("       " + l)
    else:
        print("[OK ] 只含修改与已批准新增，符合同名覆盖规则")

    probe_rows = run_probes(root, package)
    probe_bad = [r for r in probe_rows if not r[1]]
    if probe_rows:
        print("\n== 版本代际探针 ==")
        for name, ok, detail in probe_rows:
            print(f"[{'OK ' if ok else 'FAIL'}] {name} → {detail}")
    else:
        print("\n[WARN] probes.json 中无本包探针，代际确认缺失")

    commit_cmd = "git add -A -- " + " ".join(paths or baseline["scope"])
    print(f"\n建议提交命令：\n  {commit_cmd}\n  git commit -m \"{message or package + ' overlay: ' + datetime.now().strftime('%m%d')}\"")

    if do_commit:
        add = run(["git", "add", "-A", "--"] + (paths or baseline["scope"]), root)
        if add.returncode != 0:
            print("[FAIL] git add 失败：" + (add.stderr or "")[:300])
            return 1
        staged = run(["git", "diff", "--cached", "--name-only"], root).stdout.splitlines()
        if not staged:
            print("[FAIL] 暂存区为空，add 未生效")
            return 1
        msg = message or f"{package} overlay: {datetime.now().strftime('%m%d')}"
        c = run(["git", "commit", "-m", msg], root)
        if c.returncode != 0:
            print("[FAIL] commit 失败：" + (c.stderr or c.stdout)[:400])
            return 1
        # 只数文件名：`git log` 默认格式带 Author/Date/标题与 "N files changed" 汇总行，旧写法
        # splitlines()[1:] 把这 4 行也算成文件，自检恒为「文件数+4」（2026-11-23 实测 21 != 18）
        stat = run(["git", "show", "--name-only", "--format=", "HEAD"], root).stdout
        listed = [l for l in stat.splitlines() if l.strip()]
        print(f"[OK ] 已提交，log --stat 自检：{len(listed)} 个文件")
        if len(listed) != len(staged):
            print(f"[FAIL] 提交文件数 {len(listed)} != 暂存 {len(staged)}")
            return 1
        behind = run(["git", "status", "-sb"], root).stdout.splitlines()[:1]
        print(f"      {behind[0] if behind else ''}（记得 push）")

    return 0 if (not bad and not probe_bad) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="服务器回传 overlay 校验")
    ap.add_argument("stage", choices=["pre", "post"])
    ap.add_argument("--package", required=True, choices=sorted(PACKAGE_SCOPE))
    ap.add_argument("--paths", nargs="*", default=[], help="本次覆盖涉及的路径")
    ap.add_argument("--commit", action="store_true", help="post 阶段真正执行 add+commit")
    ap.add_argument("--message", help="提交信息")
    ap.add_argument("--approved-adds",
                    help="用户批准的新增清单文件（pack_diff 的 pack_only 桶），每行一个 <AREA>/<rel>；"
                         "清单外的新增仍判 FAIL")
    args = ap.parse_args()
    root = repo_root()
    if args.stage == "pre":
        return cmd_pre(root, args.package)
    adds: list[str] = []
    if args.approved_adds:
        adds = [l.strip() for l in Path(args.approved_adds).read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")]
    return cmd_post(root, args.package, args.paths, args.commit, args.message, adds)


if __name__ == "__main__":
    sys.exit(main())

# ymzhu 2026-11-23 16:12
