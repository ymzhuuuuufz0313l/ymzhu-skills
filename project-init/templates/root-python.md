# {PROJECT_NAME} 项目指南

## 1. 项目概述

这是一个 Python 项目，位于 `{PROJECT_PATH}`。

请在此处补充：
- 项目目标和核心功能
- 目标用户
- 部署方式

## 2. 技术栈

- 语言：Python 3.x
- 包管理：TODO（pip / poetry / pdm / conda）
- Web 框架：TODO（如 FastAPI / Flask / Django，无则删除）
- 数据库：TODO（如 PostgreSQL / MySQL / SQLite，无则删除）
- 测试框架：pytest

## 3. 目录结构

```
{PROJECT_NAME}/
├── .kimi/
│   └── AGENTS.md          # Agent 工作偏好
├── src/ 或 {package_name}/ # 源代码
├── tests/                 # 测试
├── docs/                  # 文档
├── pyproject.toml / requirements.txt
└── README.md
```

## 4. AI 必须遵守的规则

1. **先读上下文**：每次对话开始时，先读取当前目录及子目录中的 `AGENTS.md`。
2. **保持 Pythonic 风格**：遵循 PEP 8，使用 4 空格缩进，函数名使用 `snake_case`，类名使用 `PascalCase`。
3. **依赖管理**：新增第三方依赖前，必须征得用户同意，并更新 `pyproject.toml` 或 `requirements.txt`。
4. **变更同步**：
   - 修改数据库模型 → 生成迁移并更新 `docs/schema.md`（如存在）
   - 修改 API → 更新 `docs/api.md`（如存在）
   - 修改运行/构建方式 → 更新 `README.md`
   - 新增功能 → 补充 `tests/`
5. **禁止行为**：未经用户同意，不得删除、重命名或移动 `AGENTS.md` 文件。
6. **完成汇报**：每次修改后，向用户简要说明变更摘要。

## 5. 核心文件维护责任

| 文件/目录 | 维护时机 |
|----------|---------|
| `README.md` | 项目结构、运行方式、主要功能变更 |
| `pyproject.toml` / `requirements.txt` | 依赖变化 |
| `docs/api.md` | API 变更 |
| `docs/schema.md` | 数据库模型变更 |
| `tests/` | 新增或修改功能时 |
| `.kimi/AGENTS.md` | Agent 工作偏好变化时 |

## 6. 常见任务

- 安装依赖：`pip install -r requirements.txt` 或 `poetry install`
- 运行测试：`pytest tests/`
- 启动服务：TODO（请补充，如 `python -m src.main`）
- 生成迁移：`alembic revision --autogenerate -m "msg"`（如使用 Alembic）
