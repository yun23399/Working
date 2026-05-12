import { useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ApiRequestError } from '../api/client'
import {
  fetchWorkflowArtifactBlob,
  fetchWorkflowArtifactText,
  fetchWorkflowArtifacts,
} from '../api/workflowArtifacts'
import type { WorkflowArtifact } from '../types/workflow'

interface UseWorkflowArtifactsOptions {
  conversationId: number | null
  workflowId: number | null
  selectedArtifactPath: string | null
  token: string | null
  onUnauthorized: () => void
}

// 将产物接口错误转换为前端可直接提示的文案
function resolveArtifactError(error: unknown): string | null {
  if (error instanceof ApiRequestError) {
    return error.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return null
}

// 判断当前错误是否属于鉴权失效，便于页面统一清理登录态
function isUnauthorizedArtifactError(error: unknown): boolean {
  return error instanceof ApiRequestError && error.status === 401
}

// 在未明确选中文件时优先展示更适合可视化查看的产物
function resolveDefaultArtifact(artifacts: WorkflowArtifact[]): WorkflowArtifact | null {
  const priorityOrder: WorkflowArtifact['preview_type'][] = ['image', 'document', 'code', 'binary']
  for (const previewType of priorityOrder) {
    const matchedArtifact = artifacts.find((artifact) => artifact.preview_type === previewType)
    if (matchedArtifact) {
      return matchedArtifact
    }
  }

  return artifacts[0] ?? null
}

// 统一管理工作流产物列表、文本内容和图片对象 URL 的读取状态
export function useWorkflowArtifacts({
  conversationId,
  workflowId,
  selectedArtifactPath,
  token,
  onUnauthorized,
}: UseWorkflowArtifactsOptions) {
  const hasWorkflowContext =
    token !== null && conversationId !== null && workflowId !== null

  const artifactListQuery = useQuery({
    queryKey: ['workflow-artifacts', conversationId, workflowId],
    queryFn: () =>
      fetchWorkflowArtifacts(
        token as string,
        conversationId as number,
        workflowId as number,
      ),
    enabled: hasWorkflowContext,
  })

  const artifactList = artifactListQuery.data ?? []
  const selectedArtifact =
    artifactList.find((artifact) => artifact.relative_path === selectedArtifactPath) ??
    resolveDefaultArtifact(artifactList)
  const shouldLoadText =
    hasWorkflowContext &&
    selectedArtifact !== null &&
    (selectedArtifact.preview_type === 'code' || selectedArtifact.preview_type === 'document')
  const shouldLoadImage =
    hasWorkflowContext &&
    selectedArtifact !== null &&
    selectedArtifact.preview_type === 'image'

  const artifactTextQuery = useQuery({
    queryKey: [
      'workflow-artifact-text',
      conversationId,
      workflowId,
      selectedArtifact?.relative_path ?? '',
    ],
    queryFn: () =>
      fetchWorkflowArtifactText(
        token as string,
        conversationId as number,
        workflowId as number,
        selectedArtifact?.relative_path ?? '',
      ),
    enabled: shouldLoadText,
  })

  const artifactImageQuery = useQuery({
    queryKey: [
      'workflow-artifact-image',
      conversationId,
      workflowId,
      selectedArtifact?.relative_path ?? '',
    ],
    queryFn: () =>
      fetchWorkflowArtifactBlob(
        token as string,
        conversationId as number,
        workflowId as number,
        selectedArtifact?.relative_path ?? '',
      ),
    enabled: shouldLoadImage,
  })

  const imageObjectUrl = useMemo(() => {
    if (!artifactImageQuery.data) {
      return null
    }

    return URL.createObjectURL(artifactImageQuery.data)
  }, [artifactImageQuery.data])

  useEffect(() => {
    const unauthorizedErrors = [
      artifactListQuery.error,
      artifactTextQuery.error,
      artifactImageQuery.error,
    ]
    if (unauthorizedErrors.some((error) => isUnauthorizedArtifactError(error))) {
      onUnauthorized()
    }
  }, [
    artifactImageQuery.error,
    artifactListQuery.error,
    artifactTextQuery.error,
    onUnauthorized,
  ])

  useEffect(() => {
    return () => {
      if (imageObjectUrl) {
        URL.revokeObjectURL(imageObjectUrl)
      }
    }
  }, [imageObjectUrl])

  return {
    artifacts: artifactList,
    artifactListError: resolveArtifactError(artifactListQuery.error),
    isLoadingArtifacts: artifactListQuery.isLoading,
    isLoadingPreview: artifactTextQuery.isLoading || artifactImageQuery.isLoading,
    previewError:
      resolveArtifactError(artifactTextQuery.error) ??
      resolveArtifactError(artifactImageQuery.error),
    previewText: artifactTextQuery.data ?? null,
    imageObjectUrl,
    selectedArtifact,
  }
}
