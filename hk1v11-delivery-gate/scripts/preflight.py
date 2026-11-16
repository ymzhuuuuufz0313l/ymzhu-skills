#!/usr/bin/env python3
"""HK1V11 交付前闸门（preflight）。

用法（在项目根或任意位置运行）：

    python script/gates/preflight.py --level L2
    python script/gates/preflight.py --level L2 --files a.v b.sv
    python script/gates/preflight.py --level L3 --require-pushed

关卡依 --level 决定（L0 < L1 < L2 < L3）：

    L0  文档/注释类      ：文件尾签名 + CHANGES 覆盖
    L1  非功能性 RTL     ：L0 + iverilog 语法 + verilator lint
    L2  功能性 RTL       ：L1 + 对抗评审报告（critical==0 且 high<=1，且新于最后一次 RTL 改动）
    L3  重定时/时序敏感  ：L2 + 最小对拍 TB 证据 + 信号追踪报告

退出码 0 = 全绿可交付；1 = 有红项。报告写入 script/gates/reports/preflight_<ts>.json。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # 老终端不支持 reconfigure
    pass

TOOL_DIRS = [Path("D:/msys64/ucrt64/bin"), Path("C:/msys64/ucrt64/bin"),
             Path("D:/msys64/mingw64/bin"), Path("C:/msys64/mingw64/bin")]


def find_tool(name: str) -> str | None:
    """PATH 找不到时回落到已知 MSYS2 安装目录。"""
    hit = shutil.which(name)
    if hit:
        return hit
    for d in TOOL_DIRS:
        for suffix in ("", ".exe"):
            cand = d / (name + suffix)
            if cand.is_file():
                return str(cand)
    return None


def tool_env() -> dict[str, str]:
    """给 iverilog/verilator 一个可写的临时目录，并保证其 bin 在 PATH 前部。"""
    env = os.environ.copy()
    tmp = tempfile.mkdtemp(prefix="hkpre_")
    env["TMP"] = env["TEMP"] = env["TMPDIR"] = tmp
    extra = [str(d) for d in TOOL_DIRS if d.is_dir()]
    env["PATH"] = os.pathsep.join(extra + [env.get("PATH", "")])
    return env


LEVELS = {"L0": 0, "L1": 1, "L2": 2, "L3": 3}

SIGNATURE_RE = re.compile(r"ymzhu\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})")
SIGNATURE_BY_EXT = {
    ".v": "//", ".sv": "//", ".svh": "//", ".f": "//",
    ".tcl": "#", ".pl": "#", ".py": "#", ".sh": "#",
    ".c": "/*", ".h": "/*",
    ".md": "<!--", ".html": "<!--",
}
RTL_EXT = {".v", ".sv", ".svh"}
CHANGES_CANDIDATES = ["修改记录/CHANGES.md", "修改记录/changes.md"]


def run(cmd: list[str], cwd: Path, timeout: int = 300,
        env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout, env=env)


def repo_root(bootstrap: Path) -> Path:
    p = run(["git", "rev-parse", "--show-toplevel"], bootstrap)
    if p.returncode != 0:
        return bootstrap
    return Path(p.stdout.strip())


def git_changed(root: Path) -> tuple[list[str], list[str]]:
    tracked: list[str] = []
    p = run(["git", "diff", "--name-only", "HEAD"], root)
    if p.returncode == 0:
        tracked = [x for x in p.stdout.splitlines() if x.strip()]
    p = run(["git", "ls-files", "--others", "--exclude-standard"], root)
    untracked = [x for x in p.stdout.splitlines() if x.strip()] if p.returncode == 0 else []
    return tracked, untracked


def head_pushed(root: Path) -> tuple[bool | None, str]:
    p = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], root)
    if p.returncode != 0:
        return None, "无上游分支（尚未 push / 没设 upstream）"
    upstream = p.stdout.strip()
    p = run(["git", "rev-list", "--count", f"{upstream}..HEAD"], root)
    if p.returncode != 0:
        return None, f"无法比较 {upstream}"
    n = int(p.stdout.strip() or 0)
    return (n == 0), f"{n} 个提交未推送（{upstream}）" if n else f"已同步 {upstream}"


def incdirs(root: Path) -> list[str]:
    hdl = root / "HDL"
    dirs = [hdl / "HK1V11_digital_top"]
    for d in (hdl).rglob("*"):
        if d.is_dir():
            dirs.append(d)
    return [f"+incdir+{d.relative_to(root).as_posix()}" for d in dirs]


def iverilog_check(root: Path, files: list[str]) -> list[dict]:
    exe = find_tool("iverilog")
    if not exe:
        return [{"tool": "iverilog", "status": "skipped", "detail": "iverilog 不在 PATH"}]
    define = root / "HDL" / "HK1V11_digital_top" / "HDL_define.v"
    out = []
    for f in files:
        cmd = [exe, "-t", "null", "-g2012", "-o", os.devnull, str(define), f]
        try:
            p = run(cmd, root, timeout=120, env=tool_env())
        except subprocess.TimeoutExpired:
            out.append({"tool": "iverilog", "file": f, "status": "fail", "detail": "超时"})
            continue
        if p.returncode != 0:
            tail = (p.stderr or p.stdout).strip().splitlines()
            out.append({"tool": "iverilog", "file": f, "status": "fail",
                        "detail": " | ".join(tail[:3])})
        else:
            warn = [l for l in (p.stderr or "").splitlines() if "warning" in l.lower()]
            out.append({"tool": "iverilog", "file": f,
                        "status": "pass" if not warn else "warn",
                        "detail": f"{len(warn)} warning(s)" if warn else "clean"})
    return out


def verilator_env(exe: str) -> dict[str, str]:
    """verilator_bin 需要 VERILATOR_ROOT（包装脚本平时替我们设好）。"""
    env = tool_env()
    if not env.get("VERILATOR_ROOT"):
        root_dir = Path(exe).resolve().parent.parent / "share" / "verilator"
        if root_dir.is_dir():
            env["VERILATOR_ROOT"] = str(root_dir)
    return env


def verilator_check(root: Path, files: list[str], max_warn: int) -> list[dict]:
    exe = find_tool("verilator_bin") or find_tool("verilator.exe")
    if not exe:
        return [{"tool": "verilator", "status": "skipped",
                 "detail": "verilator 未安装（pacman -S mingw-w64-ucrt-x86_64-verilator）"}]
    venv = verilator_env(exe)
    define = root / "HDL" / "HK1V11_digital_top" / "HDL_define.v"
    base = [exe, "--lint-only", "-Wall", "-Wno-fatal", "-Wno-UNUSEDSIGNAL",
            "-Wno-UNDRIVEN", "-Wno-DECLFILENAME", "-Wno-SYNCASYNCNET",
            "-Wno-VARHIDDEN", "-Wno-WIDTH"] + incdirs(root)
    out = []
    for f in files:
        try:
            p = run(base + [str(define), f], root, timeout=240, env=venv)
        except subprocess.TimeoutExpired:
            out.append({"tool": "verilator", "file": f, "status": "fail", "detail": "超时"})
            continue
        text = (p.stderr or "") + (p.stdout or "")
        errors = [l for l in text.splitlines() if l.startswith("%Error")]
        warns = [l for l in text.splitlines() if l.startswith("%Warning")]
        if errors:
            status = "fail"
        elif len(warns) > max_warn:
            status = "fail"
        elif warns:
            status = "warn"
        else:
            status = "pass"
        out.append({"tool": "verilator", "file": f, "status": status,
                    "errors": len(errors), "warnings": len(warns),
                    "detail": (errors[0] if errors else
                               (warns[0] if warns else "clean"))[:300]})
    return out


def signature_check(root: Path, files: list[str]) -> list[dict]:
    out = []
    for f in files:
        path = root / f
        ext = path.suffix.lower()
        if ext not in SIGNATURE_BY_EXT:
            continue
        if not path.is_file():
            out.append({"tool": "signature", "file": f, "status": "skipped",
                        "detail": "文件不存在（删除类改动）"})
            continue
        tail = path.read_text(encoding="utf-8", errors="replace").splitlines()[-6:]
        hits = [m for m in (SIGNATURE_RE.search(l) for l in tail) if m]
        if not hits:
            out.append({"tool": "signature", "file": f, "status": "fail",
                        "detail": "文件尾缺少 `ymzhu YYYY-MM-DD HH:MM` 签名"})
        else:
            last = hits[-1]
            out.append({"tool": "signature", "file": f, "status": "pass",
                        "detail": f"签名 {last.group(1)} {last.group(2)}"})
    return out


def changes_coverage(root: Path, files: list[str]) -> dict:
    doc = None
    for c in CHANGES_CANDIDATES:
        if (root / c).is_file():
            doc = root / c
            break
    if doc is None:
        return {"tool": "changes", "status": "fail", "detail": "找不到 修改记录/CHANGES.md"}
    text = doc.read_text(encoding="utf-8", errors="replace")
    missing = [f for f in files if Path(f).name not in text]
    if missing:
        return {"tool": "changes", "status": "fail",
                "detail": f"CHANGES.md 未提及 {len(missing)} 个改动文件",
                "missing": missing[:12]}
    return {"tool": "changes", "status": "pass", "detail": f"{doc.name} 覆盖全部 {len(files)} 个文件"}


def newest_review(root: Path, kind: str, newer_than: float | None) -> dict:
    rdir = root / "script" / "gates" / "reports"
    if not rdir.is_dir():
        return {"tool": kind, "status": "fail", "detail": "script/gates/reports/ 不存在"}
    cands = sorted(rdir.glob(f"*{kind}*.json"), key=lambda p: p.stat().st_mtime)
    if not cands:
        return {"tool": kind, "status": "fail", "detail": f"缺少 {kind} 报告"}
    latest = cands[-1]
    if newer_than is not None and latest.stat().st_mtime < newer_than:
        return {"tool": kind, "status": "fail",
                "detail": f"{latest.name} 早于最后一次 RTL 改动"}
    try:
        data = json.loads(latest.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - 损坏的报告等同于缺失
        return {"tool": kind, "status": "fail", "detail": f"{latest.name} 不可解析: {exc}"}
    if kind == "review":
        crit = int(data.get("critical", 0))
        high = int(data.get("high", 0))
        ok = crit == 0 and high <= 1
        return {"tool": kind, "status": "pass" if ok else "fail",
                "detail": f"{latest.name}: critical={crit} high={high}（门禁 critical==0, high<=1）"}
    if kind == "trace":
        ok = data.get("status") == "pass"
        return {"tool": kind, "status": "pass" if ok else "fail",
                "detail": f"{latest.name}: status={data.get('status')}"}
    return {"tool": kind, "status": "pass", "detail": latest.name}


def tb_evidence(root: Path, newer_than: float | None) -> dict:
    rdir = root / "script" / "gates" / "reports"
    cands = sorted(rdir.glob("*tb*.json"), key=lambda p: p.stat().st_mtime) if rdir.is_dir() else []
    if not cands:
        return {"tool": "tb", "status": "fail",
                "detail": "L3 需要最小对拍 TB 证据（script/gates/reports/*tb*.json）"}
    latest = cands[-1]
    if newer_than is not None and latest.stat().st_mtime < newer_than:
        return {"tool": "tb", "status": "fail", "detail": f"{latest.name} 早于最后一次 RTL 改动"}
    return {"tool": "tb", "status": "pass", "detail": latest.name}


def main() -> int:
    ap = argparse.ArgumentParser(description="HK1V11 交付前闸门")
    ap.add_argument("--level", required=True, choices=sorted(LEVELS))
    ap.add_argument("--files", nargs="*", help="显式指定改动文件（默认取 git 改动 + 未跟踪）")
    ap.add_argument("--require-pushed", action="store_true", help="要求 HEAD 已推送")
    ap.add_argument("--allow-dirty-changes", action="store_true",
                    help="CHANGES.md 未覆盖时只告警不判红")
    ap.add_argument("--max-warn", type=int, default=20, help="单文件 verilator 告警上限")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    root = repo_root(Path(__file__).resolve().parent)
    level_rank = LEVELS[args.level]
    tracked, untracked = git_changed(root)
    files = [f.replace("\\", "/") for f in (args.files or (tracked + untracked))]
    rtl_files = [f for f in files if Path(f).suffix.lower() in RTL_EXT]
    newest_rtl = max((root / f).stat().st_mtime for f in rtl_files
                     if (root / f).is_file()) if rtl_files else None

    checks: list[dict] = []

    pushed_ok, pushed_detail = head_pushed(root)
    if args.require_pushed and pushed_ok is not True:
        checks.append({"tool": "git-push", "status": "fail", "detail": pushed_detail})
    else:
        checks.append({"tool": "git-push",
                       "status": "pass" if pushed_ok else "warn",
                       "detail": pushed_detail})

    checks.append({"tool": "scope", "status": "pass",
                   "detail": f"{len(files)} 个改动文件（{len(rtl_files)} 个 RTL）",
                   "files": files})

    checks.extend(signature_check(root, files))
    cov = changes_coverage(root, files)
    if cov["status"] == "fail" and args.allow_dirty_changes:
        cov["status"] = "warn"
    checks.append(cov)

    if level_rank >= LEVELS["L1"] and rtl_files:
        checks.extend(iverilog_check(root, rtl_files))
        checks.extend(verilator_check(root, rtl_files, args.max_warn))

    if level_rank >= LEVELS["L2"]:
        checks.append(newest_review(root, "review", newest_rtl))
    if level_rank >= LEVELS["L3"]:
        checks.append(newest_review(root, "trace", newest_rtl))
        checks.append(tb_evidence(root, newest_rtl))

    fails = [c for c in checks if c["status"] == "fail"]
    warns = [c for c in checks if c["status"] == "warn"]
    verdict = "pass" if not fails else "fail"

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rdir = root / "script" / "gates" / "reports"
    rdir.mkdir(parents=True, exist_ok=True)
    report = {
        "kind": "preflight",
        "level": args.level,
        "verdict": verdict,
        "generated_at": ts,
        "git": {"head": run(["git", "rev-parse", "--short", "HEAD"], root).stdout.strip(),
                "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root).stdout.strip()},
        "files": files,
        "checks": checks,
        "fails": len(fails),
        "warns": len(warns),
    }
    out_path = rdir / f"preflight_{ts}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.json_only:
        icon = {"pass": "OK ", "warn": "WARN", "fail": "FAIL", "skipped": "SKIP"}
        print(f"== preflight {args.level} == root={root}")
        for c in checks:
            name = c.get("file") or c["tool"]
            print(f"[{icon.get(c['status'], c['status'])}] {name}: {c.get('detail', '')}")
        print(f"\nverdict={verdict.upper()} fails={len(fails)} warns={len(warns)}")
        print(f"report: {out_path.relative_to(root).as_posix()}")

    return 0 if verdict == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())

# ymzhu 2026-11-16 15:20
