# {PROJECT_NAME}/test 验证用例子目录指南

## 1. 子目录概述

本目录为 **验证用例（test）子目录**，属于 `{PROJECT_PATH}` 项目子模块的一部分。

## 2. 目录内容

- 测试用例文件（`*_case.sv` / `*_tc.sv` / `*_test.sv`）
- Testbench 顶层（`*_tb.sv`）
- 仿真脚本/ Makefile
- Case 列表或验证计划表（`case_list.txt`）

## 3. AI 规则

1. 修改本目录下文件前，先阅读本文件和父目录 `AGENTS.md`。
2. 保持 testbench / case 风格一致。
3. 新增/删除/重命名 case 时，同步更新 `case_list.txt`。
4. 修改公共 testbench / checker 时，同步更新父目录 `AGENTS.md` 中的验证环境说明。
5. 每次修改后，变更记录统一写入**父目录根级的 `CHANGES.md`**。
6. 不在本地跑仿真，只进行代码可靠性检查。

## 4. 维护责任

| 文件/目录 | 维护时机 |
|----------|---------|
| 父目录 `AGENTS.md` | 用例列表、验证环境说明变更 |
| 父目录 `CHANGES.md` | 每次文件修改后 |
| `case_list.txt` | 用例新增/删除/重命名 |
| `markdown/*.md` | 验证计划文档变更 |
