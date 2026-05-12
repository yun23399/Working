# FRONTEND_SPEC

本文档用于描述当前前端页面、组件、状态和交互规范，便于后续直接继续编码。

## 1. 当前已实现页面

### 1.1 登录页 `Login.tsx`

功能说明：

- 支持登录和注册两种模式
- 注册成功后自动登录
- 登录成功后保存 Token 与用户信息
- 成功后跳转到聊天页
- 失败时展示用户可见错误提示

状态定义：

- `mode`: `login | register`
- `credentials.username`
- `credentials.password`
- `isSubmitting`
- `authError`

交互说明：

- 点击“登录/注册”切换模式
- 点击提交按钮后调用认证接口
- 若接口失败，则显示错误卡片

### 1.2 聊天页 `Chat.tsx`

功能说明：

- 进入页面后自动恢复用户信息
- 自动加载对话列表
- 若没有对话则自动创建首条对话
- 自动建立 WebSocket 连接
- 支持发送消息和接收流式回复
- 支持退出登录

状态定义：

- `activeConversationId`
- `conversations`
- `messages`
- `draft`
- `activityLogs`
- `isBootstrapping`
- `isCreatingConversation`
- `isSending`
- `isStreaming`
- `socketStatus`
- `errorMessage`

交互说明：

- 新建对话按钮：创建新对话并切换
- 历史对话项：加载该对话的历史消息
- 发送按钮：提交当前输入内容
- WebSocket 断线：自动重连最多 3 次

### 1.3 项目页 `Projects.tsx`

当前状态：

- 占位骨架页面

后续职责：

- 项目列表
- 搜索和筛选
- 新建项目
- 项目切换

### 1.4 设置页 `Settings.tsx`

当前状态：

- 占位骨架页面

后续职责：

- 主题切换
- 语言切换
- 模型并发设置
- 工具开关配置

## 2. 当前已实现组件

### 2.1 `TopNav`

功能说明：

- 展示项目标题
- 展示连接状态
- 展示当前用户名
- 提供退出登录入口

Props：

```ts
interface TopNavProps {
  username: string | null
  socketStatus: SocketStatus
  onLogout: () => void
}
```

可选状态：

- `connected`
- `connecting`
- `reconnecting`
- `error`
- `idle`

### 2.2 `Sidebar`

功能说明：

- 展示项目占位列表
- 展示真实对话列表
- 新建对话
- 切换对话

Props：

```ts
interface SidebarProps {
  conversations: Conversation[]
  activeConversationId: number | null
  isCreatingConversation: boolean
  onCreateConversation: () => void
  onSelectConversation: (conversation: Conversation) => void
}
```

### 2.3 `ChatWindow`

功能说明：

- 展示消息列表
- 展示连接状态
- 展示实时日志
- 展示错误提示
- 提供消息输入和发送能力

Props：

```ts
interface ChatWindowProps {
  draft: string
  errorMessage: string | null
  isBootstrapping: boolean
  isSending: boolean
  isStreaming: boolean
  logs: ActivityLog[]
  messages: ChatMessage[]
  socketStatus: SocketStatus
  onDraftChange: (draft: string) => void
  onSend: () => void
}
```

### 2.4 `MessageBubble`

功能说明：

- 区分用户与 Manager 消息
- 流式消息时使用 `StreamingText`
- 支持消息进入动效

Props：

```ts
interface MessageBubbleProps {
  message: ChatMessage
}
```

### 2.5 `StreamingText`

功能说明：

- 展示逐段追加的流式消息
- 提供尾部光标动画

Props：

```ts
interface StreamingTextProps {
  content: string
}
```

## 3. Store 规范

### 3.1 `authStore`

负责：

- 保存 Token
- 保存当前用户
- 本地存储会话
- 提供清理登录态能力

### 3.2 `chatStore`

负责：

- 对话列表
- 当前对话 ID
- 消息列表
- 输入草稿
- 实时日志
- 流式状态
- 发送状态
- WebSocket 状态
- 错误提示

### 3.3 `projectStore`

当前状态：

- 仅保留最小项目名状态
- 后续阶段会接入真实项目实体

## 4. Hook 规范

### `useWebSocket`

功能说明：

- 根据 `conversationId` 和 `token` 建立实时连接
- 解析事件类型
- 处理日志、流式 token、状态切换和错误提示
- 最多自动重连 3 次

输入：

```ts
useWebSocket(conversationId: number | null, token: string | null)
```

## 5. API 模块规范

### `client.ts`

负责：

- 解析 `VITE_API_BASE_URL`
- 统一 JSON 请求
- 统一错误转换
- 推导 WebSocket 地址

### `auth.ts`

负责：

- `registerUser`
- `loginUser`
- `fetchCurrentUser`

### `conversations.ts`

负责：

- `fetchConversations`
- `createConversation`
- `fetchConversationMessages`
- `sendChatMessage`

## 6. 当前交互闭环

当前已经可以跑通：

1. 注册
2. 自动登录
3. 进入聊天页
4. 自动创建或加载对话
5. 建立 WebSocket
6. 发送消息
7. 接收流式回复
8. 刷新页面后恢复登录态

## 7. 规划中的可复用组件

以下组件来自完整平台目标，当前尚未实现，但命名和职责已经确定：

- `AgentCard`
  - 展示 Agent 头像、角色、状态、Token 用量
- `TaskCard`
  - 展示任务摘要、负责人、执行状态
- `CodePreviewCard`
  - 展示代码片段与文件路径
- `FileCard`
  - 展示图片、文档、数据文件信息
- `LogItem`
  - 展示结构化日志
- `RiskApprovalModal`
  - 展示高风险操作确认弹窗
- `ModelSelector`
  - 切换 LLM 提供商与模型
- `ToolStatusBadge`
  - 展示工具启用状态
- `TokenCounter`
  - 统计会话 Token 消耗

## 8. 后续前端优先级建议

1. 接入真实 LLM 流式输出后的消息状态适配
2. 项目实体持久化与项目切换
3. 工作流确认卡片与执行状态面板
4. 代码/图片/文档预览组件
5. 暗色主题切换
