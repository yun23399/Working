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
- 若当前项目没有对话则自动创建首条对话
- 自动建立 WebSocket 连接
- 支持发送消息和接收流式回复
- 支持按最小项目分组切换历史对话
- 支持生成、重新规划和确认工作流预览
- 支持启动最小工作流执行，并实时展示进度
- 支持在节点完成、失败和终态后自动刷新执行日志与节点摘要消息
- 支持在独立日志面板中实时展示编排器与节点运行日志
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
- `workflowsByConversation`
- `workflowLogsByWorkflowId`
- `loadingConversationId`
- `generatingConversationId`
- `confirmingWorkflowId`
- `executingWorkflowId`
- `workflowErrorMessage`

交互说明：

- 项目切换：仅展示当前项目下的历史对话
- 新建对话按钮：在当前项目下创建新对话并切换
- 历史对话项：加载该对话的历史消息
- 工作流预览卡片：展示结构化需求摘要、节点列表和预览状态
- 节点模板标签：展示 PM / 前端 / 后端 / 测试 / 设计师模板归属
- 生成预览按钮：基于当前对话历史请求后端生成预览
- 重新规划按钮：基于当前对话历史重新创建预览版本
- 确认工作流按钮：将当前预览标记为已确认
- 开始执行按钮：启动当前已确认工作流的最小串行执行
- 执行进度条：显示当前工作流进度百分比
- 节点状态标签：展示 waiting / running / done / failed
- 执行刷新：节点完成或工作流结束时自动回拉最新工作流和消息历史
- 工作流日志面板：单独展示 `orchestrator` 与 `node_*` 的实时运行日志
- 发送按钮：提交当前输入内容
- WebSocket 断线：自动重连最多 3 次

### 1.3 项目页 `Projects.tsx`

当前状态：

- 本地多项目管理页面已可用
- 支持项目搜索与筛选
- 支持新建项目、编辑项目名称与摘要
- 支持删除项目，并自动回收项目下的对话
- 支持在项目页选中对话并迁移到其他项目
- 支持直接打开指定项目下的某条对话

后续职责：

- 接入真实后端项目实体

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
- 展示当前会话标题
- 展示连接状态
- 展示当前用户名
- 提供项目页入口
- 提供设置页入口
- 提供退出登录入口

Props：

```ts
interface TopNavProps {
  conversationTitle: string | null
  projectName: string
  username: string | null
  socketStatus: SocketStatus
  onOpenProjects: () => void
  onOpenSettings: () => void
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

- 展示最小项目分组列表
- 展示真实对话列表
- 新建对话
- 切换项目
- 切换对话

Props：

```ts
interface SidebarProps {
  activeProjectId: string
  conversations: Conversation[]
  activeConversationId: number | null
  isCreatingConversation: boolean
  projects: ProjectSummary[]
  onCreateConversation: () => void
  onSelectProject: (projectId: string) => void
  onSelectConversation: (conversation: Conversation) => void
}
```

### 2.3 `MainArea`

功能说明：

- 展示当前项目名称与摘要
- 展示当前项目的历史对话数
- 展示当前会话标题
- 承载聊天窗口主区域

Props：

```ts
interface MainAreaProps {
  activeConversationTitle: string | null
  children: ReactNode
  conversationCount: number
  projectName: string
  projectSummary: string
}
```

### 2.4 `ChatWindow`

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

### 2.5 `WorkflowConfirm`

功能说明：

- 展示当前对话的最新工作流预览
- 展示需求摘要、约束、输出类型和节点拆分结果
- 支持生成预览、重新规划、确认预览和开始执行
- 展示执行进度、节点状态和交接摘要
- 展示工作流相关错误与加载状态

Props：

```ts
interface WorkflowConfirmProps {
  workflow: WorkflowPreview | null
  hasConversation: boolean
  canGenerate: boolean
  errorMessage: string | null
  isLoading: boolean
  isGenerating: boolean
  isConfirming: boolean
  isExecuting: boolean
  onGenerate: () => void
  onReplan: () => void
  onConfirm: () => void
  onExecute: () => void
}
```

### 2.6 `MessageBubble`

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

### 2.7 `LogViewer`

功能说明：

- 展示当前工作流运行期的结构化日志
- 区分 `INFO / WARNING / ERROR` 日志等级
- 默认仅承载编排器与工作流节点日志
- 执行新一轮工作流前清空旧日志

Props：

```ts
interface LogViewerProps {
  logs: ActivityLog[]
}
```

### 2.8 `StreamingText`

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

- 维护最小项目分组、当前项目 ID 和项目下的对话映射
- 数据持久化到本地存储 `agentflow.project.state`
- 未归属的对话会自动归入当前激活项目
- 已支持本地项目创建、编辑、删除和对话迁移
- 删除项目时会自动把对话转移到当前项目或首个可用项目
- 后续阶段会接入真实项目实体

### 3.4 `workflowStore`

负责：

- 按对话缓存工作流预览列表
- 维护预览加载、生成和确认中的状态
- 维护执行中的工作流编号与节点状态
- 维护按工作流编号分组的运行时日志
- 保存工作流相关错误提示
- 为聊天页提供当前对话的最新预览

## 4. Hook 规范

### `useWebSocket`

功能说明：

- 根据 `conversationId` 和 `token` 建立实时连接
- 解析事件类型
- 处理日志、流式 token、状态切换和错误提示
- 支持将工作流事件和日志事件回调给页面层
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

### `workflows.ts`

负责：

- `fetchConversationWorkflows`
- `createWorkflowPreview`
- `confirmWorkflowPreview`
- `executeWorkflow`

## 6. 当前交互闭环

当前已经可以跑通：

1. 注册
2. 自动登录
3. 进入聊天页
4. 按项目查看历史对话
5. 自动创建或加载当前项目下的对话
6. 建立 WebSocket
7. 发送消息
8. 接收流式回复
9. 基于当前对话生成工作流预览
10. 确认或重新规划工作流预览
11. 启动最小工作流执行并查看节点状态
12. 在独立日志面板查看工作流编排与节点实时日志
13. 在项目页搜索、管理本地项目并迁移对话
14. 刷新页面后恢复登录态和项目映射

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
2. 项目实体持久化与后端项目接口
3. 共享工作区与项目级记忆
4. 代码/图片/文档预览组件
5. 暗色主题切换
