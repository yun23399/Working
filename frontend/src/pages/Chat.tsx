import { useCallback, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchCurrentUser } from '../api/auth'
import { ApiRequestError } from '../api/client'
import {
  createConversation,
  fetchConversationMessages,
  fetchConversations,
  sendChatMessage,
} from '../api/conversations'
import { ChatWindow } from '../components/chat/ChatWindow'
import { MainArea } from '../components/layout/MainArea'
import { Sidebar } from '../components/layout/Sidebar'
import { TopNav } from '../components/layout/TopNav'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'
import type { ChatMessage, Conversation, MessageRecord } from '../types/chat'

function toChatMessage(message: MessageRecord): ChatMessage {
  return {
    id: String(message.id),
    role: message.role,
    content: message.content,
    createdAt: message.created_at,
    tokenCount: message.token_count,
  }
}

function buildConversationTitle(): string {
  const formatter = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    month: '2-digit',
    day: '2-digit',
  })
  return `新对话 ${formatter.format(new Date())}`
}

function resolveChatError(error: unknown): string {
  if (error instanceof ApiRequestError) {
    return error.message
  }

  return '请求失败，请稍后重试'
}

// 聊天页面，负责串联认证、对话列表、消息流与实时连接
export function Chat() {
  const navigate = useNavigate()
  const bootstrappedRef = useRef(false)
  const clearSession = useAuthStore((state) => state.clearSession)
  const setUser = useAuthStore((state) => state.setUser)
  const token = useAuthStore((state) => state.token)
  const user = useAuthStore((state) => state.user)

  const activeConversationId = useChatStore((state) => state.activeConversationId)
  const activityLogs = useChatStore((state) => state.activityLogs)
  const clearChatState = useChatStore((state) => state.clearChatState)
  const conversations = useChatStore((state) => state.conversations)
  const draft = useChatStore((state) => state.draft)
  const errorMessage = useChatStore((state) => state.errorMessage)
  const isBootstrapping = useChatStore((state) => state.isBootstrapping)
  const isCreatingConversation = useChatStore((state) => state.isCreatingConversation)
  const isSending = useChatStore((state) => state.isSending)
  const isStreaming = useChatStore((state) => state.isStreaming)
  const messages = useChatStore((state) => state.messages)
  const setActiveConversationId = useChatStore((state) => state.setActiveConversationId)
  const setBootstrapping = useChatStore((state) => state.setBootstrapping)
  const setConversations = useChatStore((state) => state.setConversations)
  const setCreatingConversation = useChatStore((state) => state.setCreatingConversation)
  const setDraft = useChatStore((state) => state.setDraft)
  const setError = useChatStore((state) => state.setError)
  const setMessages = useChatStore((state) => state.setMessages)
  const setSending = useChatStore((state) => state.setSending)
  const prependConversation = useChatStore((state) => state.prependConversation)
  const resetMessages = useChatStore((state) => state.resetMessages)
  const addPendingUserMessage = useChatStore((state) => state.addPendingUserMessage)
  const confirmPendingUserMessage = useChatStore((state) => state.confirmPendingUserMessage)
  const removeMessage = useChatStore((state) => state.removeMessage)
  const touchConversation = useChatStore((state) => state.touchConversation)
  const socketStatus = useChatStore((state) => state.socketStatus)

  useWebSocket(activeConversationId, token)

  useEffect(() => {
    if (!token) {
      navigate('/login', { replace: true })
    }
  }, [navigate, token])

  const handleUnauthorized = useCallback(() => {
    clearSession()
    clearChatState()
    navigate('/login', { replace: true })
  }, [clearChatState, clearSession, navigate])

  const loadMessages = useCallback(async (nextConversationId: number, authToken: string) => {
    try {
      const records = await fetchConversationMessages(authToken, nextConversationId)
      setMessages(records.map(toChatMessage))
      setActiveConversationId(nextConversationId)
      setError(null)
    } catch (error) {
      const message = resolveChatError(error)
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }
      setError(message)
    }
  }, [handleUnauthorized, setActiveConversationId, setError, setMessages])

  const handleCreateConversation = async () => {
    if (!token) {
      handleUnauthorized()
      return
    }

    setCreatingConversation(true)
    try {
      const conversation = await createConversation(token, {
        title: buildConversationTitle(),
      })
      prependConversation(conversation)
      setActiveConversationId(conversation.id)
      resetMessages()
      setDraft('')
      setError(null)
    } catch (error) {
      const message = resolveChatError(error)
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }
      setError(message)
    } finally {
      setCreatingConversation(false)
    }
  }

  useEffect(() => {
    if (!token || bootstrappedRef.current) {
      return
    }

    bootstrappedRef.current = true

    const bootstrapChat = async () => {
      setBootstrapping(true)
      try {
        if (!user) {
          const currentUser = await fetchCurrentUser(token)
          setUser(currentUser)
        }

        const items = await fetchConversations(token)
        setConversations(items)

        if (items.length === 0) {
          const firstConversation = await createConversation(token, {
            title: buildConversationTitle(),
          })
          prependConversation(firstConversation)
          setActiveConversationId(firstConversation.id)
          resetMessages()
        } else {
          await loadMessages(items[0].id, token)
        }
      } catch (error) {
        if (error instanceof ApiRequestError && error.status === 401) {
          handleUnauthorized()
          return
        }
        setError(resolveChatError(error))
      } finally {
        setBootstrapping(false)
      }
    }

    void bootstrapChat()
  }, [
    handleUnauthorized,
    loadMessages,
    prependConversation,
    resetMessages,
    setActiveConversationId,
    setBootstrapping,
    setConversations,
    setError,
    setUser,
    token,
    user,
  ])

  const handleSelectConversation = async (conversation: Conversation) => {
    if (!token) {
      handleUnauthorized()
      return
    }

    setBootstrapping(true)
    await loadMessages(conversation.id, token)
    setBootstrapping(false)
  }

  const handleSendMessage = async () => {
    if (!token) {
      handleUnauthorized()
      return
    }

    if (activeConversationId === null) {
      await handleCreateConversation()
      return
    }

    const content = draft.trim()
    if (!content) {
      return
    }

    if (socketStatus !== 'connected') {
      setError('实时连接尚未建立，请等待连接成功后再发送消息')
      return
    }

    setSending(true)
    setError(null)
    const tempId = addPendingUserMessage(content)
    setDraft('')

    try {
      const result = await sendChatMessage(token, activeConversationId, {
        content,
      })
      confirmPendingUserMessage(tempId, result.message_id)
      touchConversation(activeConversationId)
    } catch (error) {
      removeMessage(tempId)
      setDraft(content)
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }
      setError(resolveChatError(error))
    } finally {
      setSending(false)
    }
  }

  const handleLogout = () => {
    clearSession()
    clearChatState()
    navigate('/login', { replace: true })
  }

  return (
    <main className="min-h-screen p-6">
      <section className="mx-auto grid min-h-[720px] max-w-7xl grid-cols-[300px_1fr] grid-rows-[56px_1fr] overflow-hidden rounded-[28px] border border-line bg-surface-panel shadow-panel">
        <TopNav username={user?.username ?? null} socketStatus={socketStatus} onLogout={handleLogout} />
        <Sidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          isCreatingConversation={isCreatingConversation}
          onCreateConversation={handleCreateConversation}
          onSelectConversation={handleSelectConversation}
        />
        <MainArea>
          <ChatWindow
            draft={draft}
            errorMessage={errorMessage}
            isBootstrapping={isBootstrapping}
            isSending={isSending}
            isStreaming={isStreaming}
            logs={activityLogs}
            messages={messages}
            socketStatus={socketStatus}
            onDraftChange={setDraft}
            onSend={handleSendMessage}
          />
        </MainArea>
      </section>
    </main>
  )
}
