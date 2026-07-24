# {PROJECT_NAME} 验证用例目录指南

## 1. 目录概述

本目录为 **验证用例（case）目录**，位于 `{PROJECT_PATH}`。

请在此处补充：
- 本目录验证的模块或功能（如 TCON、LVDS、OTP、DRD/OD、HDMI-RX 等）
- 所属项目/芯片（如 HK1V11、HV2M23 等）
- 验证策略（UVM 仿真 / Python 脚本驱动 / 图像 PPM 对比 / FPGA）
- 负责人或验证计划链接

## 2. 目录结构

本目录常见两种组织风格：

### 风格 A：UVM 验证环境（如 HK1V11/DV_TCON_C）

```
{PROJECT_NAME}/
├── AGENTS.md                  # 本项目上下文与 Agent 工作规则（本文件）
├── CHANGES.md                 # 变更日志
├── REVIEW.md                  # 服务器回传前检查清单（临时）
├── agents/                    # UVM agent
├── filelist/                  # 仿真文件列表（tb.f）
├── regression/                # 回归测试配置
├── tb/                        # Testbench 顶层
│   ├── base_test.sv
│   ├── chip_tb_top.sv
│   ├── intf_connect.sv
│   └── waves_dumper.sv
├── tests/                     # 测试用例
│   ├── case_list.txt
│   ├── t_8b1lane/
│   ├── t_reg_i2c_xxx/
│   └── ppm_mix_xxxx/
├── vseq/                      # Virtual sequence
├── script/                    # 运行脚本
│   ├── makefile
│   └── run_tc.sh
└── README.md
```

### 风格 B：Python 驱动验证环境（如 HV2M23/tests）

```
{PROJECT_NAME}/
├── AGENTS.md                  # 本项目上下文与 Agent 工作规则（本文件）
├── CHANGES.md                 # 变更日志
├── REVIEW.md                  # 服务器回传前检查清单（临时）
├── create_*.py                # case 生成脚本
├── regression.py              # 回归脚本
├── run_parallel.py            # 并行运行脚本
├── run_case.py                # 单 case 运行脚本
├── setup_drd_ppms.py          # PPM 部署脚本
├── ppm_drd/                   # 共享 PPM 图像池
│   ├── solid_255_0_0/
│   ├── solid_0_255_0/
│   └── ...
├── t_8b2lane_DRD_xxx/         # 单个 case 目录
│   ├── cfg_frame0.txt
│   ├── ppm_ref.txt
│   ├── t_8b2lane_DRD_xxx.sv
│   ├── test.f
│   ├── user_def.sv
│   └── waves_dumper.sv
└── README.md
```

实际项目可能是以上两种风格的混合。

## 3. AI 必须遵守的规则

### 3.1 通用规则

1. **先读上下文**：每次对话开始时，先读取本目录中的 `AGENTS.md` 和 `CHANGES.md`。
2. **只改代码，不跑仿真**：本项目不在本地运行 case 仿真。AI 修改代码后，重点进行代码可靠性检查（语法、风格、case 结构一致性、检查器逻辑正确性）。
3. **严格记录变更**：每次文件修改必须记录到 `CHANGES.md`，包括文件路径、修改类型、行号范围、修改摘要。
4. **服务器回传前 review**：当用户要求"准备回传服务器"时，生成 `REVIEW.md`，列出所有变更、关联文件和肉眼检查建议。
5. **禁止行为**：未经用户同意，不得删除、重命名或移动 `AGENTS.md`、`CHANGES.md` 文件。
6. **完成汇报**：每次修改后，向用户简要说明变更摘要。

### 3.2 Case 修改规则

1. **Case 风格一致**：遵循项目已有 testbench 架构、激励生成方式、检查机制和命名规范。
2. **Case 列表同步**：
   - 新增 case 目录 → 更新本文件"用例列表"，并同步更新 `case_list.txt` / 验证计划表
   - 删除 case 目录 → 从 case 列表中移除
   - 重命名 case → 同步更新所有引用（case_list、回归脚本、文档）
3. **UVM 环境维护**：
   - 新增/修改 agent → 更新 `agents/` 说明和 `tb/` 中的连接
   - 修改公共 testbench / checker → 更新"验证环境说明"
   - 修改 filelist → 同步更新 `filelist/tb.f`
4. **Python 环境维护**：
   - 新增/修改 `.py` 生成脚本 → 更新脚本说明和运行方式
   - 新增/删除 PPM 池 → 更新 `DRD_PPM_SETUP.md` 或等效说明
   - 修改回归逻辑 → 更新回归命令说明
5. **修改记录**：重大环境调整应同步到项目 `修改记录` 或 `changelist` 文档。

## 4. 核心文件维护责任

| 文件/目录 | 维护时机 |
|----------|---------|
| `AGENTS.md` | 目录结构、用例列表、环境说明、工作流规则变更 |
| `CHANGES.md` | 每次文件修改后 |
| `REVIEW.md` | 服务器回传前（临时文件，可覆盖） |
| `README.md` | 运行方式、环境配置变更 |
| `case_list.txt` / `*.xlsx` | 新增/删除/修改用例 |
| `filelist/tb.f` | UVM 仿真文件列表变更 |
| `script/makefile`、`script/run_tc.sh` | 运行命令、编译选项变更 |
| `tb/` 公共 testbench / checker | 环境架构或检查逻辑变更 |
| `agents/` | UVM agent 新增/修改 |
| `create_*.py`、`regression.py`、`run_parallel.py` | Python 脚本逻辑变更 |
| `ppm_drd/` 等共享资源 | PPM 池变更 |
| `修改记录/` 或 `changelist` | 重大环境/用例调整 |

## 5. 用例列表

TODO：请在此处列出本目录的主要用例、目标覆盖点和当前状态。

| 用例名 | 测试目标 | 覆盖点 | 状态 |
|-------|---------|--------|------|
| TODO  | TODO    | TODO   | TODO |

## 6. 验证环境说明

TODO：请说明 testbench 结构、激励来源、参考模型、检查器和覆盖率收集方式。

### UVM 环境
- Agent 列表：TODO
- Scoreboard/Checker：TODO
- Virtual Sequence：TODO
- 覆盖率收集：TODO

### Python 驱动环境
- case 生成脚本：TODO
- 并行运行方式：TODO
- 结果检查方式：TODO
- PPM 引用方式：TODO

## 7. 工作流偏好

TODO：在此处补充你个人或本项目的工作流偏好。例如：

- 修改 case 后只做代码检查，不跑本地仿真
- 每次修改必须记录到 CHANGES.md
- 回传服务器前必须生成 REVIEW.md
- 使用中文回复
- 修改前优先进入 Plan Mode

## 8. 常见任务

- 查看 case 列表：`cat case_list.txt` 或打开 `*.xlsx`
- 查看变更日志：`cat CHANGES.md`
- 生成回传清单：`@workflow-maintainer 准备回传服务器`
- 运行单个 UVM case：TODO（如 `make run_tc TC=t_8b1lane` / `./script/run_tc.sh t_8b1lane`）
- 运行单个 Python case：TODO（如 `python run_case.py --case t_8b2lane_DRD_xxx`）
- 运行回归：TODO（如 `make regression` / `python regression.py`）
- 查看波形：TODO（如 `dvpv.sh` / `verdi`）
- 查看覆盖率：TODO（如 `urg` / `verdi -cov`）
- 生成新 case：TODO（如 `./create_new_case.sh <case_name>` / `python create_drd_case.py`）
