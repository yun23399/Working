# PROGRESS.md — 开发进度记录

> 最后更新：2026-05-13
> 更新者：Codex（会话 #25）
> 规则：每完成一个任务更新一次；每次会话结束前必须更新一次

---

## 当前阶段

**⏳ 阶段四：完善体验（已完成系统通知最小链路，下一步继续完善多项目管理、搜索与日志体验）**

---

## 阶段总览

| 阶段 | 状态 | 说明 |
|------|------|------|
| 阶段一：基础骨架 MVP | ✅ 已完成 | 登录、对话、WebSocket、真实 LLM 普通对话、最小项目/历史视图已打通 |
| 阶段二：工作流引擎 | ✅ 已完成 | 已完成最小工作流预览、重新规划、确认、执行、结果刷新、模板、共享工作区、断点、错误恢复与项目级记忆链路 |
| 阶段三：工具集接入 | ✅ 已完成 | 已完成代码、文件、API、浏览器、图像工具、前端产物预览、导出与 Token 展示链路 |
| 阶段四：完善体验 | ⏳ 进行中 | 已完成系统通知最小链路，后续继续完善多项目管理、搜索与日志体验 |
| 阶段五：扩展能力 | ⏳ 待开始 | 持续迭代 |

---

## 阶段一：执行顺序（优化后）

### Step 0 — 仓库状态对齐
- [x] 核对 `frontend/`、`backend/`、`README.md`、`.env.example`、`.gitignore`、`.github/workflows/ci.yml` 是否在当前仓库真实存在
- [x] 若缺失，先在当前仓库落地真实目录与文件，再继续后续开发
- [x] `PROGRESS.md` 的目录快照、完成项、操作日志必须与真实仓库一致
- 验收标准：当前仓库目录结构与 `PROGRESS.md` 快照一致

### Step 1 — 工程骨架与依赖验证
- [x] 创建前端真实脚手架（Vite + React + TypeScript）
- [x] 创建后端真实骨架（FastAPI + SQLAlchemy + Alembic）
- [x] 落地 ESLint / Prettier / Husky / lint-staged / Ruff / Black / CI / `.env.example` / `.gitignore`
- [x] 执行 `npm install`、`npm run lint`、`npm run build`
- [x] 执行 `pip install -r requirements.txt`、`ruff check .`、`black --check .`、`alembic upgrade head`、`uvicorn app.main:app`
- 验收标准：前后端依赖安装、Lint、构建、迁移、启动全部通过

### Step 2 — 后端真实认证闭环
- [x] `backend/app/utils/security.py`：实现 bcrypt + JWT 工具函数
- [x] `POST /api/auth/register`：唯一校验、密码哈希、DB 持久化
- [x] `POST /api/auth/login`：密码校验、JWT 签发
- [x] `backend/app/api/deps.py`：实现 `get_current_user`
- [x] 后端错误返回统一符合 AGENTS.md 第 9 条格式
- 验收标准：注册、登录、鉴权接口可用

### Step 3 — 日志与最小对话后端闭环
- [x] `backend/app/utils/logger.py`：配置 loguru，输出控制台与 `logs/`
- [x] `backend/app/api/ws.py`：实现 WebSocket 端点与 `ConnectionManager`
- [x] 对话与消息接口最小可用，支持消息持久化
- [x] 在真实 LLM 接入前，先提供可验证的模拟流式回复
- [x] Alembic 迁移已补为真实表结构初始化，不依赖启动时自动建表
- 验收标准：后端可创建对话、保存消息、推送流式消息

### Step 4 — 前端登录与聊天最小闭环
- [x] `frontend/src/pages/Login.tsx`、`frontend/src/stores/authStore.ts`、认证 API 封装
- [x] `frontend/src/pages/Chat.tsx`、`ChatWindow.tsx`、`MessageBubble.tsx`、`StreamingText.tsx`
- [x] `frontend/src/stores/chatStore.ts`、`frontend/src/hooks/useWebSocket.ts`
- [x] 请求错误与 WebSocket 断线均有用户可见提示，自动重连最多 3 次
- [x] 浏览器实测通过 `注册 -> 进入聊天页 -> 发送消息 -> 收到流式回复`
- 验收标准：用户可登录、进入聊天页、发送消息并看到流式回复

### Step 5 — LLM 适配层
- [x] `backend/app/core/llm/adapter.py`：统一 `chat()` 接口
- [x] `backend/app/core/llm/providers.py`：读取环境变量并适配 OpenAI / Anthropic / Ollama
- [x] `backend/app/core/llm/streaming.py`：处理 token 流并推送 WebSocket
- 验收标准：可通过统一接口拿到真实模型流式输出

### Step 6 — Manager Agent 基础对话
- [x] `backend/app/core/manager/manager_agent.py`：接收用户消息并调用 LLM
- [x] `POST /api/conversations/{id}/chat`：接入真实 Manager 普通对话
- [x] 本阶段只做普通对话，不进入工作流规划
- 验收标准：Manager 可基于真实模型完成基础对话

### Step 7 — 最小项目/历史视图与阶段收尾
- [x] `frontend/src/components/layout/TopNav.tsx`、`Sidebar.tsx`、`MainArea.tsx`
- [x] `frontend/src/stores/projectStore.ts`：项目与对话列表最小读取和切换
- [x] `CHANGELOG.md` 初始化并补充当前阶段记录
- [x] 复跑阶段一全部验证命令
- 验收标准：`登录 -> 进入对话 -> 流式回复 -> 历史持久化 -> 最小列表切换` 全部跑通

---

## 阶段二：任务清单（进行中）

- [x] 需求提取器（requirement_extractor.py）
- [x] 工作流规划器（workflow_planner.py）
- [x] 工作流预览 API 与持久化（workflow.py / workflow_service.py / workflows.py）
- [x] 工作流预览确认界面（WorkflowConfirm.tsx）
- [x] DAG 编排器（dag_orchestrator.py）
- [x] Agent 生成器（agent_spawner.py）
- [x] 预置角色模板（前端/后端/测试/PM/设计师）
- [x] 共享工作区（workspace.py）
- [x] 断点控制（checkpoint.py）
- [x] 错误处理与层级上报（error_handler.py）
- [x] 工作流日志实时展示（LogViewer.tsx）
- [x] 项目级记忆（project_memory.py）

---

## 阶段三：任务清单（已完成）

- [x] 代码执行工具（code_executor.py）
- [x] 文件读写工具（file_tool.py）
- [x] 外部 API 调用工具（api_caller.py）
- [x] Playwright 浏览器自动化工具（browser_tool.py）
- [x] 图像生成工具（image_tool.py）
- [x] 代码预览组件（CodePreview.tsx）
- [x] 图片预览组件（ImagePreview.tsx）
- [x] 文档预览组件（DocumentPreview.tsx）
- [x] 产出物导出功能（file_export.py）
- [x] Token 用量展示（TokenCounter.tsx）

---

## 阶段四：任务清单（进行中）

- [x] 系统通知（notifier.py）
- [ ] 多项目管理完善
- [ ] 对话内搜索
- [ ] 用户自定义 Agent 角色管理
- [ ] Agent 配置导入/导出
- [ ] 并发工作流上限配置
- [ ] 页面过渡动效优化
- [ ] 日志面板完善（分级过滤 + 写入文件）

---

## 已完成模块

- ✅ 规范与开发引导文档 — 2026-05-12 | AGENTS.md、架构文档、开发引导 Prompt、PROGRESS.md
- ✅ UI 演示稿 — 2026-05-12 | `multi_agent_platform_ui_demo.html`
- ✅ 项目基础文档体系 — 2026-05-12 | README、API、WebSocket、产品流程、测试与部署文档
- ✅ 前端规格文档体系 — 2026-05-12 | `DESIGN_SYSTEM.md`、`PAGE_STRUCTURE.md`、`FRONTEND_SPEC.md`
- ✅ GitHub 基础文件与本地 Git 基线 — 2026-05-12 | `.env.example`、`.gitignore`、GitHub Actions、git init、dev 分支
- ✅ GitHub 远程备份 — 2026-05-12 | 已连接 `https://github.com/yun23399/Working.git` 并推送到 `origin/dev`
- ✅ 前后端真实工程骨架 — 2026-05-12 | frontend Vite/React/TS + backend FastAPI/SQLAlchemy/Alembic
- ✅ 阶段一 Step 1 基础验证 — 2026-05-12 | 前端 lint/build 与后端 ruff/black/alembic/health 通过
- ✅ 阶段一 Step 2 认证闭环 — 2026-05-12 | 注册、登录、JWT 鉴权与 `/api/auth/me` 实测通过
- ✅ 阶段一 Step 3 最小对话后端闭环 — 2026-05-12 | 对话、消息、WebSocket、最小流式回复、日志与迁移实测通过
- ✅ 阶段一 Step 4 前端最小聊天闭环 — 2026-05-12 | 登录、聊天、日志、流式回复与浏览器实测通过
- ✅ 阶段一 Step 5 LLM 适配层 — 2026-05-12 | 统一 LLM 配置、流式适配与 Ollama 原生流式兼容路径实测通过
- ✅ 阶段一 Step 6 Manager 基础对话 — 2026-05-12 | Manager 真实普通对话、消息持久化与 WebSocket 事件链实测通过
- ✅ 阶段一 Step 7 最小项目/历史视图收尾 — 2026-05-12 | 项目分组、本地历史映射、项目页切换、环境统一与浏览器回归通过
- ✅ 阶段二最小工作流预览链路 — 2026-05-12 | 需求提取、DAG 预览、重新规划、确认状态与聊天页预览卡片实测通过
- ✅ 阶段二最小工作流执行链路 — 2026-05-12 | 串行节点执行、进度回推、执行日志与节点摘要消息实测通过
- ✅ 阶段二执行结果前端刷新链路 — 2026-05-12 | 节点完成后自动回拉工作流与消息历史，执行日志和节点摘要可在前端补齐
- ✅ 阶段二预置角色模板链路 — 2026-05-12 | PM/前端/后端/测试/设计师模板已接入预览规划、执行提示词与前端展示
- ✅ 阶段二工作流日志面板链路 — 2026-05-13 | 工作流编排日志已从聊天日志拆分为独立面板，并随 WebSocket 实时回显
- ✅ 阶段二共享工作区链路 — 2026-05-13 | 工作流已具备根目录共享工作区、状态快照与节点交接记录能力
- ✅ 阶段二断点控制链路 — 2026-05-13 | 工作流已支持运行快照、等待确认、恢复执行与控制接口
- ✅ 阶段二错误恢复链路 — 2026-05-13 | 工作流已支持节点重试、失败回滚、层级上报、恢复建议与人工改向重跑
- ✅ 阶段二项目级记忆链路 — 2026-05-13 | 工作流已支持跨工作流沉淀长期目标、关键摘要与最近异常
- ✅ 阶段三代码执行工具链路 — 2026-05-13 | 工作流已支持最小受限 `python` / `node` 执行、真实计划产物落盘与产物路径回传
- ✅ 阶段三文件读写工具链路 — 2026-05-13 | 工作流已支持在共享工作区安全写入文本摘要，并将 `.md` 产物回传到执行结果
- ✅ 阶段三外部 API 调用工具链路 — 2026-05-13 | 工作流已支持受限 HTTP 调用、响应落盘与 `api_response.json` 产物回传
- ✅ 阶段三浏览器自动化工具链路 — 2026-05-13 | 工作流已支持受限页面访问、截图落盘与 `browser_result.json` / `snapshot.png` 产物回传
- ✅ 阶段三图像生成工具链路 — 2026-05-13 | 工作流已支持真实设计图落盘与 `design_image_result.json` 元数据回传，缺少 Key 时可回退本地占位图链路
- ✅ 阶段三前端产物预览链路 — 2026-05-13 | 聊天页已支持按工作流读取真实产物列表，并预览代码、文档和图片产物
- ✅ 阶段三产物导出链路 — 2026-05-13 | 后端已支持导出当前工作流真实产物 zip，聊天页可一键下载全部产物
- ✅ 阶段三 Token 用量展示链路 — 2026-05-13 | 聊天头部已通过独立 `TokenCounter` 组件展示本次会话累计 Token 数
- ✅ 阶段四系统通知链路 — 2026-05-13 | 后端已支持关键工作流状态的本地通知日志、桌面提醒与声音回退机制

---

## 当前实际目录结构快照

```text
0000001-1/
├── .env.example
├── .git/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── AGENTS.md
├── backend/
│   ├── alembic/
│   ├── alembic.ini
│   ├── app/
│   ├── pyproject.toml
│   └── requirements.txt
├── CHANGELOG.md
├── Codex_完整开发引导Prompt.md
├── docs/
│   ├── api-reference.md
│   ├── deployment.md
│   ├── DESIGN_SYSTEM.md
│   ├── FRONTEND_SPEC.md
│   ├── PAGE_STRUCTURE.md
│   ├── product-flow.md
│   ├── testing-and-acceptance.md
│   └── websocket-protocol.md
├── files.zip
├── frontend/
│   ├── package.json
│   ├── postcss.config.js
│   ├── src/
│   ├── tailwind.config.ts
│   ├── tsconfig.app.json
│   └── vite.config.ts
├── multi_agent_platform_ui_demo.html
├── PROGRESS.md
├── README.md
├── 前端.txt
└── 多智能体平台_完整架构与开发文档.md
```

---

## 操作日志

### 2026-05-12 会话 #1（原记录待核实）
- 原记录：阶段一脚手架搭建
- 复核结果：当前仓库未发现 `frontend/`、`backend/`、`README.md`、`.env.example`、`.gitignore`、`.github/` 等实体
- 处理说明：该记录不再作为当前实施依据，后续以当前仓库实际状态为准

### 2026-05-12 会话 #2
- 执行内容：重构阶段推进流程，改为“仓库状态对齐 -> 最小可运行闭环 -> 增量完善”
- 修改文件：`PROGRESS.md`、`Codex_完整开发引导Prompt.md`、`多智能体平台_完整架构与开发文档.md`
- 复核结论：
  1. 当前仓库仅包含文档与演示文件
  2. `files.zip` 仅包含文档副本，不包含前后端工程代码
  3. 后续必须从 Step 0 开始，而不是直接进入 JWT / WebSocket / LLM 实现

### 2026-05-12 会话 #3
- 执行内容：补齐完整项目所需核心文档，并准备 GitHub 上传基线
- 创建文件：
  1. `README.md`
  2. `CHANGELOG.md`
  3. `.env.example`
  4. `.gitignore`
  5. `.github/workflows/ci.yml`
  6. `docs/api-reference.md`
  7. `docs/websocket-protocol.md`
  8. `docs/product-flow.md`
  9. `docs/testing-and-acceptance.md`
  10. `docs/deployment.md`
- 执行结果：
  1. 当前仓库已初始化本地 Git 仓库
  2. 当前开发分支已切换为 `dev`
  3. 当前仍未绑定 GitHub 远程仓库，后续需补充 remote 后才能 push

### 2026-05-12 会话 #4
- 执行内容：连接 GitHub 空仓库并完成首次推送
- 远程仓库：`https://github.com/yun23399/Working.git`
- 本次 Git 操作：
  1. 配置本地 Git 身份
  2. 添加 `origin`
  3. 初始提交：`6ba25d0` `📝 docs: 初始化项目文档与 Git 基线`
  4. 推送分支：`dev -> origin/dev`

### 2026-05-12 会话 #5
- 执行内容：按用户要求更新 Git 规范，新增“每次执行完成后推送到 GitHub 仓库”的强制规则
- 修改文件：
  1. `AGENTS.md`
  2. `PROGRESS.md`

### 2026-05-12 会话 #6
- 执行内容：落地阶段一真实前后端工程骨架并完成 Step 1 基础验证
- 创建目录：
  1. `frontend/`
  2. `backend/`
  3. `backend/data/`
- 验证结果：
  1. `frontend`: `npm install`、`npm run lint`、`npm run build` 通过
  2. `backend`: `pip install -r requirements.txt`、`python -m ruff check .`、`python -m black --check .`、`alembic upgrade head` 通过
  3. `http://127.0.0.1:8001/health` 返回 `200`

### 2026-05-12 会话 #7
- 执行内容：完成阶段一 Step 2 后端真实认证闭环
- 创建文件：
  1. `backend/app/models/user.py`
  2. `backend/app/schemas/auth.py`
  3. `backend/app/utils/security.py`
  4. `backend/app/services/auth_service.py`
  5. `backend/app/api/deps.py`
  6. `backend/app/api/auth.py`
- 验证结果：
  1. `python -m ruff check .` 通过
  2. `python -m black --check .` 通过
  3. `/api/auth/register`、`/api/auth/login`、`/api/auth/me` 实测通过

### 2026-05-12 会话 #8
- 执行内容：完成阶段一 Step 3 最小对话后端闭环与 Step 4 前端最小聊天闭环
- 新增后端文件：
  1. `backend/app/utils/logger.py`
  2. `backend/app/models/conversation.py`
  3. `backend/app/models/message.py`
  4. `backend/app/schemas/conversation.py`
  5. `backend/app/services/conversation_service.py`
  6. `backend/app/api/conversations.py`
  7. `backend/app/api/ws.py`
  8. `backend/alembic/versions/20260512_000002_add_core_tables.py`
- 新增前端文件：
  1. `frontend/src/api/auth.ts`
  2. `frontend/src/api/conversations.ts`
  3. `frontend/src/types/auth.ts`
  4. `frontend/src/types/chat.ts`
  5. `frontend/src/hooks/useWebSocket.ts`
- 关键改造：
  1. 后端新增统一错误响应处理
  2. 后端新增真实 CORS 配置
  3. WebSocket 新增对话归属校验
  4. 对话消息会刷新 `updated_at`
  5. 前端接入真实登录、对话列表、消息流和日志流
  6. 前端支持 WebSocket 自动重连 3 次
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .`、`alembic upgrade head` 通过
  3. 使用临时数据库和端口实测：注册 `201`、登录 `200`、创建对话 `201`、聊天 `200`、消息查询 `200`
  4. WebSocket 事件序列实测通过：`log -> agent_status -> log -> token -> ... -> agent_status(done)`
  5. 浏览器联调实测通过：`/login -> /chat -> 发送消息 -> 收到流式回复`
  6. 使用 `httpx.AsyncClient(trust_env=False)` 避免本地代理导致的误判

### 2026-05-12 会话 #9
- 执行内容：完成阶段一 Step 5 LLM 适配层与 Step 6 Manager 真实普通对话接入
- 新增文件：
  1. `backend/app/core/llm/providers.py`
  2. `backend/app/core/llm/adapter.py`
  3. `backend/app/core/llm/streaming.py`
  4. `backend/app/core/manager/manager_agent.py`
- 关键改造：
  1. 后端新增统一 LLM 提供商配置解析，支持 `openai`、`anthropic`、`ollama` 与 `auto`
  2. 对话服务由模拟回复切换为真实 Manager Agent 普通对话
  3. 保持现有 WebSocket 协议不变，前端无需改动即可消费真实流式输出
  4. 为本地 Ollama 增加原生 `/api/chat` 流式兼容路径，绕过当前 LiteLLM 版本的流式兼容问题
  5. `.env.example`、README 与部署/接口文档已同步更新到真实 LLM 流程
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  2. `frontend`: `npm run lint`、`npm run build` 通过
  3. 最小适配器实测：`LLM_PROVIDER=ollama`、`LLM_MODEL=qwen2.5-coder:3b` 可产生真实流式输出
  4. 临时后端联调实测：注册 `201`、登录 `200`、创建对话 `201`、聊天 `200`、消息查询 `200`
  5. WebSocket 事件链实测通过：`log -> agent_status(running) -> log -> token -> ... -> agent_status(done)`
  6. assistant 最终消息已真实持久化到数据库

### 2026-05-12 会话 #10
- 执行内容：完成阶段一 Step 7 最小项目/历史视图收尾，并统一本地联调环境
- 新增前端文件：
  1. `frontend/src/types/project.ts`
- 关键改造：
  1. 聊天页接入最小项目分组、本地项目与对话映射、空项目态与项目过滤
  2. `TopNav`、`Sidebar`、`MainArea` 改为真实项目/历史视图布局
  3. `Projects.tsx` 改为可切换的最小项目页
  4. `frontend/vite.config.ts` 改为读取仓库根目录环境，并固定默认开发/预览端口
  5. `backend/app/config.py` 改为统一读取仓库根目录 `.env`
  6. README、产品流程、前端规格、页面结构、测试文档与 CHANGELOG 已同步到当前实现
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  3. 浏览器实测通过：`注册 -> 进入聊天页 -> 切换空项目 -> 新建对话 -> 发送消息 -> 收到流式回复 -> 切回其它项目仅显示各自历史 -> 打开项目页并返回`
  4. 当前联调已稳定在 `http://127.0.0.1:8000` + `http://127.0.0.1:5173`

### 2026-05-12 会话 #11
- 执行内容：完成阶段二最小工作流预览确认链路
- 新增后端文件：
  1. `backend/app/models/workflow.py`
  2. `backend/app/schemas/workflow.py`
  3. `backend/app/core/manager/requirement_extractor.py`
  4. `backend/app/core/manager/workflow_planner.py`
  5. `backend/app/services/workflow_service.py`
  6. `backend/app/api/workflows.py`
  7. `backend/alembic/versions/20260512_000003_add_workflows_table.py`
- 新增前端文件：
  1. `frontend/src/types/workflow.ts`
  2. `frontend/src/api/workflows.ts`
  3. `frontend/src/stores/workflowStore.ts`
  4. `frontend/src/components/workflow/WorkflowConfirm.tsx`
- 关键改造：
  1. 聊天页新增工作流预览卡片，展示需求摘要、节点拆分和状态
  2. 前端支持生成预览、重新规划和确认工作流
  3. 后端新增工作流预览查询、生成与确认接口
  4. 新增 `workflows` 表保存需求摘要、DAG 预览与确认状态
  5. README、API、产品流程、前端规格、页面结构、测试文档与 CHANGELOG 已同步到当前实现
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .`、`alembic upgrade head` 通过
  3. 实测通过：`注册 -> 登录 -> 创建对话 -> 发送需求 -> 生成预览 -> 确认预览 -> 强制重新规划`
  4. 当前联调可访问：`http://127.0.0.1:8000` + `http://127.0.0.1:5173`

### 2026-05-12 会话 #12
- 执行内容：完成阶段二最小工作流执行链路
- 新增后端文件：
  1. `backend/app/agents/base_agent.py`
  2. `backend/app/agents/agent_runner.py`
  3. `backend/app/workflow/agent_spawner.py`
  4. `backend/app/workflow/dag_orchestrator.py`
  5. `backend/alembic/versions/20260512_000004_add_workflow_execution_state.py`
- 关键改造：
  1. `workflows` 表新增 `progress` 与 `execution_log_json`
  2. 工作流新增执行接口 `/api/workflows/{conversation_id}/{workflow_id}/execute`
  3. 已确认工作流可进入最小串行执行流程，并通过 WebSocket 推送 `workflow_update`
  4. 节点执行结果会写入 `execution_logs`，同时追加到对话历史消息
  5. 前端工作流卡片新增开始执行、进度条、节点状态与交接摘要展示
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .`、`alembic upgrade head` 通过
  3. 实测通过：`注册 -> 登录 -> 创建对话 -> 发送需求 -> 生成预览 -> 确认预览 -> 开始执行 -> 工作流 completed`
  4. 实测结果：工作流 `progress=100`、`execution_logs=3`、对话新增 3 条节点摘要消息

### 2026-05-12 会话 #13
- 执行内容：补齐阶段二执行结果前端刷新链路，并统一工作流响应中的节点运行态
- 关键改造：
  1. `frontend/src/hooks/useWebSocket.ts` 增加工作流事件回调扩展点
  2. `frontend/src/pages/Chat.tsx` 在节点完成/失败与终态时自动回拉 `workflows` 与 `messages`
  3. `backend/app/services/workflow_service.py` 为工作流接口响应推导 `runtime_status`
  4. 重新执行已完成工作流时会重置 `progress` 与 `execution_logs`
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  3. API 实测通过：执行启动响应返回节点运行态 `running / waiting / waiting`
  4. API 实测通过：执行完成后工作流 `completed`、`progress=100`、`execution_logs=3`、节点摘要消息入库

### 2026-05-12 会话 #14
- 执行内容：完成阶段二预置角色模板链路
- 新增后端文件：
  1. `backend/app/agents/templates/role_templates.py`
- 关键改造：
  1. 新增 `pm`、`frontend`、`backend`、`qa`、`designer` 五类预置角色模板
  2. `workflow_planner.py` 改为按需求动态选择角色模板并生成节点
  3. `agent_runner.py` 按模板注入角色职责与系统提示词
  4. 前端工作流卡片新增模板标签展示
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .`、`alembic upgrade head` 通过
  3. API 实测通过：包含前端/后端/设计/测试关键词的需求可生成 `pm / frontend / designer / backend / qa`
  4. API 实测通过：角色模板工作流执行完成后 `progress=100`、`execution_logs=5`

### 2026-05-13 会话 #15
- 执行内容：完成阶段二工作流日志实时展示链路
- 新增前端文件：
  1. `frontend/src/components/workflow/LogViewer.tsx`
- 关键改造：
  1. `workflowStore.ts` 新增按工作流维度缓存实时日志的状态与读写方法
  2. `useWebSocket.ts` 新增 `log` 事件回调扩展点，允许页面侧按场景分流日志
  3. `Chat.tsx` 将编排器与节点运行日志拆分到独立日志面板，聊天窗口仅保留系统与 Manager 日志
  4. 工作流执行前会清空当前工作流运行时日志，避免多次执行时旧日志残留
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. API/运行态实测通过：工作流执行完成后 `execution_logs_count=5`
  3. WebSocket 日志分流实测通过：`orchestrator` 与 `node_*` 日志进入 `LogViewer`，聊天日志区不再混入工作流编排日志

### 2026-05-13 会话 #16
- 执行内容：完成阶段二共享工作区链路
- 新增后端文件：
  1. `backend/app/workflow/workspace.py`
  2. `backend/alembic/versions/20260513_000005_add_workflow_workspace_state.py`
- 关键改造：
  1. `workflow.py` 新增 `workspace_path`、`workspace_state_json`、`handoff_log_json` 字段
  2. `workflow_service.py` 在预览创建与执行启动时初始化共享工作区，并将工作区状态纳入响应
  3. `dag_orchestrator.py` 在节点执行前后回写工作区状态、交接记录与执行上下文
  4. `base_agent.py`、`agent_runner.py` 将共享工作区路径注入节点执行上下文
  5. `workflow` API 响应新增 `workspace` 和 `handoff_logs`
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .`、`python -m alembic upgrade head` 通过
  2. `frontend`: `npm run lint`、`npm run build` 通过
  3. API 实测通过：工作流执行完成后返回根目录共享工作区路径 `workspace/projects/conversation_23/workflow_19`
  4. API 实测通过：`workspace_state.json` 与 `handoff_log.json` 已落盘，响应中可返回 `workspace` 与 `handoff_logs`

### 2026-05-13 会话 #17
- 执行内容：完成阶段二断点控制链路
- 新增后端文件：
  1. `backend/app/models/workflow_run.py`
  2. `backend/app/workflow/checkpoint.py`
  3. `backend/alembic/versions/20260513_000006_add_workflow_runs_table.py`
- 关键改造：
  1. 新增 `workflow_runs` 表保存运行轮次、断点快照、控制信号与改向说明
  2. `dag_orchestrator.py` 接入断点等待、恢复执行、中断处理与节点级快照保存
  3. `workflows.py` 新增 `/api/workflows/{conversation_id}/{workflow_id}/control` 控制接口
  4. 工作流响应新增 `workflow_run` 运行态，前端工作流卡片新增暂停、恢复、改向和中断入口
  5. 预览接口支持 `pause_after_nodes`，用于声明断点节点列表
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .`、`python -m alembic upgrade head` 通过
  2. `frontend`: `npm run lint`、`npm run build` 通过
  3. API 实测通过：`pause_after_nodes=['node_1']` 时工作流在首节点后进入 `waiting_confirm`
  4. API 实测通过：调用 `resume` 后工作流可继续执行至 `completed`

### 2026-05-13 会话 #18
- 执行内容：完成阶段二错误处理与层级上报链路
- 新增后端文件：
  1. `backend/app/workflow/error_handler.py`
- 关键改造：
  1. `dag_orchestrator.py` 接入节点失败自动重试、快照回滚与失败节点重跑
  2. `checkpoint.py` 支持读取断点快照，并在快照中持久化 `error_report`
  3. `workspace.py` 支持从最近安全快照恢复工作区状态与交接记录
  4. `workflow_service.py` / 前端工作流类型响应新增 `error_report`
  5. `WorkflowConfirm.tsx` 可直接展示失败节点、错误原因、上级角色与恢复建议
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  2. `frontend`: `npm run lint`、`npm run build` 通过
  3. API 实测通过：构造错误节点后，工作流进入 `waiting_confirm`，并返回 `error_report`
  4. API 实测通过：修正失败节点后调用 `redirect`，工作流可继续执行至 `completed`

### 2026-05-13 会话 #19
- 执行内容：完成阶段二项目级记忆链路
- 新增后端文件：
  1. `backend/app/core/memory/project_memory.py`
- 关键改造：
  1. 工作流预览创建时初始化 `project_memory.json`，沉淀长期目标与约束
  2. `dag_orchestrator.py` 在节点完成后将摘要写入项目级记忆
  3. `error_handler.py` 在节点失败后将最近异常同步写入项目级记忆
  4. 工作流响应新增 `project_memory`，前端卡片可展示关键记忆与最近异常
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  2. `frontend`: `npm run lint`、`npm run build` 通过
  3. API 实测通过：工作流预览响应返回 `project_memory`
  4. API 实测通过：执行完成后 `workspace/projects/conversation_<id>/project_memory.json` 已落盘并包含节点摘要

### 2026-05-13 会话 #20
- 执行内容：完成阶段三 `code_executor` 最小真实链路
- 新增后端文件：
  1. `backend/app/tools/base_tool.py`
  2. `backend/app/tools/code_executor.py`
- 关键改造：
  1. `backend/app/tools/__init__.py` 新增工具层统一导出
  2. `backend/app/agents/agent_runner.py` 接入 `CodeExecutorTool`
  3. `backend` / `frontend` 角色模板命中 `code_executor` 时，会在共享工作区 `artifacts/` 下真实生成计划文件
  4. `code_executor.py` 会记录执行结果，并将真实业务产物与 `code_execution_result.json` 一并回传
  5. 修复 Windows 下 `uvicorn --reload` 环境中的子进程执行兼容问题
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  2. `frontend`: `npm run lint`、`npm run build` 通过
  3. API 实测通过：`conversation_38 / workflow_38` 执行完成后，`workspace.artifacts` 返回 `backend_plan.json` 与 `code_execution_result.json`
  4. API 实测通过：节点 `execution_logs[].artifacts` 与磁盘目录 `workspace/projects/conversation_38/workflow_38/artifacts/` 内容一致

### 2026-05-13 会话 #21
- 执行内容：完成阶段三 `file_tool` 最小真实链路
- 新增后端文件：
  1. `backend/app/tools/file_tool.py`
- 关键改造：
  1. `backend/app/tools/__init__.py` 新增 `FileTool` 与 `FileToolError` 导出
  2. `backend/app/agents/agent_runner.py` 接入 `FileTool`
  3. 命中 `file_tool` 的角色模板会在共享工作区 `artifacts/` 下生成 `.md` 交付摘要
  4. 文件工具增加工作区路径越界校验，仅允许在当前工作流目录内读写
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  2. `frontend`: `npm run lint`、`npm run build` 通过
  3. API 实测通过：`conversation_40 / workflow_40` 执行完成后，`workspace.artifacts` 返回 `pm_summary.md`、`backend_summary.md`、`backend_plan.json` 与 `code_execution_result.json`
  4. API 实测通过：节点 `execution_logs[].artifacts` 与磁盘目录 `workspace/projects/conversation_40/workflow_40/artifacts/` 内容一致

### 2026-05-13 会话 #22
- 执行内容：完成阶段三 `api_caller` 最小真实链路
- 新增后端文件：
  1. `backend/app/tools/api_caller.py`
- 关键改造：
  1. `backend/app/tools/__init__.py` 新增 `ApiCallerTool` 与 `ApiCallerError` 导出
  2. `backend/app/agents/templates/role_templates.py` 为后端模板接入 `api_caller`
  3. `backend/app/agents/agent_runner.py` 接入 `ApiCallerTool`
  4. 外部 API 工具当前仅允许 `GET / POST` 和 `http / https` 协议，并关闭环境代理影响
  5. 接口响应会落盘到共享工作区 `artifacts/api_response.json`
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  2. `frontend`: `npm run lint`、`npm run build` 通过
  3. API 实测通过：`conversation_41 / workflow_41` 执行完成后，`workspace.artifacts` 返回 `api_response.json`、`pm_summary.md`、`backend_summary.md`、`backend_plan.json` 与 `code_execution_result.json`
  4. API 实测通过：`workspace/projects/conversation_41/workflow_41/artifacts/api_response.json` 已落盘，并包含 `/health` 返回 `200`

### 2026-05-13 会话 #23
- 执行内容：完成阶段三 `browser_tool` 最小真实链路
- 新增后端文件：
  1. `backend/app/tools/browser_tool.py`
- 关键改造：
  1. `backend/app/tools/__init__.py` 新增 `BrowserTool` 与 `BrowserToolError` 导出
  2. `backend/app/agents/templates/role_templates.py` 为前端与测试模板接入 `browser_tool`
  3. `backend/app/agents/agent_runner.py` 接入 `BrowserTool`，并按当前前后端地址生成页面校验指令
  4. `backend/app/config.py` 新增 `frontend_app_url` 配置项，用于统一前端访问地址
  5. `browser_tool.py` 改为通过独立 Python 子进程执行 Playwright，规避 Windows 下 `uvicorn --reload` 工作流进程中的浏览器子进程限制
  6. `requirement_extractor.py` 与 `workflow_planner.py` 补充英文关键词识别，确保英文页面/测试需求也能命中前端与测试模板
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  2. 工具级实测通过：`workspace/manual_browser_subprocess_test/artifacts/` 已生成 `manual_browser_subprocess.png` 与 `manual_browser_subprocess.json`
  3. Agent 级实测通过：`workspace/manual_agent_browser_subprocess_test/artifacts/` 已生成浏览器截图、元数据、摘要和执行结果文件
  4. API 实测通过：`conversation_48 / workflow_47` 执行完成后，`workspace.artifacts` 返回 `frontend_snapshot.png`、`frontend_browser_result.json`、`qa_snapshot.png` 与 `qa_browser_result.json`
  5. API 实测通过：`frontend_browser_result.json` 与 `qa_browser_result.json` 已落盘，并包含页面标题 `AgentFlow` 与状态码 `200`

### 2026-05-13 会话 #24
- 执行内容：完成阶段三 `image_tool` 最小真实链路
- 新增后端文件：
  1. `backend/app/tools/image_tool.py`
- 关键改造：
  1. `backend/app/tools/__init__.py` 新增 `ImageTool` 与 `ImageToolError` 导出
  2. `backend/app/agents/templates/role_templates.py` 为设计师模板接入 `image_tool`
  3. `backend/app/agents/agent_runner.py` 接入 `ImageTool`，并为设计师节点生成设计概念图指令
  4. `backend/app/config.py` 新增 `image_model`、`image_size`、`image_quality`、`image_timeout_seconds` 配置项
  5. `image_tool.py` 在配置 `OPENAI_API_KEY` 时可走 OpenAI 图像接口，在未配置时回退到基于 Playwright 的本地占位图渲染链路，保证当前环境可完成真实回归
  6. 统一修正 `agent_runner.py` 内多个工具的角色命名映射逻辑，优先以 `task.role` 作为产物命名依据
- 验证结果：
  1. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  2. 工具级实测通过：`workspace/manual_image_tool_test/artifacts/` 已生成 `manual_design_mockup.png` 与 `manual_design_result.json`
  3. Agent 级实测通过：设计师模板可生成真实图片产物与元数据文件
  4. API 实测通过：`conversation_50 / workflow_48` 执行完成后，`workspace.artifacts` 返回 `design_brief.md`、`design_mockup.png` 与 `design_image_result.json`
  5. API 实测通过：`design_image_result.json` 已落盘，并记录当前环境使用 `local_placeholder_renderer` 回退链路

### 2026-05-13 会话 #25
- 执行内容：完成阶段三前端产物预览链路
- 新增后端文件：
  1. `backend/app/services/workflow_artifact_service.py`
- 新增前端文件：
  1. `frontend/src/api/workflowArtifacts.ts`
  2. `frontend/src/hooks/useWorkflowArtifacts.ts`
  3. `frontend/src/utils/workflowArtifacts.ts`
  4. `frontend/src/components/workspace/ArtifactPreviewPanel.tsx`
  5. `frontend/src/components/workspace/CodePreview.tsx`
  6. `frontend/src/components/workspace/ImagePreview.tsx`
  7. `frontend/src/components/workspace/DocumentPreview.tsx`
- 关键改造：
  1. `backend/app/api/workflows.py` 新增受保护工作流产物列表接口与单文件读取接口，统一复用现有 JWT 与对话归属校验
  2. `backend/app/schemas/workflow.py` 新增 `WorkflowArtifactSchema`，用于描述前端可消费的产物元数据
  3. `frontend/src/pages/Chat.tsx` 接入产物预览面板，与现有工作流卡片和日志面板并列展示
  4. 前端新增代码、文档、图片三类预览组件，并按真实文件类型自动切换
  5. 默认会优先选择图片产物，其次文档和代码产物，便于直接查看设计图和页面截图
  6. `README.md`、`docs/api-reference.md`、`docs/product-flow.md`、`docs/testing-and-acceptance.md` 与 `CHANGELOG.md` 已同步到当前实现
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  3. 接口实测通过：`GET /api/workflows/50/48/artifacts` 返回 `200`，当前工作流可见产物共 `12` 项
  4. 接口实测通过：`GET /api/workflows/50/48/artifacts/file?path=design_mockup.png` 返回 `200`，`content-type=image/png`
  5. 接口实测通过：`GET /api/workflows/50/48/artifacts/file?path=design_brief.md` 返回 `200`，`content-type=text/markdown`
  6. 越权/不存在会话实测通过：`GET /api/workflows/999999/48/artifacts` 返回 `404`，错误码 `CONVERSATION_NOT_FOUND`

### 2026-05-13 会话 #26
- 执行内容：完成阶段三工作流产物导出链路
- 新增后端文件：
  1. `backend/app/tools/file_export.py`
  2. `backend/app/services/workflow_export_service.py`
- 新增前端文件：
  1. `frontend/src/utils/export.ts`
- 关键改造：
  1. `backend/app/api/workflows.py` 新增受保护导出接口 `/api/workflows/{conversation_id}/{workflow_id}/artifacts/export`
  2. `file_export.py` 支持将当前工作流 `artifacts/` 目录内真实文件打包到 `exports/workflow_<id>_artifacts.zip`
  3. `ArtifactPreviewPanel.tsx` 新增“导出产物”按钮与导出中/失败提示
  4. `frontend/src/api/workflowArtifacts.ts` 新增导出压缩包 API 封装，聊天页接入真实下载动作
  5. README、API、产品流程、测试文档与 CHANGELOG 已同步到当前导出实现
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  3. 接口实测通过：`GET /api/workflows/51/49/artifacts/export` 返回 `200`
  4. 接口实测通过：响应头包含 `attachment; filename=\"workflow_49_artifacts.zip\"`
  5. 接口实测通过：压缩包内文件列表为 `plan.json`、`summary.md`

### 2026-05-13 会话 #27
- 执行内容：完成阶段三 Token 用量展示链路
- 新增前端文件：
  1. `frontend/src/components/chat/TokenCounter.tsx`
- 关键改造：
  1. 将聊天头部原有的消息 Token 汇总逻辑抽离为独立 `TokenCounter` 组件
  2. `ChatWindow.tsx` 改为复用 `TokenCounter`，保持当前文案和统计口径不变
  3. README、CHANGELOG、测试文档与当前阶段说明已同步为阶段三完成状态
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  3. 聊天头部已通过独立组件显示 `messages[].tokenCount` 汇总结果

### 2026-05-13 会话 #28
- 执行内容：完成阶段四系统通知最小链路
- 新增后端文件：
  1. `backend/app/notifications/notifier.py`
- 关键改造：
  1. `backend/app/notifications/notifier.py` 新增本地通知器，支持通知日志、Windows 气泡提醒和声音回退
  2. `dag_orchestrator.py` 在工作流开始执行、等待确认、完成和中断时接入关键状态通知
  3. `backend/app/config.py` 与 `.env.example` 新增 `NOTIFICATIONS_ENABLED`、`NOTIFICATION_SOUND_ENABLED`
  4. `backend/app/utils/logger.py` 与通知器统一改为使用仓库根目录 `logs/`，避免运行目录漂移
  5. README、部署文档、产品流程、测试文档与 CHANGELOG 已同步到当前通知实现
- 验证结果：
  1. `frontend`: `npm run lint`、`npm run build` 通过
  2. `backend`: `python -m ruff check .`、`python -m black --check .` 通过
  3. 代码级实测通过：`SystemNotifier.notify()` 调用后，会在仓库根目录生成 `logs/notifications.log`
  4. 代码级实测通过：日志目录解析固定在仓库根目录，不再漂移到 `backend/logs/`

---

## 已知问题 / 待决定事项

| 编号 | 描述 | 状态 | 优先级 |
|------|------|------|--------|
| #002 | `files.zip` 不包含前后端工程代码，仅包含文档文件 | ⚠️ 已确认 | 中 |
| #005 | 本机未发现 `gh`，若后续需要 CLI 创建仓库或发 PR，需先安装并登录 GitHub CLI | ⏳ 待处理 | 中 |
| #006 | 本机其他项目可能重新占用 `127.0.0.1:8000` 或 `5173`，联调前需先确认归属；本次已按优先级清理并恢复本项目默认端口 | ⚠️ 已确认 | 中 |
| #007 | 本地可用默认模型为 `qwen2.5-coder` 系列，更偏代码场景；普通中文需求跟随质量后续仍需更通用模型验证 | ⏳ 待处理 | 中 |
