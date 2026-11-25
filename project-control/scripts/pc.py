#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""project-control：工程目录骨架 init + 根目录白名单自检 check（只依赖标准库）。

在工程根目录执行：
  python pc.py init --roundtrip HDL,SYNTHESIS [--exceptions X,Y] [--tools script,修改记录,docs,plan]
                        [--projects a,b] [--site 路径或URL]
  python pc.py check [--cfg script/gates/repo_layout.json]

init 只建缺失的目录和 README、写配置、把本脚本同步一份到 script/gates/pc.py；
不移动、不删除任何既有文件；做完自动跑一遍 check。
配置文件 script/gates/repo_layout.json；白名单 = roundtrip + GITHUB/内部分享/外部分享 + tools
+ exceptions + root_files + hidden。
check 的判据：根目录只含白名单；GITHUB 根只许 README.md 和登记的文件夹；内部分享与外部分享的
日期文件夹（YYYYMMDD）下只许 NN.中文说明/ 且含 readme.md；外部分享里只有 md；项目文件夹含 README.md。
"""
import argparse
import collections
import datetime
import io
import json
import os
import re
import shutil
import subprocess
import sys

CFG_REL = os.path.join("script", "gates", "repo_layout.json")
SHARE = ["GITHUB", "内部分享", "外部分享"]
LIST_KEYS = ("roundtrip", "github_subfolders", "tools", "exceptions", "root_files", "hidden", "internal_projects")
DEFAULT = {
    "roundtrip": [],
    "github_subfolders": ["PPT", "IMAGE", "ISSUE"],
    "tools": ["script", "修改记录", "docs", "plan"],
    "exceptions": [],
    "root_files": ["AGENTS.md", "README.md", "REVIEW.md"],
    "hidden": [".git", ".gitignore", ".gitattributes"],
    "internal_projects": [],
    "site_repo": "",
}
DATE_RE = re.compile(r"^\d{8}$")
ITEM_RE = re.compile(r"^(\d{2})\.(.+)$")
PROJ_RE = re.compile(r"^[a-z][a-z0-9_]*$")
CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")


def md_sign():
    return "\n<!-- ymzhu %s -->\n" % now()


def rd(p):
    return io.open(p, "rb").read().decode("utf-8")


def wr(p, s):
    io.open(p, "wb").write(s.encode("utf-8"))


SIGN_RE = re.compile(r"<!-- ymzhu \d{4}-\d\d-\d\d \d\d:\d\d -->\s*$")


def split(s):
    return [x.strip() for x in s.split(",") if x.strip()]


def write_if_missing(path, text):
    """文件不存在才写（目录一并建）；返回是否新建。"""
    if os.path.exists(path):
        return False
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return True


def load_cfg(root, cfg_path=None):
    p = cfg_path or os.path.join(root, CFG_REL)
    if not os.path.isfile(p):
        return None
    with io.open(p, encoding="utf-8") as f:
        raw = json.load(f)
    cfg = dict(DEFAULT)
    cfg.update(raw)
    for k in LIST_KEYS:
        cfg[k] = list(cfg.get(k) or [])
    return cfg


def whitelist(cfg):
    return set(cfg["roundtrip"]) | set(SHARE) | set(cfg["tools"]) | set(cfg["exceptions"]) | set(cfg["root_files"]) | set(cfg["hidden"])


def readme_for(kind, name, cfg):
    site = cfg.get("site_repo") or "（待填：init 时用 --site 指定）"
    if kind == "roundtrip":
        return "# %s\n\n回传目录：存放服务器回传的 %s 内容。进出走 server-pack-overlay 的纪律（合并式覆盖、diff-first、overlay 校验）。\n%s" % (name, name, md_sign())
    if kind == "github":
        return ("# GITHUB\n\n对外发布物的**暂存区**。根上只放本 README 和文件夹（%s），每个文件夹用自己的 README.md 说明用途。\n\n"
                "网站本体在站点仓库：%s。发布走 team-share skill，这里不建站点副本。\n%s"
                % ("、".join(cfg["github_subfolders"]), site, md_sign()))
    if kind == "github_sub":
        desc = {"PPT": "幻灯片与配图（含表格图、对比图的生成器与版本图）",
                "IMAGE": "对外分享的图片",
                "ISSUE": "issue 汇总、议题材料"}.get(name, "对外分享内容")
        return "# %s\n\n用途：%s。\n%s" % (name, desc, md_sign())
    if kind == "internal":
        return ("# 内部分享\n\nagent 之间、subagent 之间的交接内容。三层边界：\n\n"
                "| 层 | 只允许 |\n|---|---|\n"
                "| 顶层 | md 文件、日期文件夹 YYYYMMDD、项目文件夹 |\n"
                "| 日期文件夹 | NN.中文说明/ 目录（NN 两位补零），每个目录必须有 readme.md |\n"
                "| 项目文件夹 | 小写加下划线，必须有 README.md，内部不限类型 |\n\n"
                "readme.md 第一行写结论，然后是背景、方法、证据路径。规则全文见 project-control skill。\n%s" % md_sign())
    if kind == "external":
        return ("# 外部分享\n\n发给同事的 md。下面只有 YYYYMMDD/NN.中文说明/readme.md，内容全是 md；图片用外链或放 GITHUB/IMAGE。\n\n"
                "## 台账\n\n| 日期 | 主题 | 收件人 | 对应的内部分享链接 |\n|---|---|---|---|\n%s" % md_sign())
    if kind == "script":
        return ("# script\n\n工具写入区：人和 agent 都不往根上手工放报告。根上只允许四类——闸门代码；回传包机器产物（固定文件名模式）；"
                "还会再跑的一次性脚本；本 README 索引。新报告一律去 内部分享/YYYYMMDD/NN.中文说明/。\n\n"
                "## 索引\n\n（由 preflight 自动刷新：名称 / 类别 / 最后修改 / 是否入库）\n%s" % md_sign())
    if kind == "changes":
        return "# CHANGES\n\n统一变更记录。格式与签名规则见 workflow-maintainer skill。\n\n| 日期 | 目录/文件 | L 级 | 摘要 | 签名 |\n|---|---|---|---|---|\n%s" % md_sign()
    if kind == "docs":
        return "# docs\n\n只放规则类长期文档：agent 规则（agents/）、架构决定（adr/）、术语表（GLOSSARY.md）。分析类文档进 内部分享/；已对外发布的直接删。\n%s" % md_sign()
    if kind == "local_simulation":
        return "# local_simulation\n\n本机仿真工作区（local-simulation skill）。\n%s" % md_sign()
    return "# %s\n\n%s" % (name, md_sign())


def cmd_init(root, a):
    cfg = load_cfg(root) or dict(DEFAULT)
    if a.roundtrip:
        cfg["roundtrip"] = split(a.roundtrip)
    if a.exceptions is not None:
        cfg["exceptions"] = split(a.exceptions)
    if a.tools:
        cfg["tools"] = split(a.tools)
    if a.projects is not None:
        cfg["internal_projects"] = split(a.projects)
    if a.site:
        cfg["site_repo"] = a.site
    cfg["project"] = cfg.get("project") or os.path.basename(os.path.abspath(root))
    for k in LIST_KEYS:
        cfg[k] = list(cfg.get(k) or [])
    made = []

    def mk(rel, kind=None, name=None):
        p = os.path.join(root, rel)
        if kind is None:
            if not os.path.isdir(p):
                os.makedirs(p)
                made.append(rel + "/")
            return
        if write_if_missing(p, readme_for(kind, name or os.path.basename(os.path.dirname(rel)) or rel, cfg)):
            made.append(rel.replace("\\", "/"))

    for r in cfg["roundtrip"]:
        if not os.path.isdir(os.path.join(root, r)):      # 已有的回传目录归 overlay 管，不往里塞 README
            mk(os.path.join(r, "README.md"), "roundtrip", r)
    mk(os.path.join("GITHUB", "README.md"), "github")
    for s in cfg["github_subfolders"]:
        mk(os.path.join("GITHUB", s, "README.md"), "github_sub", s)
    mk(os.path.join("内部分享", "README.md"), "internal")
    mk(os.path.join("外部分享", "README.md"), "external")
    for t in cfg["tools"]:
        if t == "修改记录":
            mk(os.path.join(t, "CHANGES.md"), "changes")
        elif t == "local_simulation":
            mk(os.path.join(t, "README.md"), "local_simulation")
        elif t == "plan":
            pass                                        # 只登记进白名单，不预建：dated-plan-mode 用到时自建
        else:
            mk(os.path.join(t, "README.md"), t, t)
    cfg_p = os.path.join(root, CFG_REL)
    os.makedirs(os.path.dirname(cfg_p), exist_ok=True)
    with io.open(cfg_p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write("\n")
    made.append(CFG_REL.replace("\\", "/"))
    dst = os.path.join(root, "script", "gates", "pc.py")
    src = os.path.abspath(__file__)
    if os.path.normcase(os.path.abspath(dst)) != os.path.normcase(src):
        same = os.path.exists(dst) and io.open(dst, "rb").read() == io.open(src, "rb").read()
        if not same:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            made.append(os.path.join("script", "gates", "pc.py").replace("\\", "/"))
    print("project-control init：%s" % root)
    print("  新建 %d 项：%s" % (len(made), "、".join(made)))
    print("  既有文件一律未动；配置已写入 %s" % CFG_REL)
    cmd_index(root, cfg)
    return cmd_check(root, cfg)


MACHINE_PREFIX = ("PACK_TAR_", "approved_", "overlay_", "OVERLAY_LOG_", "README_中间版本说明_", "pack_diff_")
IDX_A, IDX_B = "<!-- pc:index-start -->", "<!-- pc:index-end -->"


def classify(name, isdir, tracked):
    if name == "gates":
        return "闸门代码"
    if name.startswith(MACHINE_PREFIX):
        return "回传包产物"
    if name == "README.md":
        return "本索引"
    if isdir:
        return "目录（已入库）" if tracked else "目录（未入库）"
    e = os.path.splitext(name)[1].lower()
    if e in (".py", ".sh", ".tcl", ".pl", ".bat", ".ys"):
        return "脚本"
    if e in (".md", ".pdf", ".xlsx", ".txt", ".json"):
        return "报告/文档"
    return "数据/其它"


def cmd_index(root, cfg=None):
    """刷新 script/README.md 的索引（名称 / 类别 / 最后修改 / 是否入库）；内容没变不写盘"""
    d = os.path.join(root, "script")
    rp = os.path.join(d, "README.md")
    if not os.path.isdir(d):
        return 0
    tracked = set()
    try:
        out = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "--", "script"], cwd=root,
                             capture_output=True).stdout.decode("utf-8", "replace")
        tracked = {l.split("/")[1] for l in out.split("\n") if l.count("/") >= 2}
    except (OSError, IndexError):
        pass
    rows, stat = [], collections.Counter()
    for e in sorted(os.listdir(d)):
        if e in (".", ".."):
            continue
        p = os.path.join(d, e)
        isdir = os.path.isdir(p)
        k = classify(e, isdir, e in tracked)
        stat[k] += 1
        rows.append("| %s | %s | %s | %s |" % (e, k, datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d"),
                                              "是" if e in tracked else "否"))
    block = (IDX_A + "\n由 project-control 自动生成（pc.py index），请勿手改；共 %d 个一级条目：%s\n\n"
             "| 名称 | 类别 | 最后修改 | 已入库 |\n|---|---|---|---|\n%s\n" % (len(rows), "、".join("%s %d" % kv for kv in stat.most_common()), "\n".join(rows))
             + IDX_B)
    cfg = cfg or load_cfg(root) or dict(DEFAULT)
    old = rd(rp) if os.path.exists(rp) else readme_for("script", "script", cfg)
    m = SIGN_RE.search(old)
    sign = m.group(0) if m else ("<!-- ymzhu %s -->\n" % now())
    body = SIGN_RE.sub("", old).rstrip()
    if IDX_A in body and IDX_B in body:
        new = re.sub(re.escape(IDX_A) + r".*?" + re.escape(IDX_B), lambda _: block, body, flags=re.S)
    else:
        new = body + "\n\n" + block
    new = new.rstrip() + "\n\n" + sign
    if not os.path.exists(rp) or new != rd(rp):
        wr(rp, new)
        print("script/README.md 索引已刷新：%d 个一级条目（%s）" % (len(rows), "、".join("%s %d" % kv for kv in stat.most_common())))
    else:
        print("script/README.md 索引无变化（%d 个一级条目）" % len(rows))
    return 0


def cmd_check(root, cfg=None, cfg_path=None):
    cfg = cfg or load_cfg(root, cfg_path)
    if cfg is None:
        print("project-control check：没有配置 %s，先在工程根目录跑 init。" % (cfg_path or CFG_REL))
        return 2
    errs, warns = [], []
    allow = whitelist(cfg)
    for e in sorted(os.listdir(root)):
        if e not in allow:
            errs.append("根目录白名单外：%s" % e)
    for must in cfg["roundtrip"] + SHARE:
        if not os.path.isdir(os.path.join(root, must)):
            errs.append("缺少目录：%s/" % must)
    for f in cfg["root_files"]:
        if not os.path.isfile(os.path.join(root, f)):
            warns.append("根文件不存在：%s" % f)
    g = os.path.join(root, "GITHUB")
    if os.path.isdir(g):
        for e in sorted(os.listdir(g)):
            if os.path.isdir(os.path.join(g, e)):
                if e not in cfg["github_subfolders"]:
                    errs.append("GITHUB 下未登记的文件夹：%s（登记的有 %s）" % (e, "、".join(cfg["github_subfolders"])))
            elif e.lower() != "readme.md":
                errs.append("GITHUB 根上只许 README.md，发现文件：%s" % e)

    def check_date(d, label, md_only):
        for e in sorted(os.listdir(d)):
            p = os.path.join(d, e)
            m = ITEM_RE.match(e) if os.path.isdir(p) else None
            if not m:
                errs.append("%s 下条目应为 NN.中文说明/ 目录：%s" % (label, e))
                continue
            if not CJK_RE.search(m.group(2)):
                errs.append("%s 条目名缺中文说明：%s" % (label, e))
            if not any(x.lower() == "readme.md" for x in os.listdir(p)):
                errs.append("%s 条目缺 readme.md：%s" % (label, e))
            if md_only:
                for dp, dn, fn in os.walk(p):
                    for f in fn:
                        if not f.lower().endswith(".md"):
                            errs.append("外部分享只许 md：%s" % os.path.relpath(os.path.join(dp, f), root).replace("\\", "/"))

    def check_share(name, md_only):
        d = os.path.join(root, name)
        if not os.path.isdir(d):
            return
        for e in sorted(os.listdir(d)):
            p = os.path.join(d, e)
            if os.path.isdir(p):
                if DATE_RE.match(e):
                    check_date(p, "%s/%s" % (name, e), md_only)
                elif md_only:
                    errs.append("%s 下只许 YYYYMMDD 日期文件夹：%s" % (name, e))
                elif os.path.isfile(os.path.join(p, "README.md")) and PROJ_RE.match(e):
                    continue
                elif e in cfg["internal_projects"]:
                    (warns if os.path.isfile(os.path.join(p, "README.md")) else errs).append(
                        "内部分享 项目文件夹%s：%s" % ("命名不是小写_下划线" if os.path.isfile(os.path.join(p, "README.md")) else "缺 README.md", e))
                else:
                    errs.append("内部分享 下不合规的条目：%s（日期文件夹应为 YYYYMMDD；项目文件夹应为小写_下划线且含 README.md）" % e)
            elif os.path.isfile(p):
                if e.lower() == "readme.md":
                    continue
                if md_only:
                    errs.append("%s 顶层只许 README.md 与日期文件夹：%s" % (name, e))
                elif not e.lower().endswith(".md"):
                    errs.append("内部分享 顶层只许 md 文件：%s" % e)

    check_share("内部分享", False)
    check_share("外部分享", True)
    print("project-control check：%s（配置：%s）" % (root, cfg_path or CFG_REL))
    for w in warns:
        print("  ! " + w)
    for e in errs:
        print("  x " + e)
    print("  verdict: %s（违规 %d，提醒 %d）" % ("PASS" if not errs else "FAIL", len(errs), len(warns)))
    return 1 if errs else 0


def main():
    ap = argparse.ArgumentParser(description="project-control：目录骨架 init 与白名单自检 check")
    ap.add_argument("cmd", choices=["init", "check", "index"])
    ap.add_argument("--root", default=".", help="工程根目录（默认当前目录）")
    ap.add_argument("--roundtrip", help="回传目录，逗号分隔，如 HDL,SYNTHESIS,DV_TCON_C")
    ap.add_argument("--exceptions", help="特例目录（保持原状），逗号分隔；给空串表示没有")
    ap.add_argument("--tools", help="工具与记录目录，逗号分隔；默认 script,修改记录,docs,plan")
    ap.add_argument("--projects", help="内部分享里已有的项目文件夹，逗号分隔；给空串表示没有")
    ap.add_argument("--site", help="对外网站的仓库路径或 URL")
    ap.add_argument("--cfg", help="配置文件路径（check 可用它在落盘前预览）")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    if a.cmd == "init":
        if not a.roundtrip and load_cfg(root) is None:
            sys.exit("init 需要用 --roundtrip 给出回传目录名，如 --roundtrip HDL,SYNTHESIS")
        sys.exit(cmd_init(root, a))
    if a.cmd == "index":
        sys.exit(cmd_index(root))
    sys.exit(cmd_check(root, cfg_path=a.cfg))


if __name__ == "__main__":
    main()

# ymzhu 2026-11-24 17:04
