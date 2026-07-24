# {PROJECT_NAME} 项目指南

## 1. 项目概述

这是一个 Verilog / 数字 IC 设计验证项目，位于 `{PROJECT_PATH}`。

请在此处补充：
- 模块功能和目标芯片/平台
- 设计规格和接口协议
- 验证策略

## 2. 技术栈

- 设计语言：Verilog / SystemVerilog
- 仿真工具：TODO（如 VCS / Verilator / Icarus Verilog / ModelSim）
- 综合工具：TODO（如 DC / Yosys / Genus）
- 版本控制：TODO（如 SVN / Git）

## 3. 目录结构

```
{PROJECT_NAME}/
├── .kimi/
│   └── AGENTS.md          # Agent 工作偏好
├── rtl/                   # 设计源码
├── tb/                    # 测试平台
├── sim/                   # 仿真脚本
├── docs/                  # 文档
├── tests/                 # 测试用例 / case 列表
└── README.md
```

## 4. AI 必须遵守的规则

1. **先读上下文**：每次对话开始时，先读取当前目录及子目录中的 `AGENTS.md`。
2. **保持 RTL 风格**：遵循项目已有的命名规范、时钟/复位处理方式和代码结构。
3. **变更同步**：
   - 修改接口/信号 → 更新接口文档和波形说明
   - 修改状态机 → 更新状态机文档
   - 新增/修改寄存器 → 更新寄存器表
   - 修改仿真/综合流程 → 更新 `README.md`
4. **禁止行为**：未经用户同意，不得删除、重命名或移动 `AGENTS.md` 文件。
5. **完成汇报**：每次修改后，向用户简要说明变更摘要。

## 5. 核心文件维护责任

| 文件/目录 | 维护时机 |
|----------|---------|
| `README.md` | 项目结构、仿真/综合方式、主要功能变更 |
| `docs/` | 接口、状态机、寄存器、时序变更 |
| `rtl/` | 设计源码变更 |
| `tb/` | 测试平台变更 |
| `tests/` | 测试用例新增或修改 |
| `.kimi/AGENTS.md` | Agent 工作偏好变化时 |

## 6. 常见任务

- 运行仿真：TODO（请补充，如 `make sim` / `vcs -f filelist.f`）
- 查看波形：TODO（如 `dvpv.sh` / `verdi`）
- 运行综合：TODO（请补充）
- 回归测试：TODO（请补充）
