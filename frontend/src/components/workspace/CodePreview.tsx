import type { WorkflowArtifact } from '../../types/workflow'
import { formatArtifactSize, formatArtifactTime } from '../../utils/workflowArtifacts'

interface CodePreviewProps {
  artifact: WorkflowArtifact
  content: string | null
  errorMessage: string | null
  isLoading: boolean
}

// 代码预览组件，负责展示 JSON、脚本和配置类产物的原始内容
export function CodePreview({
  artifact,
  content,
  errorMessage,
  isLoading,
}: CodePreviewProps) {
  return (
    <div className="flex h-full min-h-[280px] flex-col rounded-[20px] border border-line bg-[#161616] px-4 py-4 text-white">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3">
        <div>
          <div className="text-sm font-medium">{artifact.name}</div>
          <div className="mt-1 text-xs text-white/60">
            {formatArtifactSize(artifact.size_bytes)} · 更新于 {formatArtifactTime(artifact.updated_at)}
          </div>
        </div>
        <div className="rounded-full bg-white/10 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-white/70">
          {artifact.mime_type}
        </div>
      </div>

      {errorMessage ? (
        <div className="mt-4 rounded-[16px] border border-[#5e2c2c] bg-[#2e1717] px-4 py-3 text-sm text-[#ffb4b4]">
          {errorMessage}
        </div>
      ) : null}

      {isLoading ? (
        <div className="mt-4 rounded-[16px] border border-white/10 bg-white/5 px-4 py-4 text-sm text-white/70">
          正在读取代码产物内容...
        </div>
      ) : null}

      {!isLoading && !errorMessage ? (
        <pre className="mt-4 min-h-0 flex-1 overflow-auto rounded-[16px] bg-black/30 px-4 py-4 text-xs leading-6 text-white/85">
          <code>{content ?? '当前代码产物没有可展示的文本内容。'}</code>
        </pre>
      ) : null}
    </div>
  )
}
