# 多智能体编排平台

本项目是一个本地优先的多智能体编排平台。用户在网页聊天界面中与 Manager Agent 对话，系统根据需求生成工作流，并驱动多个 Agent 协作完成任务。

## 当前状态

当前仓库处于阶段一准备期，重点目标是先落地真实前后端工程，并打通最小可运行闭环：

1. 用户注册与登录
2. 创建并进入对话
3. 发送消息
4. 通过 WebSocket 接收流式回复
5. 持久化历史消息

当前仓库已具备：

- 规范文件：`AGENTS.md`
- 进度文件：`PROGRESS.md`
- 架构文档：`多智能体平台_完整架构与开发文档.md`
- 开发引导：`Codex_完整开发引导Prompt.md`
- 界面参考：`multi_agent_platform_ui_demo.html`
- 项目文档目录：`docs/`

## 目标架构

### 前端

- React 18
- TypeScript 5
- Vite 5
- TailwindCSS 3
- Zustand 4
- React Query 5
- Framer Motion 11
- i18next

### 后端

- Python 3.11+
- FastAPI
- SQLAlchemy 2
- Pydantic 2
- Alembic
- LiteLLM
- Playwright
- loguru

## 计划目录结构

```text
frontend/
backend/
docs/
.github/workflows/
workspace/
logs/
```

完整结构与职责边界见 [多智能体平台_完整架构与开发文档.md](./多智能体平台_完整架构与开发文档.md)。

## 文档导航

- 开发规范：[`AGENTS.md`](./AGENTS.md)
- 开发进度：[`PROGRESS.md`](./PROGRESS.md)
- 架构总览：[`多智能体平台_完整架构与开发文档.md`](./多智能体平台_完整架构与开发文档.md)
- 开发驱动 Prompt：[`Codex_完整开发引导Prompt.md`](./Codex_完整开发引导Prompt.md)
- API 契约：[`docs/api-reference.md`](./docs/api-reference.md)
- WebSocket 协议：[`docs/websocket-protocol.md`](./docs/websocket-protocol.md)
- 产品流程：[`docs/product-flow.md`](./docs/product-flow.md)
- 测试与验收：[`docs/testing-and-acceptance.md`](./docs/testing-and-acceptance.md)
- 部署说明：[`docs/deployment.md`](./docs/deployment.md)

## 环境变量

请参考 [`.env.example`](./.env.example)。

## Git 与分支约定

- 默认开发分支：`dev`
- 禁止直接在 `main` 分支提交业务开发
- 本地任务完成后，应推送到 GitHub 远程仓库备份

## GitHub 上传准备

当前仓库将按以下顺序准备上传：

1. 初始化本地 Git 仓库
2. 创建并切换到 `dev` 分支
3. 提交当前文档与基础文件
4. 绑定 GitHub 远程仓库
5. 推送到 `origin/dev`

若后续需要创建远程仓库或直接推送，请补充远程仓库地址，或允许使用已认证的 GitHub CLI。
