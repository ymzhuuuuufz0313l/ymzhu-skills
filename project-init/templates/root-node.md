# {PROJECT_NAME} 项目指南

## 1. 项目概述

这是一个 Node.js / 前端项目，位于 `{PROJECT_PATH}`。

请在此处补充：
- 项目目标和核心功能
- 目标用户
- 部署方式

## 2. 技术栈

- 运行时：Node.js
- 包管理器：TODO（npm / yarn / pnpm）
- 前端框架：TODO（如 React / Vue / Next.js / Nuxt，无则删除）
- 构建工具：TODO（如 Vite / Webpack / Rollup）
- 测试框架：TODO（如 Jest / Vitest / Playwright）

## 3. 目录结构

```
{PROJECT_NAME}/
├── .kimi/
│   └── AGENTS.md          # Agent 工作偏好
├── src/                   # 源代码
├── public/                # 静态资源
├── tests/                 # 测试
├── docs/                  # 文档
├── package.json
└── README.md
```

## 4. AI 必须遵守的规则

1. **先读上下文**：每次对话开始时，先读取当前目录及子目录中的 `AGENTS.md`。
2. **保持前端风格**：遵循项目已有的 ESLint / Prettier 配置，使用 2 空格缩进（如配置未指定）。
3. **依赖管理**：新增第三方依赖前，必须征得用户同意，并更新 `package.json`。
4. **变更同步**：
   - 修改 API 接口 → 更新 `docs/api.md`（如存在）
   - 修改构建/运行脚本 → 更新 `README.md`
   - 新增组件/页面 → 补充对应文档或测试
5. **禁止行为**：未经用户同意，不得删除、重命名或移动 `AGENTS.md` 文件。
6. **完成汇报**：每次修改后，向用户简要说明变更摘要。

## 5. 核心文件维护责任

| 文件/目录 | 维护时机 |
|----------|---------|
| `README.md` | 项目结构、运行方式、主要功能变更 |
| `package.json` | 依赖、脚本变化 |
| `docs/api.md` | 后端接口或前端数据流变更 |
| `tests/` | 新增或修改功能时 |
| `.kimi/AGENTS.md` | Agent 工作偏好变化时 |

## 6. 常见任务

- 安装依赖：`npm install` / `yarn` / `pnpm install`
- 启动开发服务器：`npm run dev`
- 构建项目：`npm run build`
- 运行测试：`npm run test`
