---
name: spec-traceability
description: >-
  Lightweight spec-to-code traceability for RTL projects: requirement ID
  (REQ_ID) allocation and uniqueness checks, spec hash injection and drift
  detection, and version-consistency audits across spec docs, RTL, and
  verification collateral. Use when the user asks about traceability,
  requirement coverage, spec/RTL version drift, or pre-delivery consistency
  checks. 触发词: "追溯", "traceability", "REQ_ID", "spec hash", "版本一致性",
  "文档漂移", "需求覆盖". Do not use for full-blown requirements-management
  system setup or DOORS-style tooling.
---

# Spec Traceability（轻量版）

核心思想：spec（需求/接口/寄存器文档）与代码之间建立**机器可校验**的双向追溯，让"文档改了代码没改"这类漂移从人工检查发现变成脚本检查发现。

## Runtime Compatibility

运行脚本或读取 reference 之前，先把本 `SKILL.md` 所在目录解析为 `SKILL_ROOT`（Kimi Code / Claude Code 中使用 skill 加载信息给出的绝对路径；Claude Code 可用 `${CLAUDE_SKILL_DIR}`）。下文命令块各自设置 `SKILL_ROOT`。

脚本为纯 Python 3 标准库实现，直接 `python3` 运行。

## 三层追溯模型（按需采用，不强求全套）

| 层 | 位置 | 标注 |
| --- | --- | --- |
| 1. 文件头 | RTL 文件头注释 | `@requirement REQ-xxx` / `@spec_ref <spec 文件>` / `@spec_hash sha256:<12位>` |
| 2. 行内断言 | SVA / 关键逻辑旁 | `@verifies REQ-xxx` / `@constraint` |
| 3. 交叉引用 | 约束文件（SDC 等） | `@requirement` + `@spec_ref` |

**采用原则**：先在单个模块试点 Layer 1（文件头 + spec hash），验证价值后再推广；不要全项目一次性铺开。

## REQ_ID 编码规范

见 `$SKILL_ROOT/references/req-id-conventions.md`。要点：`REQ-<模块>-<类别><序号>`，类别 F=功能 / P=性能 / I=实现(DFT) / C=约束；ID 一旦分配**只废弃不删除不复用**。

## Workflow A：spec hash 漂移检测（最易落地，推荐先做）

1. 对关键 spec 文档计算归一化 SHA256 短哈希：

```bash
SKILL_ROOT="/absolute/path/to/this/skill"
python3 "$SKILL_ROOT/scripts/compute_spec_hash.py" <spec_file>
```

2. 把 `Spec Hash: sha256:<12位>` 写入消费该文档的 RTL/脚本头部注释。
3. 一致性检查时重算哈希并比对：不一致 = spec 已漂移，消费方需要同步。

归一化规则（脚本内置）：去行尾空白、去空行、去 HTML 注释行，避免纯格式变化误报。

## Workflow B：REQ_ID 分配与唯一性检查

```bash
SKILL_ROOT="/absolute/path/to/this/skill"
# 为模块分配下一个 REQ_ID（默认类别 F）
python3 "$SKILL_ROOT/scripts/allocate_req_id.py" <模块ID> --category F
# 检查追溯登记表中 REQ_ID 唯一性 / 是否有被删除的 ID
python3 "$SKILL_ROOT/scripts/check_req_uniqueness.py" --registry <requirements_matrix.csv>
python3 "$SKILL_ROOT/scripts/check_req_uniqueness.py" --registry <csv> --check-deleted
```

登记表为 CSV（至少含 `req_id` 列），默认路径为 `<项目>/traceability/requirements_matrix.csv`。

## Workflow C：版本一致性审计（交付/回传前）

对"spec 文档 ↔ RTL ↔ 验证环境（env/checker/文档）"三方做对应检查：

1. 收集本次变更文件清单（`git diff --name-only` 或用户提供）。
2. 逐项问：
   - RTL 变了 → 依赖它的 env/checker 的**版本头声明**是否同步？文件列表、接口文档是否同步？
   - spec 文档变了 → 消费方的 `@spec_hash` 是否还有效（Workflow A 重算）？
   - 任何变更 → 项目的变更登记（changelog 等）是否已记录？
3. 输出不一致项清单：`文件 | 当前声明 | 应为 | 建议动作`。修复前经用户确认。

## 硬性规则

- 检查和生成可以做；**修复漂移前必须经用户确认**。
- REQ_ID 只增不删不复用；废弃的 ID 在登记表中标记 deprecated。
- 试点 → 验证 → 推广；不要一次在全项目强制铺开全套三层模型。
