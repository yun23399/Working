// 对话基础信息类型
export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
}

// 创建对话请求体类型
export interface ConversationCreateRequest {
  title: string
}

// 后端消息记录类型
export interface MessageRecord {
  id: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  token_count: number
  created_at: string
}

// 聊天发送请求体类型
export interface ChatRequest {
  content: string
}

// 聊天请求受理响应类型
export interface ChatAccepted {
  message_id: number
  conversation_id: number
  accepted: boolean
}

// 前端时间线消息类型
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
  tokenCount: number
  isPending?: boolean
  isStreaming?: boolean
}

// 日志面板使用的实时日志类型
export interface ActivityLog {
  id: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  message: string
  agentId: string
}

// WebSocket 连接状态类型
export type SocketStatus = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'error'

// token 事件类型
export interface TokenEvent {
  type: 'token'
  conversation_id: string
  timestamp: string
  payload: {
    content: string
    agent_id: string
  }
}

// Agent 状态事件类型
export interface AgentStatusEvent {
  type: 'agent_status'
  conversation_id: string
  timestamp: string
  payload: {
    agent_id: string
    status: 'waiting' | 'running' | 'done' | 'failed'
    role: string
  }
}

// 日志事件类型
export interface LogEvent {
  type: 'log'
  conversation_id: string
  timestamp: string
  payload: {
    level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
    message: string
    agent_id: string
  }
}

// 错误事件类型
export interface ErrorEvent {
  type: 'error'
  conversation_id: string
  timestamp: string
  payload: {
    message: string
    recoverable: boolean
  }
}

// 运行时暂不消费，但保留协议兼容的产物事件类型
export interface ArtifactEvent {
  type: 'artifact'
  conversation_id: string
  timestamp: string
  payload: {
    type: string
    name: string
    path: string
  }
}

// 运行时暂不消费，但保留协议兼容的工作流事件类型
export interface WorkflowUpdateEvent {
  type: 'workflow_update'
  conversation_id: string
  timestamp: string
  payload: {
    node_id: string
    status: string
    progress: number
  }
}

// 前端支持解析的 WebSocket 消息联合类型
export type ConversationSocketEvent =
  | AgentStatusEvent
  | ArtifactEvent
  | ErrorEvent
  | LogEvent
  | TokenEvent
  | WorkflowUpdateEvent
