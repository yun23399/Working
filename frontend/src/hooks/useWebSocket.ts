import { useEffect } from 'react'
import { buildConversationWebSocketUrl } from '../api/client'
import { useChatStore } from '../stores/chatStore'
import { useWorkflowStore } from '../stores/workflowStore'
import type { ConversationSocketEvent } from '../types/chat'

function isConversationSocketEvent(value: unknown): value is ConversationSocketEvent {
  if (typeof value !== 'object' || value === null) {
    return false
  }

  const candidate = value as Partial<ConversationSocketEvent>
  return (
    typeof candidate.type === 'string' &&
    typeof candidate.conversation_id === 'string' &&
    typeof candidate.timestamp === 'string' &&
    typeof candidate.payload === 'object' &&
    candidate.payload !== null
  )
}

function parseConversationSocketEvent(rawValue: string): ConversationSocketEvent | null {
  try {
    const parsed = JSON.parse(rawValue) as unknown
    if (isConversationSocketEvent(parsed)) {
      return parsed
    }
  } catch {
    return null
  }

  return null
}

interface UseWebSocketOptions {
  onWorkflowUpdate?: (event: Extract<ConversationSocketEvent, { type: 'workflow_update' }>) => void
}

// 建立对话级 WebSocket 连接，并处理最多三次自动重连
export function useWebSocket(
  conversationId: number | null,
  token: string | null,
  options?: UseWebSocketOptions,
) {
  const addLog = useChatStore((state) => state.addLog)
  const appendAssistantToken = useChatStore((state) => state.appendAssistantToken)
  const finalizeAssistantStream = useChatStore((state) => state.finalizeAssistantStream)
  const setError = useChatStore((state) => state.setError)
  const setSocketStatus = useChatStore((state) => state.setSocketStatus)
  const startAssistantStream = useChatStore((state) => state.startAssistantStream)
  const updateWorkflowProgress = useWorkflowStore((state) => state.updateWorkflowProgress)
  const onWorkflowUpdate = options?.onWorkflowUpdate

  useEffect(() => {
    if (conversationId === null || token === null) {
      setSocketStatus('idle')
      return undefined
    }

    let socket: WebSocket | null = null
    let heartbeatTimer: number | null = null
    let reconnectTimer: number | null = null
    let reconnectAttempts = 0
    let isDisposed = false

    const clearTimers = () => {
      if (heartbeatTimer !== null) {
        window.clearInterval(heartbeatTimer)
      }
      if (reconnectTimer !== null) {
        window.clearTimeout(reconnectTimer)
      }
    }

    const connect = () => {
      if (isDisposed) {
        return
      }

      setSocketStatus(reconnectAttempts === 0 ? 'connecting' : 'reconnecting')
      socket = new WebSocket(buildConversationWebSocketUrl(conversationId, token))

      socket.onopen = () => {
        reconnectAttempts = 0
        setSocketStatus('connected')
        setError(null)
        heartbeatTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) {
            socket.send('ping')
          }
        }, 20000)
      }

      socket.onmessage = (messageEvent) => {
        const event = parseConversationSocketEvent(messageEvent.data)
        if (!event || Number(event.conversation_id) !== conversationId) {
          return
        }

        switch (event.type) {
          case 'agent_status':
            if (event.payload.status === 'running') {
              startAssistantStream()
            }
            if (event.payload.status === 'done' || event.payload.status === 'failed') {
              finalizeAssistantStream()
            }
            break
          case 'token':
            appendAssistantToken(event.payload.content)
            break
          case 'log':
            addLog({
              id: `${event.timestamp}-${event.payload.agent_id}`,
              level: event.payload.level,
              message: event.payload.message,
              agentId: event.payload.agent_id,
            })
            break
          case 'workflow_update':
            updateWorkflowProgress(
              conversationId,
              event.payload.workflow_id,
              event.payload.node_id,
              event.payload.status,
              Math.round(event.payload.progress * 100),
            )
            onWorkflowUpdate?.(event)
            break
          case 'error':
            finalizeAssistantStream()
            setError(event.payload.message)
            break
          default:
            break
        }
      }

      socket.onerror = () => {
        setError('实时连接出现异常，系统正在尝试恢复')
      }

      socket.onclose = () => {
        if (heartbeatTimer !== null) {
          window.clearInterval(heartbeatTimer)
        }

        if (isDisposed) {
          return
        }

        finalizeAssistantStream()
        if (reconnectAttempts >= 3) {
          setSocketStatus('error')
          setError('实时连接已断开，请刷新页面或重新进入当前对话')
          return
        }

        reconnectAttempts += 1
        setSocketStatus('reconnecting')
        setError(`实时连接已断开，正在进行第 ${reconnectAttempts} 次重连`)
        reconnectTimer = window.setTimeout(() => {
          connect()
        }, reconnectAttempts * 1000)
      }
    }

    connect()

    return () => {
      isDisposed = true
      clearTimers()
      finalizeAssistantStream()
      setSocketStatus('idle')
      if (socket && socket.readyState !== WebSocket.CLOSED) {
        socket.close()
      }
    }
  }, [
    addLog,
    appendAssistantToken,
    conversationId,
    finalizeAssistantStream,
    setError,
    setSocketStatus,
    startAssistantStream,
    token,
    onWorkflowUpdate,
    updateWorkflowProgress,
  ])
}
