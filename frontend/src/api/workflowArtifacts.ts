import { requestBlob, requestJson, requestText } from './client'
import type { WorkflowArtifact } from '../types/workflow'

// 构造工作流产物文件读取地址，统一复用后端受保护路由
function buildWorkflowArtifactFilePath(
  conversationId: number,
  workflowId: number,
  relativePath: string,
): string {
  const params = new URLSearchParams({
    path: relativePath,
  })
  return `/api/workflows/${conversationId}/${workflowId}/artifacts/file?${params.toString()}`
}

// 读取指定工作流的产物列表
export async function fetchWorkflowArtifacts(
  token: string,
  conversationId: number,
  workflowId: number,
): Promise<WorkflowArtifact[]> {
  return requestJson<WorkflowArtifact[]>(`/api/workflows/${conversationId}/${workflowId}/artifacts`, {
    token,
  })
}

// 读取文本型产物内容，供代码和文档预览组件展示
export async function fetchWorkflowArtifactText(
  token: string,
  conversationId: number,
  workflowId: number,
  relativePath: string,
): Promise<string> {
  return requestText(buildWorkflowArtifactFilePath(conversationId, workflowId, relativePath), {
    token,
  })
}

// 读取二进制产物内容，供图片预览组件创建本地对象 URL
export async function fetchWorkflowArtifactBlob(
  token: string,
  conversationId: number,
  workflowId: number,
  relativePath: string,
): Promise<Blob> {
  return requestBlob(buildWorkflowArtifactFilePath(conversationId, workflowId, relativePath), {
    token,
  })
}
