---
name: version-archive
description: 为"多版本归档目录"（类似 LC_CPUWR_history，同一模块按版本迭代归档 RTL/env/文档的目录）建立独立的目录级维护规则：目录内 CHANGES.md 总览、README 版本速查表、归档结构规范。触发词："新建归档目录"、"多版本目录"、"version archive"、"像 cpuwr_history 这样的目录"、"目录内变更总览"、"目录级 CHANGES"。
---

# Version Archive Directory Skill

> 多版本归档目录 = 一个模块的 RTL / env / 文档按版本迭代归档的目录，典型如本项目 `LC_CPUWR_history/`（含 `verilog_hdl/`、`markdownfile/`、`current_env/` 等按版本归类的子目录，且根目录仅保留当前版本文件）。

## 触发条件

以下情况触发本 Skill：
- 用户说："新建归档目录"、"多版本目录"、"version archive"、"像 LC_CPUWR_history 这种目录"、"有很多个版本的目录"、"建立目录级维护规则"。
- 用户说："目录内变更总览"、"这个目录下所有改动"、"目录级 CHANGES"、"本目录的改动记录"。
- 用户新建目录结构类似 `LC_CPUWR_history/`（RTL + env + markdown 三件套按版本归档）。

## 核心原则（三层文件体系）

1. **目录级 CHANGES.md（本目录变更总览）**：在归档目录根下放一个 `CHANGES.md`，**按时间倒序累积记录本目录内全部版本的改动**（RTL + env + 文档）。这是"看到本目录所有改动"的唯一入口，不依赖外部汇总。
2. **README.md（版本速查表）**：`当前版本表` + `历史版本表（基于版本 / 主要变更）` + `目录结构说明`，方便快速跳转。
3. **不冲突规则（双轨记录）**：目录级 `CHANGES.md` 是**目录内独立记录**，与项目根级 `修改记录/CHANGES.md`（或主规则 workflow-maintainer 的 CHANGES）**并行维护、互不替代**：
   - 根级 CHANGES 继续按 AGENTS.md 第 3.1 条汇总**整个项目**的变更，不能因为有了目录级 CHANGES 而省略。
   - 目录级 CHANGES 只覆盖该归档目录内的文件。
   - 每次变更：目录级 CHANGES 记一条（概要+指针），根级 CHANGES 也要记（外部汇总保留）。

## 工作流

### 场景 1：新建一个多版本归档目录

1. 先问用户确认：该目录是否作为"多版本归档目录"（多个版本共存）管理，还是普通工作目录。
2. 确认后，为该目录生成：
   - `README.md`：目录结构说明 + 当前版本表 + 历史版本表模板（表头：文件名 / 基于版本 / 主要变更 / 备注）。
   - `CHANGES.md`：目录内变更总览，模板如下（初始只有一条"目录建立"记录）。
   - 可选 `AGENTS.md`：若该目录规则复杂（如 env/checker 映射 RTL 版本、cfg_frame 解析一致性），单独生成目录级 AGENTS.md。
3. 向用户汇报生成的清单，并说明根级 `修改记录/CHANGES.md` 仍需按主规则维护（双轨）。

### 场景 2：版本迭代时维护目录内 CHANGES.md

每个新版本发布时，除按原规则归档 RTL/env/changelist 外，必须更新目录内 `CHANGES.md`：

1. 读取目录根下 `CHANGES.md`（不存在则创建）。
2. 在**文件顶部**追加新版本记录，格式：

```markdown
## YYYYMMDDvN（YYYY-MM-DD）

- **基线**：`<上一版本文件路径>`
- **RTL**：<主要变更一句话到几句话>
- **env**：<版本头升版 / 功能改动>
- **状态**：✅ 完成 / ⏳ 待办
- **详细**：`markdownfile/<版本>/..._changelist.md`
```

3. 同步更新 `README.md` 的当前版本表与历史版本表。
4. 若同时改了外部（`HDL/`、`DV_TCON_C/`），根级 `修改记录/CHANGES.md` 也要记录（双轨）。

### 场景 2.5：版本发布前必须执行的"验收三关"

新版本归档到 `LC_CPUWR_history/` 根目录、对外发布（回传服务器 / 推送 GitHub / 交付）**之前**，必须依次完成三关检查，任一关不过则打回修改、复检通过后才允许归档：

1. **第一关：语法检查（iverilog）**
   - 对三件套（`LC_CPUWR` / `LC_REG_MAPPING` / `LINK_LOGIC` 及改动到的 RTL）执行 `iverilog -g2005-sv -DFF_DLY=0` 语法检查。
   - 仅允许缺失标准单元 / 子模块（`CLKINVX4AL9`、`CLKGEN` 等）的预期错误；出现语法错误必须修复。

2. **第二关：RTL 对抗评审（`rtl-code-review` skill）**
   - 对新版本 vs 上一版本的 diff（或指定文件）执行分维度对抗评审。
   - 重点维度：多驱动/重复 assign、接口一致性（端口/位宽是否同步上层实例化与 file_list）、门控与 `ifdef` 一致、注释与实现同步。
   - 门禁：`critical == 0 && high <= 1`，不通过则先修复再复评。

3. **第三关：信号链路追踪（`rtl-signal-trace` skill）**
   - 对新增/变更的输出信号逐条做 source → sink 跨模块追踪，确认：
     - 端口连接真实连通（无 `ifdef` 未定义分支把连接关掉、无漏接）。
     - 悬空/空接信号与注释声明一致（如 0716v1 `FSEL` 明确标注 unused）。
     - 跨时钟域路径有同步处理。
   - 输出追踪表（模块 / 信号 / 位置 / 时钟域）。

**验收记录**：三关结果写入该版本的 `*_changelist.md` 的"静态检查 / 验证状态"章节（`iverilog 通过`、`rtl-code-review pass: true/false`、`signal-trace 结论`）。不涉及 RTL 变更的纯文档/env 版本头升版可跳过第二、三关，但第一关（如 RTL 有改动）必须执行。

### 场景 3：查看目录内所有改动

1. 直接读目录根下 `CHANGES.md`（全部版本按时间倒序）。
2. 需要版本速查表 → 读 `README.md`。
3. 需要逐条 diff → 按 CHANGES.md 中的"详细"指针打开 `markdownfile/<版本>/`。

## CHANGES.md 模板

```markdown
# <目录名> 目录内变更总览

> 本文件是 `<目录名>/` 目录自身的累积变更总览，按时间倒序记录该目录下所有版本的改动。
> 详细 diff 见 `markdownfile/<版本>/`；项目级汇总仍在根目录 `修改记录/CHANGES.md`，两者并行维护、互不替代。

## 版本总览速查表

| 版本 | 日期 | 基于版本 | 核心变更（一句话） |
|------|------|----------|--------------------|

## 分版本变更详情

### YYYYMMDDvN（YYYY-MM-DD）
- **基线**：...
- **RTL**：...
- **env**：...
- **状态**：...
- **详细**：`..._changelist.md`

## 维护记录（本文件自身变更）
| 日期 | 说明 |
|------|------|
```

## 输出格式

完成后汇报：

```markdown
已建立/更新多版本归档目录规则：

- 操作：{新建归档目录 / 版本迭代归档 / 查看目录内变更}
- 涉及目录：{路径}
- 更新的文件：
  - `CHANGES.md`（目录内变更总览）
  - `README.md`（版本速查表）
  - `修改记录/CHANGES.md`（根级汇总，双轨保留）
- 后续建议：...
```

## 注意事项

- **禁止**：有了目录级 CHANGES 后就不更新根级 `修改记录/CHANGES.md`——两者必须并存。
- **禁止**：把目录级 CHANGES 放在归档目录的 `markdownfile/<版本>/` 子目录里，它必须在归档目录**根级**。
- 版本号命名遵循项目约定（如 `LC_CPUWR_20260716_v1_decimal.v`）；env 文件不改名只升版本头。
- 与 `workflow-maintainer` 的关系：本 Skill 负责"目录内记录"；`workflow-maintainer` 负责"项目根级记录与回传清单"，调用时可同时触发两者。
