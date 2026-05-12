# AGENTS.md — Codex 开发规范

> 本文件是 Codex 的强制规范文件。执行任何代码操作前必须先完整阅读本文件。
> 不允许跳过、违反或修改本文件中的任何规定。

---

## 0. 执行前必做事项

在开始任何任务之前，必须：
1. 完整阅读本文件（AGENTS.md）
2. 完整阅读 PROGRESS.md
3. 确认本次任务在 PROGRESS.md 标注的当前阶段范围内
4. 任务完成后立即更新 PROGRESS.md

---

## 1. 项目技术栈

### 前端
- React 18 + TypeScript 5 + Vite 5
- TailwindCSS 3（样式）
- Zustand 4（状态管理）
- React Query 5（数据请求）
- Framer Motion 11（动效）
- i18next（国际化）

### 后端
- Python 3.11+ / FastAPI / SQLAlchemy 2 / Pydantic 2
- LiteLLM（LLM 统一接口）
- Playwright（浏览器自动化）
- loguru（日志）

---

## 2. 目录结构规范

严格遵守 README.md 中定义的目录结构，不允许在规定目录之外创建文件。

- 前端组件放 `frontend/src/components/`
- 前端页面放 `frontend/src/pages/`
- 后端 API 路由放 `backend/app/api/`
- 后端业务逻辑放 `backend/app/services/`
- 核心 AI 逻辑放 `backend/app/core/`
- 工具集放 `backend/app/tools/`

完整目录结构参见主架构文档（多智能体平台_完整架构与开发文档.md）第二章。

---

## 3. 命名约定

### 前端（TypeScript）
- 组件文件：PascalCase（如 `ChatWindow.tsx`）
- Hook 文件：camelCase，以 `use` 开头（如 `useWebSocket.ts`）
- Store 文件：camelCase，以 `Store` 结尾（如 `chatStore.ts`）
- 工具函数：camelCase（如 `formatDate.ts`）
- 类型定义：PascalCase 接口（如 `interface AgentConfig`）
- CSS 类名：使用 Tailwind 原子类，自定义类用 kebab-case

### 后端（Python）
- 文件名：snake_case（如 `agent_runner.py`）
- 类名：PascalCase（如 `BaseAgent`）
- 函数名：snake_case（如 `run_workflow`）
- 常量：UPPER_SNAKE_CASE（如 `MAX_RETRIES`）
- Pydantic 模型：PascalCase + Schema 后缀（如 `WorkflowCreateSchema`）
- SQLAlchemy 模型：PascalCase（如 `WorkflowRun`）

---

## 4. 代码注释规范

- 所有注释使用**中文**
- 每个函数/方法必须有简短的中文注释说明用途
- 复杂逻辑块必须有行内注释
- 类必须有中文 docstring

示例（Python）：
```python
class LLMAdapter:
    """LLM 统一适配器，屏蔽不同提供商的 API 差异"""

    async def chat(self, messages: list, model: str) -> AsyncGenerator:
        """统一的对话接口，支持流式输出"""
        # 根据 model 前缀判断使用哪个提供商
        ...
```

示例（TypeScript）：
```typescript
// 管理 WebSocket 连接，支持自动重连
const useWebSocket = (conversationId: string) => {
  ...
}
```

---

## 5. 代码规范工具

### 前端
- ESLint：使用 `@typescript-eslint` 规则集
- Prettier：单引号、无分号、2 空格缩进、100 字符换行
- 提交前通过 Husky + lint-staged 自动检查

### 后端
- Ruff：启用 E、F、I、N 规则组
- Black：88 字符换行
- 提交前必须通过 `ruff check .` 和 `black --check .`

---

## 6. Git 规范

### 分支策略
- `main`：稳定版本，只接受来自 `dev` 的合并
- `dev`：开发分支，所有功能在此开发
- 不允许直接推送到 `main`

### Commit 消息格式（Gitmoji）
```
<emoji> <类型>: <中文描述>

常用示例：
✨ feat: 实现 Manager Agent 需求收集功能
🐛 fix: 修复 WebSocket 断线不重连的问题
📝 docs: 更新 API 接口文档
♻️ refactor: 重构 DAG 编排器错误处理逻辑
🎨 style: 统一前端组件间距规范
⚡️ perf: 优化 Agent 并发执行性能
🔧 chore: 更新依赖版本
✅ test: 补充认证模块测试用例
🔒 security: 修复路径穿越安全漏洞
```

---

## 7. 模块责任边界

### 前端模块
- `components/`：只负责 UI 渲染，不包含业务逻辑
- `stores/`：只管理状态，不直接调用 API
- `api/`：只负责 HTTP/WebSocket 请求，不处理业务逻辑
- `hooks/`：封装可复用的副作用逻辑
- `pages/`：组合组件与 store，处理页面级逻辑

### 后端模块
- `api/`（路由层）：只负责请求/响应处理，不写业务逻辑
- `services/`（服务层）：业务逻辑，调用 `core/` 和 `models/`
- `core/`（核心层）：AI 相关核心逻辑，不依赖 `api/`
- `tools/`（工具层）：各工具独立，互不依赖
- `models/`（数据层）：只定义数据结构，不写业务逻辑

---

## 8. 禁止事项

以下操作严格禁止，违反将导致代码被拒绝：

1. **禁止**在 `.env` 文件中提交真实 API Key（只能提交 `.env.example`）
2. **禁止**将 LLM 调用逻辑写在 `api/` 路由层，必须放在 `core/` 或 `services/`
3. **禁止**跨模块直接调用（如 `tools/` 调用 `api/`）
4. **禁止**在组件中直接调用 fetch/axios，必须通过 `api/` 层
5. **禁止**硬编码 Agent 权限层级结构（必须从工作流 DAG JSON 中动态读取）
6. **禁止**在任务未完成时更新 PROGRESS.md 的已完成状态
7. **禁止**修改 AGENTS.md 中的任何内容
8. **禁止**在 `main` 分支直接提交代码
9. **禁止**忽略错误：所有异步操作必须有 try/catch
10. **禁止**提交未通过 Lint 检查的代码
11. **禁止**使用 `any` 类型（TypeScript）——必须定义明确类型
12. **禁止**在 `except` 块中使用空 `pass`——必须记录日志或处理错误

---

## 9. 错误处理规范

- 所有 `async` 函数必须有 `try/catch`（前端）/ `try/except`（后端）
- 后端 API 错误统一返回格式：
  ```json
  {"error": "错误描述", "code": "错误码", "detail": "详细信息"}
  ```
- 前端所有请求错误必须有用户可见的提示（Toast 或错误边界）
- Agent 执行错误必须通过 loguru 以 ERROR 级别记录
- WebSocket 断开必须自动重连，最多重试 3 次

---

## 10. 安全规范

- 密码必须使用 `bcrypt` 加密，禁止明文存储
- 所有 API 接口（除 `/api/auth/register` 和 `/api/auth/login` 外）必须通过 JWT 验证
- 文件路径操作必须做路径穿越检查（不允许 `../` 等跳出工作区）
- 代码执行工具必须有超时限制（默认 30 秒，可配置）
- 用户上传文件必须做类型和大小校验（最大 50MB）
- 沙盒模式开启时必须使用 Docker 容器隔离，禁止宿主机直接执行

---

## 11. WebSocket 消息格式规范

所有 WebSocket 消息统一使用以下 JSON 结构：

```json
{
  "type": "token | agent_status | log | artifact | workflow_update | error",
  "conversation_id": "string",
  "payload": {},
  "timestamp": "ISO8601"
}
```

各类型 payload 定义：
- `token`：`{"content": "string", "agent_id": "string"}`
- `agent_status`：`{"agent_id": "string", "status": "waiting|running|done|failed", "role": "string"}`
- `log`：`{"level": "DEBUG|INFO|WARNING|ERROR", "message": "string", "agent_id": "string"}`
- `artifact`：`{"type": "code|image|document|data", "name": "string", "path": "string"}`
- `workflow_update`：`{"node_id": "string", "status": "string", "progress": 0.0}`
- `error`：`{"message": "string", "recoverable": true}`

---

## 12. 环境变量规范

所有配置必须通过环境变量读取，禁止硬编码。必需的环境变量：

```
# LLM 提供商（至少配置一个）
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

# 数据库
DATABASE_URL=sqlite:///./data/app.db

# 认证
JWT_SECRET_KEY=
JWT_EXPIRE_MINUTES=10080

# 应用
APP_HOST=127.0.0.1
APP_PORT=8000
WORKSPACE_DIR=./workspace
LOG_DIR=./logs
MAX_CONCURRENT_WORKFLOWS=3
CODE_EXEC_TIMEOUT=30
SANDBOX_ENABLED=false
```
