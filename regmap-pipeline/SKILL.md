---
name: regmap-pipeline
description: >-
  Single-source register map pipeline: keep one regmap.md per module as the
  source of truth, generate register documentation (Markdown + CMSIS-SVD) and
  SystemVerilog assertions (reset / RO / W1C / reserved / address-range) from
  it, and check RTL vs. register map consistency. Use when the user adds or
  modifies register definitions, asks for register docs/assertions, or wants
  RTL-to-register-map consistency checks. 触发词: "regmap", "寄存器映射",
  "寄存器地址表", "寄存器一致性", "生成寄存器文档", "生成寄存器断言".
  Do not use for bus-protocol VIP development or full UVM RAL model generation.
---

# Regmap Pipeline

核心思想：每个模块的 `regmap.md` 是寄存器定义的**单一事实源**，文档、SVA 断言、RTL 比对全部从它派生，禁止多头手工维护。

## Runtime Compatibility

运行脚本或读取 reference 之前，先把本 `SKILL.md` 所在目录解析为 `SKILL_ROOT`（Kimi Code / Claude Code 中使用 skill 加载信息给出的绝对路径；Claude Code 可用 `${CLAUDE_SKILL_DIR}`）。下文命令块各自设置 `SKILL_ROOT`，不要依赖前一次 shell 调用留下的变量。

脚本为纯 Python 3 标准库实现（`argparse/re/pathlib/xml`），无第三方依赖，直接 `python3` 运行即可。

## regmap.md 格式

脚本解析的格式定义见 `$SKILL_ROOT/references/regmap-format.md`（寄存器总表 + 每寄存器位域表）。字段不齐的寄存器表会导致解析遗漏，变更前先核对格式。

## Workflow A：寄存器定义变更同步

1. **先改 `regmap.md`**（新增/删除/修改字段，注明版本与日期）。
2. 再改 RTL，保持字段名、位宽、复位值与表一致。
3. 做 RTL ↔ regmap 一致性比对（Workflow D）。
4. 全部一致后，按项目自身的变更管理约定登记（changelog / commit message）。

规则：禁止只改 RTL 不改表；禁止只改表不改 RTL 后不做比对。

## Workflow B：生成寄存器文档

```bash
SKILL_ROOT="/absolute/path/to/this/skill"
python3 "$SKILL_ROOT/scripts/generate_regmap_doc.py" --regmap <regmap.md> --output <output_dir>
```

- 产物：Markdown 寄存器文档 + CMSIS-SVD 文件
- 适用于交付文档、review 附件、跨团队接口对齐

## Workflow C：生成寄存器 SVA 断言草案

```bash
SKILL_ROOT="/absolute/path/to/this/skill"
python3 "$SKILL_ROOT/scripts/generate_regmap_assertions.py" --regmap <regmap.md> --output <output.sv>
```

生成五类 SystemVerilog 断言：

| 断言类型 | 检查内容 |
| --- | --- |
| reset 值 | 复位后寄存器读出值等于表中复位值 |
| RO 保护 | 写操作不改变 RO 字段 |
| W1C | 写 1 清除、写 0 无影响 |
| reserved 位 | 写 reserved 位被忽略 |
| 地址范围 | 访问落在合法地址区间内 |

**产物是草案**：必须由人 review 后再接入验证环境（时钟/复位信号名、断言绑定方式需要按项目适配），不要直接合入。

## Workflow D：RTL ↔ regmap 一致性比对

无现成脚本时由 Agent 执行：

1. 从 `regmap.md` 解析：寄存器名、地址偏移、位宽、访问类型、复位值。
2. 在 RTL 中定位寄存器实现（case 译码、复位赋值、写使能逻辑），逐项比对。
3. 输出差异表：`寄存器 | 字段 | regmap 值 | RTL 值 | 差异类型`。
4. 差异修复后重新比对，直到一致。

## 硬性规则

- 修改顺序永远是：regmap.md → RTL → 比对 → 登记。
- 生成的文档/断言标注来源 regmap 文件与生成日期，便于追溯过期产物。
- 访问类型只使用表内约定值（RO / WO / RW / W1C 等），新增类型前先更新 `references/regmap-format.md`。
