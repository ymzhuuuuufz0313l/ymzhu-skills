---
name: daily-report
description: Summarize the current conversation and write the user's work into the local daily/weekly/legacy-issue Markdown system under E:\每日记录\. Use when the user says "记录到日报", "写入今日记录", "整理今天的工作", "整理日报", "写日报", "日报", "daily report", or asks to record today's work into the daily record system.
---

# Daily Record Skill

## Trigger

When the user asks to record today's work into the daily record system (e.g., "记录到日报", "写入今日记录", "整理今天的工作", "整理日报", "写日报", "日报"), execute the workflow below.

## Workflow

1. **Read the guide**: Read `E:\每日记录\每日记录AI协作指南.md` before any file operation.
2. **Summarize the conversation**: Distill what was actually completed, key conclusions, and next steps. Do **not** copy-paste chat history.
3. **Identify the project by conversation path**: Use the current working directory / conversation scope to decide the target project. Match rules:
   - Path contains `HV2M23` (case-insensitive) → `E:\每日记录\HV2M23\`
   - Path contains `HK1V11` (case-insensitive) → `E:\每日记录\HK1V11\`
   - If no match, infer from file paths mentioned in the conversation; if still unclear, ask the user.
4. **Locate or create today's daily record**:
   - **默认使用当前系统日期**生成文件名中的 `MMDD` 部分。
   - 文件路径为 `E:\每日记录\<project>\每日记录_MMDD.md`。
   - 如果用户明确指定了日期（如"记录昨天的日报"、"补 6 月 25 日的日报"），按用户指定日期生成 `MMDD`。
   - 如果用户没有指定日期，**绝对不要**从对话上下文中推断日期，必须使用当前系统日期。
   - 如果文件已存在，追加；如果不存在，从模板创建。
5. **Write/update the daily record**: Follow the fixed structure (see Template section below):
   - `### 今日完成`
   - `### 下一步待做`
   - `### 发现问题`
   - `### 明日计划`
   - Optional: `### 备注`
   - Module titles: `#### [模块名]`
   - Items: `- [动作/类别] 内容` or table rows
6. **Sync to GitHub Pages site (if exists)**: After the daily record is saved, check whether `E:\每日记录\daily-record-site-github\generate.py` exists. If it does:
   - Run `cd "E:\每日记录\daily-record-site-github" && python generate.py`
   - Run `git add .`
   - Run `git commit -m "update daily records"`
   - Run `git push`
   - This regenerates and deploys the static daily-record site to `https://ymzhuuuuufz0313l.github.io/daily-record/`
   - If any step fails, report the failure to the user but do not block the rest of the daily-record workflow.
7. **Sync weekly record**: Check and update `E:\每日记录\<project>\每周记录.md`. Ensure the current daily record is referenced.
8. **Update legacy issues**: Check `E:\每日记录\<project>\遗留问题.md`. Only record cross-day or tracking-required issues. Close resolved items with 🔵 and a close date.
9. **Report to user**: List files written/updated, synced contents, and any remaining legacy issues.

## 日期处理规则（必须遵守）

1. **默认使用当前系统日期**：除非用户明确指定，否则日报文件名中的 `MMDD` 必须使用当前系统日期。
2. **禁止推断日期**：不要根据对话中的"昨天"、"刚才"、"之前"等词语推断日期。
3. **用户指定日期时**：如果用户说"补昨天的日报"、"记录 6 月 25 日"等，按用户要求生成对应 `MMDD`。
4. **日期确认**：在写入日报前，向用户说明"我将使用日期 MMDD"，让用户有机会纠正。
5. **跨天会话**：如果对话从昨天持续到凌晨，仍然使用**当前系统日期**，除非用户明确要求记录到昨天。

## Format rules (must follow)

- **降低文字密度，提升可读性**：日报是给别人快速扫一眼看的，不是流水账。避免长篇描述和细节罗列。
- **优先使用表格**：每个模块的完成项、跨模块的下一步/问题/计划，尽量用表格呈现。
- **单条描述精简**：控制在 20 字左右，只说“做了什么”和“状态”，不写具体信号名、位宽、行号等细节。
- **Use tables when a module has ≥ 4 completed items; use lists for 1-3 items.**
- **Use tables for cross-module next-steps/issues/plans when ≥ 3 items; use lists for 1-2 items.**
- Table column width ≤ 80 characters; split long content into new lines or notes.
- Visual style: alternate row backgrounds, soft but visible column/row separators; highlight status/key columns.
- Status symbols: ✅ completed, 🔄 in progress, ⏸️ paused, ❌ failed/blocked, ⏳ pending confirmation.
- Empty states ("暂无", "无新增") should be a single line of text, not a forced table.
- **Recommended columns** (based on 0713 template):
  - 今日完成 per-module table: `| 类型 | 事项 | 结果/状态 |`
  - 下一步待做 table: `| 模块 | 事项 | 优先级 |`
  - 发现问题 table: `| 模块 | 问题 | 影响 | 状态 |` or `| 区域 | 字节数 | 错误数 | 正确数 | 说明 |`
- **必要时应画图解释**：如果当天工作涉及架构关系、数据流向、状态机、调试链路或流程步骤，优先使用 `fireworks-tech-graph` skill 生成 SVG+PNG 图表，插入日报的 📐 图解说明部分。一图胜千言，可降低文字密度并避免歧义。
- Messy format equals unqualified record.

## Content scope rule (user preference)

When summarizing work for the daily record, **only include items that represent real functional work**:

- ✅ RTL code changes / verification / review
- ✅ Test case creation / modification / regression
- ✅ Verification environment changes that directly affect simulation or bring-up

Do **not** include the following unless the user explicitly asks:

- ❌ Script refactoring details (e.g. how a script was rewritten, option added, internal logic changed)
- ❌ Documentation-only updates (e.g. `CHANGES.md`, `REVIEW.md`, internal notes)
- ❌ Non-public / project-management artifacts that are not part of the deliverable

If a script or doc change is tightly coupled with a functional result (e.g. "新增 case 已加入 `case_list.txt` 使其可被回归调用"), mention only the functional outcome, not the file-edit detail.

## Project rules

### Daily record
- Fixed sections: 今日完成, 下一步待做, 发现问题, 明日计划.
- Module title: `#### [模块名]`.
- Item format: `- [动作/类别] 内容`.
- Keep facts only; do not exaggerate results.
- Closed-in-day issues do **not** need to go into legacy issues.

### 推荐模板（基于 0713 格式）

Use this structure as the default template when creating a new daily record. Adjust tables/lists based on actual content density.

```markdown
# 每日记录 - MM/DD (星期X)

### 今日完成

#### [模块名]

| 类型 | 事项 | 结果/状态 |
|------|------|----------|
| [动作/类别] | 具体内容 | ✅ |

### 发现问题

#### [问题分类]

| 区域 | 字节数 | 错误数 | 正确数 | 说明 |
|------|--------|--------|--------|------|
| ... | ... | ... | ... | ... |

#### 错误逻辑

1. **问题点 1**
   - 子说明
2. **问题点 2**
   - 子说明

#### 当前正确的内容

- 正确点 1
- 正确点 2

### 下一步待做

| 模块 | 事项 | 优先级 |
|------|------|--------|
| [模块名] | 具体内容 | 中 |

### 明日计划

- 计划事项

### 备注

- 补充说明、关键数字或用户确认。
```

### 标杆模板（基于 0717 格式，适用于复杂问题/需要证据链的日报）

When the day's work involves complex debugging, cross-validation, evidence collection, or root-cause analysis, use this richer template as the **gold standard**. It front-loads the key conclusion, structures the verification process, and keeps screenshots/code evidence close to each problem.

```markdown
# 每日记录 - MM/DD (星期X)

### 今日完成

#### [模块名]

| 类型 | 事项 | 结果/状态 |
|------|------|----------|
| Debug 增强 | 新增 `xxx.md`：用途说明 | ✅ 待仿真 |
| 编译修复 | 修复点说明 | ✅ |
| RTL 验证 | 修改/验证点说明 | ✅ |
| 结论确认 | 与用户确认的结论文案 | ✅ |

---

## 🎯 关键结论：[一句话核心结论] ✅

> ### 📌 一句话背景说明：核心发现或判定 —— **结论强调**。

### 🔍 验证过程（三级独立交叉验证）

| 步骤 | 内容 | 产出 |
|------|------|------|
| ① 抓取 | 如何抓取信号/数据 | 文件名/日志 |
| ② 解码/分析 | 用什么工具/方法分析 | 输出文件 |
| ③ 比对 | 与什么预期对比 | 报告文件 |

### ✅ 比对结果

| 区域 | 期望内容 | 实际结果 | 结果 |
|------|----------|----------|------|
| 区域 A | 期望描述 | 实际描述 | ✅ |
| 区域 B | 期望描述 | 实际描述 | ✅ |

### 🖼️ 证据截图

![图片描述](https://ymzhuuuuufz0313l.github.io/daily-record/images/<project>/<filename>.jpg)

> 本地原图：`E:\每日记录\<project>\image\<filename>.jpg`（补充说明）

### 📐 图解说明（可选）

当任务涉及架构关系、数据流向、状态机跳转或调试链路时，使用 `fireworks-tech-graph` skill 生成 SVG+PNG 技术图表，插入日报提升可读性。

![图标题](https://ymzhuuuuufz0313l.github.io/daily-record/images/<project>/<diagram>.svg)

> 本地原图：`E:\每日记录\<project>\image\<diagram>.svg` / `.png`

### ⚠️ 过程中定位并处理的问题

| 问题 | 侧 | 状态 |
|------|-----|------|
| 问题简述 | RTL/TX/RX/Env | 🔵 已修复 |
| 问题简述 | RTL | 🟡 待跟进 |

---

### 发现问题

#### [问题标题 1] ✅

**根因**：问题根因说明。

```verilog
// 关键代码片段（可选）
assign signal = a & b;
```

**处理**：处理人或下一步，遗留问题状态。

#### [问题标题 2] ✅

...

---

### 下一步待做

| 模块 | 事项 | 优先级 |
|------|------|--------|
| 模块名 | 具体事项 | 高 |

### 明日计划

- 明日具体计划。

### 备注

- 补充说明、关键数字或用户确认。
```

#### 0717 标杆模板使用指南

| 场景 | 使用部分 | 说明 |
|------|----------|------|
| 复杂 Debug 日 | 🎯 关键结论 + 🔍 验证过程 + 🖼️ 证据截图 | 把结论和证据链放在第一位 |
| 问题已闭环 | 每个问题小标题后加 ✅，状态用 🔵 | 明确哪些已解决 |
| 问题待跟进 | 状态用 🟡/⚠️，写明负责人 | 便于后续跟踪 |
| 有截图证据 | 🖼️ 证据截图 + 本地原图路径 | 线上图 + 本地原图双备份 |
| 涉及代码根因 | 发现问题内加 ````verilog` 代码块 | 让根因可 review |
| 需要架构/流程/数据流可视化 | 📐 图解说明 + `fireworks-tech-graph` skill | 生成 SVG+PNG，插入日报 |

#### 模板选择建议

- **常规工作日**（无复杂问题）：使用默认 0713 轻量模板。
- **Debug/验证/问题闭环日**：使用 0717 标杆模板，完整记录结论、过程、证据。
- **需要画图解释的复杂任务**：在 0717 标杆模板中加入 📐 图解说明，调用 `fireworks-tech-graph` skill 生成架构图/数据流图/流程图/状态机等 SVG+PNG 图表。
- 如果用户没有特殊要求，根据当天工作复杂度自动选择：复杂度低 → 0713；复杂度高 → 0717；需要可视化 → 0717 + 图解说明。

### Weekly record
- Append detailed records in reverse chronological order.
- Weekly summary only lists key outputs and status; no流水账.
- After daily record is finished, confirm the weekly record references the current daily record.

### Legacy issues
- Only record cross-day or tracking-required issues.
- Closed items use 🔵 with close date.
- ⚠️/🔴/🟡 issues must keep a reviewable reason or next step.

## State definitions

- 🔴 high priority / blocking / must handle soon
- ⚠️ risk / external dependency / needs attention
- 🟡 pending confirmation / low-risk observation
- 🔵 resolved / closed
