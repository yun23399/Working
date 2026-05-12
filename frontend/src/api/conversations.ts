import { requestJson } from './client'
import type {
  ChatAccepted,
  ChatRequest,
  Conversation,
  ConversationCreateRequest,
  MessageRecord,
} from '../types/chat'

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
