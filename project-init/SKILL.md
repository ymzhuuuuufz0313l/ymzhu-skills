---
name: project-init
description: Initialize a complete AGENTS.md project context system for a newly opened empty folder. Detect project type, generate root AGENTS.md, .kimi/AGENTS.md, submodule AGENTS.md files, and README.md based on templates. Trigger when user says "初始化项目文档", "init project", "create AGENTS.md", "初始化 AGENTS.md", or confirms initialization after the global AGENTS.md prompt.
---

# Project Init Skill

## Trigger

以下情况触发本 Skill：
- 用户说："初始化项目文档"、"init project"、"create AGENTS.md"、"初始化 AGENTS.md"
- 用户在全局 AGENTS.md 提示后确认："是"、"好"、"初始化"、"可以"
- 用户明确表达希望为一空文件夹生成项目上下文文档

## Workflow

### 步骤 1：扫描当前目录

使用 `Shell` 或 `Glob` 获取当前目录结构：
- 一级子目录列表
- 标志性配置文件（如 `package.json`、`pyproject.toml`、`requirements.txt`、`*.v`、`*.sv`、`Makefile` 等）
- 是否已存在 `README.md` 或 `AGENTS.md`

### 步骤 2：检测项目类型

根据目录名、子目录结构和标志性文件判断项目类型（按优先级）：

| 优先级 | 检测条件 | 项目类型 |
|-------|---------|---------|
| 1 | 目录下同时存在两类及以上以下子目录：hdl 类、`test` 类、`markdown` 类 | `project-subdir` |
| 2 | 目录名为 `case` / `cases` / `test` / `tests` / `tb` / `verification` / `sim`，或目录名包含 `DV_` / `_case` / `_cases` / `_test` / `_tests` / `-case` / `-test` | `case` |
| 3 | 目录名为 `HDL` / `hdl` / `rtl` / `RTL` / `design` / `DESIGN`，或目录内以 `*.v` / `*.sv` / `*.vhd` 为主且**不含** testbench/case 特征文件 | `hdl` |

其中：
- **hdl 类子目录**：`hdl/`、`HDL/`、`rtl/`、`RTL/`、`design/`、`design_src/`
- **test 类子目录**：`test/`、`tests/`、`case/`、`cases/`、`tb/`、`verification/`、`sim/`、`DV_*`
- **markdown 类子目录**：`markdown/`、`md/`、`docs/`、`doc/`、`analysis/`

**testbench/case 特征文件**包括：
- `tb/` 子目录
- `tests/` 子目录
- `agents/`、`vseq/`、`regression/` 等 UVM 验证子目录
- `*_case*` / `*_tc*` / `*_tb*` 文件（如 `chip_tb_top.sv`、`t_8b1lane.sv`）
- `case_list.txt`、`*_cases.sh`、`*_case.py` 等脚本
- 大量 `frame_*.ppm` 图像文件

> `project-subdir` 用于你常见的"一个路径下包含 hdl / test / markdown 三类文件夹"的工作模式。
| 3 | 同时存在 Node 标志 **和** Python 标志 | `fullstack` |
| 4 | 存在 `package.json` / `vite.config.*` / `next.config.*` / `vue.config.*` / `nuxt.config.*` | `node` |
| 5 | 存在 `pyproject.toml` / `requirements.txt` / `setup.py` / `setup.cfg` / `Pipfile` | `python` |
| 6 | 存在大量 `*.v` / `*.sv` / `*.vhd` 或含 `iverilog` / `vcs` / `verilator` 的 Makefile | `verilog` |
| 7 | 以上皆无 | `generic` |

其中：
- Node 标志：`package.json`、`vite.config.*`、`next.config.*`、`vue.config.*`、`nuxt.config.*`、`pnpm-lock.yaml`、`yarn.lock`
- Python 标志：`pyproject.toml`、`requirements.txt`、`setup.py`、`setup.cfg`、`Pipfile`

如果当前目录为空，默认使用 `generic`。

> 对于 HDL 和 case 目录，通常直接以该目录作为工作目录打开，因此生成的 `AGENTS.md` 是**根级**的，不再是子模块级。

### 步骤 3：生成根目录 `AGENTS.md`

根据项目类型选择模板：
- `project-subdir` → `templates/root-project-subdir.md`
- `hdl` → `templates/root-hdl.md`
- `case` → `templates/root-case.md`
- `generic` → `templates/root-generic.md`
- `python` → `templates/root-python.md`
- `node` → `templates/root-node.md`
- `fullstack` → `templates/root-fullstack.md`
- `verilog` → `templates/root-verilog.md`

写入当前工作目录：`{cwd}/AGENTS.md`

### 步骤 4：生成子模块 `AGENTS.md`（可选）

如果检测到对应子目录存在，且**用户明确要求**，生成：

**通用子模块**：
- `backend/AGENTS.md` → `templates/sub-backend.md`
- `frontend/AGENTS.md` → `templates/sub-frontend.md`
- `docs/AGENTS.md` → `templates/sub-docs.md`
- `tests/AGENTS.md` → `templates/sub-tests.md`

**芯片设计验证子模块（project-subdir 类型）**：
- `hdl/AGENTS.md` → `templates/sub-hdl.md`
- `test/AGENTS.md` → `templates/sub-test.md`
- `markdown/AGENTS.md` → `templates/sub-markdown.md`

**默认行为**：project-subdir 类型只生成根目录 `AGENTS.md`，不自动为 `hdl/`、`test/`、`markdown/` 子目录生成 `AGENTS.md`。如果用户后续说"为 hdl 子目录生成 AGENTS.md"或"子目录也需要规则"，再单独生成。

### 步骤 5：生成 `README.md`

如果当前目录不存在 `README.md`，使用 `templates/readme-generic.md` 生成一个基础版本。

### 步骤 6：汇报

向用户列出所有创建/更新的文件，并说明：
- 判断的项目类型及依据；
- 生成的文件清单；
- 后续维护 AGENTS.md 的注意事项。

## 输出格式

```markdown
已为您初始化项目上下文文档：

- 项目类型：{type}
- 依据：{reason}

创建的文件：
1. `{cwd}/AGENTS.md`
2. `{cwd}/README.md`
3. 根据子目录生成的子模块 `AGENTS.md`（如存在）

后续建议：
- 请根据实际项目情况补充 `AGENTS.md` 中的技术栈和目录结构。
- 每次修改核心文件、接口、构建方式时，同步更新对应 `AGENTS.md`。
```

## 持续维护规则（初始化之后）

`project-init` 不仅用于首次创建，还应在后续对话中指导 AI 维护这些 `AGENTS.md`：

1. **每次修改前先读**：修改当前目录下任何 RTL / testbench / case 文件前，先读取当前目录的 `AGENTS.md`。
2. **变更同步**：
   - HDL 目录中新增/删除/修改 `.v` / `.sv` 文件 → 更新 `AGENTS.md` 的"目录结构"和"接口说明"
   - HDL 目录中修改端口、位宽、状态机 → 更新"接口说明"和"状态机/关键逻辑"
   - case 目录中新增/删除 case → 更新"用例列表"和 `case_list` / 验证计划表
   - case 目录中修改公共 testbench / checker → 更新"验证环境说明"
3. **自动扫描更新**：当用户要求"整理文档"、"更新 AGENTS.md"、"同步 case 列表"等时，重新扫描当前目录内容，用实际文件更新 `AGENTS.md` 中的表格和列表。
4. **不覆盖用户手写内容**：更新时只替换模板化章节，保留用户在 TODO 区域填写的实际内容。

## 注意事项

- 不要覆盖已存在的 `AGENTS.md` 或 `README.md`，除非用户明确要求。
- 生成内容时，用实际扫描到的目录名和文件名替换模板中的占位符。
- 如果当前目录不是项目目录（如用户主目录、系统根目录），拒绝执行并提示用户切换到正确目录。
