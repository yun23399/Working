import { create } from 'zustand'
import type { ActivityLog } from '../types/chat'
import type { WorkflowExecutionLog, WorkflowPreview } from '../types/workflow'

interface WorkflowState {
  workflowsByConversation: Record<number, WorkflowPreview[]>
  workflowLogsByWorkflowId: Record<number, ActivityLog[]>
  loadingConversationId: number | null
  generatingConversationId: number | null
  confirmingWorkflowId: number | null
  executingWorkflowId: number | null
  controllingWorkflowId: number | null
  errorMessage: string | null
  setWorkflowList: (conversationId: number, workflows: WorkflowPreview[]) => void
  upsertWorkflow: (workflow: WorkflowPreview) => void
  setLoadingConversationId: (conversationId: number | null) => void
  setGeneratingConversationId: (conversationId: number | null) => void
  setConfirmingWorkflowId: (workflowId: number | null) => void
  setExecutingWorkflowId: (workflowId: number | null) => void
  setControllingWorkflowId: (workflowId: number | null) => void
  updateWorkflowProgress: (
    conversationId: number,
    workflowId: number,
    nodeId: string,
    status: string,
    progress: number,
  ) => void
  appendExecutionLog: (
    conversationId: number,
    workflowId: number,
    executionLog: WorkflowExecutionLog,
  ) => void
  appendRuntimeLog: (workflowId: number, log: ActivityLog) => void
  replaceRuntimeLogs: (workflowId: number, logs: ActivityLog[]) => void
  clearRuntimeLogs: (workflowId: number) => void
  setError: (message: string | null) => void
  clearConversationWorkflows: (conversationId: number) => void
  clearWorkflowState: () => void
}

const maxWorkflowLogCount = 80

// 按更新时间倒序整理工作流列表，保证最新预览排在最前面
function sortWorkflows(workflows: WorkflowPreview[]): WorkflowPreview[] {
  return [...workflows].sort((left, right) => {
    const timeDiff =
      new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime()

    if (timeDiff !== 0) {
      return timeDiff
    }

    return right.workflow_id - left.workflow_id
  })
}

// 读取指定对话的最新工作流预览
export function getLatestWorkflowPreview(
  workflowsByConversation: Record<number, WorkflowPreview[]>,
  conversationId: number | null,
): WorkflowPreview | null {
  if (conversationId === null) {
    return null
  }

  const workflowList = workflowsByConversation[conversationId] ?? []
  return workflowList[0] ?? null
}

// 读取指定工作流的实时日志列表
export function getWorkflowRuntimeLogs(
  workflowLogsByWorkflowId: Record<number, ActivityLog[]>,
  workflowId: number | null,
): ActivityLog[] {
  if (workflowId === null) {
    return []
  }

  return workflowLogsByWorkflowId[workflowId] ?? []
}

export const useWorkflowStore = create<WorkflowState>((set) => ({
  workflowsByConversation: {},
  workflowLogsByWorkflowId: {},
  loadingConversationId: null,
  generatingConversationId: null,
  confirmingWorkflowId: null,
  executingWorkflowId: null,
  controllingWorkflowId: null,
  errorMessage: null,
  setWorkflowList: (conversationId, workflows) =>
    set((state) => ({
      workflowsByConversation: {
        ...state.workflowsByConversation,
        [conversationId]: sortWorkflows(workflows),
      },
    })),
  upsertWorkflow: (workflow) =>
    set((state) => {
      const currentList = state.workflowsByConversation[workflow.conversation_id] ?? []
      const nextList = sortWorkflows([
        workflow,
        ...currentList.filter((item) => item.workflow_id !== workflow.workflow_id),
      ])

      return {
        workflowsByConversation: {
          ...state.workflowsByConversation,
          [workflow.conversation_id]: nextList,
        },
      }
    }),
  setLoadingConversationId: (loadingConversationId) => set({ loadingConversationId }),
  setGeneratingConversationId: (generatingConversationId) =>
    set({ generatingConversationId }),
  setConfirmingWorkflowId: (confirmingWorkflowId) => set({ confirmingWorkflowId }),
  setExecutingWorkflowId: (executingWorkflowId) => set({ executingWorkflowId }),
  setControllingWorkflowId: (controllingWorkflowId) => set({ controllingWorkflowId }),
  updateWorkflowProgress: (conversationId, workflowId, nodeId, status, progress) =>
    set((state) => {
      const currentList = state.workflowsByConversation[conversationId] ?? []
      return {
        workflowsByConversation: {
          ...state.workflowsByConversation,
          [conversationId]: currentList.map((workflow) => {
            if (workflow.workflow_id !== workflowId) {
              return workflow
            }

            const normalizedStatus =
              status === 'failed'
                ? 'failed'
                : status === 'done' && progress >= 100
                  ? 'completed'
                  : workflow.status === 'confirmed' && status === 'running'
                    ? 'running'
                    : workflow.status

            return {
              ...workflow,
              status: normalizedStatus,
              progress,
              dag: {
                ...workflow.dag,
                nodes: workflow.dag.nodes.map((node) =>
                  node.id === nodeId
                    ? {
                        ...node,
                        runtime_status: status,
                      }
                    : node,
                ),
              },
            }
          }),
        },
      }
    }),
  appendExecutionLog: (conversationId, workflowId, executionLog) =>
    set((state) => {
      const currentList = state.workflowsByConversation[conversationId] ?? []
      return {
        workflowsByConversation: {
          ...state.workflowsByConversation,
          [conversationId]: currentList.map((workflow) => {
            if (workflow.workflow_id !== workflowId) {
              return workflow
            }

            return {
              ...workflow,
              execution_logs: [
                ...workflow.execution_logs.filter(
                  (item) => item.node_id !== executionLog.node_id,
                ),
                executionLog,
              ],
            }
          }),
        },
      }
    }),
  appendRuntimeLog: (workflowId, log) =>
    set((state) => ({
      workflowLogsByWorkflowId: {
        ...state.workflowLogsByWorkflowId,
        [workflowId]: [
          ...(state.workflowLogsByWorkflowId[workflowId] ?? []),
          log,
        ].slice(-maxWorkflowLogCount),
      },
    })),
  replaceRuntimeLogs: (workflowId, logs) =>
    set((state) => ({
      workflowLogsByWorkflowId: {
        ...state.workflowLogsByWorkflowId,
        [workflowId]: logs.slice(-maxWorkflowLogCount),
      },
    })),
  clearRuntimeLogs: (workflowId) =>
    set((state) => {
      const nextLogs = { ...state.workflowLogsByWorkflowId }
      delete nextLogs[workflowId]

      return {
        workflowLogsByWorkflowId: nextLogs,
      }
    }),
  setError: (errorMessage) => set({ errorMessage }),
  clearConversationWorkflows: (conversationId) =>
    set((state) => {
      const nextMap = { ...state.workflowsByConversation }
      delete nextMap[conversationId]

      return {
        workflowsByConversation: nextMap,
      }
    }),
  clearWorkflowState: () =>
    set({
      workflowsByConversation: {},
      workflowLogsByWorkflowId: {},
      loadingConversationId: null,
      generatingConversationId: null,
      confirmingWorkflowId: null,
      executingWorkflowId: null,
      controllingWorkflowId: null,
      errorMessage: null,
    }),
}))
