# {PROJECT_NAME} 项目指南

## 1. 项目概述

这是一个全栈项目（前端 + 后端），位于 `{PROJECT_PATH}`。

请在此处补充：
- 项目目标和核心功能
- 目标用户
- 部署方式

## 2. 技术栈

### 后端
- 语言/框架：TODO（如 Python + FastAPI / Node + Express / Java + Spring Boot）
- 数据库：TODO（如有）

### 前端
- 框架：TODO（如 React / Vue / Next.js / Nuxt）
- 构建工具：TODO（如 Vite / Webpack）

## 3. 目录结构

```
{PROJECT_NAME}/
├── .kimi/
│   └── AGENTS.md          # Agent 工作偏好
├── backend/               # 后端服务
├── frontend/              # 前端应用
├── docs/                  # 文档
├── tests/                 # 测试
└── README.md
```

## 4. AI 必须遵守的规则

1. **先读上下文**：每次对话开始时，先读取当前目录及子目录中的 `AGENTS.md`。
2. **前后端隔离**：修改后端代码时遵循后端规范，修改前端代码时遵循前端规范。
3. **接口同步**：前后端接口变更必须同步更新 `docs/api.md`。
4. **变更同步**：
   - 修改 API → 更新 `docs/api.md`
   - 修改数据库模型 → 更新 `docs/schema.md`（如存在）
   - 修改构建/运行方式 → 更新 `README.md`
   - 新增功能 → 补充 `tests/`
5. **禁止行为**：未经用户同意，不得删除、重命名或移动 `AGENTS.md` 文件。
6. **完成汇报**：每次修改后，向用户简要说明变更摘要。

## 5. 核心文件维护责任

| 文件/目录 | 维护时机 |
|----------|---------|
| `README.md` | 项目结构、运行方式、主要功能变更 |
| `docs/api.md` | 前后端接口变更 |
| `docs/schema.md` | 数据库模型变更 |
| `backend/AGENTS.md` | 后端规范变化 |
| `frontend/AGENTS.md` | 前端规范变化 |
| `tests/` | 新增或修改功能时 |
| `.kimi/AGENTS.md` | Agent 工作偏好变化时 |

## 6. 常见任务

- 启动后端：TODO（请补充）
- 启动前端：TODO（如 `npm run dev`）
- 运行测试：TODO（请补充）
- 构建部署：TODO（请补充）
