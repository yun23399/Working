import type { WorkflowArtifact } from '../../types/workflow'
import { formatArtifactSize, formatArtifactTime } from '../../utils/workflowArtifacts'

interface DocumentPreviewProps {
  artifact: WorkflowArtifact
  content: string | null
  errorMessage: string | null
  isLoading: boolean
}

// 文档预览组件，负责展示 Markdown、TXT 等可直接阅读的文本产物
export function DocumentPreview({
  artifact,
  content,
  errorMessage,
  isLoading,
}: DocumentPreviewProps) {
  return (
    <div className="flex h-full min-h-[280px] flex-col rounded-[20px] border border-line bg-[#fcfbf7] px-5 py-5">
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
        <div className="mt-4 rounded-[16px] border border-dashed border-line bg-[#f7f3eb] px-4 py-4 text-sm text-ink-soft">
          正在读取文档产物内容...
        </div>
      ) : null}

      {!isLoading && !errorMessage ? (
        <div className="mt-4 min-h-0 flex-1 overflow-auto rounded-[18px] border border-line bg-white px-4 py-4">
          <div className="whitespace-pre-wrap text-sm leading-7 text-ink-soft">
            {content ?? '当前文档产物没有可展示的文本内容。'}
          </div>
        </div>
      ) : null}
    </div>
  )
}
