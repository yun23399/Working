import { create } from 'zustand'
import type { WorkflowPreview } from '../types/workflow'

interface WorkflowState {
  workflowsByConversation: Record<number, WorkflowPreview[]>
  loadingConversationId: number | null
  generatingConversationId: number | null
  confirmingWorkflowId: number | null
  errorMessage: string | null
  setWorkflowList: (conversationId: number, workflows: WorkflowPreview[]) => void
  upsertWorkflow: (workflow: WorkflowPreview) => void
  setLoadingConversationId: (conversationId: number | null) => void
  setGeneratingConversationId: (conversationId: number | null) => void
  setConfirmingWorkflowId: (workflowId: number | null) => void
  setError: (message: string | null) => void
  clearConversationWorkflows: (conversationId: number) => void
  clearWorkflowState: () => void
}

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

export const useWorkflowStore = create<WorkflowState>((set) => ({
  workflowsByConversation: {},
  loadingConversationId: null,
  generatingConversationId: null,
  confirmingWorkflowId: null,
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
      loadingConversationId: null,
      generatingConversationId: null,
      confirmingWorkflowId: null,
      errorMessage: null,
    }),
}))
