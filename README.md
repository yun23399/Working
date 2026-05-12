# 多智能体编排平台

本项目是一个本地优先的多智能体编排平台。用户在网页聊天界面中与 Manager Agent 对话，系统根据需求生成工作流，并逐步驱动多个 Agent 协作完成任务。

## 当前状态

当前仓库已完成阶段一闭环，并进入阶段三的可用增量：

1. 用户注册与登录
2. JWT 鉴权与当前用户恢复
3. 创建并切换对话
4. 发送消息并通过 WebSocket 接收流式回复
5. 持久化对话与消息历史
6. 统一 LLM 适配层与 Manager Agent 普通对话
7. 最小项目分组、历史视图与项目页切换
8. 前后端真实联调验证
9. 工作流预览生成、重新规划与确认链路

当前阶段二已实现：

1. 基于对话历史提取最小结构化需求摘要
2. 生成 3 节点最小工作流 DAG 预览
3. 在聊天页展示工作流预览确认卡片
4. 支持重新规划与确认预览状态
5. 支持确认后启动最小串行执行链路
6. 支持节点状态、执行进度和交接摘要回显
7. 支持 PM / 前端 / 后端 / 测试 / 设计师预置角色模板动态选角
8. 支持在聊天页独立展示工作流实时运行日志
9. 支持为每条工作流创建共享工作区、状态快照与交接记录
10. 支持在指定节点进入断点等待，并通过控制接口恢复或改向继续执行
11. 支持节点失败后的自动重试、快照回滚、层级上报与人工恢复建议展示
12. 支持项目级记忆跨工作流沉淀长期目标、关键摘要与最近异常

当前阶段三已实现：

1. 新增最小代码执行工具 `code_executor.py`
2. 新增最小文件读写工具 `file_tool.py`
3. 新增最小外部接口调用工具 `api_caller.py`
4. 当前仅允许在共享工作区内执行受限 `python` / `node` 命令
5. 工具执行结果会写入工作区 `artifacts/code_execution_result.json`
6. 角色模板命中 `file_tool` 时，会在共享工作区真实生成 `.md` 摘要产物
7. 后端模板命中 `api_caller` 时，会在共享工作区真实生成 `api_response.json`
8. 后端或前端模板命中 `code_executor` 时，会在共享工作区真实生成计划产物
9. 当前接口返回的 `workspace.artifacts` 会同步包含执行结果文件和真实业务产物
10. 前端与测试模板命中 `browser_tool` 时，会在共享工作区真实生成页面截图和浏览器访问元数据
11. 设计师模板命中 `image_tool` 时，会在共享工作区真实生成设计概念图和图像结果元数据
12. 新增受保护工作流产物接口，可按工作流读取产物列表与单个文件内容
13. 聊天页新增产物预览面板，支持代码、文档、图片三类真实产物预览

当前下一步目标：

1. 补齐产出物导出链路
2. 继续增强工具执行上下文、权限边界与验收展示
3. 补齐工作流 Token 用量展示
4. 在具备有效图像模型 Key 的环境下补充真实 AI 出图回归

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

如需使用本地 Ollama，建议额外配置：

```powershell
$env:LLM_PROVIDER='ollama'
$env:LLM_MODEL='qwen2.5-coder:3b'
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

如果 `8000` 或 `5173` 已被占用，请切换端口，并同步调整：

- 后端 `APP_PORT`
- 根目录 `.env` 中的 `VITE_API_BASE_URL`
- 后端 `CORS_ALLOW_ORIGINS`

## 目录说明

```text
frontend/   前端应用
backend/    FastAPI + SQLAlchemy + Alembic 后端
docs/       接口、流程、部署、前端规格文档
.github/    CI 工作流
```

完整职责边界见 [多智能体平台_完整架构与开发文档.md](./多智能体平台_完整架构与开发文档.md)。

## 运行时目录

- `workspace/`：工作流共享工作区根目录
- `workspace/projects/conversation_<id>/workflow_<id>/`：单条工作流的运行目录
- `workspace/projects/conversation_<id>/project_memory.json`：同一对话下共享的项目级记忆文件
- `artifacts/code_execution_result.json`：代码执行工具的命令、退出码和标准输出记录
- `artifacts/pm_summary.md` / `backend_summary.md` / `frontend_summary.md`：文件工具生成的角色摘要产物
- `artifacts/api_response.json`：外部接口调用工具记录的请求地址、状态码和响应体
- `artifacts/backend_plan.json` / `artifacts/frontend_plan.json`：当前最小工具链路生成的计划产物
- `artifacts/frontend_snapshot.png` / `artifacts/qa_snapshot.png`：浏览器工具生成的页面截图
- `artifacts/frontend_browser_result.json` / `artifacts/qa_browser_result.json`：浏览器工具记录的访问结果元数据
- `artifacts/design_mockup.png`：图像工具生成的设计概念图或本地占位图
- `artifacts/design_image_result.json`：图像工具记录的生成来源、提示词和输出参数
- `context/workspace_state.json`：当前工作区状态快照
- `context/handoff_log.json`：节点间交接记录
- `workflow_runs`：工作流运行快照、控制信号与断点状态表
- `workflow_runs.checkpoint_json.error_report`：节点失败报告、回滚位置与恢复建议

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

说明：

- `LLM_PROVIDER=auto` 时，后端会优先使用已配置的云模型 Key，否则回退到本地 Ollama
- `LLM_MODEL` 留空时，会按当前提供商选择默认模型
- `OPENAI_API_KEY` 已配置时，`image_tool` 会优先调用 OpenAI 图像接口；未配置时会回退到本地占位图渲染链路
