import { create } from 'zustand'
import type {
  ActivityLog,
  ChatMessage,
  Conversation,
  SocketStatus,
} from '../types/chat'

interface ChatState {
  conversations: Conversation[]
  activeConversationId: number | null
  messages: ChatMessage[]
  draft: string
  activityLogs: ActivityLog[]
  currentStreamingId: string | null
  isBootstrapping: boolean
  isCreatingConversation: boolean
  isSending: boolean
  isStreaming: boolean
  socketStatus: SocketStatus
  errorMessage: string | null
  setConversations: (conversations: Conversation[]) => void
  prependConversation: (conversation: Conversation) => void
  setActiveConversationId: (conversationId: number | null) => void
  touchConversation: (conversationId: number) => void
  setMessages: (messages: ChatMessage[]) => void
  resetMessages: () => void
  setDraft: (draft: string) => void
  addPendingUserMessage: (content: string) => string
  confirmPendingUserMessage: (tempId: string, messageId: number) => void
  removeMessage: (messageId: string) => void
  startAssistantStream: () => void
  appendAssistantToken: (content: string) => void
  finalizeAssistantStream: () => void
  addLog: (log: ActivityLog) => void
  setBootstrapping: (isBootstrapping: boolean) => void
  setCreatingConversation: (isCreatingConversation: boolean) => void
  setSending: (isSending: boolean) => void
  setSocketStatus: (status: SocketStatus) => void
  setError: (message: string | null) => void
  clearChatState: () => void
}

const maxLogCount = 4

function buildTimestamp(): string {
  return new Date().toISOString()
}

function moveConversationToFront(
  conversations: Conversation[],
  conversationId: number,
): Conversation[] {
  const targetConversation = conversations.find((item) => item.id === conversationId)
  if (!targetConversation) {
    return conversations
  }

  const updatedConversation: Conversation = {
    ...targetConversation,
    updated_at: buildTimestamp(),
  }

  return [
    updatedConversation,
    ...conversations.filter((item) => item.id !== conversationId),
  ]
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  activeConversationId: null,
  messages: [],
  draft: '',
  activityLogs: [],
  currentStreamingId: null,
  isBootstrapping: false,
  isCreatingConversation: false,
  isSending: false,
  isStreaming: false,
  socketStatus: 'idle',
  errorMessage: null,
  setConversations: (conversations) => set({ conversations }),
  prependConversation: (conversation) =>
    set((state) => ({
      conversations: [
        conversation,
        ...state.conversations.filter((item) => item.id !== conversation.id),
      ],
    })),
  setActiveConversationId: (conversationId) =>
    set({
      activeConversationId: conversationId,
      activityLogs: [],
      currentStreamingId: null,
      errorMessage: null,
      isStreaming: false,
      socketStatus: conversationId === null ? 'idle' : 'connecting',
    }),
  touchConversation: (conversationId) =>
    set((state) => ({
      conversations: moveConversationToFront(state.conversations, conversationId),
    })),
  setMessages: (messages) =>
    set({
      messages,
      currentStreamingId: null,
      isStreaming: false,
    }),
  resetMessages: () =>
    set({
      messages: [],
      currentStreamingId: null,
      isStreaming: false,
    }),
  setDraft: (draft) => set({ draft }),
  addPendingUserMessage: (content) => {
    const tempId = `user-${Date.now()}`
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id: tempId,
          role: 'user',
          content,
          createdAt: buildTimestamp(),
          tokenCount: content.length,
          isPending: true,
        },
      ],
    }))
    return tempId
  },
  confirmPendingUserMessage: (tempId, messageId) =>
    set((state) => ({
      messages: state.messages.map((message) =>
        message.id === tempId
          ? {
              ...message,
              id: String(messageId),
              isPending: false,
            }
          : message,
      ),
    })),
  removeMessage: (messageId) =>
    set((state) => ({
      messages: state.messages.filter((message) => message.id !== messageId),
    })),
  startAssistantStream: () =>
    set((state) => {
      if (state.currentStreamingId) {
        return { isStreaming: true }
      }

      const messageId = `assistant-${Date.now()}`
      return {
        currentStreamingId: messageId,
        isStreaming: true,
        messages: [
          ...state.messages,
          {
            id: messageId,
            role: 'assistant',
            content: '',
            createdAt: buildTimestamp(),
            tokenCount: 0,
            isStreaming: true,
          },
        ],
      }
    }),
  appendAssistantToken: (content) =>
    set((state) => {
      const streamingId = state.currentStreamingId ?? `assistant-${Date.now()}`
      const hasStreamingMessage = state.messages.some((message) => message.id === streamingId)

      if (!hasStreamingMessage) {
        return {
          currentStreamingId: streamingId,
          isStreaming: true,
          messages: [
            ...state.messages,
            {
              id: streamingId,
              role: 'assistant',
              content,
              createdAt: buildTimestamp(),
              tokenCount: 1,
              isStreaming: true,
            },
          ],
        }
      }

      return {
        currentStreamingId: streamingId,
        isStreaming: true,
        messages: state.messages.map((message) =>
          message.id === streamingId
            ? {
                ...message,
                content: `${message.content}${content}`,
                tokenCount: message.tokenCount + 1,
                isStreaming: true,
              }
            : message,
        ),
      }
    }),
  finalizeAssistantStream: () =>
    set((state) => ({
      currentStreamingId: null,
      isStreaming: false,
      messages: state.messages.map((message) =>
        message.id === state.currentStreamingId
          ? {
              ...message,
              isStreaming: false,
            }
          : message,
      ),
    })),
  addLog: (log) =>
    set((state) => ({
      activityLogs: [...state.activityLogs, log].slice(-maxLogCount),
    })),
  setBootstrapping: (isBootstrapping) => set({ isBootstrapping }),
  setCreatingConversation: (isCreatingConversation) => set({ isCreatingConversation }),
  setSending: (isSending) => set({ isSending }),
  setSocketStatus: (socketStatus) => set({ socketStatus }),
  setError: (errorMessage) => set({ errorMessage }),
  clearChatState: () =>
    set({
      conversations: [],
      activeConversationId: null,
      messages: [],
      draft: '',
      activityLogs: [],
      currentStreamingId: null,
      isBootstrapping: false,
      isCreatingConversation: false,
      isSending: false,
      isStreaming: false,
      socketStatus: 'idle',
      errorMessage: null,
    }),
}))
