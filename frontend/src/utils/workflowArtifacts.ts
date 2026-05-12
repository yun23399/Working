import type { WorkflowArtifactPreviewType } from '../types/workflow'

const artifactTypeLabelMap: Record<WorkflowArtifactPreviewType, string> = {
  code: '代码',
  image: '图片',
  document: '文档',
  binary: '二进制',
}

// 将预览类型转换为界面可读的中文标签
export function resolveArtifactTypeLabel(previewType: WorkflowArtifactPreviewType): string {
  return artifactTypeLabelMap[previewType] ?? previewType
}

// 格式化文件大小，便于在产物列表与预览头部展示
export function formatArtifactSize(sizeBytes: number): string {
  if (sizeBytes < 1024) {
    return `${sizeBytes} B`
  }

  if (sizeBytes < 1024 * 1024) {
    return `${(sizeBytes / 1024).toFixed(1)} KB`
  }

  return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`
}

// 格式化产物更新时间，统一聊天页中的时间展示风格
export function formatArtifactTime(updatedAt: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(updatedAt))
}
