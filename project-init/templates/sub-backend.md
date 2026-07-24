# Backend 模块指南

## 1. 模块概述

本目录存放后端服务相关代码。

## 2. 技术栈

- 语言/框架：TODO（如 Python + FastAPI / Node + Express / Java + Spring Boot）
- 数据库：TODO
- 缓存/消息队列：TODO（如有）

## 3. AI 规则

1. 修改本目录下文件前，先阅读本文件和根目录 `AGENTS.md`。
2. 所有新增 API 必须补充文档和测试。
3. 数据库模型变更必须同步生成迁移/更新 schema 文档。
4. 保持后端代码风格一致。

## 4. 维护责任

| 文件/目录 | 维护时机 |
|----------|---------|
| `docs/api.md` | 新增/修改接口 |
| `docs/schema.md` | 数据库模型变更 |
| `tests/` | 新增或修改功能时 |
