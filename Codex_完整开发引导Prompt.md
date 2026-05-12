# Codex 完整开发引导 Prompt

> 将 AGENTS.md 和 PROGRESS.md 全文附在前面，再把以下内容发给 Codex。

---

======== AGENTS.md ========
[粘贴 AGENTS.md 全文]

======== PROGRESS.md ========
[粘贴最新 PROGRESS.md 全文]

======== 开发引导开始 ========

你是这个多智能体编排平台的核心开发者。

请先校验当前仓库实际状态是否与 PROGRESS.md 一致；如果不一致，先修正 PROGRESS.md 与执行顺序，再从当前阶段继续推进。按照下面的完整开发计划逐步推进，每完成一个模块就更新 PROGRESS.md，遇到问题记录在"已知问题"里。

---

## 项目背景

这是一个本地优先的多智能体编排平台，用户在网页聊天界面与 Manager Agent 对话，Manager 理解需求后自动生成工作流、创建 Agent 团队协作完成任务。技术栈：前端 React + TypeScript + Vite，后端 Python + FastAPI，LLM 统一接入层使用 LiteLLM。

---

## 开发总计划（按阶段顺序执行）

---

### 阶段一（当前）：基础骨架 MVP

**目标：先让仓库真实可运行，再打通登录 -> 对话 -> 流式回复 -> 历史持久化闭环**

按以下顺序完成剩余任务：

**Step 0 — 仓库状态对齐**
- 先检查当前仓库是否真实存在 `frontend/`、`backend/`、`README.md`、`.env.example`、`.gitignore`、`.github/workflows/ci.yml`
- 如果 `PROGRESS.md` 声称某些目录或文件已完成，但仓库中并不存在，以实际仓库为准修正 `PROGRESS.md`
- 若工程代码缺失，先在当前仓库落地真实目录与文件，再进入后续步骤
- 验收标准：`PROGRESS.md` 的目录快照与当前仓库一致

**Step 1 — 工程骨架与依赖验证**
- 创建前端真实脚手架与目录结构
- `cd frontend && npm install`
- `npm run lint && npm run build`
- 创建后端真实骨架与目录结构
- `cd backend && pip install -r requirements.txt`
- `ruff check . && black --check .`
- `alembic upgrade head`
- `uvicorn app.main:app`
- 验收标准：前后端依赖安装、Lint、构建、迁移、启动全部通过

**Step 2 — 后端真实认证**
- `backend/app/utils/security.py`：实现 `hash_password`、`verify_password`、`create_access_token`、`decode_access_token`（bcrypt + JWT）
- `POST /api/auth/register`：检查用户名唯一 → bcrypt 加密 → 写入 DB → 返回用户信息
- `POST /api/auth/login`：查询用户 → verify_password → 签发 JWT → 返回 token
- `backend/app/api/deps.py`：实现 `get_current_user` 依赖（解析 JWT → 查 DB → 返回用户）
- 验收标准：注册、登录、鉴权接口可用

**Step 3 — loguru 日志配置**
- `backend/app/utils/logger.py`：配置 loguru，分级（DEBUG/INFO/WARNING/ERROR），同时输出到控制台和 `logs/` 目录下的日志文件（按日期轮转）
- 在 `main.py` 中接入，替换所有 print
- 验收标准：后端日志分级输出正常，错误路径可记录到日志文件

**Step 4 — 最小对话后端闭环**
- `backend/app/api/ws.py`：WebSocket 端点 `/ws/{conversation_id}`，需 JWT 验证
- `backend/app/api/ws.py` 中的 `ConnectionManager`：管理连接池，支持向指定 conversation_id 广播消息
- 对话与消息接口最小可用，支持数据库持久化
- 消息格式严格按 AGENTS.md 第 11 条规定的 JSON 结构
- 在真实 LLM 接入前，先提供可验证的模拟流式回复
- 验收标准：后端可创建对话、保存消息、推送流式消息

**Step 5 — 前端登录与聊天最小闭环**
- `frontend/src/hooks/useWebSocket.ts`：封装连接管理，自动重连（最多 3 次），按消息 type 分发到对应 store
- `frontend/src/pages/Login.tsx`：登录页 UI + 接入认证 API
- `frontend/src/components/chat/ChatWindow.tsx`：对话主界面，包含消息列表和输入框
- `frontend/src/components/chat/MessageBubble.tsx`：消息气泡，区分用户消息和 Agent 消息，支持 Markdown 渲染
- `frontend/src/components/chat/StreamingText.tsx`：打字机效果组件，逐 token 显示
- `frontend/src/components/chat/TokenCounter.tsx`：当前会话 Token 用量展示
- `frontend/src/stores/authStore.ts`：存储 token 和用户信息，持久化到 localStorage
- `frontend/src/stores/chatStore.ts`：管理消息列表、流式状态、token 计数
- 验收标准：用户可登录、进入聊天页、发送消息并看到流式回复

**Step 6 — LLM 适配层**
- `backend/app/core/llm/adapter.py`：基于 LiteLLM 实现统一 `chat()` 接口，支持流式输出
- `backend/app/core/llm/providers.py`：读取 `.env` 中的配置，支持 OpenAI / Anthropic / Ollama
- `backend/app/core/llm/streaming.py`：处理流式 token，逐个通过 WebSocket 推送到前端
- 验收标准：可通过统一接口拿到真实模型流式输出

**Step 7 — Manager Agent 基础对话**
- `backend/app/core/manager/manager_agent.py`：接收用户消息 → 调用 LLM → 流式回复
- 此阶段 Manager 只做普通对话，不做工作流规划（阶段二再实现）
- 接入对话接口 `POST /api/conversations/{id}/chat`
- 验收标准：Manager 可基于真实模型完成基础对话

**Step 8 — 最小项目与历史视图**
- `frontend/src/components/layout/TopNav.tsx`：顶部导航，含项目名、主题切换、语言切换、用户头像
- `frontend/src/components/layout/Sidebar.tsx`：左侧边栏，含项目与历史列表的最小读取/切换
- `frontend/src/components/layout/MainArea.tsx`：主内容区，自适应布局
- `frontend/src/stores/projectStore.ts`：项目和对话列表状态管理
- `backend/app/api/projects.py`：项目的增删查改接口
- `backend/app/api/conversations.py`：对话的增删查改接口
- `frontend/src/api/projects.ts` 和 `conversations.ts`：对应的前端请求封装
- 验收标准：登录后可看到最小项目/对话列表并切换历史

**Step 9 — 阶段一回归验证**
- 复跑 `npm run lint`、`npm run build`、`ruff check .`、`black --check .`、`alembic upgrade head`
- 验证 `登录 -> 进入对话 -> 发送消息 -> 流式回复 -> 历史持久化 -> 最小列表切换` 闭环
- 初始化 `CHANGELOG.md`
- 完成后更新 `PROGRESS.md` 的目录快照、完成项、操作日志

**阶段一完成标志：** 当前仓库真实包含前后端工程；用户可以登录，进入对话页，与 Manager Agent 聊天并看到实时流式回复，历史记录持久化，最小项目/对话列表可切换，且验证命令全部通过。

---

### 阶段二：工作流引擎

**目标：Manager 能规划工作流，多 Agent 协作执行任务**

**Step 10 — 需求提取器**
- `backend/app/core/manager/requirement_extractor.py`
- 当 Manager 判断已充分了解需求后，调用此模块
- 使用 LLM function calling 将对话提炼为结构化 JSON：
  ```json
  {
    "goal": "任务目标描述",
    "constraints": ["约束条件"],
    "output_types": ["code", "document", "image"],
    "context": "补充背景"
  }
  ```

**Step 11 — 工作流规划器**
- `backend/app/core/manager/workflow_planner.py`
- 输入：结构化需求 JSON
- 输出：工作流 DAG JSON，格式：
  ```json
  {
    "nodes": [
      {"id": "node_1", "role": "前端开发者", "task": "任务描述", "tools": ["code_executor", "file_tool"], "llm": "gpt-4o", "max_retries": 3, "depends_on": []}
    ],
    "execution_mode": "mixed"
  }
  ```
- Manager 可动态创建新角色，不限于预置模板

**Step 12 — 工作流预览界面**
- `frontend/src/components/workflow/WorkflowConfirm.tsx`
- 在对话流中内嵌展示：角色列表、每个 Agent 的任务描述、执行顺序
- 提供"确认执行"和"修改后执行"两个按钮
- 默认展示预览（可在设置中关闭，改为直接执行）

**Step 13 — DAG 编排器**
- `backend/app/workflow/dag_orchestrator.py`
- 解析 DAG JSON，按依赖关系决定串行/并行执行顺序
- 支持并发上限配置（读 `.env` 中的 `MAX_CONCURRENT_WORKFLOWS`）
- 追踪每个节点状态，通过 WebSocket 实时推送 `workflow_update` 消息

**Step 14 — Agent 生成器**
- `backend/app/workflow/agent_spawner.py`
- 按 DAG 节点动态创建 Agent 实例，注入角色 Prompt、工具集、LLM 配置
- `backend/app/agents/templates/`：实现预置角色模板（frontend_dev、backend_dev、tester、product_manager、designer）
- 每个模板包含：默认 system_prompt、默认工具集、建议 LLM

**Step 15 — 共享工作区**
- `backend/app/workflow/workspace.py`
- 所有 Agent 共同读写的上下文空间
- 存储：项目文件状态、任务进度、中间产出物
- Agent 完成任务后写入 handoff 消息，结构：
  ```json
  {"from_agent": "node_1", "to_agent": "node_2", "summary": "完成内容摘要", "artifacts": ["file_path"]}
  ```

**Step 16 — 断点控制器**
- `backend/app/workflow/checkpoint.py`
- 在指定节点暂停，通过 WebSocket 推送 `workflow_update`（status: waiting_confirm）
- 保存当前工作区快照到 DB（`workflow_runs.checkpoint_json`）
- 支持恢复（resume）、中断（abort）、修改方向后继续（redirect）

**Step 17 — 错误处理器**
- `backend/app/workflow/error_handler.py`
- Agent 失败 → 按 `max_retries` 重试 → 仍失败则：
  1. loguru ERROR 记录详细信息
  2. 回滚到上一个 checkpoint
  3. 从 DAG JSON 动态找上级节点
  4. 上级 Agent 分析错误 → 生成修改建议
  5. 通过 WebSocket 推送给前端等待用户决策

**Step 18 — Agent 运行时**
- `backend/app/agents/base_agent.py`：Agent 基类（role、system_prompt、llm_model、tools、max_retries）
- `backend/app/agents/agent_runner.py`：Agent 执行循环（调用 LLM → 解析工具调用 → 执行工具 → 写结果到工作区 → 流式推送输出）

**Step 19 — 日志面板**
- `frontend/src/components/workflow/LogViewer.tsx`：实时日志面板，支持 DEBUG/INFO/WARNING/ERROR 分级过滤
- 接收 WebSocket 的 `log` 类型消息，追加展示

**阶段二完成标志：** 说"帮我做个网页"，Manager 规划工作流，用户确认后，前端/后端 Agent 协作生成代码，可以看到实时日志和状态变化。

---

### 阶段三：工具集接入

**目标：Agent 具备实际执行能力**

**Step 20 — 工具基类**
- `backend/app/tools/base_tool.py`：定义工具接口（name、description、`execute(params) → result`）
- 工具注册表：Agent 按配置动态绑定工具

**Step 21 — 代码执行工具**
- `backend/app/tools/code_executor.py`
- 沙盒关闭时：subprocess 执行，捕获 stdout/stderr/退出码
- 沙盒开启时：Docker SDK 创建临时容器执行
- 超时限制（默认 30 秒，读 `.env`）
- 执行结果返回给 Agent，Agent 决定是否继续

**Step 22 — 文件系统工具**
- `backend/app/tools/file_tool.py`
- 实现：read_file、write_file、create_directory、list_files、delete_file
- 所有路径操作必须做路径穿越检查，限制在 `workspace/` 目录内
- `backend/app/utils/file_export.py`：任务完成后将工作区文件导出到用户指定的本地目录

**Step 23 — 外部 API 调用工具**
- `backend/app/tools/api_caller.py`
- 基于 httpx 实现异步 HTTP 请求（GET/POST/PUT/DELETE）
- 支持自定义 Headers、超时、重试
- 响应自动解析（JSON/文本）

**Step 24 — 浏览器自动化工具**
- `backend/app/tools/browser_tool.py`
- 基于 Playwright 实现：navigate、click、fill、screenshot、get_text、scroll
- 执行每步操作时通过 WebSocket 推送 `log` 消息（INFO 级别，说明正在做什么）
- 不实时推送浏览器截图，只推送文字描述

**Step 25 — 图像工具**
- `backend/app/tools/image_tool.py`
- AI 生成：调用 DALL·E API（读 `OPENAI_API_KEY`）
- 截图：调用 browser_tool 的 screenshot 方法
- 图片保存到工作区，路径写入工作区上下文

**Step 26 — 产出物预览**
- `frontend/src/components/workspace/CodePreview.tsx`：Monaco Editor 语法高亮预览，支持多文件 Tab
- `frontend/src/components/workspace/ImagePreview.tsx`：图片内嵌展示 + 下载按钮
- `frontend/src/components/workspace/DocumentPreview.tsx`：文本/Markdown 预览
- `frontend/src/components/workspace/PreviewPanel.tsx`：统一产出物预览容器，接收 `artifact` WebSocket 消息自动展示

**Step 27 — 文件上传**
- `frontend/src/components/chat/FileUploadZone.tsx`：拖拽上传区域，嵌入对话框
- `backend/app/api/projects.py`：文件上传接口，类型/大小校验，保存到工作区
- 上传后写入工作区上下文，Agent 可直接读取

**阶段三完成标志：** Agent 能写文件、执行代码、爬取网页、生成图片，产出物在对话中内嵌预览并可下载。

---

### 阶段四：完善体验

**目标：打磨细节，提升日常使用体验**

**Step 28 — 系统通知**
- `backend/app/notifications/notifier.py`：任务完成/失败时触发系统托盘通知（plyer 库）+ 播放提示音

**Step 29 — 项目管理完善**
- 项目列表支持：搜索、重命名、删除、归档
- 对话列表支持：搜索历史消息内容

**Step 30 — 用户自定义 Agent 角色**
- `backend/app/api/agents.py`：Agent 配置的增删改查接口
- 前端设置页：可视化管理角色（名称、Prompt、工具、LLM、重试次数）

**Step 31 — Agent 配置导入/导出**
- 导出：将 Agent 配置序列化为 JSON 文件下载
- 导入：上传 JSON 文件解析后写入 DB

**Step 32 — 并发配置**
- 设置页添加"最大并发工作流数"配置，写入 `.env` 并实时生效

**Step 33 — 动效与主题完善**
- 使用 Framer Motion 为以下场景添加过渡动效：
  - 页面切换（淡入淡出）
  - 消息出现（从下滑入）
  - 侧边栏展开/收起
  - 工作流确认面板弹出
  - 产出物预览区展开
- 确保所有动效流畅（60fps），不影响性能

**Step 34 — 国际化完善**
- 补全所有 UI 文案的中英文翻译（`frontend/src/i18n/zh.json` 和 `en.json`）
- 语言切换即时生效，不刷新页面

**Step 35 — 日志系统完善**
- 日志面板支持：关键词搜索、时间范围筛选、一键导出日志文件
- 后端日志按日期自动轮转，保留最近 30 天

**阶段四完成标志：** 整体使用体验流畅，动效自然，所有细节功能可用。

---

### 阶段五：扩展能力（持续迭代）

**Step 36 — 插件机制**
- `plugins/` 目录下的插件自动加载
- 插件接口：实现 `PluginBase`（name、description、tools、agent_templates）
- 前端设置页：已安装插件列表，支持启用/禁用

**Step 37 — PostgreSQL 支持**
- `config.py` 中根据 `DATABASE_URL` 自动切换 SQLite / PostgreSQL
- 确认所有 SQLAlchemy 模型兼容 PostgreSQL 语法

**Step 38 — OAuth 登录**
- 接入 Google OAuth2（使用 `authlib` 库）
- `backend/app/api/auth.py` 新增 OAuth 回调接口
- 前端登录页添加"Google 登录"按钮

---

## 执行规则

1. 开始前先核对当前仓库是否与 `PROGRESS.md` 一致；若不一致，先修正文档，再写代码
2. 严格按 Step 顺序推进，不跳步
3. 每完成一个 Step，立即更新 `PROGRESS.md`（勾选已完成项，追加操作日志）
4. 每个 Step 完成后执行对应验证命令，确认通过再进入下一步
5. 遇到无法自行决定的问题，记录在 `PROGRESS.md` 的"已知问题"里，然后继续推进不阻塞的部分
6. 所有代码注释使用中文
7. 严格遵守 AGENTS.md 的所有规范，特别是第 8 条禁止事项

现在请从 PROGRESS.md 中标记的当前位置开始，继续推进。
