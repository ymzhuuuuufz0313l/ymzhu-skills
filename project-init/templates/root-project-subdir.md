# {PROJECT_NAME} 项目子模块指南

## 1. 目录概述

本目录是一个**芯片设计验证子模块**，位于 `{PROJECT_PATH}`。

目录下包含三类核心文件夹：
- `hdl/` —— RTL 设计源码
- `test/` —— 验证用例与测试环境
- `markdown/` —— 代码分析、验证计划、设计文档等 Markdown 文档

请在此处补充：
- 本模块所属芯片/项目（如 HK1V11、HV2M23 等）
- 本模块承担的功能（如 TCON、LVDS、OTP、DRD/OD、HDMI-RX 等）
- 三类文件夹之间的协作关系
- 负责人或相关文档链接

## 2. 目录结构

```
{PROJECT_NAME}/
├── AGENTS.md                  # 子模块上下文与 Agent 工作规则（本文件）
├── CHANGES.md                 # 统一变更日志
├── REVIEW.md                  # 服务器回传前检查清单（临时）
├── hdl/                       # RTL 设计源码
│   └── *.v / *.sv
├── test/                      # 验证用例与测试环境
│   ├── case_list.txt
│   └── *_case.sv / *_tb.sv
├── markdown/                  # 代码分析、验证计划、设计文档
│   └── *.md
└── README.md                  # 本模块简介
```

> 子目录 `hdl/`、`test/`、`markdown/` 默认不单独生成 `AGENTS.md`。如后续某类文件夹规则复杂，可再单独生成。

## 3. AI 必须遵守的规则

### 3.1 通用规则

1. **先读上下文**：每次对话开始时，先读取本目录中的 `AGENTS.md` 和 `CHANGES.md`。
2. **只改代码，不跑仿真**：本项目不在本地运行 case 仿真。AI 修改代码后，重点进行代码可靠性检查（语法、风格、接口一致性、时序影响分析、case 结构一致性）。
3. **统一变更记录**：无论修改 `hdl/`、`test/` 还是 `markdown/` 下的文件，所有变更都必须汇总记录到**本目录根级的 `CHANGES.md`**。
4. **服务器回传前 review**：当用户要求"准备回传服务器"时，生成本目录根级的 `REVIEW.md`，汇总三类文件夹的所有变更。
5. **禁止行为**：未经用户同意，不得删除、重命名或移动 `AGENTS.md`、`CHANGES.md` 文件。
6. **完成汇报**：每次修改后，向用户简要说明变更摘要，包括涉及了哪类文件夹（hdl/test/markdown）。

### 3.2 三类文件夹协作规则

#### hdl/ 文件夹

- 修改 RTL 后，同步检查是否需要更新：
  - `hdl/file_list/*.f`（如存在）
  - `markdown/` 中的接口/寄存器/状态机文档
  - 上层实例化文件
- 新增/删除/重命名 `.v` / `.sv` 文件时，同步更新文件列表。
- 修改端口、位宽、状态机时，同步更新接口说明文档。
- 若将来 `hdl/` 规则复杂，可单独生成 `hdl/AGENTS.md`。

#### test/ 文件夹

- 新增/删除/修改 case 时，同步检查是否需要更新：
  - `test/case_list.txt` 或等效验证计划表
  - `markdown/` 中的验证计划文档
  - 公共 testbench / checker
- 修改 UVM 环境或 Python 脚本时，同步更新验证环境说明。
- 若将来 `test/` 规则复杂，可单独生成 `test/AGENTS.md`。

#### markdown/ 文件夹

- 修改代码后，若相关分析文档、验证计划、接口说明在 `markdown/` 中有描述，必须同步更新。
- 新增分析文档时，在本文件"文档索引"章节补充说明。
- 若将来 `markdown/` 规则复杂，可单独生成 `markdown/AGENTS.md`。

## 4. 核心文件维护责任

| 文件/目录 | 维护时机 |
|----------|---------|
| `AGENTS.md` | 目录结构、功能、协作关系、工作流规则变更 |
| `CHANGES.md` | 每次修改 hdl/test/markdown 中任何文件后 |
| `REVIEW.md` | 服务器回传前（临时文件，可覆盖） |
| `README.md` | 模块简介、运行方式变更 |
| `hdl/AGENTS.md` | HDL 子目录规则变更（如存在） |
| `test/AGENTS.md` | test 子目录规则变更（如存在） |
| `markdown/AGENTS.md` | markdown 子目录规则变更（如存在） |
| `hdl/file_list/*.f` | hdl 源文件新增/删除/重命名 |
| `test/case_list.txt` | test 用例新增/删除/重命名 |
| `markdown/*.md` | 分析结论、验证计划、接口说明变更 |

## 5. 文档索引

TODO：请列出 `markdown/` 中的重要文档及其用途。

| 文档路径 | 用途 | 维护时机 |
|---------|------|---------|
| `markdown/TODO.md` | TODO | TODO |

## 6. 接口/关键设计说明

TODO：在此处补充本模块的关键接口、寄存器、状态机说明。可引用 `markdown/` 中的详细文档。

| 项目 | 说明 | 对应文档 |
|-----|------|---------|
| 关键接口 | TODO | `markdown/TODO.md` |
| 关键寄存器 | TODO | `markdown/TODO.md` |
| 状态机 | TODO | `markdown/TODO.md` |

## 7. 工作流偏好

TODO：在此处补充你个人或本项目的工作流偏好。例如：

- 修改顺序：先改 `hdl/`，再同步改 `test/` 和 `markdown/`
- 只改代码，不跑仿真
- 每次修改必须记录到根目录 `CHANGES.md`
- 回传服务器前必须生成根目录 `REVIEW.md`
- 使用中文回复
- 修改前优先进入 Plan Mode

## 8. 常见任务

- 查看变更日志：`cat CHANGES.md`
- 生成回传清单：`@workflow-maintainer 准备回传服务器`
- 查看 hdl 文件列表：`cat hdl/file_list/*.f`
- 查看 test case 列表：`cat test/case_list.txt`
- 查看分析文档：`ls markdown/`
- 统计 RTL 规模：`find hdl/ -name "*.v" -o -name "*.sv" | wc -l`
