# PAGE_STRUCTURE

本文档描述页面目录结构、路由映射和组件归属，便于后续继续扩展前端工程。

## 1. 当前路由结构

### 已实现

- `/login`
  - 登录与注册页面
- `/chat`
  - 最小聊天闭环页面，含项目分组与历史视图
- `/projects`
  - 最小项目分组页
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
- 工作流预览区：`WorkflowConfirm`
- 产物预览区：`ArtifactPreviewPanel`
- 工作流日志区：`LogViewer`
- 聊天窗口：`ChatWindow`
- 对话内搜索：内嵌在 `ChatWindow` 顶部

依赖：

- `conversations.ts`
- `workflows.ts`
- `workflowArtifacts.ts`
- `authStore.ts`
- `chatStore.ts`
- `projectStore.ts`
- `workflowStore.ts`
- `useWorkflowArtifacts.ts`
- `useWebSocket.ts`

### 项目页 `frontend/src/pages/Projects.tsx`

当前状态：

- 本地项目管理页已接入
- 当前支持项目搜索、筛选、创建、编辑、删除与对话迁移
- 当前支持从项目页直接打开指定对话
- 后续用于接入真实后端项目实体

### 设置页 `frontend/src/pages/Settings.tsx`

当前状态：

- 自定义角色模板管理页已接入
- 当前支持角色模板创建、编辑、启停、删除、关键词配置与 JSON 导入/导出
- 当前支持系统级工作流并发上限查看与保存
- 后续用于主题、语言与更多系统配置

## 3. 组件目录结构

```text
frontend/src/
├── api/
│   ├── agentRoleTemplates.ts
│   ├── auth.ts
│   ├── client.ts
│   ├── conversations.ts
│   ├── systemSettings.ts
│   ├── workflowArtifacts.ts
│   └── workflows.ts
├── components/
│   ├── chat/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── StreamingText.tsx
│   │   └── TokenCounter.tsx
│   ├── layout/
│   │   ├── MainArea.tsx
│   │   ├── Sidebar.tsx
│   │   └── TopNav.tsx
│   ├── workflow/
│   │   ├── LogViewer.tsx
│   │   └── WorkflowConfirm.tsx
│   └── workspace/
│       ├── ArtifactPreviewPanel.tsx
│       ├── CodePreview.tsx
│       ├── DocumentPreview.tsx
│       └── ImagePreview.tsx
├── hooks/
│   ├── useWebSocket.ts
│   └── useWorkflowArtifacts.ts
├── i18n/
│   ├── en.json
│   ├── index.ts
│   └── zh.json
├── pages/
│   ├── AppRouter.tsx
│   ├── Chat.tsx
│   ├── Login.tsx
│   ├── Projects.tsx
│   └── Settings.tsx
├── stores/
│   ├── authStore.ts
│   ├── chatStore.ts
│   ├── projectStore.ts
│   └── workflowStore.ts
├── types/
│   ├── agentRoleTemplate.ts
│   ├── auth.ts
│   ├── chat.ts
│   ├── project.ts
│   ├── systemSettings.ts
│   └── workflow.ts
├── utils/
│   ├── export.ts
│   └── workflowArtifacts.ts
├── App.tsx
├── main.tsx
└── styles.css
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

- 负责保存登录态、对话态、流式态和最小项目态
- 负责保存工作流预览态
- 负责保存按工作流归档的实时运行日志

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
