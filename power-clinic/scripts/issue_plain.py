#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 GitHub issue 正文/评论整理成"无删除线、无灰底代码体"的普通字体。

根因（2026-11-24）：范围写法 "18~20" 里的半角波浪号被 GitHub(GFM) 当成删除线标记，
同一段里出现两个就把中间整段划掉。另外反引号行内代码是灰底等宽字体，读者不要。

处理：
  1. 围栏代码块 ```…``` -> 引用块（GitHub 引用文字为淡灰色、正常字体），保留缩进与换行
  2. 行内代码 `X`        -> *X*（斜体）
  3. 正文里所有未转义的半角 ~ -> \\~（渲染为普通波浪号，不再成对触发删除线）
  "维护者原话"区、HTML 注释行原样不动。
用法:
  python issue_plain.py show   <issue>...   # 预览变化
  python issue_plain.py apply  <issue>...   # 写回正文
  python issue_plain.py comment <issue>...  # 改写该票下本人最后一条评论
  python issue_plain.py check  <issue>...   # 用 GitHub /markdown 接口渲染，统计 <del>/<code>/<pre>/<hr>
"""
import re, sys, subprocess, json

REPO = "ymzhuuuuufz0313l/HK1V11"
SPECIALS = "*_`[]()#<>~|@"


def esc(s):
    s = s.replace("\\", "\\\\")
    for ch in SPECIALS:
        s = s.replace(ch, "\\" + ch)
    return s


def fence(m):
    lines = m.group(1).strip("\n").split("\n")
    out = []
    for ln in lines:
        core = ln.strip(" ")
        ind = len(ln) - len(ln.lstrip(" "))
        out.append("> " + "&nbsp;" * ind + esc(core).replace(" ", "&nbsp;") + "  ")
    return "\n".join(out)


def inline(m):
    c = m.group(1).replace("\\|", "|")
    return "*" + esc(c) + "*"


def protect_tilde(body):
    """正文里的半角 ~ 一律转义；维护者原话区与 HTML 注释行不动。"""
    out, prot = [], False
    for ln in body.split("\n"):
        if ln.startswith("<!--"):
            out.append(ln)
            continue
        if ln.startswith("## "):
            prot = ln.strip() == "## 维护者原话"
            out.append(ln)
            continue
        if not prot:
            ln = re.sub(r"(?<!\\)~", r"\\~", ln)
        out.append(ln)
    return "\n".join(out)


def transform(body):
    body = body.replace("非空洞对照（把 `\\|r` 项去掉的错误使能）", '非空洞对照（把"链内非零"项去掉的错误使能）')
    body = re.sub(r"```[A-Za-z]*\n(.*?)\n```", fence, body, flags=re.S)
    body = re.sub(r"`([^`\n]+)`", inline, body)
    body = protect_tilde(body)
    return body


def _lf(s):
    """行尾统一成 \\n（GitHub 上出现过的 \\r\\r\\n 是 Windows 文本模式写子进程时二次翻译造成的）"""
    return s.replace("\r\r\n", "\n").replace("\r\n", "\n").replace("\r", "\n")


def gh(*args, inp=None):
    """行尾安全：输入按 UTF-8 字节写（不经文本模式翻译），输出读回后统一成 \\n"""
    data = None if inp is None else _lf(inp).encode("utf-8")
    r = subprocess.run(["gh"] + list(args), input=data, capture_output=True)
    out, err = r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
    if r.returncode != 0:
        sys.exit("gh 失败: %s %s" % (err.strip(), out.strip()))
    return _lf(out)


def patch_body(n, new):
    """用 JSON 体精确写回 issue 正文（字节级，不做任何换行翻译）"""
    payload = json.dumps({"body": _lf(new)}, ensure_ascii=False).encode("utf-8")
    r = subprocess.run(["gh", "api", "-X", "PATCH", "repos/%s/issues/%s" % (REPO, n), "--input", "-"],
                       input=payload, capture_output=True)
    if r.returncode != 0:
        sys.exit("PATCH 失败: %s" % r.stderr.decode("utf-8", "replace").strip())


def render(text):
    """GitHub 官方 GFM 渲染：POST /markdown"""
    payload = json.dumps({"text": text, "mode": "gfm", "context": REPO})
    return gh("api", "-X", "POST", "markdown", "--input", "-", inp=payload)


def tags(html):
    return {t: len(re.findall("<" + t + r"[\s>]", html)) for t in ("del", "s", "strike", "code", "pre", "hr")}


def texts_of(n):
    """返回 [(where, text)]：正文 + 全部评论"""
    body = gh("issue", "view", n, "-R", REPO, "--json", "body", "-q", ".body")
    cs = json.loads(gh("api", "repos/%s/issues/%s/comments" % (REPO, n)))
    return [("正文", body)] + [("评论", c["body"]) for c in cs]


def main():
    mode, nums = sys.argv[1], sys.argv[2:]
    for n in nums:
        if mode == "lf":
            # 行尾统一：正文与全部评论里的 \r 全部去掉（字节级读写）
            raw = subprocess.run(["gh", "api", "repos/%s/issues/%s" % (REPO, n)], capture_output=True).stdout.decode("utf-8", "replace")
            cur = json.loads(raw)["body"]
            cr0 = cur.count("\r")
            if cr0:
                patch_body(n, cur)
            rawc = subprocess.run(["gh", "api", "repos/%s/issues/%s/comments" % (REPO, n)], capture_output=True).stdout.decode("utf-8", "replace")
            nc = 0
            for c in json.loads(rawc):
                if "\r" in c["body"]:
                    r = subprocess.run(["gh", "api", "-X", "PATCH", "repos/%s/issues/comments/%d" % (REPO, c["id"]), "--input", "-"],
                                       input=json.dumps({"body": _lf(c["body"])}, ensure_ascii=False).encode("utf-8"), capture_output=True)
                    nc += r.returncode == 0
            chk = json.loads(subprocess.run(["gh", "api", "repos/%s/issues/%s" % (REPO, n)], capture_output=True).stdout.decode("utf-8", "replace"))["body"]
            print("#%s 正文回车 %d -> %d；评论改写 %d 条" % (n, cr0, chk.count("\r"), nc))
            continue
        if mode == "check":
            for where, t in texts_of(n):
                tg = tags(render(t))
                bad = tg["del"] or tg["s"] or tg["strike"] or tg["code"] or tg["pre"]
                print("%s#%s %s 渲染：%s" % ("OK " if not bad else "!!", n, where, tg))
            continue
        if mode == "comment":
            cs = json.loads(gh("api", "repos/%s/issues/%s/comments" % (REPO, n)))
            if not cs:
                print("#%s 没有评论" % n)
                continue
            cid, old = cs[-1]["id"], cs[-1]["body"]
            new = transform(old)
            if new == old:
                print("#%s 评论无需改" % n)
                continue
            gh("api", "-X", "PATCH", "repos/%s/issues/comments/%s" % (REPO, cid), "-f", "body=" + new)
            print("#%s 评论已改写（%d 字符）" % (n, len(new)))
            continue
        old = gh("issue", "view", n, "-R", REPO, "--json", "body", "-q", ".body")
        new = transform(old)
        if mode == "show":
            print("== #%s：反引号 %d -> %d，未转义 ~ %d -> %d" % (
                n, old.count("`"), new.count("`") - new.count("\\`"),
                len(re.findall(r"(?<!\\)~", old)), len(re.findall(r"(?<!\\)~", new))))
        elif mode == "apply":
            if new == old:
                print("#%s 无需改" % n)
                continue
            gh("issue", "edit", n, "-R", REPO, "--body-file", "-", inp=new)
            print("#%s 正文已写回" % n)


if __name__ == "__main__":
    main()

# ymzhu 2026-11-24 14:45
