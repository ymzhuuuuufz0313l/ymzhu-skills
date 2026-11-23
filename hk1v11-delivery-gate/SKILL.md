---
name: hk1v11-delivery-gate
description: >-
  HK1V11 交付闸门：变更分级（L0-L3）、一条命令跑完 preflight（签名/CHANGES/lint/评审报告）、
  回传包 overlay 校验（只改不增删、代际探针、提交自检）。交付完成与 VM/服务器无关。
  触发词："交付闸门"、"跑闸门"、"preflight"、"能不能交付"、"准备回传"、
  "overlay 校验"、"代际探针"、"L2/L3 检查"、"delivery gate"、"提交前检查"、
  "推送前检查"、"改完图要交付"、"站点改动交付".
---

# HK1V11 交付闸门

项目侧权威规则在 `E:\project\HK1V11\AGENTS.md`（§3.1 分级 / §3.6 交付定义 / §3.7 探针 / §3.8 overlay）。本 skill 只承载**可执行部分**与跨项目通用规则。

## 铁律

1. **交付完成与 VM/服务器无关**：完成 = `preflight` pass + `REVIEW.md` 生成 + commit 已 push。不得把"服务器 case 跑绿"作为完成条件，也不得默认登录 VM（`root@192.168.206.128`）。
2. **报告即证据**：任何关卡只认 `script/gates/reports/*.json`。散文结论、口头"我检查过了"一律不算。
3. **REVIEW.md 是生成物**：手写视为不合规。

## 分级与关卡

| 级别 | 判定 | 关卡 |
|---|---|---|
| L0 | 文档/注释 | 签名 + CHANGES |
| L1 | 非功能性 RTL | + iverilog + verilator lint |
| L2 | 功能性 RTL | + `*_review.json`（critical==0 && high<=1，且新于最后 RTL 改动） |
| L3 | 重定时/时序敏感 | + `*_trace.json`（Workflow C）+ `*_tb.json` 对拍证据 |

级别由 agent 判定，用户可否决；级别写进提交信息。

## 用法

```bash
# 交付检查（自动取 git 改动；--files 可显式指定）
python script/gates/preflight.py --level L2
python script/gates/preflight.py --level L3 --require-pushed

# 回传 overlay
python script/gates/overlay_check.py pre  --package HDL
python script/gates/overlay_check.py post --package HDL --paths HDL/ [--commit]
python script/gates/overlay_check.py post --package SYNTHESIS --paths SYNTHESIS/ --approved-adds script/approved_adds_<ver>.txt [--commit]
# pre 只要求「本包范围内」干净；新增（含未 git add 的未跟踪新文件）必须在 --approved-adds 清单内，清单外 FAIL（2026-11-23）
```

`--package` 取 `SYNTHESIS` / `HDL` / `DV_TCON_C`。

## 依赖

- `iverilog`（语法）、`verilator`（lint；MSYS2: `pacman -S mingw-w64-ucrt-x86_64-verilator`）。脚本会在 PATH 找不到时回落到 `D:/msys64/ucrt64/bin`，并自设 `VERILATOR_ROOT` 与可写 `TMP`。
- `script/gates/probes.json`：代际探针表（`expect` 支持 `==N` / `>0` / `>=N`）。
- `script/pack_diff.py`：回传包 diff-first（谁覆盖谁拍板）——本 skill 的 overlay 校验在其**之后**跑。

## 站点 / 图改动专用条款（2026-11-18 加，team-share 站点审计沉淀）

站点改动（team-share-public 下的 `*.html` / `images/*.svg` / `js/` / `search-index.*`）虽是 L0/L1，但有四条独立硬约束：

1. **preflight 会清空 git 暂存区**——顺序固定为 **`preflight` → `git add -A -- <显式路径...>` → `commit`**。反了就会出现"33 个待提交只落了 2 个"（2026-11-18 实测事故）。提交后 `git log --stat -1` 核对文件数与暂存数一致。
2. **`--files` 只跑本次改动，不做全量脏树**：工作区存在他人/其他线并发改动时，`preflight --level L0 --files <本次文件>` 才是与本次相关的判定；全量跑会把别人的红项算到自己头上，也会掩盖自己的红项。
3. **图改动必须先过图门再交付**：在 `E:/project/HK1V11` 下跑 `python script/_chapter_viz/_svg_qa.py` 与 `python script/_chapter_viz/_svg_anim_qa.py`，双 PASS（exit 0）才并入交付结论；站点侧再跑 `validate_kit_v4.py` / `qa_site.py`。
4. **fetch / ls-remote 也要一次性代理**：HK1V11 的 fetch URL 是 https、push URL 是 ssh:443，https 侧在本机需要
   `git -c http.proxy=http://127.0.0.1:12450 -c https.proxy=http://127.0.0.1:12450 fetch origin main`；
   **不要**因为 fetch 报 `schannel: failed to receive handshake` 就宣布"已推送"。确认用同一组 flags 的 `git ls-remote origin main` 比对 HEAD。

## 事故依据

- 2026-09-29 G13 双事故：静态"几何保持"推演全过后动态回归才暴露 → L3 强制对拍 TB。
- 2026-10-28 回传包漏采（changed-list 不全）→ diff-first 强制（`pack_diff.py`）。
- 2026-11-13 overlay 多路径 `git add` 失败漏推 → `overlay_check.py post --commit` 的 `git log --stat` 自检。
- 2026-11-18 先 `git add` 后跑 preflight → 暂存区被清空、33 个文件只提交 2 个 → 顺序条款（见上节第 1 条）。

## 脚本副本

`scripts/preflight.py`、`scripts/overlay_check.py` 是项目 `script/gates/` 的镜像。**以项目内副本为准**；改脚本时两处同步（项目改完覆盖本目录），然后各自提交。

<!-- ymzhu 2026-11-23 16:20 -->
