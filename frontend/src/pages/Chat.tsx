import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchCurrentUser } from '../api/auth'
import { ApiRequestError } from '../api/client'
import { exportWorkflowArtifactsArchive } from '../api/workflowArtifacts'
import {
  createConversation,
  fetchConversationManagerState,
  fetchConversationMessages,
  fetchConversations,
  sendChatMessage,
  startConversationTask,
  updateConversationManagerRole,
} from '../api/conversations'
import {
  confirmWorkflowPreview,
  controlWorkflow,
  createWorkflowPreview,
  executeWorkflow,
  fetchConversationWorkflows,
  fetchWorkflowRuntimeLogs,
} from '../api/workflows'
import { ChatWindow } from '../components/chat/ChatWindow'
import { MainArea } from '../components/layout/MainArea'
import { ArtifactPreviewPanel } from '../components/workspace/ArtifactPreviewPanel'
import { Sidebar } from '../components/layout/Sidebar'
import { TopNav } from '../components/layout/TopNav'
import { LogViewer } from '../components/workflow/LogViewer'
import { WorkflowConfirm } from '../components/workflow/WorkflowConfirm'
import { useWorkflowArtifacts } from '../hooks/useWorkflowArtifacts'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuthStore } from '../stores/authStore'
import { useChatStore } from '../stores/chatStore'
import {
  filterConversationsForProject,
  findProjectByConversationId,
  getProjectById,
  useProjectStore,
} from '../stores/projectStore'
import {
  getWorkflowRuntimeLogs,
  getLatestWorkflowPreview,
  useWorkflowStore,
} from '../stores/workflowStore'
import type { ChatMessage, Conversation, MessageRecord } from '../types/chat'
import { downloadBlobFile } from '../utils/export'
import type { ConversationManagerState } from '../types/chat'

const managerRoleOptions = [
  { id: 'general_manager', label: '总代理' },
  { id: 'delivery_manager', label: '交付总代理' },
  { id: 'product_manager', label: '产品总代理' },
  { id: 'technical_manager', label: '技术总代理' },
]

// 将后端消息记录映射为前端聊天时间线结构
function toChatMessage(message: MessageRecord): ChatMessage {
  return {
    id: String(message.id),
    role: message.role,
    content: message.content,
    createdAt: message.created_at,
    tokenCount: message.token_count,
  }
}

// 生成默认的新对话标题，保持时间可读性
function buildConversationTitle(): string {
  const formatter = new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    month: '2-digit',
    day: '2-digit',
  })
  return `新对话 ${formatter.format(new Date())}`
}

// 统一解析页面级请求错误文案，避免散落重复分支
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
  const workflowRefreshTimersRef = useRef<Record<string, number>>({})
  const [artifactExportError, setArtifactExportError] = useState<string | null>(null)
  const [isExportingArtifacts, setIsExportingArtifacts] = useState(false)
  const [selectedArtifactPath, setSelectedArtifactPath] = useState<string | null>(null)
  const [managerState, setManagerState] = useState<ConversationManagerState | null>(null)
  const [isLoadingManagerState, setIsLoadingManagerState] = useState(false)
  const [isStartingTask, setIsStartingTask] = useState(false)
  const [isUpdatingManagerRole, setIsUpdatingManagerRole] = useState(false)
  const clearSession = useAuthStore((state) => state.clearSession)
  const setUser = useAuthStore((state) => state.setUser)
  const token = useAuthStore((state) => state.token)
  const user = useAuthStore((state) => state.user)
  const activeProjectId = useProjectStore((state) => state.activeProjectId)
  const attachConversationToActiveProject = useProjectStore(
    (state) => state.attachConversationToActiveProject,
  )
  const projects = useProjectStore((state) => state.projects)
  const setActiveProjectId = useProjectStore((state) => state.setActiveProjectId)
  const syncProjectConversations = useProjectStore((state) => state.syncConversations)

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
  const workflowsByConversation = useWorkflowStore((state) => state.workflowsByConversation)
  const workflowLogsByWorkflowId = useWorkflowStore((state) => state.workflowLogsByWorkflowId)
  const workflowErrorMessage = useWorkflowStore((state) => state.errorMessage)
  const loadingConversationId = useWorkflowStore((state) => state.loadingConversationId)
  const generatingConversationId = useWorkflowStore((state) => state.generatingConversationId)
  const confirmingWorkflowId = useWorkflowStore((state) => state.confirmingWorkflowId)
  const executingWorkflowId = useWorkflowStore((state) => state.executingWorkflowId)
  const controllingWorkflowId = useWorkflowStore((state) => state.controllingWorkflowId)
  const setWorkflowList = useWorkflowStore((state) => state.setWorkflowList)
  const upsertWorkflow = useWorkflowStore((state) => state.upsertWorkflow)
  const appendWorkflowRuntimeLog = useWorkflowStore((state) => state.appendRuntimeLog)
  const replaceWorkflowRuntimeLogs = useWorkflowStore((state) => state.replaceRuntimeLogs)
  const clearWorkflowRuntimeLogs = useWorkflowStore((state) => state.clearRuntimeLogs)
  const setWorkflowLoadingConversationId = useWorkflowStore(
    (state) => state.setLoadingConversationId,
  )
  const setWorkflowGeneratingConversationId = useWorkflowStore(
    (state) => state.setGeneratingConversationId,
  )
  const setWorkflowConfirmingWorkflowId = useWorkflowStore(
    (state) => state.setConfirmingWorkflowId,
  )
  const setWorkflowExecutingWorkflowId = useWorkflowStore(
    (state) => state.setExecutingWorkflowId,
  )
  const setWorkflowControllingWorkflowId = useWorkflowStore(
    (state) => state.setControllingWorkflowId,
  )
  const setWorkflowError = useWorkflowStore((state) => state.setError)
  const clearWorkflowState = useWorkflowStore((state) => state.clearWorkflowState)
  const activeProject = getProjectById(projects, activeProjectId)
  const activeConversation =
    conversations.find((conversation) => conversation.id === activeConversationId) ?? null
  const visibleConversations = filterConversationsForProject(
    projects,
    activeProjectId,
    conversations,
  )
  const activeWorkflowPreview = getLatestWorkflowPreview(
    workflowsByConversation,
    activeConversationId,
  )
  const workflowRuntimeLogs = getWorkflowRuntimeLogs(
    workflowLogsByWorkflowId,
    activeWorkflowPreview?.workflow_id ?? null,
  )
  const hasUserMessages = messages.some((message) => message.role === 'user')
  const canGenerateWorkflow =
    activeConversationId !== null && hasUserMessages && !isBootstrapping
  const isLoadingWorkflow =
    activeConversationId !== null && loadingConversationId === activeConversationId
  const isGeneratingWorkflow =
    activeConversationId !== null && generatingConversationId === activeConversationId
  const isConfirmingWorkflow =
    activeWorkflowPreview !== null && confirmingWorkflowId === activeWorkflowPreview.workflow_id
  const isExecutingWorkflow =
    activeWorkflowPreview !== null && executingWorkflowId === activeWorkflowPreview.workflow_id
  const isControllingWorkflow =
    activeWorkflowPreview !== null && controllingWorkflowId === activeWorkflowPreview.workflow_id
  const chatWindowLogs = activityLogs.filter(
    (log) => log.agentId === 'system' || log.agentId === 'manager',
  )

  const handleUnauthorized = useCallback(() => {
    clearSession()
    clearChatState()
    clearWorkflowState()
    navigate('/login', { replace: true })
  }, [clearChatState, clearSession, clearWorkflowState, navigate])

  const {
    artifacts: workflowArtifacts,
    artifactListError,
    imageObjectUrl,
    isLoadingArtifacts,
    isLoadingPreview,
    previewError,
    previewText,
    selectedArtifact,
  } = useWorkflowArtifacts({
    conversationId: activeConversationId,
    workflowId: activeWorkflowPreview?.workflow_id ?? null,
    selectedArtifactPath,
    token,
    onUnauthorized: handleUnauthorized,
  })

  useEffect(() => {
    if (!token) {
      navigate('/login', { replace: true })
    }
  }, [navigate, token])

  const loadManagerState = useCallback(
    async (conversationId: number, authToken: string) => {
      setIsLoadingManagerState(true)
      try {
        const nextManagerState = await fetchConversationManagerState(authToken, conversationId)
        setManagerState(nextManagerState)
      } catch (error) {
        if (error instanceof ApiRequestError && error.status === 401) {
          handleUnauthorized()
          return
        }
      } finally {
        setIsLoadingManagerState(false)
      }
    },
    [handleUnauthorized],
  )

  const loadMessages = useCallback(async (nextConversationId: number, authToken: string) => {
    try {
      setArtifactExportError(null)
      const records = await fetchConversationMessages(authToken, nextConversationId)
      setMessages(records.map(toChatMessage))
      setActiveConversationId(nextConversationId)
      void loadManagerState(nextConversationId, authToken)
      setError(null)
    } catch (error) {
      const message = resolveChatError(error)
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }
      setError(message)
    }
  }, [
    handleUnauthorized,
    loadManagerState,
    setActiveConversationId,
    setArtifactExportError,
    setError,
    setMessages,
  ])

  const refreshConversationRuntimeState = useCallback(
    async (conversationId: number, authToken: string) => {
      try {
        const [workflows, records] = await Promise.all([
          fetchConversationWorkflows(authToken, conversationId),
          fetchConversationMessages(authToken, conversationId),
        ])
        setWorkflowList(conversationId, workflows)
        setMessages(records.map(toChatMessage))
        touchConversation(conversationId)
        setError(null)
        setWorkflowError(null)
      } catch (error) {
        if (error instanceof ApiRequestError && error.status === 401) {
          handleUnauthorized()
          return
        }

        setWorkflowError(resolveChatError(error))
      }
    },
    [
      handleUnauthorized,
      setError,
      setMessages,
      setWorkflowError,
      setWorkflowList,
      touchConversation,
    ],
  )

  const scheduleWorkflowRefresh = useCallback(
    (conversationId: number, workflowId: number, delayMs: number) => {
      if (!token) {
        return
      }

      const refreshKey = `${conversationId}-${workflowId}`
      const existingTimer = workflowRefreshTimersRef.current[refreshKey]
      if (existingTimer !== undefined) {
        window.clearTimeout(existingTimer)
      }

      workflowRefreshTimersRef.current[refreshKey] = window.setTimeout(() => {
        delete workflowRefreshTimersRef.current[refreshKey]
        void refreshConversationRuntimeState(conversationId, token)
      }, delayMs)
    },
    [refreshConversationRuntimeState, token],
  )

  const handleWorkflowUpdateEvent = useCallback(
    (event: {
      conversation_id: string
      payload: {
        workflow_id: number
        node_id: string
        status: string
        progress: number
      }
    }) => {
      const nextConversationId = Number(event.conversation_id)
      if (!Number.isFinite(nextConversationId) || activeConversationId !== nextConversationId) {
        return
      }

      if (event.payload.status === 'done' || event.payload.status === 'failed') {
        scheduleWorkflowRefresh(nextConversationId, event.payload.workflow_id, 250)
      }

      if (
        event.payload.progress >= 1 ||
        event.payload.status === 'failed' ||
        event.payload.node_id === 'workflow'
      ) {
        scheduleWorkflowRefresh(nextConversationId, event.payload.workflow_id, 500)
      }
    },
    [activeConversationId, scheduleWorkflowRefresh],
  )

  const handleWorkflowLogEvent = useCallback(
    (event: {
      timestamp: string
      payload: {
        level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
        message: string
        agent_id: string
      }
    }) => {
      if (
        activeWorkflowPreview === null ||
        (event.payload.agent_id !== 'orchestrator' &&
          !event.payload.agent_id.startsWith('node_'))
      ) {
        return
      }

      appendWorkflowRuntimeLog(activeWorkflowPreview.workflow_id, {
        id: `${event.timestamp}-${event.payload.agent_id}`,
        level: event.payload.level,
        message: event.payload.message,
        agentId: event.payload.agent_id,
        timestamp: event.timestamp,
      })
    },
    [activeWorkflowPreview, appendWorkflowRuntimeLog],
  )

  useWebSocket(activeConversationId, token, {
    onLogEvent: handleWorkflowLogEvent,
    onWorkflowUpdate: handleWorkflowUpdateEvent,
    onAgentDone: (event) => {
      if (
        event.payload.agent_id === 'manager' &&
        activeConversationId !== null &&
        token
      ) {
        void loadManagerState(activeConversationId, token)
      }
    },
  })

  useEffect(() => {
    return () => {
      Object.values(workflowRefreshTimersRef.current).forEach((timerId) => {
        window.clearTimeout(timerId)
      })
      workflowRefreshTimersRef.current = {}
    }
  }, [])

  useEffect(() => {
    if (!token || activeConversationId === null || activeWorkflowPreview === null) {
      return
    }

    let isCurrent = true

    const loadWorkflowRuntimeLogs = async () => {
      try {
        const runtimeLogs = await fetchWorkflowRuntimeLogs(
          token,
          activeConversationId,
          activeWorkflowPreview.workflow_id,
        )
        if (!isCurrent) {
          return
        }

        replaceWorkflowRuntimeLogs(
          activeWorkflowPreview.workflow_id,
          runtimeLogs.map((log) => ({
            id: log.id,
            level: log.level,
            message: log.message,
            agentId: log.agent_id,
            timestamp: log.timestamp,
          })),
        )
      } catch (error) {
        if (error instanceof ApiRequestError && error.status === 401) {
          handleUnauthorized()
        }
      }
    }

    void loadWorkflowRuntimeLogs()

    return () => {
      isCurrent = false
    }
  }, [
    activeConversationId,
    activeWorkflowPreview,
    handleUnauthorized,
    replaceWorkflowRuntimeLogs,
    token,
  ])

  const createConversationForCurrentProject = useCallback(async (authToken: string) => {
    try {
      setCreatingConversation(true)
      const conversation = await createConversation(authToken, {
        title: buildConversationTitle(),
        manager_role: 'general_manager',
      })
      prependConversation(conversation)
      attachConversationToActiveProject(conversation.id)
      syncProjectConversations([...conversations, conversation])
      setWorkflowList(conversation.id, [])
      setWorkflowError(null)
      setError(null)
      return conversation
    } catch (error) {
      const message = resolveChatError(error)
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return null
      }
      setError(message)
      return null
    } finally {
      setCreatingConversation(false)
    }
  }, [
    attachConversationToActiveProject,
    conversations,
    handleUnauthorized,
    prependConversation,
    setCreatingConversation,
    setError,
    setWorkflowError,
    setWorkflowList,
    syncProjectConversations,
  ])

  const handleCreateConversation = async () => {
    if (!token) {
      handleUnauthorized()
      return
    }

    try {
      const conversation = await createConversationForCurrentProject(token)
      if (!conversation) {
        return
      }

      setActiveConversationId(conversation.id)
      resetMessages()
      setDraft('')
      setError(null)
    } catch (error) {
      const message = resolveChatError(error)
      setError(message)
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
        syncProjectConversations(items)

        if (items.length === 0) {
          const firstConversation = await createConversationForCurrentProject(token)
          if (!firstConversation) {
            return
          }

          setActiveConversationId(firstConversation.id)
          resetMessages()
        } else {
          const projectState = useProjectStore.getState()
          const projectConversations = filterConversationsForProject(
            projectState.projects,
            projectState.activeProjectId,
            items,
          )
          const chatState = useChatStore.getState()
          const nextConversation =
            projectConversations.find(
              (conversation) => conversation.id === chatState.activeConversationId,
            ) ??
            projectConversations[0] ??
            null
          if (!nextConversation) {
            setActiveConversationId(null)
            resetMessages()
            setManagerState(null)
            setError(null)
            return
          }

          const ownerProject = findProjectByConversationId(
            projectState.projects,
            nextConversation.id,
          )

          if (ownerProject && ownerProject.id !== projectState.activeProjectId) {
            setActiveProjectId(ownerProject.id)
          }

          await loadMessages(nextConversation.id, token)
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
    createConversationForCurrentProject,
    handleUnauthorized,
    loadMessages,
    resetMessages,
    setActiveConversationId,
    setBootstrapping,
    setConversations,
    setError,
    setActiveProjectId,
    setUser,
    syncProjectConversations,
    user,
    token,
  ])

  useEffect(() => {
    if (!token || activeConversationId === null) {
      setWorkflowLoadingConversationId(null)
      setWorkflowError(null)
      return
    }

    let isCurrent = true

    const loadWorkflowPreview = async () => {
      setWorkflowLoadingConversationId(activeConversationId)
      setWorkflowError(null)

      try {
        const workflows = await fetchConversationWorkflows(token, activeConversationId)
        if (!isCurrent) {
          return
        }

        setWorkflowList(activeConversationId, workflows)
      } catch (error) {
        if (error instanceof ApiRequestError && error.status === 401) {
          handleUnauthorized()
          return
        }

        if (isCurrent) {
          setWorkflowError(resolveChatError(error))
        }
      } finally {
        if (isCurrent) {
          setWorkflowLoadingConversationId(null)
        }
      }
    }

    void loadWorkflowPreview()

    return () => {
      isCurrent = false
    }
  }, [
    activeConversationId,
    handleUnauthorized,
    setWorkflowError,
    setWorkflowList,
    setWorkflowLoadingConversationId,
    token,
  ])

  const handleSelectConversation = async (conversation: Conversation) => {
    if (!token) {
      handleUnauthorized()
      return
    }

    try {
      setBootstrapping(true)
      const ownerProject = findProjectByConversationId(projects, conversation.id)
      if (ownerProject && ownerProject.id !== activeProjectId) {
        setActiveProjectId(ownerProject.id)
      }

      await loadMessages(conversation.id, token)
    } catch (error) {
      setError(resolveChatError(error))
    } finally {
      setBootstrapping(false)
    }
  }

  const handleSelectProject = async (projectId: string) => {
    if (!token) {
      handleUnauthorized()
      return
    }

    try {
      setBootstrapping(true)
      setActiveProjectId(projectId)
      const nextProjectState = useProjectStore.getState()
      const nextVisibleConversations = filterConversationsForProject(
        nextProjectState.projects,
        projectId,
        conversations,
      )

      if (nextVisibleConversations.length === 0) {
        setActiveConversationId(null)
        resetMessages()
        setManagerState(null)
        setError(null)
        return
      }

      await loadMessages(nextVisibleConversations[0].id, token)
    } catch (error) {
      setError(resolveChatError(error))
    } finally {
      setBootstrapping(false)
    }
  }

  const handleSendMessage = async () => {
    if (!token) {
      handleUnauthorized()
      return
    }

    if (activeConversationId === null) {
      try {
        const conversation = await createConversationForCurrentProject(token)
        if (!conversation) {
          return
        }

        setActiveConversationId(conversation.id)
        resetMessages()
        setError('已为当前项目创建首条对话，请等待实时连接建立后再发送消息')
      } catch (error) {
        setError(resolveChatError(error))
      }
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
      void loadManagerState(activeConversationId, token)
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

  const handleGenerateWorkflowPreview = async (forceReplan: boolean) => {
    if (!token) {
      handleUnauthorized()
      return
    }

    if (activeConversationId === null) {
      setWorkflowError('请先创建或选择一条对话，再生成工作流预览')
      return
    }

    if (!hasUserMessages) {
      setWorkflowError('请先发送至少一条用户需求，再生成工作流预览')
      return
    }

    setWorkflowGeneratingConversationId(activeConversationId)
    setWorkflowError(null)
    setArtifactExportError(null)

    try {
      const preview = await createWorkflowPreview(token, activeConversationId, {
        force_replan: forceReplan,
        pause_after_nodes: ['node_1'],
      })
      upsertWorkflow(preview)
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }

      setWorkflowError(resolveChatError(error))
    } finally {
      setWorkflowGeneratingConversationId(null)
    }
  }

  const handleUpdateManagerRole = async (managerRole: string) => {
    if (!token || activeConversationId === null) {
      return
    }

    setIsUpdatingManagerRole(true)
    setError(null)

    try {
      const updatedConversation = await updateConversationManagerRole(
        token,
        activeConversationId,
        managerRole,
      )
      setConversations(
        conversations.map((conversation) =>
          conversation.id === updatedConversation.id ? updatedConversation : conversation,
        ),
      )
      void loadManagerState(activeConversationId, token)
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }

      setError(resolveChatError(error))
    } finally {
      setIsUpdatingManagerRole(false)
    }
  }

  const handleStartTaskFromManager = async () => {
    if (!token || activeConversationId === null) {
      return
    }

    setIsStartingTask(true)
    setWorkflowError(null)
    setArtifactExportError(null)

    try {
      const workflow = await startConversationTask(token, activeConversationId)
      upsertWorkflow(workflow)
      void loadManagerState(activeConversationId, token)
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }

      setWorkflowError(resolveChatError(error))
    } finally {
      setIsStartingTask(false)
    }
  }

  const handleConfirmWorkflowPreview = async () => {
    if (!token) {
      handleUnauthorized()
      return
    }

    if (activeConversationId === null || !activeWorkflowPreview) {
      setWorkflowError('当前还没有可确认的工作流预览')
      return
    }

    setWorkflowConfirmingWorkflowId(activeWorkflowPreview.workflow_id)
    setWorkflowError(null)
    setArtifactExportError(null)

    try {
      const confirmedWorkflow = await confirmWorkflowPreview(
        token,
        activeConversationId,
        activeWorkflowPreview.workflow_id,
      )
      upsertWorkflow(confirmedWorkflow)
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }

      setWorkflowError(resolveChatError(error))
    } finally {
      setWorkflowConfirmingWorkflowId(null)
    }
  }

  const handleExecuteWorkflow = async () => {
    if (!token) {
      handleUnauthorized()
      return
    }

    if (activeConversationId === null || !activeWorkflowPreview) {
      setWorkflowError('当前还没有可执行的工作流')
      return
    }

    setWorkflowExecutingWorkflowId(activeWorkflowPreview.workflow_id)
    setWorkflowError(null)
    setArtifactExportError(null)

    try {
      clearWorkflowRuntimeLogs(activeWorkflowPreview.workflow_id)
      const runningWorkflow = await executeWorkflow(
        token,
        activeConversationId,
        activeWorkflowPreview.workflow_id,
      )
      upsertWorkflow(runningWorkflow)
      scheduleWorkflowRefresh(activeConversationId, activeWorkflowPreview.workflow_id, 400)
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }

      setWorkflowError(resolveChatError(error))
    } finally {
      setWorkflowExecutingWorkflowId(null)
    }
  }

  const handleControlWorkflow = async (
    action: 'pause' | 'resume' | 'abort' | 'redirect',
  ) => {
    if (!token) {
      handleUnauthorized()
      return
    }

    if (activeConversationId === null || !activeWorkflowPreview) {
      setWorkflowError('当前还没有可控制的工作流')
      return
    }

    setWorkflowControllingWorkflowId(activeWorkflowPreview.workflow_id)
    setWorkflowError(null)
    setArtifactExportError(null)

    try {
      const redirectInstruction =
        action === 'redirect'
          ? '请在当前断点基础上补充更偏文档交付的说明后继续执行。'
          : undefined
      const nextWorkflow = await controlWorkflow(
        token,
        activeConversationId,
        activeWorkflowPreview.workflow_id,
        {
          action,
          redirect_instruction: redirectInstruction,
        },
      )
      upsertWorkflow(nextWorkflow)
      scheduleWorkflowRefresh(
        activeConversationId,
        activeWorkflowPreview.workflow_id,
        500,
      )
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }

      setWorkflowError(resolveChatError(error))
    } finally {
      setWorkflowControllingWorkflowId(null)
    }
  }

  const handleExportArtifacts = async () => {
    if (!token) {
      handleUnauthorized()
      return
    }

    if (activeConversationId === null || activeWorkflowPreview === null) {
      setArtifactExportError('当前还没有可导出的工作流产物')
      return
    }

    setIsExportingArtifacts(true)
    setArtifactExportError(null)

    try {
      const archiveBlob = await exportWorkflowArtifactsArchive(
        token,
        activeConversationId,
        activeWorkflowPreview.workflow_id,
      )
      downloadBlobFile(
        archiveBlob,
        `workflow_${activeWorkflowPreview.workflow_id}_artifacts.zip`,
      )
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        handleUnauthorized()
        return
      }

      setArtifactExportError(resolveChatError(error))
    } finally {
      setIsExportingArtifacts(false)
    }
  }

  const handleLogout = () => {
    clearSession()
    clearChatState()
    clearWorkflowState()
    navigate('/login', { replace: true })
  }

  const handleOpenProjects = () => {
    navigate('/projects')
  }

  const handleOpenSettings = () => {
    navigate('/settings')
  }

  return (
    <main className="min-h-screen p-6">
      <section className="mx-auto grid min-h-[720px] max-w-7xl grid-cols-[300px_1fr] grid-rows-[56px_1fr] overflow-hidden rounded-[28px] border border-line bg-surface-panel shadow-panel">
        <TopNav
          conversationTitle={activeConversation?.title ?? null}
          projectName={activeProject?.name ?? '未命名项目'}
          username={user?.username ?? null}
          socketStatus={socketStatus}
          onLogout={handleLogout}
          onOpenProjects={handleOpenProjects}
          onOpenSettings={handleOpenSettings}
        />
        <Sidebar
          activeProjectId={activeProjectId}
          conversations={visibleConversations}
          activeConversationId={activeConversationId}
          isCreatingConversation={isCreatingConversation}
          projects={projects}
          onCreateConversation={handleCreateConversation}
          onSelectProject={handleSelectProject}
          onSelectConversation={handleSelectConversation}
        />
        <MainArea
          activeConversationTitle={activeConversation?.title ?? null}
          conversationCount={visibleConversations.length}
          projectName={activeProject?.name ?? '未命名项目'}
          projectSummary={
            activeProject?.summary ?? '当前还没有项目摘要，后续阶段会接入真实项目实体。'
          }
        >
          <div className="flex h-full min-h-0 flex-col gap-4 p-4">
            <section className="shrink-0 overflow-hidden rounded-[24px] border border-line bg-[linear-gradient(180deg,rgba(255,255,255,0.96)_0%,rgba(245,240,231,0.98)_100%)] shadow-sm">
              <div className="border-b border-line/80 px-6 py-5">
                <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                  <div>
                    <div className="inline-flex items-center gap-2 rounded-full bg-[#ebe7db] px-3 py-1 text-xs text-ink-soft">
                      阶段五 · 总代理需求收集
                    </div>
                    <h2 className="mt-3 text-xl font-semibold text-ink">
                      先把需求问完整，再由总代理自动组建执行 Agent
                    </h2>
                    <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-soft">
                      用户先配置模型并选择总代理角色，在聊天中逐步补齐目标、范围、约束和验收标准。当总代理判断信息足够完整后，才进入任务启动与自动拆分。
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {managerRoleOptions.map((role) => {
                      const isSelected = activeConversation?.manager_role === role.id
                      return (
                        <button
                          key={role.id}
                          type="button"
                          onClick={() => {
                            void handleUpdateManagerRole(role.id)
                          }}
                          disabled={activeConversationId === null || isUpdatingManagerRole}
                          className={`rounded-full px-3 py-2 text-xs transition ${
                            isSelected
                              ? 'bg-[#1f1c17] text-white'
                              : 'border border-line bg-white text-ink-soft'
                          } disabled:cursor-not-allowed disabled:opacity-60`}
                        >
                          {role.label}
                        </button>
                      )
                    })}
                  </div>
                </div>
              </div>

              <div className="grid gap-4 px-6 py-5 xl:grid-cols-[1.1fr_0.9fr]">
                <div className="space-y-4">
                  <div className="rounded-[20px] border border-line bg-white/80 px-5 py-5">
                    <div className="text-sm font-medium text-ink">总代理准备进度</div>
                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#ece7dc]">
                      <div
                        className="h-full rounded-full bg-[#4c6ef5] transition-all"
                        style={{
                          width: `${managerState?.manager_progress.completion_score ?? 0}%`,
                        }}
                      />
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-ink-faint">
                      <span>
                        当前完成度：{managerState?.manager_progress.completion_score ?? '--'}%
                      </span>
                      <span>
                        开始阈值：{managerState?.manager_progress.readiness_threshold ?? '--'}%
                      </span>
                      <span>
                        状态：
                        {managerState?.manager_progress.is_ready_to_start
                          ? ' 可开始任务'
                          : ' 继续收集需求'}
                      </span>
                    </div>
                    <div className="mt-4 rounded-[18px] border border-line bg-[#faf7f0] px-4 py-3 text-sm text-ink-soft">
                      {isLoadingManagerState
                        ? '正在同步总代理理解进度...'
                        : managerState?.manager_progress.summary ??
                          '当前还没有总代理状态，请先发送需求消息。'}
                    </div>
                  </div>

                  <div className="rounded-[20px] border border-line bg-white/80 px-5 py-5">
                    <div className="text-sm font-medium text-ink">已收集到的任务点</div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(managerState?.manager_progress.collected_points ?? []).length > 0 ? (
                        managerState?.manager_progress.collected_points.map((item) => (
                          <span
                            key={item}
                            className="rounded-full bg-[#ece7dc] px-3 py-1 text-xs text-ink-soft"
                          >
                            {item}
                          </span>
                        ))
                      ) : (
                        <span className="text-sm text-ink-faint">暂未提取到关键点。</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="rounded-[20px] border border-line bg-[#fbf8f2] px-5 py-5">
                    <div className="text-sm font-medium text-ink">当前仍缺的信息</div>
                    <div className="mt-3 space-y-2">
                      {(managerState?.manager_progress.missing_slots ?? []).length > 0 ? (
                        managerState?.manager_progress.missing_slots.map((item) => (
                          <div
                            key={item}
                            className="rounded-2xl border border-line bg-white/90 px-4 py-3 text-sm text-ink-soft"
                          >
                            {item}
                          </div>
                        ))
                      ) : (
                        <div className="rounded-2xl border border-line bg-white/90 px-4 py-3 text-sm text-ink-soft">
                          当前关键信息已经补齐，可以考虑开始任务。
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="rounded-[20px] border border-line bg-[#fbf8f2] px-5 py-5">
                    <div className="text-sm font-medium text-ink">总代理建议下一步问什么</div>
                    <div className="mt-3 space-y-2">
                      {(managerState?.manager_progress.suggested_next_questions ?? []).length > 0 ? (
                        managerState?.manager_progress.suggested_next_questions.map((item) => (
                          <div
                            key={item}
                            className="rounded-2xl border border-line bg-white/90 px-4 py-3 text-sm text-ink-soft"
                          >
                            {item}
                          </div>
                        ))
                      ) : (
                        <div className="rounded-2xl border border-line bg-white/90 px-4 py-3 text-sm text-ink-soft">
                          当前没有更多必问项。
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        void handleStartTaskFromManager()
                      }}
                      disabled={
                        activeConversationId === null ||
                        !managerState?.manager_progress.is_ready_to_start ||
                        isStartingTask
                      }
                      className="mt-4 inline-flex items-center justify-center rounded-2xl bg-[#4c6ef5] px-4 py-3 text-sm text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {isStartingTask ? '总代理正在创建任务...' : '开始任务'}
                    </button>
                  </div>
                </div>
              </div>
            </section>
            <WorkflowConfirm
              workflow={activeWorkflowPreview}
              hasConversation={activeConversationId !== null}
              canGenerate={canGenerateWorkflow}
              errorMessage={workflowErrorMessage}
              isLoading={isLoadingWorkflow}
              isGenerating={isGeneratingWorkflow}
              isConfirming={isConfirmingWorkflow}
              isExecuting={isExecutingWorkflow}
              isControlling={isControllingWorkflow}
              onGenerate={() => {
                void handleGenerateWorkflowPreview(false)
              }}
              onReplan={() => {
                void handleGenerateWorkflowPreview(true)
              }}
              onConfirm={() => {
                void handleConfirmWorkflowPreview()
              }}
              onExecute={() => {
                void handleExecuteWorkflow()
              }}
              onPause={() => {
                void handleControlWorkflow('pause')
              }}
              onResume={() => {
                void handleControlWorkflow('resume')
              }}
              onAbort={() => {
                void handleControlWorkflow('abort')
              }}
              onRedirect={() => {
                void handleControlWorkflow('redirect')
              }}
            />
            <div className="grid min-h-0 gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
              <ArtifactPreviewPanel
                artifactListError={artifactListError}
                artifacts={workflowArtifacts}
                exportError={artifactExportError}
                isExporting={isExportingArtifacts}
                isLoadingArtifacts={isLoadingArtifacts}
                isLoadingPreview={isLoadingPreview}
                previewError={previewError}
                previewImageUrl={imageObjectUrl}
                previewText={previewText}
                selectedArtifact={selectedArtifact}
                workflow={activeWorkflowPreview}
                onExportArtifacts={() => {
                  void handleExportArtifacts()
                }}
                onSelectArtifact={setSelectedArtifactPath}
              />
              <LogViewer logs={workflowRuntimeLogs} />
            </div>
            <div className="min-h-0 flex-1 overflow-hidden rounded-[24px] border border-line bg-white/80 shadow-sm">
              <ChatWindow
                key={activeConversationId ?? 'empty-conversation'}
                draft={draft}
                errorMessage={errorMessage}
                isBootstrapping={isBootstrapping}
                isSending={isSending}
                isStreaming={isStreaming}
                logs={chatWindowLogs}
                messages={messages}
                socketStatus={socketStatus}
                onDraftChange={setDraft}
                onSend={handleSendMessage}
              />
            </div>
          </div>
        </MainArea>
      </section>
    </main>
  )
}
