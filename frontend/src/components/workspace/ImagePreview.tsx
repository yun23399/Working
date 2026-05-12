import type { WorkflowArtifact } from '../../types/workflow'
import { formatArtifactSize, formatArtifactTime } from '../../utils/workflowArtifacts'

interface ImagePreviewProps {
  artifact: WorkflowArtifact
  errorMessage: string | null
  imageUrl: string | null
  isLoading: boolean
}

// 图片预览组件，负责展示设计图、页面截图等图像型产物
export function ImagePreview({
  artifact,
  errorMessage,
  imageUrl,
  isLoading,
}: ImagePreviewProps) {
  return (
    <div className="flex h-full min-h-[280px] flex-col rounded-[20px] border border-line bg-[#fbf8f2] px-5 py-5">
      <div className="border-b border-line pb-3">
        <div className="text-sm font-medium text-ink">{artifact.name}</div>
        <div className="mt-1 text-xs text-ink-faint">
          {formatArtifactSize(artifact.size_bytes)} · 更新于 {formatArtifactTime(artifact.updated_at)}
        </div>
      </div>

      {errorMessage ? (
        <div className="mt-4 rounded-[16px] border border-[#e3c2bf] bg-[#fff5f4] px-4 py-3 text-sm text-[#9b4b46]">
          {errorMessage}
        </div>
      ) : null}

      {isLoading ? (
        <div className="mt-4 rounded-[16px] border border-dashed border-line bg-white/80 px-4 py-4 text-sm text-ink-soft">
          正在加载图片产物...
        </div>
      ) : null}

      {!isLoading && !errorMessage ? (
        <div className="mt-4 min-h-0 flex-1 overflow-auto rounded-[18px] border border-line bg-white p-3">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={artifact.name}
              className="h-full w-full rounded-[14px] object-contain"
            />
          ) : (
            <div className="flex h-full min-h-[220px] items-center justify-center rounded-[14px] bg-[#f7f3eb] px-4 text-sm text-ink-soft">
              当前图片产物暂时无法渲染。
            </div>
          )}
        </div>
      ) : null}
    </div>
  )
}
