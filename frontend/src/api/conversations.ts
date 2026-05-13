import { requestJson } from './client'
import type {
  ChatAccepted,
  ChatRequest,
  Conversation,
  ConversationManagerState,
  ConversationCreateRequest,
  MessageRecord,
} from '../types/chat'
import type { WorkflowPreview } from '../types/workflow'

// 获取当前用户的对话列表
export async function fetchConversations(token: string): Promise<Conversation[]> {
  return requestJson<Conversation[]>('/api/conversations', {
    token,
  })
}

// 创建新对话并返回基础信息
export async function createConversation(
  token: string,
  payload: ConversationCreateRequest,
): Promise<Conversation> {
  return requestJson<Conversation>('/api/conversations', {
    method: 'POST',
    token,
    body: payload,
  })
}

// 读取指定对话的历史消息
export async function fetchConversationMessages(
  token: string,
  conversationId: number,
): Promise<MessageRecord[]> {
  return requestJson<MessageRecord[]>(`/api/conversations/${conversationId}/messages`, {
    token,
  })
}

// 发送用户消息并触发后端流式回复
export async function sendChatMessage(
  token: string,
  conversationId: number,
  payload: ChatRequest,
): Promise<ChatAccepted> {
  return requestJson<ChatAccepted>(`/api/conversations/${conversationId}/chat`, {
    method: 'POST',
    token,
    body: payload,
  })
}

// 读取当前对话的总代理需求收集状态
export async function fetchConversationManagerState(
  token: string,
  conversationId: number,
): Promise<ConversationManagerState> {
  return requestJson<ConversationManagerState>(
    `/api/conversations/${conversationId}/manager-state`,
    {
      token,
    },
  )
}

// 在总代理判断准备完成后开始任务，并返回最新工作流预览
export async function startConversationTask(
  token: string,
  conversationId: number,
): Promise<WorkflowPreview> {
  return requestJson<WorkflowPreview>(`/api/conversations/${conversationId}/start-task`, {
    method: 'POST',
    token,
  })
}

// 更新当前对话的总代理角色
export async function updateConversationManagerRole(
  token: string,
  conversationId: number,
  managerRole: string,
): Promise<Conversation> {
  return requestJson<Conversation>(`/api/conversations/${conversationId}/manager-role`, {
    method: 'PUT',
    token,
    body: {
      manager_role: managerRole,
    },
  })
}
