---
name: hk1v11-delivery-gate
description: >-
  HK1V11 交付闸门：变更分级（L0-L3）、一条命令跑完 preflight（签名/CHANGES/lint/评审报告）、
  回传包 overlay 校验（只改不增删、代际探针、提交自检）。交付完成与 VM/服务器无关。
  触发词："交付闸门"、"跑闸门"、"preflight"、"能不能交付"、"准备回传"、
  "overlay 校验"、"代际探针"、"L2/L3 检查"、"delivery gate".
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
```

`--package` 取 `SYNTHESIS` / `HDL` / `DV_TCON_C`。

## 依赖

- `iverilog`（语法）、`verilator`（lint；MSYS2: `pacman -S mingw-w64-ucrt-x86_64-verilator`）。脚本会在 PATH 找不到时回落到 `D:/msys64/ucrt64/bin`，并自设 `VERILATOR_ROOT` 与可写 `TMP`。
- `script/gates/probes.json`：代际探针表（`expect` 支持 `==N` / `>0` / `>=N`）。
- `script/pack_diff.py`：回传包 diff-first（谁覆盖谁拍板）——本 skill 的 overlay 校验在其**之后**跑。

## 事故依据

- 2026-09-29 G13 双事故：静态"几何保持"推演全过后动态回归才暴露 → L3 强制对拍 TB。
- 2026-10-28 回传包漏采（changed-list 不全）→ diff-first 强制（`pack_diff.py`）。
- 2026-11-13 overlay 多路径 `git add` 失败漏推 → `overlay_check.py post --commit` 的 `git log --stat` 自检。

## 脚本副本

`scripts/preflight.py`、`scripts/overlay_check.py` 是项目 `script/gates/` 的镜像。**以项目内副本为准**；改脚本时两处同步（项目改完覆盖本目录），然后各自提交。
