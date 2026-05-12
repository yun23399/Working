# PAGE_STRUCTURE

本文档描述页面目录结构、路由映射和组件归属，便于后续继续扩展前端工程。

## 1. 当前路由结构

### 已实现

- `/login`
  - 登录与注册页面
- `/chat`
  - 最小聊天闭环页面
- `/projects`
  - 项目页骨架
- `/settings`
  - 设置页骨架

### 规划中

- `/dashboard`
- `/agents`
- `/models`
- `/tools`
- `/logs`

## 2. 页面到组件映射

### 登录页 `frontend/src/pages/Login.tsx`

区域映射：

- 顶部品牌区
- 功能说明区
- 登录/注册切换区
- 表单区
- 错误提示区

依赖：

- `auth.ts`
- `authStore.ts`

### 聊天页 `frontend/src/pages/Chat.tsx`

区域映射：

- 顶部导航：`TopNav`
- 左侧栏：`Sidebar`
- 主内容容器：`MainArea`
- 聊天窗口：`ChatWindow`

依赖：

- `conversations.ts`
- `authStore.ts`
- `chatStore.ts`
- `useWebSocket.ts`

### 项目页 `frontend/src/pages/Projects.tsx`

当前状态：

- 骨架页面
- 后续用于项目列表、搜索、切换和新建项目

### 设置页 `frontend/src/pages/Settings.tsx`

当前状态：

- 骨架页面
- 后续用于主题、语言、模型并发等配置

## 3. 组件目录结构

```text
frontend/src/
├── api/
│   ├── auth.ts
│   ├── client.ts
│   └── conversations.ts
├── components/
│   ├── chat/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageBubble.tsx
│   │   └── StreamingText.tsx
│   └── layout/
│       ├── MainArea.tsx
│       ├── Sidebar.tsx
│       └── TopNav.tsx
├── hooks/
│   └── useWebSocket.ts
├── pages/
│   ├── AppRouter.tsx
│   ├── Chat.tsx
│   ├── Login.tsx
│   ├── Projects.tsx
│   └── Settings.tsx
├── stores/
│   ├── authStore.ts
│   ├── chatStore.ts
│   └── projectStore.ts
└── types/
    ├── auth.ts
    └── chat.ts
```

## 4. 页面功能边界

### `pages/`

- 负责组合组件、调用 store、组织页面级交互

### `components/`

- 负责渲染与交互外观
- 不直接访问后端接口

### `api/`

- 负责统一 HTTP / WebSocket 地址和请求封装

### `stores/`

- 负责保存登录态、对话态、流式态

### `hooks/`

- 负责副作用逻辑，例如 WebSocket 建连与重连

## 5. 后续扩展建议

为匹配完整平台目标，建议后续新增以下页面与组件：

- `Dashboard.tsx`
- `AgentManagement.tsx`
- `ModelConfig.tsx`
- `ToolConfig.tsx`
- `ExecutionLogs.tsx`

以及以下组件：

- `AgentCard`
- `TaskCard`
- `CodePreviewCard`
- `FileCard`
- `RiskApprovalModal`
- `ModelSelector`
- `ToolStatusBadge`
- `TokenCounter`
