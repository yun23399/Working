import { requestJson } from './client'
import type { WorkflowPreview, WorkflowPreviewRequest } from '../types/workflow'

// 读取指定对话下的工作流预览列表
export async function fetchConversationWorkflows(
  token: string,
  conversationId: number,
): Promise<WorkflowPreview[]> {
  return requestJson<WorkflowPreview[]>(`/api/workflows/${conversationId}`, {
    token,
  })
}

// 生成或刷新当前对话的工作流预览
export async function createWorkflowPreview(
  token: string,
  conversationId: number,
  payload: WorkflowPreviewRequest,
): Promise<WorkflowPreview> {
  return requestJson<WorkflowPreview>(`/api/workflows/${conversationId}/preview`, {
    method: 'POST',
    token,
    body: payload,
  })
}

// 确认指定工作流预览
export async function confirmWorkflowPreview(
  token: string,
  conversationId: number,
  workflowId: number,
): Promise<WorkflowPreview> {
  return requestJson<WorkflowPreview>(
    `/api/workflows/${conversationId}/${workflowId}/confirm`,
    {
      method: 'POST',
      token,
    },
  )
}

// 启动指定工作流的最小执行链路
export async function executeWorkflow(
  token: string,
  conversationId: number,
  workflowId: number,
): Promise<WorkflowPreview> {
  return requestJson<WorkflowPreview>(
    `/api/workflows/${conversationId}/${workflowId}/execute`,
    {
      method: 'POST',
      token,
    },
  )
}
