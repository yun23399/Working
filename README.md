# 多智能体编排平台

本项目是一个本地优先的多智能体编排平台。用户在网页聊天界面中与 Manager Agent 对话，系统根据需求生成工作流，并逐步驱动多个 Agent 协作完成任务。

## 当前状态

当前仓库已完成阶段一的最小闭环：

1. 用户注册与登录
2. JWT 鉴权与当前用户恢复
3. 创建并切换对话
4. 发送消息并通过 WebSocket 接收流式回复
5. 持久化对话与消息历史
6. 前后端真实联调验证

当前下一步目标：

1. 接入统一 LLM 适配层
2. 将模拟流式回复替换为真实模型输出
3. 让 Manager Agent 进入真实普通对话阶段

## 技术栈

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
- Alembic
- Pydantic 2
- LiteLLM
- Playwright
- loguru

## 本地启动

### 后端

```powershell
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 前端

```powershell
cd frontend
npm install
$env:VITE_API_BASE_URL='http://127.0.0.1:8000'
npm run dev
```

如果 `8000` 或 `5173` 已被占用，请切换端口，并同步调整：

- 后端 `APP_PORT`
- 前端 `VITE_API_BASE_URL`
- 后端 `CORS_ALLOW_ORIGINS`

## 目录说明

```text
frontend/   前端应用
backend/    FastAPI + SQLAlchemy + Alembic 后端
docs/       接口、流程、部署、前端规格文档
.github/    CI 工作流
```

完整职责边界见 [多智能体平台_完整架构与开发文档.md](./多智能体平台_完整架构与开发文档.md)。

## 文档导航

- 开发规范：[`AGENTS.md`](./AGENTS.md)
- 开发进度：[`PROGRESS.md`](./PROGRESS.md)
- 架构总览：[`多智能体平台_完整架构与开发文档.md`](./多智能体平台_完整架构与开发文档.md)
- 开发引导：[`Codex_完整开发引导Prompt.md`](./Codex_完整开发引导Prompt.md)
- API 契约：[`docs/api-reference.md`](./docs/api-reference.md)
- WebSocket 协议：[`docs/websocket-protocol.md`](./docs/websocket-protocol.md)
- 产品流程：[`docs/product-flow.md`](./docs/product-flow.md)
- 测试与验收：[`docs/testing-and-acceptance.md`](./docs/testing-and-acceptance.md)
- 部署说明：[`docs/deployment.md`](./docs/deployment.md)
- 设计系统：[`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md)
- 页面结构：[`docs/PAGE_STRUCTURE.md`](./docs/PAGE_STRUCTURE.md)
- 前端规格：[`docs/FRONTEND_SPEC.md`](./docs/FRONTEND_SPEC.md)

## Git 约定

- 默认开发分支：`dev`
- 禁止直接在 `main` 分支开发
- 每次阶段性完成后都需要推送到 GitHub 远程仓库备份
- 当前远程仓库：`https://github.com/yun23399/Working.git`

## 环境变量

请参考 [`.env.example`](./.env.example)。
