import { Box, Braces, FileImage, FileText } from 'lucide-react'
import { CodePreview } from './CodePreview'
import { DocumentPreview } from './DocumentPreview'
import { ImagePreview } from './ImagePreview'
import type { WorkflowArtifact, WorkflowPreview } from '../../types/workflow'
import {
  formatArtifactSize,
  formatArtifactTime,
  resolveArtifactTypeLabel,
} from '../../utils/workflowArtifacts'

interface ArtifactPreviewPanelProps {
  artifactListError: string | null
  artifacts: WorkflowArtifact[]
  exportError: string | null
  isExporting: boolean
  isLoadingArtifacts: boolean
  isLoadingPreview: boolean
  previewError: string | null
  previewImageUrl: string | null
  previewText: string | null
  selectedArtifact: WorkflowArtifact | null
  workflow: WorkflowPreview | null
  onExportArtifacts: () => void
  onSelectArtifact: (relativePath: string) => void
}

// 根据产物类型返回对应图标，便于在侧边列表中快速识别
function resolveArtifactIcon(previewType: WorkflowArtifact['preview_type']) {
  if (previewType === 'image') {
    return FileImage
  }

  if (previewType === 'document') {
    return FileText
  }

  if (previewType === 'code') {
    return Braces
  }

  return Box
}

// 工作流产物预览面板，负责展示产物列表并切换不同预览组件
export function ArtifactPreviewPanel({
  artifactListError,
  artifacts,
  exportError,
  isExporting,
  isLoadingArtifacts,
  isLoadingPreview,
  previewError,
  previewImageUrl,
  previewText,
  selectedArtifact,
  workflow,
  onExportArtifacts,
  onSelectArtifact,
}: ArtifactPreviewPanelProps) {
  const hasWorkflow = workflow !== null
  const canExport = hasWorkflow && artifacts.length > 0 && !isExporting

  return (
    <section className="rounded-[20px] border border-line bg-white/85 px-5 py-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-medium text-ink">产物预览</div>
          <div className="mt-1 text-xs text-ink-faint">
            基于当前工作流的真实 `artifacts/` 目录展示代码、文档和图片产物。
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="rounded-full bg-[#f3efe6] px-3 py-1 text-xs text-ink-soft">
            {artifacts.length} 项
          </div>
          <button
            type="button"
            onClick={onExportArtifacts}
            disabled={!canExport}
            className="rounded-full border border-line bg-white px-4 py-2 text-xs font-medium text-ink transition hover:bg-[#f8f5ee] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isExporting ? '正在导出...' : '导出产物'}
          </button>
        </div>
      </div>

      {!hasWorkflow ? (
        <div className="mt-4 rounded-[18px] border border-dashed border-line bg-[#faf7f0] px-4 py-4 text-sm text-ink-soft">
          当前还没有可用工作流。生成并执行工作流后，这里会自动展示共享工作区中的真实产物。
        </div>
      ) : null}

      {hasWorkflow && artifactListError ? (
        <div className="mt-4 rounded-[18px] border border-[#e3c2bf] bg-[#fff5f4] px-4 py-3 text-sm text-[#9b4b46]">
          {artifactListError}
        </div>
      ) : null}

      {hasWorkflow && exportError ? (
        <div className="mt-4 rounded-[18px] border border-[#e3c2bf] bg-[#fff5f4] px-4 py-3 text-sm text-[#9b4b46]">
          {exportError}
        </div>
      ) : null}

      {hasWorkflow && isLoadingArtifacts ? (
        <div className="mt-4 rounded-[18px] border border-dashed border-line bg-[#faf7f0] px-4 py-4 text-sm text-ink-soft">
          正在同步当前工作流的产物列表...
        </div>
      ) : null}

      {hasWorkflow && !isLoadingArtifacts && artifacts.length === 0 ? (
        <div className="mt-4 rounded-[18px] border border-dashed border-line bg-[#faf7f0] px-4 py-4 text-sm text-ink-soft">
          当前工作流还没有生成可预览的产物。开始执行后，文本摘要、截图、设计图和计划文件会在这里出现。
        </div>
      ) : null}

      {hasWorkflow && artifacts.length > 0 ? (
        <div className="mt-4 grid gap-4 xl:grid-cols-[240px_1fr]">
          <div className="max-h-[360px] space-y-2 overflow-y-auto pr-1">
            {artifacts.map((artifact) => {
              const Icon = resolveArtifactIcon(artifact.preview_type)
              const isSelected = selectedArtifact?.relative_path === artifact.relative_path

              return (
                <button
                  key={artifact.relative_path}
                  type="button"
                  onClick={() => onSelectArtifact(artifact.relative_path)}
                  className={`w-full rounded-[18px] border px-4 py-3 text-left transition ${
                    isSelected
                      ? 'border-[#4c6ef5] bg-[#eef2ff]'
                      : 'border-line bg-[#faf7f0] hover:bg-white'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`mt-0.5 rounded-full p-2 ${
                        isSelected ? 'bg-[#dbe4ff] text-[#3950c5]' : 'bg-white text-ink-soft'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm font-medium text-ink">{artifact.name}</div>
                      <div className="mt-1 text-xs text-ink-faint">
                        {resolveArtifactTypeLabel(artifact.preview_type)} ·{' '}
                        {formatArtifactSize(artifact.size_bytes)}
                      </div>
                      <div className="mt-1 text-xs text-ink-faint">
                        {formatArtifactTime(artifact.updated_at)}
                      </div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>

          <div className="min-h-[360px]">
            {selectedArtifact?.preview_type === 'image' ? (
              <ImagePreview
                artifact={selectedArtifact}
                errorMessage={previewError}
                imageUrl={previewImageUrl}
                isLoading={isLoadingPreview}
              />
            ) : null}

            {selectedArtifact?.preview_type === 'code' ? (
              <CodePreview
                artifact={selectedArtifact}
                content={previewText}
                errorMessage={previewError}
                isLoading={isLoadingPreview}
              />
            ) : null}

            {selectedArtifact?.preview_type === 'document' ? (
              <DocumentPreview
                artifact={selectedArtifact}
                content={previewText}
                errorMessage={previewError}
                isLoading={isLoadingPreview}
              />
            ) : null}

            {selectedArtifact?.preview_type === 'binary' ? (
              <div className="flex h-full min-h-[280px] items-center justify-center rounded-[20px] border border-line bg-[#faf7f0] px-6 text-center text-sm leading-7 text-ink-soft">
                当前产物类型暂不支持内联预览。已识别文件：{selectedArtifact.name}（{selectedArtifact.mime_type}）。
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </section>
  )
}
