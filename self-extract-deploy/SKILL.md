---
name: self-extract-deploy
description: 自解压部署脚本（paste-and-run installer）工作模式：当服务器只能通过远程桌面粘贴纯文本创建文件时，用 generator 在本机生成单文件 Python installer（zlib+base64 嵌入全部 payload），粘贴到服务器一条命令解出多文件。触发词："回传服务器"、"打包成 python 脚本"、"paste-and-run"、"deploy 脚本"、"自解压"、"自解压部署"、"多文件回传"、"生成 installer"、"打包回传"。
---

# Self-Extract Deploy Skill（自解压部署脚本）

一句话定位：**generator 本机生成 → 单文件 installer（payload 全部 zlib+base64 内嵌，纯 ASCII）→ 粘贴到服务器 → `python3 deploy_xxx.py <目标目录>` 一条命令落盘多文件**，专治"服务器只能粘贴文本、不能 scp/upload"的回传场景。

## 触发条件

以下情况触发本 Skill：

- 用户说："回传服务器"但上传通道只有远程桌面粘贴 / 文本终端
- 用户说："打包成 python 脚本"、"打包回传"、"生成 installer"、"deploy 脚本"
- 用户说："paste-and-run"、"自解压"、"自解压部署"、"多文件回传"
- 服务器上没有 ssh/sftp 通道，或 ssh_upload 被防火墙挡住，只能走剪贴板
- 要回传的是**一批文件**（目录骨架 / 多个 RTL / 多个 case 目录），逐个粘贴不现实

## 适用判断（何时用本模式）

| 场景 | 做法 |
|---|---|
| 单个文件 + 有 ssh 通道 | 直接 `ssh_upload`（见 workflow-maintainer 场景 3），不要用本模式 |
| 少量文件 + 有 ssh 通道 | tar 打包 → `ssh_upload` → `ssh_exec` 解压 |
| **无 ssh 通道 / 只能粘贴文本** | **本模式：generator + installer 双文件** |
| 与 REVIEW.md 流程的衔接 | 本模式的 installer 也是"回传物"。回传前先按 workflow-maintainer 场景 3 生成 `REVIEW.md`；generator 生成的本地文件照常记入 `CHANGES.md`；installer 部署成功后，把服务器侧 `OK ... md5 ...` 输出贴回 REVIEW.md 作为回执 |

## 核心思想：generator → installer 双文件模式

```
本机（可写文件、有完整工具链）            服务器（只能粘贴纯文本）
┌─────────────────────────┐
│ gen_xxx_installer.py    │
│  1. 读源文件（utf-8）     │
│  2. CRLF→LF 规范化       │
│  3. zlib.compress(9)    │      ┌──────────────────────────┐
│  4. base64 → 纯 ASCII    │      │ deploy_xxx.py（单文件）    │
│  5. 记 md5（+size）清单   │ ────│  粘贴整个文件 → 保存        │
│  6. 套模板写 installer    │ 粘贴 │  python3 deploy_xxx.py \  │
│  7. selftest/verify      │      │      /path/to/target      │
└─────────────────────────┘      │  → 解压+md5 校验+落盘      │
  generator 留在本机，可重复跑      └──────────────────────────┘
  （幂等：本地目录每次重建）          installer 独立、纯 stdlib
```

要点：
- **payload 纯 ASCII**（zlib+base64），粘贴通道的 CRLF/空白破坏不了内容；blob 之外的少量代码行靠 LF 规范化兜底。
- installer **只用 stdlib**（base64 / hashlib / os / sys / zlib），服务器零依赖。
- installer 头部注释写清 usage 和 build 号（日期-主题格式，如 `2026-11-06-descramble-ptpx`）。

## 最小可复制模板（从 gen_rtl_fix_installer / deploy_rtl_fix 提炼）

### gen_installer.py 骨架（本机运行）

```python
# gen_installer.py : build deploy_xxx.py (paste-channel installer). Pure stdlib.
import base64, hashlib, os, zlib

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.normpath(os.path.join(ROOT, "..", "path", "to", "src"))
BUILD = "2026-11-06-mytopic"

FILES = ["a.v", "b.v"]           # 或 [(local_rel, remote_rel), ...]

entries = []
for name in FILES:
    path = os.path.join(SRC_ROOT, name)
    # 读二进制并强制 LF 规范化——不要依赖文本模式默认行为
    data = open(path, "rb").read().replace(b"\r\n", b"\n")
    md5 = hashlib.md5(data).hexdigest()
    blob = base64.encodebytes(zlib.compress(data, 9)).decode("ascii").replace("\n", "")
    entries.append('    "%s": ("%s", "%s"),' % (name, md5, blob))
    print("%s  %d bytes  md5 %s" % (name, len(data), md5))

TPL = """...见下方 installer 骨架，@BUILD@/@ENTRIES@ 占位..."""

out = TPL.replace("@BUILD@", BUILD).replace("@ENTRIES@", "\n".join(entries))
dst = os.path.join(ROOT, "deploy_xxx.py")
# 关键：显式 utf-8 + LF，绝不能用平台默认编码（GBK 陷阱，见"已知坑"）
with open(dst, "w", encoding="utf-8", newline="\n") as f:
    f.write(out)
print("wrote %s (%d bytes)" % (dst, os.path.getsize(dst)))
# ymzhu 2026-11-06 14:30
```

### 生成的 installer 骨架（deploy_xxx.py，服务器运行）

```python
# deploy_xxx.py : paste-and-run installer for <topic>.
# build: @BUILD@
#
# Usage on the server:
#     python3 deploy_xxx.py /path/to/target_dir
# <写明防覆盖策略：.bak 备份 或 拒绝覆盖已存在目录>
import base64, hashlib, os, sys, zlib

BUILD = "@BUILD@"

PAYLOADS = {
@ENTRIES@
}

def main():
    if len(sys.argv) > 1:
        tgt = sys.argv[1]
    else:
        pp = os.environ.get("PROJECT_PATH", "")
        tgt = os.path.join(pp, "default", "target") if pp else ""
    if not tgt or not os.path.isdir(tgt):
        print("ERROR: give the target dir as arg1")
        sys.exit(1)
    print("deploy_xxx build: " + BUILD)
    print("target dir: " + tgt)
    bad = 0
    for name in sorted(PAYLOADS):
        md5, blob = PAYLOADS[name]
        dst = os.path.join(tgt, name)
        # 防覆盖模式 A（就地补丁）：先备份，bak 已存在则跳过备份（幂等）
        bak = dst + ".bak_<topic>"
        if os.path.isfile(dst) and not os.path.isfile(bak):
            os.rename(dst, bak)
            print("backup: " + bak)
        # 防覆盖模式 B（全新目录）：目标已存在则直接报错退出（见 deploy_descramble_netlist）
        data = zlib.decompress(base64.b64decode(blob))
        with open(dst, "wb") as f:            # 二进制写，内容已是 LF
            f.write(data)
        got = hashlib.md5(data).hexdigest()
        status = "OK   " if got == md5 else "MD5-MISMATCH "
        print(status + name + "  " + str(len(data)) + " bytes  md5 " + md5)
        bad += (got != md5)
    if bad:
        sys.exit(1)
    print("done. <下一步动作提示，如 rerun synthesis / LEC>")

main()
# ymzhu 2026-11-06 14:30
```

## 强制规则清单

1. **编码显式声明**：generator 与 installer 模板里所有 `open(..., "w")` 必须带 `encoding="utf-8", newline="\n"`；读源文件用 `"rb"` 或显式 `encoding="utf-8"`。禁止依赖平台默认编码。
2. **LF 行尾**：payload 数据在生成时 `replace(b"\r\n", b"\n")` 规范化；写 installer 用 `newline="\n"`，服务器落盘用 `"wb"` 二进制写。
3. **payload 纯 ASCII**：zlib(level 9) + base64，blob 内不允许出现任何非 ASCII 字节；模板代码本身也只用 ASCII（注释用英文，或至少保证编码声明正确）。
4. **md5 清单**：每条 payload 记 `(md5[, size])`，installer 解压后逐一校验，任何 MISMATCH 计数并在结尾 `sys.exit(1)`。
5. **幂等**：generator 每次全量重建本地产物与 installer；installer 重跑安全——模式 A 靠 `.bak` 已存在跳过备份，模式 B 靠预检目标目录冲突。
6. **selftest / verify**：generator 写完 installer 后必须自测——或 exec 解析 PAYLOADS 做字节级 round-trip 对比（gen_fc_installer --verify），或把 installer 跑进临时目录逐文件 md5 对比（gen_descramble_netlist 的 selftest）。FAIL 则 `SystemExit(1)`。
7. **防覆盖策略二选一并写进 installer 头注释**：就地补丁用 `.bak_<topic>` 备份；全新目录用"已存在即拒绝、提示删除后重跑"。
8. **wrong-dir 保护**：就地补丁模式下，目标文件不存在即报错退出（"not found in target dir - wrong dir?"），防止把文件写进错误目录。
9. **usage 自带**：installer 头注释写明服务器侧命令与目标目录含义；支持位置参数 + `$PROJECT_PATH` 回退。
10. **文件尾签名 ymzhu 规则**：generator 与 installer 末尾 `# ymzhu YYYY-MM-DD HH:MM`（对齐 workflow-maintainer 全局签名规则）。

## 已知坑

- **GBK 陷阱（2026-11-06 实踩，务必写入每次新 generator）**：Windows 上 `open(path, "w")` 不带 `encoding=` 时默认 GBK，生成的 installer 含非 ASCII 字节 → 粘贴到服务器后 `SyntaxError`（服务器 python3 默认 UTF-8）。修复三件套：显式 `encoding="utf-8"`、`newline="\n"`、模板代码 ASCII 化。
- **粘贴通道换行破坏**：即使 CRLF 被通道改写，base64 blob 内容不受影响（只破坏 blob 外的代码行）；因此 blob 一律单行长字符串或多行相邻字符串字面量，绝不用三引号包裹原始文本。
- **大文件提示**：单个 installer 超过几百 KB 后远程桌面粘贴可能截断/卡顿；payload 多时优先选 ssh_upload tar 包，本模式是无通道时的兜底。
- **目录型 payload 的相对路径规范化**：多级目录 payload 用 `os.path.relpath(...).replace("\\\\", "/")` 统一成正斜杠存 key，installer 侧 `os.path.join(tgt, *rel.split("/"))` 还原，避免 Windows 反斜杠混进字符串字面量。
- **文本模式读源**：读 RTL 用 `"rb"` 再手动 LF 规范化，不要 `open(path, "r")`（Windows 文本模式 + 默认编码双重不可控）。

## 参考实例索引（HV2M23，两代三实例，从简到繁）

| 文件 | 特点一句话 |
|---|---|
| `E:/project/HV2M23/SYNTHESIS/fc_deploy/gen_fc_installer.py` | 第一代骨架版：20 文件 overlay 部署，多行 76 列 wrap blob，`--verify` 用 exec 做 round-trip 字节级对比，无 md5 |
| `E:/project/HV2M23/SYNTHESIS/fc_deploy/deploy_fc.py` | 对应 installer（949 行）：utf-8 解码 + 文本写 + `newline="\n"`，无条件覆盖（骨架本身就是新建目录） |
| `E:/project/HV2M23/SYNTHESIS/fc_deploy/gen_rtl_fix_installer.py` | 第二代极简补丁版：73 行，md5 清单 + `.bak_ecofix` 备份 + wrong-dir 保护，单行 blob |
| `E:/project/HV2M23/SYNTHESIS/fc_deploy/deploy_rtl_fix.py` | 对应 installer：3 个 RTL 就地替换，二进制写 + md5 校验 + 备份幂等 |
| `E:/project/HV2M23/DV_TCON_C/gen_descramble_netlist.py` | 第三代全家桶版：generator 先在本地生成 case 目录（正则改 RTL），再打包成带 relpath 的 installer，末尾 selftest 跑进临时目录逐文件 md5 对比；GBK 陷阱当日修复的实例 |
| `E:/project/HV2M23/DV_TCON_C/deploy_descramble_netlist.py` | 对应 installer：目录型 payload（`case/file` 相对路径），`(md5, size, blob)` 三元组，case 目录已存在即拒绝覆盖 |

<!-- ymzhu 2026-11-06 14:30 -->
